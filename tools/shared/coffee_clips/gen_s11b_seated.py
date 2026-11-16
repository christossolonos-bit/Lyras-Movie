#!/usr/bin/env python3
"""S11b redo: Solo stays seated through Nova's line. Writes S11b_seated_final.mp4; S11b_final.mp4 is kept.

  python gen_s11b_seated.py
"""
from __future__ import annotations

from gen_coffee_close import CLIPS, SHOTS, gen, load_key

SHOTS["S11b_seated"] = {
    "first": CLIPS / "S10_solo_ots_nova_face_last.jpg", "dur": 6,
    "prompt": "DIR:SPIELBERG. Continue THIS exact frame: over Solo's blurred shoulder onto Nova at the break-room table. "
              "Solo stays SEATED for the whole shot: his blurred shoulder and head stay low in the same place in the foreground, "
              "he does not stand, rise, lean or cross the frame, and never blocks Nova. "
              "Nova glances toward the doorway off frame right where Lyra's cyan light spills in, then back to Solo; "
              "she lifts her mug and tips it toward the door with a knowing half-smile. "
              'NOVA (dry, warm, clearly audible, full voice): "Go on. Don\'t keep the building waiting." '
              "Locked camera, tiny push in.",
}

if __name__ == "__main__":
    gen(load_key(), "S11b_seated")
