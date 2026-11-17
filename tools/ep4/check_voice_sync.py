"""Does a voiced clip keep the original's lip timing? Compares the speech loudness shape of the original take and the
voiced take window by window and reports the lag (positive = voiced speech comes EARLY = lips after sound).
  python check_voice_sync.py D4_v1 [H2_v1 ...]     (names without _voiced / .mp4)
"""
import subprocess, sys
import numpy as np

SR, HOP = 16000, 160  # 10 ms envelope


def env(f):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-vn", "-ac", "1", "-ar", str(SR), "-af", "highpass=f=150,lowpass=f=3500",
                                      "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    n = len(a) // HOP
    e = np.sqrt((a[:n * HOP].reshape(n, HOP) ** 2).mean(1))
    return np.log(e + 1e-4)


worst_all = 0.0
for name in sys.argv[1:]:
    o, v = env(f"Clips/{name}.mp4"), env(f"Clips/{name}_voiced.mp4")
    n = min(len(o), len(v))
    o, v = o[:n], v[:n]
    lags = []
    for s in range(0, n - 150, 50):  # 1.5 s windows every 0.5 s
        wo = o[s:s + 150]
        if wo.max() - np.median(o) < 2.0:  # skip windows without speech
            continue
        best, bl = -1e9, 0
        for L in range(-60, 61):  # +-0.6 s
            if s + L < 0 or s + L + 150 > n:
                continue
            wv = v[s + L:s + L + 150]
            c = np.corrcoef(wo, wv)[0, 1]
            if c > best:
                best, bl = c, L
        if best > 0.5:
            lags.append((s / 100, -bl / 100))
    worst = max((abs(l) for _, l in lags), default=0.0)
    worst_all = max(worst_all, worst)
    print(f"{name:14s} worst {worst:+.2f}s  " + " ".join(f"{t:.1f}:{l:+.2f}" for t, l in lags))
print(f"WORST {worst_all:.2f}s")
