"""Convert one speaker's line in a clip to their voice reference (Chatterbox VC, free, local). Keeps timing and the background.
  python voice_fix.py Clips/A2_v1.mp4 solo_voice_ref.wav

Demucs splits the clip's sound into voice and background first. Only the voice is converted; the background
(engine, room tone, footsteps) plays on untouched underneath, so nothing drops out while someone talks.
"""
import os, subprocess, sys
import numpy as np, soundfile as sf
from chatterbox.vc import ChatterboxVC
from faster_whisper import WhisperModel
from pathlib import Path

clip, ref = Path(sys.argv[1]), Path(__file__).resolve().parent.parent / "assets" / "lyra-refs" / sys.argv[2]
work = clip.parent / "voice_work"; work.mkdir(exist_ok=True)
SR = 24000


def mono(path: Path) -> np.ndarray:
    out = work / f"{path.stem}_24k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), str(out)], check=True)
    return sf.read(out)[0]


# 1. split voice from background
full = work / f"{clip.stem}_full.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-vn", "-ac", "2", "-ar", "44100", str(full)], check=True)
subprocess.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-n", "htdemucs", "-o", str(work), str(full)],
               check=True, capture_output=True)
stems = work / "htdemucs" / full.stem
voice, bed = mono(stems / "vocals.wav"), mono(stems / "no_vocals.wav")
n = min(len(voice), len(bed)); voice, bed = voice[:n], bed[:n]

# 2. find the line on the voice stem
vwav = work / f"{clip.stem}_vocals.wav"; sf.write(vwav, voice, SR)
words = [w for s in WhisperModel("small.en", device=os.environ.get("WHISPER_DEVICE", "cuda"), compute_type="float16" if os.environ.get("WHISPER_DEVICE", "cuda") == "cuda" else "int8").transcribe(str(vwav), word_timestamps=True)[0] for w in s.words]
a, b = max(0, words[0].start - 0.15), min(n / SR, words[-1].end + 0.25)
seg = voice[int(a * SR):int(b * SR)]
sf.write(work / f"{clip.stem}_line.wav", seg, SR)

# 3. convert only the voice, same length and loudness
vc = ChatterboxVC.from_pretrained("cuda")
out = vc.generate(str(work / f"{clip.stem}_line.wav"), target_voice_path=str(ref)).squeeze().cpu().numpy()
out = np.interp(np.linspace(0, len(out), len(seg)), np.arange(len(out)), out)
out *= (np.sqrt((seg ** 2).mean()) + 1e-9) / (np.sqrt((out ** 2).mean()) + 1e-9)
fade = int(0.03 * SR); ramp = np.linspace(0, 1, fade)
new_voice = voice.copy()
body = out.copy(); body[:fade] *= ramp; body[-fade:] *= ramp[::-1]
edge = seg.copy(); edge[fade:-fade] = 0; edge[:fade] *= ramp[::-1]; edge[-fade:] *= ramp
new_voice[int(a * SR):int(a * SR) + len(seg)] = body + edge

# 4. voice back over the untouched background
mixed = new_voice + bed
peak = np.abs(mixed).max()
if peak > 0.98:
    mixed *= 0.98 / peak
sf.write(work / f"{clip.stem}_voiced.wav", mixed, SR)
dst = clip.with_name(f"{clip.stem}_voiced.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-i", str(work / f"{clip.stem}_voiced.wav"), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(dst)], check=True)
print("VOICED", dst, f"line {a:.2f}-{b:.2f}s:", " ".join(w.word.strip() for w in words))
