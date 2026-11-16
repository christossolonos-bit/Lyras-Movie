#!/usr/bin/env python3
"""Realism pass: re-shoot each tour still as one physically coherent photograph."""
from __future__ import annotations

import shutil
import sys

from gen_s11a_ots_v10_facelock import load_key, still
from gen_tour import CAST, LYRA, NEVER_CAM, REALISM, SHOTS, SOLO, STYLE, TOUR, prep_refs

STAGING = {
    "T1": "They walk side by side mid-stride toward camera down the corridor center, Solo's near foot landing, "
          "Lyra half a step ahead turning her head to him; cyan ring light and her glow wash across the floor between them.",
    "T2": "Mid-stride on the perforated raised floor tiles, rack LEDs reflecting in Solo's glasses; Lyra's cyan spill "
          "on the rack doors next to her and on Solo's left arm.",
    "T3": "Higher, wider angle looking down the central aisle so both figures are small; their reflections and Lyra's "
          "cyan glow pool on the glossy floor; haze between the rows softens the far end.",
    "T4": "Solo stands rooted, weight on back foot, screen light warming his face and lenses; Lyra a step behind him "
          "with cyan glow on the nearest screens' bezels and on Solo's shoulder.",
    "T5": "Solo crouches on the concrete with real weight, one knee down, hand out low; Patch sits on his bed, body "
          "leaning forward to sniff; Lyra stands on the floor nearby, her glow lighting Patch's white coat cyan on one side.",
    "T6": "They stand on the steel grating MAINTENANCE WALKWAY between the cooling units (not on pipes), just through the "
          "roof access door; low warm sun gives both of them long shadows across the grating; wind moves Solo's shirt "
          "and hair; Lyra's glow is fainter and flickers in hard sunlight; steam drifts between them and the camera.",
    "T7": "Both stand at the guard rail on the walkway, Solo's forearm resting on the rail; warm sunset rim light on Solo's "
          "hair, cheek and glasses, cool cyan bounce from Lyra on the side of his face facing her; Lyra's hair stirs in wind.",
    "T8": "Mid-stride with natural gait; their reflections ghost on the office glass; Lyra's cyan glow lights the corridor "
          "wall and floor around her; Marcus inside is lit by his desk lamp and monitors.",
}


def main() -> None:
    prep_refs()
    key = load_key()
    for sid in sys.argv[1:] or list(SHOTS):
        src = TOUR / f"{sid}_bridge.jpg"
        shutil.copy2(src, TOUR / f"{sid}_bridge_comp.jpg")
        prompt = (
            STYLE + "Re-photograph Image1 as ONE real on-set photograph: keep the same location, camera angle, "
            "composition, characters and their identities, but fix anything that looks pasted-in. "
            f"STAGING: {STAGING[sid]} " + REALISM + LYRA + SOLO + NEVER_CAM
            + "Image2 is the cast sheet (Lyra face, Lyra hologram body, Solo face, Solo body) — identity only, not layout. "
            "No earbuds. NO text."
        )
        still(key, prompt, [TOUR / f"{sid}_bridge_comp.jpg", CAST], src)


if __name__ == "__main__":
    main()
