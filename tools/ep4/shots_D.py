"""Section D shots: the office, the calls. Run: python shots_D.py D1 [v2] [--check]"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

RED = ("LIGHT: from the first frame to the last it stays exactly as dark and deep red as the first frame; nothing switches on, "
       "no white light, no cyan, faces lit only by red and the flashlight. ")
OFFICE = "Marcus's office in a desert data centre at midnight during a power failure, desk, dark screens, couch, a night window, red emergency lamps"
CORRIDOR = ("the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, "
            "small red emergency lamps high on the walls")
MARCUS = "He keeps his face, grey hair, stubble, black leather jacket and grey henley exactly as in the first frame."
NOVA = "She keeps her face, dark messy bun, charcoal cardigan and necklaces exactly as in the first frame."
JUNO = ("She keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, olive tank top and charcoal overalls "
        "exactly as in the first frame.")
ONLY = " Nobody else ever appears."
LOCK = "CAMERA: locked off, exactly the first frame's framing, no push in, no cut. "

SHOTS = {
    "D1": dict(who=["Marcus", "Nova", "Juno"], director="JACKSON", duration=5, framing="wide", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "D1_office_wide_frame_v1.png", location=OFFICE, beat="The women find him already moving", engine="care",
        action="The office door flies open and Nova and Juno burst in, out of breath. Marcus, already on his feet with a lit flashlight, spins toward them, "
               "the beam swinging across the door. They stop just inside, all three frozen for a moment, frightened. "
               "CAMERA: tripod, completely locked off, exactly the first frame's wide framing, the camera never pans, drifts or pushes in, no cut. " + RED +
               "Keep the office, desk, couch and night window. " + MARCUS.replace("He keeps", "Marcus keeps") + " WARDROBE, unchanged from start to end: Nova wears a charcoal cardigan, black top, DARK trousers and her necklaces; "
               "Juno wears CHARCOAL DENIM OVERALLS (bib and straps) over an olive tank top, brass goggles on her head, tattoo sleeve. "
               "No light-coloured jeans or trousers on anyone." + ONLY,
        lines=[]),
    "D2": dict(who=["Juno"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "D2_juno_office_frame_v1.png", location=OFFICE,
        beat="She needs the voice that always answers", engine="care",
        action="Out of breath, chest heaving, Juno looks across the room and says her line, upset, her voice catching. " + LOCK + RED + JUNO + ONLY,
        lines=[Line("Juno", "out of breath, upset, voice catching", "She's not answering. She always answers.")]),
    "D3": dict(who=["Nova"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "D3_nova_office_frame_v1.png", location=OFFICE,
        beat="She realises someone is missing", engine="care",
        action="Nova catches her breath, then a sudden thought hits her, her eyes widen and she turns sharply to ask, afraid. " + LOCK + RED + NOVA + ONLY,
        lines=[Line("Nova", "turning sharply, suddenly afraid", "Where's Solo?")]),
    "D4": dict(who=["Marcus"], director="SPIELBERG", duration=9, framing="upper_body", first=FRAMES / "D4_marcus_standing_frame_v1.png", location=OFFICE,
        beat="It lands on him, and he acts", engine="care",
        action="Marcus takes the question like a blow, a beat of dread, and answers quietly. Then he snaps into action, lifts the phone to his ear and "
               "gives his order firm and fast, already turning to move. " + LOCK + RED + MARCUS + ONLY,
        lines=[Line("Marcus", "quietly, dread landing", "With her. At the end of the tour."),
               Line("Marcus", "phone to his ear, firm and fast", "Patrik. Lyra's down. I need every flashlight on site.")]),
    "D6": dict(who=["Patrik"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "D6_patrik_ops_frame_v1.png",
        location="the operations control room of a desert data centre at midnight during a power failure, rows of dead black monitors, red emergency lamps",
        beat="Calm news that is bad news", engine="care",
        action="Patrik listens on the phone, the flashlight under his face, glances at the dead monitors around him, and answers calm and steady. " + LOCK + RED +
               "He keeps his face, black hair, beard and dark operations outfit exactly as in the first frame." + ONLY,
        lines=[Line("Patrik", "calm and steady, glancing at the dead monitors", "Cameras went with her. We're blind.")]),
    "D7": dict(who=["Marcus", "Patch"], director="SPIELBERG", duration=5, framing="two_shot", first=FRAMES / "D7_marcus_patch_door_frame_v1.png", location=OFFICE,
        beat="The dog will lead", engine="care",
        action="Patch stands at the door with his nose to the gap, sniffing, tail stiff. Marcus looks down at him, a small determined nod, and says his line. "
               "Patch looks up at him, then back to the door. " + LOCK + RED + MARCUS.replace("He keeps", "Marcus keeps") +
               " Patch stays exactly the dog in the first frame." + ONLY,
        lines=[Line("Marcus", "looking down at the dog, determined", "Then we find him the old way.")]),
    "D8": dict(who=["Juno"], director="SPIELBERG", duration=6, framing="upper_body", first=FRAMES / "D2_juno_office_frame_v1.png", location=OFFICE,
        beat="She arms herself", engine="care",
        action="Juno yanks the crowbar off the red emergency cabinet beside her, weighs it in her hand and says her line with a grim little smile. " + LOCK + RED + JUNO + ONLY,
        lines=[Line("Juno", "crowbar in hand, a grim little smile", "Doors won't open without her. Good thing I don't knock.")]),
    "D9": dict(who=["Marcus"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "D9_marcus_corridor_frame_v1.png", location=CORRIDOR,
        beat="He calls the one man who can open it", engine="care",
        action="Marcus walks down the red corridor, phone to his ear, flashlight low, and speaks low and urgent. "
               "CAMERA: tracks backward ahead of him at his pace, exactly the first frame's chest-up framing, no cut. " + RED + MARCUS + ONLY,
        lines=[Line("Marcus", "walking, low and urgent", "James. It's Lyra. I need the code.")]),
    "D10": dict(who=["James"], director="BAY", duration=5, framing="upper_body", first=FRAMES / "D10_james_rover_frame_v1.png",
        location="the dark cabin of an army prototype rover at night, glowing cyan dashboard screens, a desert outside the windscreen",
        beat="No hesitation", engine="care",
        action="James listens through his headset, already reaching for the controls, and answers without a moment's hesitation, resolute. Then he throws the rover "
               "into motion, the cabin lurching. " + LOCK.replace("no push in, ", "") +
               "He keeps his face, shaved head and army camouflage uniform exactly as in the first frame." + ONLY,
        lines=[Line("James", "resolute, no hesitation", "Twenty minutes.")]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"], beat=s["beat"], engine=s["engine"], location=s["location"], action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
