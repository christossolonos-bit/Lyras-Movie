#!/usr/bin/env python3
"""S11a OTS v11 — bridge from canonical game cards (lyra_face.png + lyra_body.png).

Line locked in script/ep3/script_ep3_marcus_lyra_office.md (B5).
Bridge stills only.
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from gen_s11a_ots_v10_facelock import CLIPS, LOCK, load_key, still

CARDS = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\game\assets\characters")
PLATE = CLIPS / "S11a_ots_lyra_door_bridge_v10a_solid.jpg"
FACE = LOCK / "game_lyra_face.jpg"
BODY = LOCK / "game_lyra_body_holo.jpg"
LINE = "Solo? Whenever you're ready... I'd like to show you around."


def flatten_cards() -> None:
    LOCK.mkdir(exist_ok=True)
    Image.open(CARDS / "lyra_face.png").convert("RGB").save(FACE, quality=95)
    body = Image.open(CARDS / "lyra_body.png").convert("RGBA")
    bg = Image.new("RGBA", body.size, (12, 16, 20, 255))
    bg.alpha_composite(body)
    bg.convert("RGB").save(BODY, quality=95)


PROMPT = (
    "OUTPUT one 16:9 cinematic photoreal frame. NO text, NO collage, NO split panels. "
    "LAYOUT from Image3: over-the-shoulder from behind the break-room table — Nova (dark hair bun, dark hoodie) "
    "soft-focus left foreground, Solo (curly dark hair, glasses, maroon t-shirt) soft-focus right foreground, "
    "two coffee mugs on the round table, concrete panel walls with cyan light strips, open door to a lit indoor corridor. "
    "Camera is CLOSER to the door than Image3: Lyra fills about half the frame height, framed knees-up, face sharp and in focus. "
    "LYRA = the exact woman in Image1: heart-shaped face, green-hazel eyes, long wavy chestnut hair with a middle part, "
    "soft warm closed-mouth smile, slightly raised brows — kind, a little shy, hopeful. "
    "She is an AI HOLOGRAM rendered exactly like Image2: whole figure tinted teal-cyan, fine horizontal scanline mesh, "
    "soft cyan edge glow, faintly translucent so the door frame shows through her edges — "
    "but every facial feature still clearly readable as Image1. "
    "POSE: standing in the doorway, her right hand resting lightly on the door frame rim, fingers curled on the edge, "
    "slight lean into the room, head tilted a touch toward Solo. Her eyes look at Solo (frame right), NOT at the camera. "
    "No floor pad, no projector, no beams. Warm practical light, shallow depth of field, 35mm film look."
)


def main() -> None:
    flatten_cards()
    key = load_key()
    for tag in ("a", "b"):
        still(key, PROMPT, [FACE, BODY, PLATE], CLIPS / f"S11a_ots_lyra_door_bridge_v11{tag}.jpg")
    print(f"LINE (B5 locked): {LINE}")


if __name__ == "__main__":
    main()
