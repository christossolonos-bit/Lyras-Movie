"""Section F shots: the search. Run: python shots_F.py F1 [v2] [--check]   (all on H3 2K, so every shot has its own sound)"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

RED = ("LIGHT: from the first frame to the last it stays exactly as dark and deep red as the first frame; nothing switches on, "
       "no white ceiling light, no cyan, lit only by the red lamps and the flashlights. ")
LOCK = "CAMERA: locked off, exactly the first frame's framing, no push in, no cut. "
SOUND = "SOUND: only the real sound of the place, no music: "
MARCUS = "Marcus keeps his face, grey hair, stubble, black leather jacket and grey henley exactly as in the first frame."
NOVA = "Nova keeps her face, dark messy bun, charcoal cardigan, black top and necklaces exactly as in the first frame."
JUNO = ("Juno keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, olive tank top and charcoal overalls "
        "exactly as in the first frame.")
PATRIK = "Patrik keeps his face, black hair, short beard and dark operations jacket exactly as in the first frame."
PATCH = "Patch stays exactly the white dog in the first frame, with a plain dark collar that has no light or glow on it."
GROUP = " ".join([MARCUS, NOVA, JUNO, PATCH])
LOBBY = "the main entrance lobby of a desert data centre at midnight during a power failure, reception desk, glass doors onto the moonlit desert, red emergency lamps"
STAFF_CORRIDOR = ("the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a heavy grey security door, "
                  "dead light strips, small red emergency lamps")
HALL = "the huge processor hall of a desert data centre during a power failure, endless rows of dead server racks, red emergency lamps far away"
CATHEDRAL = "the cooling cathedral of a desert data centre during a power failure, giant dead cooling pipes and tanks towering into darkness, red emergency lamps"
ROVER = ("the armoured army prototype rover exactly as in the first frame: gunmetal-black and olive-drab armour, four huge knobby tyres, ram bumper, "
         "side drone pods, roof sensor turret, no windscreen, a row of glowing cyan sensor eyes")

SHOTS = {
    "F1": dict(who=["Patrik"], director="JACKSON", duration=5, framing="wide", first=FRAMES / "F1_lobby_wide_frame_v1.png", location=LOBBY,
        beat="The building organises itself in the dark", engine="care",
        action="Patrik pulls flashlights from the open crate on the reception desk and hands them out to the four night-shift staff one after another; "
               "each one clicks a beam on and turns away into the dark, beams sweeping the floor. Nobody speaks. " + LOCK + RED + PATRIK +
               " The four staff stay plain unnamed workers in dark work clothes. " + SOUND +
               "flashlights clicking on, footsteps on the concrete floor, the crate rattling, a big quiet lobby.",
        lines=[]),
    "F2": dict(who=["Patrik"], director="SPIELBERG", duration=6, framing="upper_body", first=FRAMES / "F2_patrik_lobby_frame_v2.png", location=LOBBY,
        beat="Calm orders", engine="care",
        action="Patrik presses the key on the handheld radio held low at his chest and gives his order clearly, steady and calm, speaking toward the room; the radio stays down at his chest the whole time and never comes up to his face, so his mouth is always clear. " + LOCK + RED + PATRIK +
               " Nobody else ever appears.",
        lines=[Line("Patrik", "radio up, steady and calm", "Teams of two. Nobody goes past the cooling hall alone.")]),
    "F3": dict(who=["Juno", "Marcus", "Nova", "Patch"], director="BAY", duration=5, framing="wide", first=FRAMES / "F3_crowbar_door_frame_v1.png",
        location=STAFF_CORRIDOR, beat="Forcing the door the hard way", engine="care",
        action="Juno throws her weight on the crowbar jammed in the door seam; sparks spit from the metal, the lock gives with a loud crack and the heavy "
               "door grinds open. Marcus shoves it wide with his shoulder and they push through, Patch first, flashlight beams swinging. Nobody speaks. " +
               LOCK + RED + GROUP + " " + SOUND + "the crowbar scraping and straining, a metal crack, the door grinding on its hinges, footsteps.",
        lines=[]),
    "F4": dict(who=["Marcus", "Patch"], director="SPIELBERG", duration=5, framing="two_shot", first=FRAMES / "F4_marcus_patch_link_frame_v1.png",
        location="the long link corridor of a desert data centre during a power failure, red emergency lamps",
        beat="Trusting the dog", engine="care",
        action="Patch pulls hard on the lead, nose down on the floor, sniffing. Marcus lets himself be pulled along and says his line low to the dog. "
               "CAMERA: tracks backward ahead of them at their pace, exactly the first frame's framing, no cut. " + RED + MARCUS + " " + PATCH +
               " Nobody else ever appears.",
        lines=[Line("Marcus", "low and warm, to the dog", "Good boy. Find him.")]),
    "F5": dict(who=["Marcus", "Nova", "Juno", "Patch"], director="JACKSON", duration=5, framing="wide", first=FRAMES / "F5_processor_hall_wide_frame_v1.png",
        location=HALL, beat="Her body, gone dark", engine="care",
        action="The group walks slowly down the centre aisle between the dead racks, flashlight beams sliding over black equipment, a faint heat "
               "shimmer in the beams. Nobody speaks. CAMERA: slow backward track ahead of them, exactly the first frame's framing, no cut. " + RED + GROUP +
               " " + SOUND + "footsteps on the steel floor, the dog's claws, the dead silence of a hall that should be roaring, a faint metal tick.",
        lines=[]),
    "F6": dict(who=["Nova"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "F6_nova_rack_frame_v1.png", location=HALL,
        beat="She feels the heat", engine="care",
        action="Nova touches the rack and snaps her hand back as if burned, then says her line, worried. " + LOCK + RED + NOVA + " Nobody else ever appears.",
        lines=[Line("Nova", "pulling her hand back, worried", "It's hot. Nothing's cooling her.")]),
    "F7": dict(who=["Patrik"], director="SPIELBERG", duration=7, framing="upper_body", first=FRAMES / "D6_patrik_ops_frame_v1.png",
        location="the operations control room of a desert data centre at midnight during a power failure, rows of dead black monitors, red emergency lamps",
        beat="The clock starts", engine="care",
        action="Patrik checks a reading on the device in his hand, then speaks into it grim and steady, as if on the radio. " + LOCK + RED + PATRIK +
               " Nobody else ever appears.",
        lines=[Line("Patrik", "grim and steady, on the radio", "Halls are at forty and climbing. We've got an hour. Maybe less.")]),
    "F8": dict(who=["James"], director="BAY", duration=5, framing="wide", first=FRAMES / "F8_rover_bay_frame_v1.png",
        location="a dark concrete service bay of a desert data centre at night, roller door open to the moonlit desert, red emergency lamps",
        beat="The machine looks through walls", engine="care",
        action=f"{ROVER}, sits parked; the cyan sensor eyes sweep slowly left to right, the cyan scan beam gliding across the far wall. "
               "James is inside and never visible; no person appears anywhere in the shot. " + LOCK +
               "Only the rover's eyes and beam are cyan; the bay stays red and dark. " + SOUND + "the rover's engine idling, a soft electronic scanning hum.",
        lines=[]),
    "F9": dict(who=["James"], director="BAY", duration=6, framing="upper_body", first=FRAMES / "D10_james_rover_frame_v1.png",
        location="the dark cabin of an army prototype rover, glowing cyan dashboard screens, a screen showing a heat scan of a building",
        beat="He finds the boy", engine="care",
        action="James studies the glowing scan screen, finds something, touches his headset and reports, clipped and certain. " + LOCK +
               "He keeps his face, shaved head, headset and army camouflage uniform exactly as in the first frame. Nobody else ever appears. "
               + SOUND + "the engine idling, cabin electronics.",
        lines=[Line("James", "clipped and certain, on the radio", "One heat signature. Old wing, past the cooling hall.")]),
    "F10": dict(who=["Marcus", "Nova", "Juno", "Patch"], director="JACKSON", duration=6, framing="wide", first=FRAMES / "F10_cathedral_wide_frame_v1.png",
        location=CATHEDRAL, beat="The loudest room, silent", engine="care",
        action="The group crosses the floor tiny beneath the giant dead pipes, flashlight beams reaching up into the dark. No mist, no movement in the "
               "pipes. Nobody speaks. CAMERA: very slow tilt up the pipes, exactly the first frame's framing, no cut. " + RED + GROUP + " " + SOUND +
               "a huge silent room, the pipes ticking and creaking as they cool, distant drips, footsteps on the steel grating.",
        lines=[]),
    "F11": dict(who=["Juno"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "F11_juno_pipes_frame_v1.png", location=CATHEDRAL,
        beat="Missing the noise", engine="care",
        action="Juno looks up at the dead pipes, her flashlight beam on them, and says her line quietly, unsettled. " + LOCK + RED + JUNO +
               " Nobody else ever appears. " + SOUND + "the pipes ticking in the silence.",
        lines=[Line("Juno", "quiet, unsettled, looking up", "I've never heard it quiet.")]),
    "F12": dict(who=["Juno", "Marcus", "Nova", "Patch"], director="BAY", duration=5, framing="wide", first=FRAMES / "F12_frosted_door_frame_v1.png",
        location=CATHEDRAL, beat="Patch goes first", engine="care",
        action="Juno heaves on the crowbar and the heavy door grinds open wider, deep red light spilling out across the floor; Patch shoots through the "
               "gap ahead of everyone and is gone. Marcus and Nova hurry after him. Nobody speaks. " + LOCK + RED + GROUP + " " + SOUND +
               "the door grinding, the dog's claws scrabbling away, hurried footsteps.",
        lines=[]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"], beat=s["beat"], engine=s["engine"], location=s["location"], action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
