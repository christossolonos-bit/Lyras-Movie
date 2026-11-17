"""Join the section previews A-I into one rough cut with transitions between sections (hard cuts stay inside sections).
  python make_rough_cut.py
"""
import subprocess
from pathlib import Path

E4 = Path(__file__).resolve().parent
SECTIONS = list("ABCDEFGHI")
# transition INTO each section after A: (xfade type, seconds)
TRANS = {
    "B": ("fadeblack", 0.6),   # cold open -> Marcus's office: new place
    "C": ("fadeblack", 0.5),   # Marcus -> the women, same second elsewhere
    "D": ("dissolve", 0.5),    # they run -> they arrive at the office
    "E": ("fadeblack", 0.6),   # calls -> out to the desert night
    "F": ("dissolve", 0.6),    # rover inbound -> the search begins
    "G": ("dissolve", 0.5),    # Patch leads -> Solo found
    "H": ("dissolve", 0.5),    # found -> James arrives
    "I": ("fadeblack", 0.7),   # inside the room -> the restart
}
END_FADE = 1.8

files = [E4 / f"Ep4_section_{s}_preview.mp4" for s in SECTIONS]
# picture length of each section (the sound is placed to match the picture, never chained, so it cannot drift)
durs = [float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(f)],
                             capture_output=True, text=True).stdout) for f in files]
fc = []
for i in range(len(files)):
    fc.append(f"[{i}:v]scale=1920:1080,fps=30,setsar=1,format=yuv420p,settb=AVTB[v{i}];"
              f"[{i}:a]aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
starts = [0.0]
vprev, t = "v0", durs[0]
for i, s_ in enumerate(SECTIONS[1:], start=1):
    kind, d = TRANS[s_]
    off = t - d
    starts.append(off)
    fc.append(f"[{vprev}][v{i}]xfade=transition={kind}:duration={d}:offset={off:.3f}[vx{i}]")
    vprev, t = f"vx{i}", off + durs[i]
mix = []
for i, s_ in enumerate(SECTIONS):
    d_in = TRANS[s_][1] if i > 0 else 0.0
    d_out = TRANS[SECTIONS[i + 1]][1] if i + 1 < len(SECTIONS) else 0.0
    ms = int(round(starts[i] * 1000))
    chain = f"[a{i}]atrim=duration={durs[i]:.3f},asetpts=PTS-STARTPTS"
    if d_in:
        chain += f",afade=t=in:d={d_in}"
    if d_out:
        chain += f",afade=t=out:st={durs[i] - d_out:.3f}:d={d_out}"
    fc.append(chain + f",adelay={ms}|{ms}[am{i}]")
    mix.append(f"[am{i}]")
fc.append("".join(mix) + f"amix=inputs={len(SECTIONS)}:normalize=0:duration=longest[amx]")
fc.append(f"[{vprev}]tpad=stop_mode=add:stop_duration=1.5:color=black,fade=t=out:st={t - END_FADE + 0.6:.3f}:d={END_FADE}[v]")
fc.append(f"[amx]apad,atrim=duration={t + 1.5:.3f},afade=t=out:st={t - END_FADE + 0.6:.3f}:d={END_FADE}[a]")
out = E4 / "Ep4_rough_cut_v3.mp4"
cmd = ["ffmpeg", "-v", "error", "-y"]
for f in files:
    cmd += ["-i", str(f)]
cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{t + 1.5:.3f}", str(out)]
subprocess.run(cmd, check=True)
print("SAVED", out, f"{t + 1.5:.1f}s")
