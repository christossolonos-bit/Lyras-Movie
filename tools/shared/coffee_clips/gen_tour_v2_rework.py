#!/usr/bin/env python3
"""Tour v2: rework T5 (close, Patch's eye patch visible) and T8 (Act A office, real eye contact with Marcus)."""
from __future__ import annotations

import shutil
import sys

from gen_s11a_ots_v10_facelock import load_key, still
from gen_tour import REFS
from gen_tour_v2 import DOG, MARCUS, OUT

SHOTS = {
    "T5": ("Image1 shows the EXACT man and hologram woman to keep: same faces, glasses, curls, wavy hair and teal-cyan tint. Image2 is "
           "Patch, the white pit bull: keep his grey patch around one eye and add a glowing cyan collar. Image3 is the room: the "
           "dark ops room with curved blue monitors. Close, low camera at dog height, framed so all three faces are large. Patch "
           "is in the center foreground facing three-quarter toward camera with the grey eye patch clearly visible, his head "
           "pushing up into Solo's hand. Solo crouches at frame right with his face clearly visible, looking down at the dog, "
           "subdued. Lyra crouches at frame left, close to them, watching the dog with a careful smile, her eyes off camera. "
           "A grey dog bed behind Patch. No platform in frame. Exactly one of each. No text, no collage.",
           lambda: [OUT / "T3_first.jpg", DOG, REFS / "lh1_ops_wake.png"]),
    "T8": ("Image1 shows the EXACT man and hologram woman to keep. Image2 is Marcus's dark command office: long lit desk, wall "
           "data screens with a glowing map, warm strip lights. Image3 shows Marcus Hale: late 40s, short salt-and-pepper hair, "
           "grey-flecked beard, black leather jacket over a grey henley. Camera stands in a dim corridor with cyan floor strips, "
           "looking through a full glass wall into that office. Marcus stands inside facing the glass, arms crossed, face clearly "
           "lit by the screens, looking at Lyra. In the corridor foreground Solo walks in profile at frame left heading left, "
           "looking ahead, and Lyra is just behind him at frame center, her head turned toward Marcus through the glass so we "
           "see her face in three-quarter. Exactly one of each person. No outside windows. No text, no collage.",
           lambda: [OUT / "T3_first.jpg", REFS / "office_master_twoshot.jpg", MARCUS]),
}


def main() -> None:
    key = load_key()
    for sid in sys.argv[1:] or SHOTS:
        shutil.copy2(OUT / f"{sid}_first.jpg", OUT / f"{sid}_first_v2_rejected.jpg")
        prompt, refs = SHOTS[sid]
        still(key, prompt, refs(), OUT / f"{sid}_first.jpg")


if __name__ == "__main__":
    main()
