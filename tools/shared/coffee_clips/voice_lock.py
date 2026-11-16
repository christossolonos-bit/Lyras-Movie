#!/usr/bin/env python3
"""Keep one voice per character: convert each line of a tour clip to that character's reference voice, same timing.

  python voice_lock.py refs
  python voice_lock.py T4b T1 ...   # writes tour_v2/voiced/<id>.mp4
"""
from __future__ import annotations

import difflib
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
import torch
import torchaudio
from chatterbox.vc import ChatterboxVC
from faster_whisper import WhisperModel

from gen_tour_v2 import CLIPS, OUT, SHOTS

VOICED = OUT / "voiced"
WORK = VOICED / "work"
REF = {"LYRA": WORK / "ref_lyra.wav", "SOLO": WORK / "ref_solo.wav"}
SOURCE = {"LYRA": (CLIPS / "S11a_ots_lyra_door_v12_h3.mp4", 0, 8), "SOLO": (CLIPS.parent / "lyra-refs" / "solo_voice_ref.wav", 0, 15)}
SR = 24000
AMBIENCE_DB = -18


def run(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def make_refs() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    for who, (src, start, dur) in SOURCE.items():
        run("-ss", str(start), "-t", str(dur), "-i", str(src), "-vn", "-ac", "1", "-ar", str(SR), str(REF[who]))
        print("REF", who, REF[who].name, flush=True)


def line_spans(wav, lines, model) -> list[tuple[str, float, float]]:
    segs, _ = model.transcribe(str(wav), language="en", word_timestamps=True)
    heard = [w for s in segs for w in (s.words or [])]
    heard_norm = [(words(w.word) or [""])[0] for w in heard]
    script, owner = [], []
    for i, (who, _how, text) in enumerate(lines):
        for w in words(text):
            script.append(w)
            owner.append(i)
    first, last = [None] * len(lines), [None] * len(lines)
    match = difflib.SequenceMatcher(None, script, heard_norm, autojunk=False)
    for block in match.get_matching_blocks():
        for k in range(block.size):
            i = owner[block.a + k]
            if first[i] is None:
                first[i] = heard[block.b + k].start
            last[i] = heard[block.b + k].end
    for i, value in enumerate(first):
        if value is None:
            raise SystemExit(f"line not found in audio: {lines[i][2]}")
    duration = sf.info(str(wav)).duration
    cuts = [0.0] + [(last[i] + first[i + 1]) / 2 for i in range(len(lines) - 1)] + [duration]
    return [(lines[i][0], cuts[i], cuts[i + 1]) for i in range(len(lines))]


def process(sid: str, vc: ChatterboxVC, model: WhisperModel) -> None:
    clip = OUT / f"{sid}_new.mp4" if (OUT / f"{sid}_new.mp4").exists() else OUT / f"{sid}.mp4"
    VOICED.mkdir(exist_ok=True)
    if not SHOTS[sid]["audio"]:
        run("-i", str(clip), "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
            "-af", "loudnorm=I=-30:TP=-6:LRA=7", str(VOICED / f"{sid}.mp4"))
        print("DONE", sid, flush=True)
        return
    wav = WORK / f"{sid}.wav"
    run("-i", str(clip), "-vn", "-ac", "1", "-ar", str(SR), str(wav))
    audio, _ = sf.read(str(wav))
    out = np.zeros_like(audio)
    for n, (who, start, end) in enumerate(line_spans(wav, SHOTS[sid]["audio"], model)):
        a, b = int(start * SR), int(end * SR)
        if who == "MUTE":
            audio[a:b] = 0
            continue
        part = WORK / f"{sid}_{n}.wav"
        sf.write(str(part), audio[a:b], SR)
        converted = vc.generate(str(part), target_voice_path=str(REF[who]))
        conv = torchaudio.functional.resample(converted, vc.sr, SR).squeeze().cpu().numpy()
        conv = np.pad(conv, (0, max(0, b - a - len(conv))))[: b - a]
        peak = max(np.abs(audio[a:b]).max(), 1e-4)
        out[a:b] = conv * min(peak / max(np.abs(conv).max(), 1e-4), 4.0)
        print(f"{sid} {who} {start:.2f}-{end:.2f}", flush=True)
    mix = np.clip(out + audio * 10 ** (AMBIENCE_DB / 20), -1, 1)
    fixed = WORK / f"{sid}_voiced.wav"
    sf.write(str(fixed), mix, SR)
    VOICED.mkdir(exist_ok=True)
    run("-i", str(clip), "-i", str(fixed), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", str(VOICED / f"{sid}.mp4"))
    print("DONE", sid, flush=True)


def main() -> None:
    make_refs()
    if sys.argv[1:] == ["refs"]:
        return
    device = "cuda" if torch.cuda.is_available() else "cpu"
    vc = ChatterboxVC.from_pretrained(device)
    model = WhisperModel("small", compute_type="int8")
    for sid in sys.argv[1:]:
        process(sid, vc, model)


if __name__ == "__main__":
    main()
