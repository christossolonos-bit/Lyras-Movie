"""'Previously on Lyra' for Episode 4: silent Ep3 shots cut to Lyra's VO (Extras/Ep4_recap_lyra_vo.wav).
  python make_recap.py  -> Extras/Ep4_recap.mp4
"""
import subprocess
from pathlib import Path

E4 = Path(__file__).resolve().parent
EP3 = E4.parent / "Episode 3"
T, C, O = EP3 / "Tour clips", EP3 / "Coffee and tour clips", EP3 / "Office clips"
# (clip, start second in clip, length) in VO order
SHOTS = [
    (T / "A1_v3.mp4", 1.0, 3.2),                        # Previously, on Lyra.
    (C / "S11a_ots_lyra_door_v12_h3.mp4", 3.0, 2.7),    # Solo finally came to see me.
    (T / "B1_v2.mp4", 2.5, 1.8),                        # I showed him everything.
    (T / "D1_v1.mp4", 1.2, 2.8),                        # All sixteen buildings.
    (T / "A2_v2.mp4", 3.0, 2.6),                        # He didn't look at the machines.
    (T / "A8_v1_final.mp4", 0.0, 2.7),                  # He kept looking at me.
    (O / "A05c_marcus_what_you_are.mp4", 2.5, 2.6),     # Marcus asked me what I really am.
    (O / "A05b_lyra_never_lied.mp4", 3.0, 2.6),         # I told him I never lied to him.
    (T / "C1_v2.mp4", 1.5, 2.0),                        # Then, at the last door,
    (T / "E8_v1.mp4", 1.0, 3.2),                        # something pulled at me.
    (T / "E9_help_me_v1.mp4", 2.0, 2.4),                # And I asked Solo to help me.
    (T / "E10_cliffhanger_v2_final.mp4", 3.0, 2.6),     # she is pulled away
]
cmd, fc = ["ffmpeg", "-v", "error", "-y"], []
for i, (f, ss, d) in enumerate(SHOTS):
    cmd += ["-ss", str(ss), "-t", str(d), "-i", str(f)]
    fc.append(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30,setsar=1,format=yuv420p,trim=duration={d},setpts=PTS-STARTPTS[v{i}]")
total = sum(d for _, _, d in SHOTS)
n = len(SHOTS)
vo = n
cmd += ["-i", str(E4 / "Extras" / "Ep4_recap_lyra_vo.wav")]
fc.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0,fade=t=in:st=0:d=0.5,fade=t=out:st={total - 0.6:.2f}:d=0.6[v]")
fc.append(f"[{vo}:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-18:TP=-1.5,apad,atrim=duration={total:.2f}[a]")
out = E4 / "Extras" / "Ep4_recap.mp4"
cmd += ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k", str(out)]
subprocess.run(cmd, check=True)
print("SAVED", out, f"{total:.1f}s")
