"""Section F setup stills (GPT Image 2, about $0.07 each). Run: python stills_F.py F1 F2 ...  (skips ones already made)"""
import sys
from ep4_lib import FRAMES, R, still

TOUR = R / "Episode 3" / "Tour plates"
REFS = R / "assets" / "lyra-refs"
DOG = REFS / "dog_ref.png"
RED = (" LIGHT: total power failure at midnight. The space is lit ONLY by small deep-red emergency lamps and white flashlight beams; "
       "every wall light strip and screen is dead and black, no cyan anywhere, no white ceiling lights. Deep shadows, dust in the beams.")
LOOK = " Live-action film still, real skin, natural faces, not glossy, not CG. 16:9. No text."
TRIO = ("Marcus (grey hair, stubble, black leather jacket, grey henley, holding a lit flashlight), Nova (dark messy bun, charcoal cardigan, black top, "
        "dark trousers, necklaces, holding a flashlight) and Juno (platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, "
        "olive tank top, charcoal denim overalls, a crowbar in her hand) exactly as in the reference frame, with Patch the dog from the dog reference")

S = {
    "F1": ("F1_lobby_wide_frame_v1.png", [FRAMES / "D6_patrik_ops_frame_v1.png", REFS / "patrik_operations_outfit.png"],
           "Wide shot of the main entrance lobby of a desert data centre: polished concrete floor, a long reception desk, glass entrance doors "
           "showing the moonlit desert, a dead logo wall. Patrik (the man in the reference: black hair, beard, dark operations outfit) stands at the "
           "reception desk handing out flashlights from an open crate to four night-shift staff in plain dark work clothes, two men and two women, "
           "their beams already switched on. Camera low and wide, everyone small in the room." + RED),
    "F2": ("F2_patrik_lobby_frame_v1.png", [FRAMES / "F1_lobby_wide_frame_v1.png", REFS / "patrik_face_34.png", FRAMES / "D6_patrik_ops_frame_v1.png"],
           "Chest-up shot of Patrik (the man in the references: black hair, beard, dark operations outfit) alone in the dark lobby from the first "
           "reference, a handheld radio raised near his mouth, steady and calm, looking slightly off camera. The lobby softly out of focus behind him, "
           "a flashlight beam crossing the background. Nobody else in frame." + RED),
    "F3": ("F3_crowbar_door_frame_v1.png", [FRAMES / "C_staff_corridor_red_plate_v1.png", FRAMES / "D1_office_wide_frame_v1.png", DOG],
           "Wide shot in the staff-level corridor from the first reference (pale concrete wall panels, dead light strips, small red emergency lamps). "
           "A heavy grey security door is shut at the side of the corridor. Juno has jammed her crowbar into the door seam and leans her weight on it; "
           "Marcus holds his flashlight on the seam, Nova stands just behind with her flashlight, Patch waits at Marcus's feet. "
           "The people: " + TRIO + "." + RED),
    "F4": ("F4_marcus_patch_link_frame_v1.png", [TOUR / "C_link_corridor_plate_v1.png", FRAMES / "D7_marcus_patch_door_frame_v1.png", DOG],
           "Knees-up shot in the long link corridor from the first reference, now dark. Marcus (from the second reference: grey hair, stubble, black "
           "leather jacket, grey henley) holds Patch on a short lead and a flashlight in the other hand; Patch (the dog in the dog reference) pulls ahead, "
           "nose down to the floor, tail stiff, leading them on. Marcus looks down at the dog. The corridor stretches into darkness behind them. "
           "Nobody else in frame." + RED),
    "F5": ("F5_processor_hall_wide_frame_v1.png", [TOUR / "B_processor_hall_plate_v2.png", FRAMES / "D1_office_wide_frame_v1.png", DOG],
           "Wide shot of the huge processor hall from the first reference, now dead: endless rows of server racks with every status light off, "
           "only red emergency lamps far away. The group walks small down the centre aisle, flashlight beams cutting through a faint heat haze. "
           "The people: " + TRIO + "." + RED),
    "F6": ("F6_nova_rack_frame_v1.png", [TOUR / "B_processor_hall_plate_v2.png", FRAMES / "D3_nova_office_frame_v1.png", REFS / "nova_ref.png"],
           "Chest-up shot of Nova (from the second reference: dark messy bun, charcoal cardigan, black top, necklaces) standing beside a dead server "
           "rack in the processor hall, flashlight in one hand, the other hand just lifting off the rack's metal side, a worried look, a sheen of "
           "sweat on her face. Rows of dark racks fall away out of focus behind her. Nobody else in frame." + RED),
    "F2b": ("F2_patrik_lobby_frame_v2.png", [FRAMES / "F2_patrik_lobby_frame_v1.png", REFS / "patrik_face_34.png", FRAMES / "D6_patrik_ops_frame_v1.png"],
           "Chest-up shot of Patrik (the man in the references: black hair, short beard, dark operations jacket) alone in the dark lobby from the first "
           "reference, facing three-quarters toward camera. He holds a handheld radio DOWN AT HIS CHEST, well below his chin, thumb on the key; "
           "his whole face, mouth and chin are completely clear and unobstructed, lips slightly parted as if about to speak. Steady and calm. "
           "The lobby softly out of focus behind him, a flashlight beam crossing the background. Nobody else in frame." + RED),
    "F8": ("F8_rover_bay_frame_v1.png", [FRAMES / "E2_gate_frame_v1.png", R / "Lyras-Movie" / "images" / "dunn_vehicle_ref.png"],
           "Wide low-angle shot inside a dark concrete service bay of a desert data centre: a big roller door open to the moonlit night behind, "
           "oil-stained floor, steel pillars, red emergency lamps. The armoured army prototype rover from the references (gunmetal-black and "
           "olive-drab armour, four huge knobby tyres, ram bumper, side drone pods, roof sensor turret, no windscreen) is parked in the middle, its row of "
           "glowing cyan sensor eyes casting a cyan scan beam across the far wall. The rover's cyan is the only cool light; everything else is "
           "red and dark. No person visible."),
    "F10": ("F10_cathedral_wide_frame_v1.png", [TOUR / "D_cooling_cathedral_plate_v1.png", FRAMES / "D1_office_wide_frame_v1.png", DOG],
            "Very wide shot of the cooling cathedral from the first reference, now silent and dead: no mist, no lights, the giant pipes and tanks "
            "towering into darkness. The group is tiny at the bottom of the frame crossing the floor, flashlight beams reaching up the pipes. "
            "The people: " + TRIO + "." + RED),
    "F11": ("F11_juno_pipes_frame_v1.png", [TOUR / "D_cooling_cathedral_plate_v1.png", FRAMES / "D2_juno_office_frame_v1.png", REFS / "juno_portrait.png"],
            "Chest-up shot of Juno (from the second reference: platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, "
            "olive tank top, charcoal denim overalls, crowbar resting on her shoulder) looking up at the huge dead cooling pipes above her, awed and "
            "uneasy, her flashlight beam pointing up. The dark pipes out of focus behind her. Nobody else in frame." + RED),
    "F12": ("F12_frosted_door_frame_v1.png", [TOUR / "D_cooling_cathedral_plate_v1.png", FRAMES / "D1_office_wide_frame_v1.png", DOG],
            "Wide shot at the far end of the cooling cathedral from the first reference: a tall frosted-glass door set in the wall. Juno has forced it "
            "open a hand's width with her crowbar and deep red light spills out through the gap onto the floor; Patch the dog is already "
            "squeezing through the gap; Marcus and Nova stand behind with flashlights. The people: " + TRIO + "." + RED),
}

for cid in sys.argv[1:]:
    name, refs, prompt = S[cid]
    out = FRAMES / name
    if out.exists():
        print("EXISTS", out); continue
    still(out, prompt + LOOK, refs)
