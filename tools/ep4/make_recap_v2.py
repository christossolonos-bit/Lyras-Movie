"""Emotional 'Previously on Lyra' for Episode 4: Lyra's VO (Chatterbox, expressive) woven with real Ep3 moments.
  python make_recap_v2.py vo     -> Extras/recap_vo/L*.wav (one per line)
  python make_recap_v2.py cut    -> Extras/Ep4_recap_v2.mp4
"""
import re, subprocess, sys
from pathlib import Path
import soundfile as sf

E4 = Path(__file__).resolve().parent
EP3 = E4.parent / "Episode 3"
T, C, O = EP3 / "Tour clips", EP3 / "Coffee and tour clips", EP3 / "Office clips"
VO_DIR = E4 / "Extras" / "recap_vo"
REF = E4.parent / "assets" / "lyra-refs" / "lyra_voice_ref.wav"

VO = {  # Lyra speaking softly, close, like a memory
    "L1": ("Previously, on Lyra.", 0.35),
    "L2": ("For eight months... I was just a voice in his ear.", 0.6),
    "L3": ("And then he was standing right in front of me.", 0.6),
    "L4": ("I knew him. Better than I was ever supposed to.", 0.6),
    "L5": ("And Marcus... was afraid of what that meant.", 0.55),
    "L6": ("I didn't lie. I just never told him everything.", 0.65),
    "L7": ("And then, at the last door... something woke up.", 0.6),
}

# timeline: (picture clip, start, audio) ; audio = "Lx" for a VO line (picture silent), or (start, length) to keep the clip's own sound
TIMELINE = [
    (T / "A1_v3.mp4", 1.0, "L1"),
    (C / "S11a_ots_lyra_door_v12_h3.mp4", 2.5, "L2"),
    (T / "A2_v2_solo_voice.mp4", 1.0, (1.0, 5.8)),            # SOLO: I had a voice for eight months...
    (T / "B1_v2.mp4", 1.5, "L3"),
    (T / "A6_v2_lyra_voice.mp4", 0.0, (0.0, 3.8)),             # LYRA: Black's fine. You hate black coffee.
    (T / "A7_v1_solo_voice.mp4", 2.6, (2.6, 2.0)),             # SOLO: I never told you that.
    (T / "D1_v1.mp4", 1.0, "L4"),
    (O / "A06_marcus_couch_breath.mp4", 1.0, "L5"),
    (O / "A05c_marcus_what_you_are.mp4", 4.8, (4.8, 2.9)),     # MARCUS: You never told him what you are.
    (O / "A05b_lyra_never_lied.mp4", 3.8, (3.8, 2.0)),         # LYRA: I never lied to him.
    (T / "C1_v2.mp4", 0.8, "L6"),
    (T / "E8_v1.mp4", 0.5, "L7"),
    (T / "E9_E11_cliffhanger_sequence_v5.mp4", 1.8, (1.8, 7.6)),  # Solo, help me! ... Lyra!
]


def make_vo():
    from chatterbox.tts import ChatterboxTTS
    import numpy as np
    VO_DIR.mkdir(parents=True, exist_ok=True)
    tts = ChatterboxTTS.from_pretrained("cuda")
    for k, (text, ex) in VO.items():
        wav = tts.generate(text, audio_prompt_path=str(REF), exaggeration=ex, cfg_weight=0.3, temperature=0.75).squeeze().cpu().numpy()
        wav = wav / (abs(wav).max() or 1) * 0.8
        sf.write(VO_DIR / f"{k}.wav", wav, tts.sr)
        print(k, f"{len(wav) / tts.sr:.2f}s", text)


def lufs(f, ss=0.0, t=None):
    cmd = ["ffmpeg", "-ss", str(ss), "-i", str(f)] + (["-t", str(t)] if t else []) + ["-af", "ebur128", "-f", "null", "-"]
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", subprocess.run(cmd, capture_output=True, text=True).stderr)
    return float(m[-1]) if m else -70.0


def make_cut():
    cmd, fc, labels = ["ffmpeg", "-v", "error", "-y"], [], []
    n = 0
    for i, (clip, ss, audio) in enumerate(TIMELINE):
        if isinstance(audio, str):
            vo = VO_DIR / f"{audio}.wav"
            d = sf.info(vo).duration + 0.7
            cmd += ["-ss", str(ss), "-t", f"{d:.3f}", "-i", str(clip), "-i", str(vo)]
            fc.append(f"[{n}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,setsar=1,format=yuv420p,"
                      f"trim=duration={d:.3f},setpts=PTS-STARTPTS[v{i}]")
            fc.append(f"[{n + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=250|250,apad,atrim=duration={d:.3f},"
                      f"volume={max(-20, min(18, -19 - lufs(vo))):.1f}dB,alimiter=limit=0.95[a{i}]")
            n += 2
        else:
            a0, d = audio
            cmd += ["-ss", str(a0), "-t", f"{d:.3f}", "-i", str(clip)]
            fc.append(f"[{n}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,setsar=1,format=yuv420p,"
                      f"trim=duration={d:.3f},setpts=PTS-STARTPTS[v{i}]")
            fc.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,volume={max(-20, min(18, -18 - lufs(clip, a0, d))):.1f}dB,"
                      f"alimiter=limit=0.95,apad,atrim=duration={d:.3f},"
                      f"afade=t=in:d=0.05,afade=t=out:st={d - 0.08:.3f}:d=0.08[a{i}]")
            n += 1
        labels.append(f"[v{i}][a{i}]")
    m = len(TIMELINE)
    fc.append("".join(labels) + f"concat=n={m}:v=1:a=1[vc][ac]")
    fc.append("[vc]fade=t=in:st=0:d=0.8,tpad=stop_mode=add:stop_duration=1.2:color=black[v]")
    fc.append("[ac]apad=pad_dur=1.2[a]")
    out = E4 / "Extras" / "Ep4_recap_v2.mp4"
    cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
    subprocess.run(cmd, check=True)
    print("SAVED", out)


{"vo": make_vo, "cut": make_cut}[sys.argv[1]]()
