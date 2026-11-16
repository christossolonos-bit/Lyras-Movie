#!/usr/bin/env python3
"""Targeted edit passes on tour stills."""
from __future__ import annotations

import sys

from gen_s11a_ots_v10_facelock import load_key, still
from gen_tour import CAST, REALISM, REFS, SOLO, LYRA, NEVER_CAM, STYLE, TOUR, prep_refs

KEEP = "Edit Image1 only as described; keep everything else in Image1 exactly the same (framing, set, lighting, Lyra). "

FIXES = {
    "T4": (
        KEEP + "Change ONLY Solo: he now stands in strict side PROFILE facing frame right toward the big seafront screen, "
        "arms hanging still at his sides, lips slightly parted, stunned and quiet — not smiling, not gesturing, "
        "not looking at camera. Remove the earbud. Same face, glasses, curly hair and maroon t-shirt. "
        "Also change Lyra's eyes to look down at the floor, embarrassed. NO text.",
        lambda: [TOUR / "T4_bridge.jpg", CAST],
    ),
    "T7": (
        KEEP + "Remove the white earbud from Solo's ear — bare ear. Nothing else changes. NO text.",
        lambda: [TOUR / "T7_bridge.jpg"],
    ),
    "T3b": (
        STYLE + "DIR:JACKSON. Extreme wide HIGH angle from up near the yellow steel beams of Image1's processor hall, "
        "looking down the full length of the central aisle — endless rows of black racks with blue/green LEDs, cable "
        "trays, glossy floor, haze into the distance. Far below in the aisle, Solo and the glowing Lyra are SMALL figures "
        "(about 1/8 of frame height), standing on the floor with long soft reflections; Solo looking up and around, "
        "Lyra beside him; her cyan light pools on the floor around them. " + LYRA + SOLO + NEVER_CAM + REALISM
        + "Image2 = cast sheet, identity only. NO text.",
        lambda: [REFS / "c1_processors.png", CAST],
    ),
    "T8real": (
        KEEP + "REMOVE the second full-body Lyra figure inside the office window — there is only ONE Lyra, the one "
        "walking in the corridor. On the glass leave at most a very faint soft cyan smear of reflected light. "
        "Make Marcus (grey hair, black leather jacket, arms crossed) clearly visible inside the office standing by "
        "his desk, lit by his desk lamp and monitors, watching the corridor. NO text.",
        lambda: [TOUR / "T8_bridge.jpg"],
    ),
    "T8": (
        STYLE + "DIR:JACKSON. Camera stands in a dim grey concrete corridor lit by cyan waist LED strips. The whole RIGHT "
        "half of the frame is a big glass window into a small cluttered office (desk, three monitors, desk lamp, "
        "papers pinned up, whiteboard of diagrams). INSIDE that office, behind the glass, Marcus — grey hair, black "
        "leather jacket, from the second reference — stands by his desk with arms crossed, watching out. "
        "In the corridor foreground at left, Solo and the glowing Lyra walk away from camera down the corridor, "
        "Lyra's head turned toward Marcus through the glass. " + LYRA + SOLO + NEVER_CAM
        + "LAST image = cast sheet (Lyra face, Lyra hologram body, Solo face, Solo body) — match identities, not layout.",
        lambda: [REFS / "lh1_ops_wake.png", CAST],
    ),
}


def main() -> None:
    prep_refs()
    key = load_key()
    for sid in sys.argv[1:] or list(FIXES):
        prompt, refs = FIXES[sid]
        still(key, prompt, refs(), TOUR / f"{sid}_bridge.jpg")


if __name__ == "__main__":
    main()
