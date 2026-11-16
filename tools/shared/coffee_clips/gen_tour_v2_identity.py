#!/usr/bin/env python3
"""Tour v2: lock Solo and Lyra to one identity on first frames, using Solo's coffee-scene face and Lyra's T4b frame.

  python gen_tour_v2_identity.py T1 T2 T3 T6
"""
from __future__ import annotations

import shutil
import subprocess
import sys

from PIL import Image

from gen_s11a_ots_v10_facelock import CLIPS, load_key, still
from gen_tour_v2 import OUT

SOLO_REF = OUT / "ref_solo_coffee.jpg"
LYRA_REF = OUT / "ref_lyra_t4b.jpg"

PROMPT = (
    "Output the same single photograph as Image1 with the same framing, set, lighting, pose and clothes. "
    "Only change the two faces and hair. The man becomes the EXACT man in Image2: same wide face, heavy dark brows, "
    "nose, short tight dark curls of the same height, thin metal-frame glasses, same age and slim build. "
    "The hologram woman becomes the EXACT woman in Image3: same face, same long wavy hair, same teal-cyan tint over her "
    "whole figure with fine scanlines. Keep their head angles and eyelines from Image1. Neither looks at the camera. "
    "No text, no collage, no extra panels."
)


def refs() -> None:
    frame = OUT / "qa" / "solo_coffee_frame.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2", "-i", str(CLIPS / "S10_nova_ots_solo_face_v2.mp4"),
                    "-frames:v", "1", "-q:v", "2", str(frame)])
    im = Image.open(frame).convert("RGB")
    w, h = im.size
    im.crop((int(w * 0.45), 0, w, h)).save(SOLO_REF, quality=95)
    lyra = Image.open(OUT / "T4b_first.jpg").convert("RGB")
    w, h = lyra.size
    lyra.crop((0, 0, int(w * 0.55), h)).save(LYRA_REF, quality=95)


SOLO_ONLY = (
    "Output the same single photograph as Image1 with the same framing, set, pose and lighting. The hologram woman does not "
    "change. Only the man's head changes: he becomes the EXACT man in Image2, same wide face, heavy dark brows, nose, short "
    "tight dark curls, thin metal-frame glasses, same age. His face is clearly visible and softly lit by the room, with his "
    "head angle unchanged. No text, no collage."
)


def main() -> None:
    refs()
    key = load_key()
    if sys.argv[1] == "solo":
        for sid in sys.argv[2:]:
            src = OUT / f"{sid}_solo_src.jpg"
            shutil.copy2(OUT / f"{sid}_first.jpg", src)
            still(key, SOLO_ONLY, [src, SOLO_REF], OUT / f"{sid}_first.jpg")
        return
    for sid in sys.argv[1:]:
        src = OUT / f"{sid}_identity_src.jpg"
        shutil.copy2(OUT / f"{sid}_first.jpg", src)
        still(key, PROMPT, [src, SOLO_REF, LYRA_REF], OUT / f"{sid}_first.jpg")


if __name__ == "__main__":
    main()
