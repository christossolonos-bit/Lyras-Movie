"""Section I setup stills: restart. Run: python stills_I.py I1 I2 I5 I7 I9 I11  (I11 needs I9 first; skips ones already made)

With a first frame, the video model gets no reference images, so Lyra must already be in the I7, I9 and I11 frames.
"""
import sys
from ep4_lib import FRAMES, R, still

REFS = R / "assets" / "lyra-refs"
JAMES_REF = R / "Lyras-Movie" / "images" / "james_dunn_ref.png"
DOG = REFS / "dog_ref.png"
RED = (" LIGHT: power failure. Lit ONLY by small deep-red emergency lamps and white flashlight beams; the wall light lines are dead and black, "
       "no cyan anywhere.")
LOOK = " Live-action film still, real skin, natural faces, not glossy, not CG. 16:9. No text."
ROOM = "the dark round core chamber from the first reference (tall black glass column wrapped in cables, low console, stairwell going down at the back)"
LYRA = ("Lyra (the woman in the Lyra references: long wavy hair, a fitted long-sleeve top, gentle face) as a translucent glowing cyan hologram, "
        "fine scan lines through her, standing on the floor")

S = {
    "I1": ("I1_james_console_frame_v1.png", [FRAMES / "H10_nova_core_frame_v1.png", FRAMES / "H2_james_corridor_frame_v1.png", JAMES_REF],
           f"Chest-up shot of James (shaved head, ruddy, heavyset, army camouflage uniform with colonel insignia, his face exactly as in the second "
           f"reference) standing at the low console in {ROOM}, his broad hand resting over a big heavy lever switch, eyes down on it, grave. "
           "The black column softly out of focus behind him. Nobody else in frame." + RED),
    "I2": ("I2_solo_core_frame_v1.png", [FRAMES / "H10_nova_core_frame_v1.png", FRAMES / "G2_solo_kneel_frame_v1.png", REFS / "solo_face_approved.jpg"],
           f"Chest-up shot of Solo (curly dark hair, glasses, black puffer jacket, maroon t-shirt, his real face exactly as in the second and third "
           f"references, not idealised) standing in {ROOM}, looking off camera toward the console, afraid, mouth closed. A flashlight beam lights "
           "his face from the side. Nobody else in frame." + RED),
    "I5": ("I5_hall_staff_frame_v2.png", [R / "Episode 3" / "Tour plates" / "B_processor_hall_plate_v2.png", FRAMES / "F1_lobby_wide_frame_v1.png", REFS / "patrik_face_34.png"],
           "Wide shot of the huge processor hall from the first reference, still dead: endless rows of dark server racks, every status light off, "
           "red emergency lamps far away. Patrik (black hair, short beard, dark operations jacket) and four night-shift staff in dark work clothes "
           "stand in the centre aisle with flashlights, waiting, looking along the racks. ONLY these five people: no leather jacket, no woman with a blonde bob, no dog." + RED),
    "I7": ("I7_lyra_returns_wide_frame_v1.png", [FRAMES / "H10_nova_core_frame_v1.png", FRAMES / "H8_door_opens_frame_v1.png", REFS / "lh3_hologram_forms.png"],
           f"Wide shot in {ROOM}, now coming back to life: thin cyan light lines glow along the floor, the black column softly lit cyan from inside "
           "(only light, nothing visible inside it), and a wall projector box with a glowing cyan ring. In the middle of the room "
           f"{LYRA}, just flickering into being, faint and half formed. Around her, seen from behind and the side, the group watches: James "
           "(shaved head, camouflage uniform), Solo (curly hair, glasses, black puffer), Marcus (grey hair, black leather jacket), Nova (dark bun, "
           "charcoal cardigan), Juno (platinum-blonde bob, goggles on her head, charcoal overalls) and Patch the white dog with a plain dark collar. "
           "Red emergency lamps still glow; cyan light now mixes in."),
    "I9": ("I9_lyra_hologram_frame_v1.png", [REFS / "lh4_lyra_closeup.png", REFS / "lyra_ref.png", FRAMES / "H10_nova_core_frame_v1.png"],
           f"Chest-up shot of {LYRA.replace(', standing on the floor', '')}, in the dark round core chamber of the third reference, a polite, bright, "
           "slightly blank smile, looking at someone just off camera as if meeting a stranger. Her face exactly as in the first two references. "
           "Dim red lamps and the cyan-lit column softly out of focus behind her. Nobody else in frame."),
    "I11": ("I11_patch_collar_frame_v1.png", [FRAMES / "I9_lyra_hologram_frame_v1.png", DOG, FRAMES / "G2_solo_kneel_frame_v1.png"],
            f"Knees-up shot in the core chamber: {LYRA.replace(', standing on the floor', '')} exactly as in the first reference, standing, looking "
            "down at Patch (the white dog in the dog reference, plain dark collar, no light on it), who sits at her feet looking up at her, tail "
            "still. Cyan hologram light falls on the dog's white coat. Nobody else in frame."),
    "I3m": ("I3_marcus_core_room_frame_v1.png", [FRAMES / "I2_solo_core_frame_v1.png", FRAMES / "G3_marcus_core_frame_v1.png", FRAMES / "D4_marcus_standing_frame_v1.png"],
            f"Chest-up shot of Marcus (from the second and third references: grey hair, stubble, black leather jacket, grey henley, flashlight in hand) "
            f"standing INSIDE {ROOM}, the same room and background as the first reference: the black glass column and the console behind him, "
            "no doorway. He looks off camera toward the console, troubled, mouth closed. Nobody else in frame." + RED),
    "H11j": ("H11_james_core_room_frame_v1.png", [FRAMES / "I1_james_console_frame_v1.png", FRAMES / "H2_james_corridor_frame_v1.png", JAMES_REF],
             f"Chest-up shot of James (shaved head, ruddy, heavyset, army camouflage uniform with colonel insignia, his face exactly as in the "
             f"references) standing INSIDE {ROOM}, the same room as the first reference, the black glass column softly out of focus behind him, "
             "flashlight in hand, facing camera, his face closed and unreadable, deliberately not looking toward the stairwell. No doorway. "
             "Nobody else in frame." + RED),
}

for cid in sys.argv[1:]:
    name, refs, prompt = S[cid]
    out = FRAMES / name
    if out.exists():
        print("EXISTS", out); continue
    still(out, prompt + LOOK, refs)
