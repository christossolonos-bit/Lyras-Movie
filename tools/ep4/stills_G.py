"""Section G setup stills: found. Run: python stills_G.py G1 G2 G3  (skips ones already made)"""
import sys
from ep4_lib import FRAMES, R, still

REFS = R / "assets" / "lyra-refs"
DOG = REFS / "dog_ref.png"
RED = (" LIGHT: total power failure at midnight. Lit ONLY by small deep-red emergency lamps and white flashlight beams; the wall light lines "
       "are dead and black, no cyan anywhere, no white ceiling lights.")
LOOK = " Live-action film still, real skin, natural faces, not glossy, not CG. 16:9. No text."
SOLO = ("Solo (the young man in the references: curly dark hair, glasses, black puffer jacket, maroon t-shirt, his real face exactly as in the "
        "references, not idealised)")
PATCH = "Patch (the white dog in the dog reference, plain dark collar with no light on it)"
SET = "the dark corridor in front of the big round steel core door from the first reference"

S = {
    "G1": ("G1_found_wide_frame_v1.png", [FRAMES / "A_corridor_red_plate_v1.png", FRAMES / "A2_A4_frame_v1.png", DOG],
           f"Wide shot of {SET}. {SOLO} is down on his knees on the floor near the round door, arms wrapped around {PATCH}, who is pressed against "
           "him licking his face, tail up. White flashlight beams spill in from behind the camera across the floor. Nobody else in frame." + RED),
    "G2": ("G2_solo_kneel_frame_v1.png", [FRAMES / "A2_A4_frame_v1.png", REFS / "solo_face_approved.jpg", DOG],
           f"Chest-up shot of {SOLO} kneeling in {SET.replace('from the first reference', 'behind him')}, one arm around {PATCH} whose head "
           "is at his chest. He looks up and slightly off camera toward someone standing, shaken, eyes wet, mouth closed. A flashlight beam lights "
           "his face from above-left. Nobody else in frame." + RED),
    "G3": ("G3_marcus_core_frame_v1.png", [FRAMES / "A_corridor_red_plate_v1.png", FRAMES / "D9_marcus_corridor_frame_v1.png", FRAMES / "D4_marcus_standing_frame_v1.png"],
           "Chest-up shot of Marcus (from the references: grey hair, stubble, black leather jacket, grey henley, flashlight in hand) standing in the "
           "dark corridor of the first reference, looking down and slightly off camera, jaw set, the edge of the big round steel core door "
           "softly out of focus beside him. Nobody else in frame." + RED),
}

for cid in sys.argv[1:]:
    name, refs, prompt = S[cid]
    out = FRAMES / name
    if out.exists():
        print("EXISTS", out); continue
    still(out, prompt + LOOK, refs)
