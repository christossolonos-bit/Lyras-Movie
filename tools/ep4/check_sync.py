"""Lip-sync check: for each piece of a joined film, find where its PICTURE and its SOUND actually land and report the gap.
  python check_sync.py <joined.mp4> <piece1.mp4> <piece2.mp4> ...   (pieces in order; probes several points per piece)
A positive gap means the sound is early (lips after the sound).
"""
import subprocess, sys
import numpy as np

SR, FPS = 8000, 30


def audio(f, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.3f}"] if ss is not None else []) + ["-i", f] + (["-t", f"{t:.3f}"] if t else [])
    return np.frombuffer(subprocess.run(cmd + ["-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)


def frames(f, ss, t):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-i", f, "-t", f"{t:.3f}", "-vf", f"fps={FPS},scale=64:36,format=gray", "-f", "rawvideo", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(-1, 36, 64).astype(np.float32)


def vdur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", f],
                                capture_output=True, text=True).stdout)


joined, pieces = sys.argv[1], sys.argv[2:]
full_a = audio(joined)
pos, worst = 0.0, 0.0
for p in pieces:
    d = vdur(p)
    for frac in (0.25, 0.5, 0.8):
        m = d * frac
        ref_v = frames(p, m, 1.0)
        win_v = frames(joined, max(0, pos + m - 3), 7)
        errs = [np.mean((win_v[k:k + len(ref_v)] - ref_v) ** 2) for k in range(len(win_v) - len(ref_v))]
        vt = max(0, pos + m - 3) + int(np.argmin(errs)) / FPS
        ref_a = audio(p, m, 2.0)
        if np.abs(ref_a).max() < 1e-3:
            continue
        lo = int(max(0, vt - 3) * SR)
        seg = full_a[lo:lo + int(8 * SR)]
        c = np.correlate(seg, ref_a, "valid")
        at = lo / SR + int(np.argmax(c)) / SR
        gap = vt - at
        worst = max(worst, abs(gap))
        print(f"{p.split('/')[-1]:32s} @{m:6.2f}s  picture {vt:7.2f}  sound {at:7.2f}  sound early by {gap:+.3f}s")
    pos = vt - m + d  # carry the measured picture position forward
print(f"WORST {worst:.3f}s")
