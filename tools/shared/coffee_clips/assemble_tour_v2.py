#!/usr/bin/env python3
"""Join the voiced tour clips, in script order, into Ep3_ActC_tour_v2.mp4 in the main Lyra folder."""
from __future__ import annotations

import subprocess

from gen_tour_v2 import CLIPS, OUT, SHOTS

FINAL = CLIPS.parent.parent / "Ep3_ActC_tour_v2.mp4"


def main() -> None:
    args = ["ffmpeg", "-v", "error", "-y"]
    for sid in SHOTS:
        args += ["-i", str(OUT / "voiced" / f"{sid}.mp4")]
    parts = "".join(
        f"[{i}:v]scale=2528:1440:force_original_aspect_ratio=decrease,pad=2528:1440:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v{i}];"
        f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}];" for i in range(len(SHOTS))
    )
    streams = "".join(f"[v{i}][a{i}]" for i in range(len(SHOTS)))
    args += ["-filter_complex", f"{parts}{streams}concat=n={len(SHOTS)}:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", str(FINAL)]
    subprocess.run(args, check=True)
    print("WROTE", FINAL, flush=True)


if __name__ == "__main__":
    main()
