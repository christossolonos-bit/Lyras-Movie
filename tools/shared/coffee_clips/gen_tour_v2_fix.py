#!/usr/bin/env python3
"""Tour v2 still fixes: closer crops, targeted edits, and reshoots on the earlier tour's physical sets."""
from __future__ import annotations

import shutil
import sys

from PIL import Image

from gen_s11a_ots_v10_facelock import load_key, still
from gen_s11a_ots_v11_cards import FACE
from gen_tour import NEVER_CAM, REALISM, STYLE
from gen_tour_v2 import CAST, CAST_MARCUS, DOG, LYRA, LYRA_REFS, OUT, PLATES, SINGLE, SOLO, prep_refs

KEEP = "Edit Image1 only as described; keep everything else in Image1 exactly the same (framing, set, lighting, people). "
TAIL = (LYRA + SOLO + SINGLE + NEVER_CAM + REALISM
        + "Earlier images = set only, ignore any people in them. LAST image = cast sheet: match identities, not layout. No text.")

CROPS = {"T2": (0.20, 0.00, 0.80)}  # left, top, right as fractions of the frame

RETOUCH = {
    "T3_glasses": KEEP + "Output the same single photograph as Image1. The only change: the man in the maroon t-shirt wears "
                  "clearly visible thin metal-frame glasses. No text, no collage.",
    "T3_screen": KEEP + "Output the same single photograph as Image1. The only change: completely remove the framed screen showing "
                 "the repair shop and its stand from the right side, replacing it with more server racks and the same aisle. "
                 "No text, no collage.",
    "T6_clean": KEEP + "Output the same single photograph as Image1. The only change: completely remove the small second hologram "
                "woman and the second person in maroon standing behind the man, filling that area with empty steel walkway and "
                "steam. The two large foreground people stay exactly the same. No text, no collage.",
    "T6_shoulder": KEEP + "Output the same single photograph as Image1. The only change: remove the small dark red shoulder fragment "
                   "sticking out just left of the man's neck and behind his head, replacing it with the background rooftop and "
                   "steam. No text, no collage.",
    "T5_tee": KEEP + "Output the same single photograph as Image1. The only change: the man is NOT wearing a jacket. He wears a plain "
              "short-sleeve maroon heather t-shirt with bare forearms, dark blue jeans and grey sneakers. His face, glasses and "
              "hair do not change. No text, no collage.",
    "T8_lyra": KEEP + "Output the same single photograph as Image1. The only change: the hologram woman is complete, with her whole "
               "body and legs visible, standing on the corridor floor in front of the glass wall, feet on the floor, teal-cyan "
               "translucent with fine scanlines, her head turned toward the man inside the office. No text, no collage.",
    "T8_ghost": KEEP + "Output the same single photograph as Image1. The only change: remove the second transparent copy of the woman "
                "on the glass and inside the office, leaving only the one hologram woman in the corridor. The office behind the "
                "glass stays clear. No text, no collage.",
    "T6_solo": KEEP + "Output the same single photograph as Image1. The hologram woman does not change at all. The only change is "
               "the man: he now wears clearly visible thin metal-frame glasses, his short dark hair is tightly CURLY, and he is "
               "slimmer with narrow shoulders and thin arms. No text, no collage.",
    "T7a_bands": KEEP + "Output the same single photograph as Image1. The only change: remove the bright glowing bands around the "
                 "hologram woman's upper arms so her sleeves look even, with the same fine scanlines. No text, no collage.",
    "T7a_top": KEEP + "Output the same single photograph as Image1. The hologram woman's clothing is a smooth fitted scoop-neck "
               "long-sleeve top with slim pants, not a ribbed sweater or a dress: smooth fabric with only very fine horizontal "
               "scanlines. Her face and pose do not change. No bright bands on her arms. No text, no collage.",
    "T2_tint": KEEP + "Output the same single photograph as Image1. The only change: the hologram woman's face, hair and skin become "
               "the same teal-cyan tint as her clothing, with fine scanlines, so her whole figure is one consistent translucent "
               "cyan hologram. Her features stay sharp and readable. No text, no collage.",
    "T6_tint": KEEP + "Output the same single photograph as Image1. The only change: the hologram woman's face, hair and skin become "
               "the same teal-cyan tint as her clothing, with fine scanlines, so her whole figure is one consistent translucent "
               "cyan hologram. Her features stay sharp and readable. No text, no collage.",
}

FIXES = {
    "T2": (KEEP + "Output the same single photograph as Image1. The only change: the man in the maroon t-shirt now wears thin "
           "metal-frame glasses. No text, no collage, no extra panels.",
           lambda: [OUT / "T2_src.jpg"]),
    "T3": (KEEP + "Output the same single photograph as Image1. The only change: the hologram woman turns her head and body toward "
           "the man at frame right, looking at him in three-quarter profile with her arms relaxed at her sides. She does not "
           "look at the camera. No text, no collage.",
           lambda: [OUT / "T3_src.jpg"]),
    "T5": (KEEP + "Output the same single photograph as Image1. The only change: the white dog turns his head three-quarter toward "
           "camera so the grey patch around one eye from Image2 is clearly visible, with the man's hand resting on top of his "
           "head, not covering his face. Only one dog. No text, no collage.",
           lambda: [OUT / "T5_src.jpg", DOG]),
    "T4a": (STYLE + "Same Memory Wall set as Image1. Chest-up two-shot, camera close: Solo at frame right, three-quarter view, "
            "slim, staring stunned at one larger screen at the right edge of frame, which shows the phone repair shop from "
            "Image2 with a small figure at the workbench. Warm screen light on his face and glasses. Lyra stands a step behind "
            "him at frame left, her face large and sharp, eyes lowered to the floor, caught. " + TAIL,
            lambda: [OUT / "T4b_first.jpg", LYRA_REFS / "src_solo_shop.png", CAST]),
    "T6": (STYLE + "Image1 shows the EXACT two people and the exact look to keep: the same woman with the same face and the same "
           "long WAVY hair, whole figure including face, hair and skin teal-cyan as in Image1, and the same man. Same golden "
           "light and same data-center rooftop as Image1. New moment earlier on that rooftop: they stand on the flat steel "
           "grating walkway from Image2, cooling fans and steam behind them, camera at eye level. Chest-up two-shot: Lyra at "
           "frame left and Solo at frame right facing each other three-quarter to camera. Image3 is Lyra's face card. "
           "Her eyes are on Solo, not the camera. Exactly one Lyra and one Solo. No text, no collage.",
           lambda: [OUT / "T7a_first.jpg", PLATES / "old_T6_1.jpg", FACE]),
    "T7a": (STYLE + "Same rooftop as Image1, same golden light. Chest-up close two-shot at the guard rail: Lyra at frame left and "
            "Solo at frame right in profile facing each other, his forearm on the rail. Behind them, out of focus, flat roof "
            "and a thin desert access road running to the horizon. Warm rim light on Solo, cool cyan bounce from Lyra on his "
            "cheek. " + TAIL,
            lambda: [PLATES / "old_T7_1.jpg", CAST]),
    "T8": (STYLE + "Same corridor and glass-walled office as Image1: dim corridor with cyan floor strips, a glass wall along frame "
           "right, and behind it the small cluttered office with desk, monitors, lamp and whiteboard. No outside windows. Marcus "
           "stands still inside the office, arms crossed, lit by his lamp and monitors, watching through the glass. Camera "
           "follows from BEHIND: Solo and Lyra both walk AWAY from camera with their backs to us, Solo a step ahead at frame "
           "left, Lyra just behind him with her head turned right in profile toward Marcus. " + TAIL,
           lambda: [PLATES / "old_T8_1.jpg", CAST_MARCUS]),
}


def crop(sid: str) -> None:
    im = Image.open(OUT / f"{sid}_first.jpg").convert("RGB")
    w, h = im.size
    left, top, right = CROPS[sid]
    box_w = (right - left) * w
    box = (int(left * w), int(top * h), int(right * w), int(top * h + box_w * 9 / 16))
    im.crop(box).resize((1920, 1080), Image.LANCZOS).save(OUT / f"{sid}_first.jpg", quality=95)


def main() -> None:
    prep_refs()
    key = load_key()
    for sid in sys.argv[1:] or [*CROPS, *FIXES]:
        if sid in CROPS and sid not in FIXES:
            crop(sid)
            continue
        if sid in RETOUCH:
            shot = sid.split("_")[0]
            src = OUT / f"{shot}_retouch_src.jpg"
            shutil.copy2(OUT / f"{shot}_first.jpg", src)
            still(key, RETOUCH[sid], [src], OUT / f"{shot}_first.jpg")
            continue
        if sid == "T7a_flip":
            im = Image.open(OUT / "T7a_first.jpg").convert("RGB")
            im.transpose(Image.FLIP_LEFT_RIGHT).save(OUT / "T7a_first.jpg", quality=95)
            continue
        if sid in ("T2", "T3", "T5") and not (OUT / f"{sid}_src.jpg").exists():
            shutil.copy2(OUT / f"{sid}_first.jpg", OUT / f"{sid}_src.jpg")
        prompt, refs = FIXES[sid]
        still(key, prompt, refs(), OUT / f"{sid}_first.jpg")
        if sid in CROPS:
            crop(sid)


if __name__ == "__main__":
    main()
