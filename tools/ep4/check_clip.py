"""Free checks on a clip: contact sheet, loudness, hard cuts, speech, and stray cyan per second.
  python check_clip.py Clips/F5_v1.mp4
"""
import subprocess, sys, re
from pathlib import Path
import numpy as np
from PIL import Image

f = Path(sys.argv[1]); E4 = Path(__file__).resolve().parent
sheet = E4 / "Frames" / f"{f.stem}_sheet.png"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-vf", "fps=2,scale=480:-1,tile=6x2", "-frames:v", "1", str(sheet)], check=True)
lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", subprocess.run(["ffmpeg", "-i", str(f), "-af", "ebur128", "-f", "null", "-"],
                                                         capture_output=True, text=True).stderr)
cuts = subprocess.run(["ffmpeg", "-i", str(f), "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-"], capture_output=True, text=True).stderr.count("pts_time")
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vf", "fps=1,scale=320:180", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 180, 320, 3).astype(int)
cyan = [round(100 * ((np.minimum(x[..., 1], x[..., 2]) - x[..., 0] > 25) & (x[..., 2] > 60)).mean(), 2) for x in fr]
from faster_whisper import WhisperModel
segs, _ = WhisperModel("small.en", device="cuda", compute_type="float16").transcribe(str(f), vad_filter=True)
print(f"{f.name}: loudness {lufs[-1] if lufs else '?'} LUFS, cuts {cuts}, cyan % per second {cyan}")
print("SPEECH:", " ".join(s.text for s in segs) or "none")
print("SHEET", sheet)
