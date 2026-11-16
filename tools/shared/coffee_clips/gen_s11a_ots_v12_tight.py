#!/usr/bin/env python3
"""S11a OTS v12 — tighter OTS: crop approved plate, re-render Lyra large from game cards."""
from __future__ import annotations

from PIL import Image

from gen_s11a_ots_v10_facelock import CLIPS, still, load_key
from gen_s11a_ots_v11_cards import BODY, FACE, flatten_cards

SRC = CLIPS / "S11a_ots_lyra_door_bridge_v10a_solid.jpg"
TIGHT = CLIPS / "S11a_ots_plate_tight.jpg"


def crop_plate() -> None:
    im = Image.open(SRC).convert("RGB")
    w, h = im.size
    cw = int(w * 0.70)
    ch = int(cw * 9 / 16)
    cx = int(w * 0.52)
    cy = int(h * 0.62)
    box = (cx - cw // 2, cy - ch // 2, cx + cw // 2, cy + ch // 2)
    im.crop(box).resize((1920, 1080), Image.LANCZOS).save(TIGHT, quality=95)
    print("CROP", box, flush=True)


PROMPT = (
    "OUTPUT one 16:9 cinematic photoreal frame at this EXACT framing of Image3 — do not zoom out, do not re-layout. "
    "Keep Nova's head/shoulder soft-focus at left edge and Solo's head/shoulder soft-focus at right edge, table and mugs bottom, "
    "open door and lit indoor corridor behind. "
    "RE-RENDER the woman in the doorway in sharp focus with high facial detail: she is the exact woman in Image1 — "
    "heart-shaped face, green-hazel eyes, long wavy chestnut hair with a middle part, soft warm closed-mouth smile, "
    "brows slightly raised, kind and a little shy. "
    "She is an AI HOLOGRAM rendered exactly like Image2: whole figure teal-cyan tinted, fine horizontal scanline mesh, "
    "soft cyan edge glow, faintly translucent at the edges — face features still clearly Image1. "
    "POSE: her right hand rests lightly on the door frame rim, fingers curled over the edge; other arm relaxed at her side; "
    "slight lean into the room, head tilted toward Solo. Eyes on Solo (frame right) — NOT at the camera. "
    "No floor pad, no projector beams. NO text."
)


def main() -> None:
    flatten_cards()
    crop_plate()
    key = load_key()
    for tag in ("a", "b"):
        still(key, PROMPT, [FACE, BODY, TIGHT], CLIPS / f"S11a_ots_lyra_door_bridge_v12{tag}.jpg")


if __name__ == "__main__":
    main()
