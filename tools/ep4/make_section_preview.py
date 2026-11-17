"""Section previews with locked lip sync: each clip's sound is cut/padded to exactly its picture length,
and levelled with a plain gain (no loudnorm, which shifts timing).
  python make_section_preview.py E F G H I
"""
import re, subprocess, sys
from pathlib import Path

E4 = Path(__file__).resolve().parent
CL = E4 / "Clips"
SECTIONS = {
    "E": "E1_v2 E2_v2 E3_v1_voiced",
    "F": "F1_v1 F2_v2_voiced F3_v1_nocyan F4_v1_voiced F5_v1 F6_v1_voiced F7_v1_voiced F8_v1 F9_v1_voiced F10_v1 F11_v1_voiced F12_v1",
    "G": "G1_v1 G2_v1_voiced G3_v1_voiced",
    "H": "H1_v1 H2_v1_voiced H3_v1 H4_v1_voiced H5_v1_voiced H6_v1_voiced H7_v1_voiced H8_v1 H9_v1 H10_v1_voiced H11_v2_voiced",
    "I": "I1_v2_voiced I2_v1_voiced I3_v2_voiced I4_v1 I5_v1 I6_v1_voiced I7_v2_fixed I8_v1_voiced I9_v1_voiced I10_v1_cyan I11_v1",
}
TARGET, MAX_UP = -20.0, 18.0


def vdur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout)


def lufs(f):
    err = subprocess.run(["ffmpeg", "-i", str(f), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    return float(m[-1]) if m else -70.0


for sec in sys.argv[1:]:
    clips = [CL / f"{c}.mp4" for c in SECTIONS[sec].split()]
    cmd, fc, lab = ["ffmpeg", "-v", "error", "-y"], [], ""
    for i, c in enumerate(clips):
        d = vdur(c)
        gain = max(-20.0, min(MAX_UP, TARGET - lufs(c)))
        cmd += ["-i", str(c)]
        fc.append(f"[{i}:v]scale=1920:1080,fps=30,setsar=1,format=yuv420p,trim=duration={d:.4f},setpts=PTS-STARTPTS[v{i}]")
        fc.append(f"[{i}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                  f"volume={gain:.1f}dB,alimiter=limit=0.95,apad,atrim=duration={d:.4f}[a{i}]")
        lab += f"[v{i}][a{i}]"
    fc.append(lab + f"concat=n={len(clips)}:v=1:a=1[v][a]")
    out = E4 / f"Ep4_section_{sec}_preview.mp4"
    subprocess.run(cmd + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                          "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(out)], check=True)
    print("SAVED", out.name, f"{vdur(out):.2f}s")
