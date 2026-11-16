#!/usr/bin/env python3
"""Tour v2 rewrite: new first frames for T2 (Solo's hand on the rack) and T5 (Patch stops Solo in the corridor)."""
from __future__ import annotations

import shutil
import sys

from gen_s11a_ots_v10_facelock import load_key, still
from gen_tour import REFS
from gen_tour_v2 import OUT

SHOTS = {
    "T2": ("Image1 shows the EXACT man and hologram woman to keep: same faces, glasses, curls, wavy hair, teal-cyan tint, maroon "
           "t-shirt. Image2 is the server aisle: black racks with blue and green LEDs, perforated raised floor, cable trays. "
           "Three-quarter WIDE shot showing both of them from head to feet, standing on the floor with contact shadows. The racks "
           "are real 2.2 metre cabinets, a little taller than both of them, in correct perspective. One rack door is open at "
           "frame right. Solo stands at it with his palm resting on a server inside, his head turned to Lyra. Lyra stands beside "
           "him at frame left, watching his hand, her cyan glow lighting the rack door and his arm. Neither looks at the camera. "
           "Exactly one of each. No text, no collage.",
           lambda: [OUT / "T3_first.jpg", REFS / "pb8_server_aisle.png"]),
    "T5": ("Image1 shows the EXACT man, hologram woman and dog to keep: same faces, glasses, curls, maroon t-shirt, teal-cyan tint, "
           "white pit bull with grey eye patch and glowing cyan collar. Image2 is the plain grey concrete corridor with cyan LED "
           "strips. Low camera in that corridor. Solo crouches at frame right, face clearly visible, tense, looking down at Patch. "
           "Patch stands center foreground, three-quarter to camera with the eye patch clearly visible, pushing his head into "
           "Solo's hand. Far behind them, several steps back and small in frame, Lyra stands alone on the corridor floor with her "
           "whole body visible, watching and keeping her distance. No dog bed, no monitors. Exactly one of each. No text, no collage.",
           lambda: [OUT / "T5_first_closeup.jpg", OUT / "T1_first.jpg"]),
}


def main() -> None:
    key = load_key()
    shutil.copy2(OUT / "T5_first.jpg", OUT / "T5_first_closeup.jpg")
    for sid in sys.argv[1:] or SHOTS:
        prompt, refs = SHOTS[sid]
        still(key, prompt, refs(), OUT / f"{sid}_first.jpg")


if __name__ == "__main__":
    main()
