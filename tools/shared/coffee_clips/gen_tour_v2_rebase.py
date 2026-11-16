#!/usr/bin/env python3
"""Tour v2: rebuild T2 and T3 first frames from T1's approved faces on their own sets."""
from __future__ import annotations

import shutil
import sys

from gen_s11a_ots_v10_facelock import load_key, still
from gen_tour import REFS
from gen_tour_v2 import OUT

BASE = (
    "Image1 shows the EXACT two people and the look to keep: same man, same glasses and curly hair, same hologram woman, "
    "same face and wavy hair, whole figure teal-cyan with fine scanlines, same size relationship. Move them to the set in "
    "Image2, ignoring anyone in Image2. Both are equal in size, framed waist-up, side by side, with faces large and sharp. "
    "The woman is at frame left and the man at frame right. Neither looks at the camera. Exactly one of each. No text, no collage. "
)
SHOTS = {
    "T2": ("Server aisle, walking toward camera mid-stride. Her head is turned to him with a shy smile; he glances up at the racks.",
           REFS / "pb8_server_aisle.png"),
    "T3": ("Vast processor hall, stopped in the central aisle, three-quarter to camera and facing each other. His smile has faded.",
           REFS / "c1_processors.png"),
    "T6": ("Completely replace the background of Image1 with the outdoor rooftop of Image2: no server racks, ceiling or screens "
           "remain. Golden-hour sky, cooling fans, steam and the flat steel grating walkway. Warm sunlight on both of them; her "
           "cyan glow is fainter outdoors.",
           OUT / "plates" / "old_T6_1.jpg"),
}


def main() -> None:
    key = load_key()
    for sid in sys.argv[1:] or SHOTS:
        text, plate = SHOTS[sid]
        shutil.copy2(OUT / f"{sid}_first.jpg", OUT / f"{sid}_rebase_src.jpg")
        still(key, BASE + text + " His face is three-quarter toward camera, well lit by the rack LEDs, with no beard or moustache.",
              [OUT / ("T3_first.jpg" if sid == "T6" else "T4a_first.jpg"), plate], OUT / f"{sid}_first.jpg")


if __name__ == "__main__":
    main()
