"""Section H setup stills: James and the door. Run: python stills_H.py H1 H2 H3 H8 H9 H10  (skips ones already made)"""
import sys
from ep4_lib import FRAMES, R, still

REFS = R / "assets" / "lyra-refs"
JAMES_REF = R / "Lyras-Movie" / "images" / "james_dunn_ref.png"
RED = (" LIGHT: total power failure at midnight. Lit ONLY by small deep-red emergency lamps and white flashlight beams; the wall light lines "
       "are dead and black, no cyan anywhere, no white ceiling lights.")
LOOK = " Live-action film still, real skin, natural faces, not glossy, not CG. 16:9. No text."
JAMES = ("James (the man in the James reference: shaved head, ruddy, heavyset, OCP army camouflage uniform with colonel insignia, his face exactly "
         "as in the reference)")
GROUP = ("Solo (curly hair, glasses, black puffer jacket), Marcus (grey hair, stubble, black leather jacket), Nova (dark messy bun, charcoal cardigan), "
         "Juno (platinum-blonde bob, goggles on her head, charcoal overalls, crowbar) and Patch the white dog with a plain dark collar")
CORE = ("a round dark chamber behind the open door: in the centre one tall column of black glass wrapped in thick cables, a low console in front "
        "of it, and at the back an open stairwell going down into darkness; two thin light lines run along the floor into the stairwell, dead and unlit")

S = {
    "H1": ("H1_james_arrives_frame_v1.png", [FRAMES / "G1_found_wide_frame_v1.png", JAMES_REF, FRAMES / "F5_processor_hall_wide_frame_v1.png"],
           f"Wide shot down the dark red corridor of the first reference, the round steel core door at the side. {JAMES} walks up the corridor "
           f"toward camera with a flashlight, tired and steady. In the foreground, seen from behind and the side, the group turns toward him: {GROUP}, "
           "as in the third reference." + RED),
    "H2": ("H2_james_corridor_frame_v1.png", [JAMES_REF, FRAMES / "D10_james_rover_frame_v1.png", FRAMES / "G3_marcus_core_frame_v1.png"],
           f"Chest-up shot of {JAMES} standing in the dark red corridor beside the edge of a big round riveted steel door (as in the third reference), "
           "a flashlight in his hand, a tired half grin, looking slightly off camera at an old friend. No headset. Nobody else in frame." + RED),
    "H3": ("H3_keypad_insert_frame_v1.png", [FRAMES / "A_corridor_red_plate_v1.png", JAMES_REF],
           "Close-up insert of the riveted steel surface of the big round core door in red emergency light: a man's broad hand with an army camouflage "
           "sleeve rests flat on the steel, and a hidden panel has just slid open beside it revealing a small numeric keypad with dim backlit grey keys. "
           "No face in frame." + RED),
    "H8": ("H8_door_opens_frame_v1.png", [FRAMES / "A_corridor_red_plate_v1.png", FRAMES / "G1_found_wide_frame_v1.png", FRAMES / "F12_frosted_door_frame_v1.png"],
           f"Wide shot from behind the group as they stand facing the big round riveted steel core door of the first reference: {JAMES}, {GROUP}, "
           "their flashlight beams on the door. The door is still shut, its locking bolts around the rim visible." + RED),
    "H9": ("H9_core_room_frame_v1.png", [FRAMES / "A_corridor_red_plate_v1.png", FRAMES / "F12_frosted_door_frame_v1.png"],
           f"Wide shot looking through the open round steel door into {CORE}. The group stands just inside the doorway seen from behind as small "
           "silhouettes, flashlight beams on the black glass column. Cold, still air, faint mist on the floor." + RED),
    "H10": ("H10_nova_core_frame_v1.png", [FRAMES / "H9_core_room_frame_v1.png", FRAMES / "D3_nova_office_frame_v1.png", REFS / "nova_ref.png"],
            "Chest-up shot of Nova (from the second reference: dark messy bun, charcoal cardigan, black top, necklaces) inside the dark round core "
            "chamber of the first reference, flashlight in hand, looking past camera toward the stairwell going down, uneasy and curious, mouth closed. "
            "The black glass column softly out of focus behind her. Nobody else in frame." + RED),
}

for cid in sys.argv[1:]:
    name, refs, prompt = S[cid]
    out = FRAMES / name
    if out.exists():
        print("EXISTS", out); continue
    still(out, prompt + LOOK, refs)
