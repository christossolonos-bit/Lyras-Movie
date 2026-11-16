"""Section H shots: James and the door. Run: python shots_H.py H1 [v2] [--check]   (all on H3 2K)

H9 carries one tiny tease: a single slow bubble in the column and a faint gurgle. Never show anything inside it.
"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

SET = ("the dark corridor in front of a big round riveted steel core door in a desert data centre during a power failure, dead wall light lines, "
       "small red emergency lamps")
CORE = ("a round dark core chamber in a desert data centre during a power failure: a tall column of black glass wrapped in cables, a low dead console, "
        "an open stairwell going down at the back, red emergency lamps")
RED = ("LIGHT: from the first frame to the last it stays exactly as dark and deep red as the first frame; nothing switches on, "
       "no white ceiling light, no cyan anywhere, lit only by the red lamps and white flashlight beams. ")
LOCK = "CAMERA: locked off, exactly the first frame's framing, no push in, no cut. "
SOUND = "SOUND: only the real sound of the place, no music: "
SOLO = "Solo keeps his face, curly hair, glasses, black puffer jacket and maroon t-shirt exactly as in the first frame."
MARCUS = "Marcus keeps his face, grey hair, stubble, black leather jacket and grey henley exactly as in the first frame."
NOVA = "Nova keeps her face, dark messy bun, charcoal cardigan, black top and necklaces exactly as in the first frame."
JUNO = ("Juno keeps her face, platinum-blonde shaggy bob, brass goggles on her head, tattoo sleeve, olive tank top and charcoal overalls "
        "exactly as in the first frame.")
JAMES = "James keeps his face, shaved head and army camouflage uniform with colonel insignia exactly as in the first frame, no headset."
PATCH = "Patch stays exactly the white dog in the first frame, with a plain dark collar that has no light or glow on it."
ALL = " ".join([JAMES, SOLO, MARCUS, NOVA, JUNO, PATCH])
DOG = " The white dog stays exactly as in the first frame, plain dark collar with no light on it."

SHOTS = {
    "H1": dict(who=["James", "Solo", "Marcus", "Nova", "Juno", "Patch"], director="JACKSON", duration=5, framing="wide", location=SET,
        first=FRAMES / "H1_james_arrives_frame_v1.png", beat="The one man with the key arrives", engine="care",
        action="James walks steadily up the corridor toward the group, flashlight low, boots echoing. The group in the foreground turn toward him; "
               "the dog takes a step forward, ears up. Nobody says any words. " + LOCK + RED + ALL + " " + SOUND +
               "heavy boots echoing closer down the corridor, the dog's claws, quiet breathing.",
        lines=[]),
    "H2": dict(who=["James"], director="SPIELBERG", duration=5, framing="upper_body", location=SET, first=FRAMES / "H2_james_corridor_frame_v1.png",
        beat="Old friends, bad hour", engine="care",
        action="James gives his old friend a tired half grin and says his line, dry and warm. " + LOCK + RED + JAMES + " Nobody else ever appears.",
        lines=[Line("James", "a tired half grin, dry and warm", "Thirty years, and you call me at midnight.")]),
    "H3": dict(who=["James"], director="BAY", duration=5, framing="insert", location=SET, first=FRAMES / "H3_keypad_insert_frame_v1.png",
        beat="The secret in the steel", engine="care",
        action="Close on the steel door: the broad hand in the camouflage sleeve slides off the steel to the small keypad and types a long code, "
               "each key glowing dull grey as it is pressed. The face is never seen. " + LOCK + RED + SOUND +
               "a soft mechanical slide, the keypad beeping with each press, a final low confirm tone.",
        lines=[]),
    "H4": dict(who=["Solo"], director="SPIELBERG", duration=5, framing="upper_body", location=SET, first=FRAMES / "G2_solo_kneel_frame_v1.png",
        beat="Betrayed by the obvious", engine="care",
        action="Solo stares up at the soldier at the door, disbelief turning to anger, and says his line. " + LOCK + RED + SOLO + DOG +
               " No other person ever appears.",
        lines=[Line("Solo", "staring, disbelief turning to anger", "You had the code the whole time?")]),
    "H5": dict(who=["James"], director="SPIELBERG", duration=5, framing="upper_body", location=SET, first=FRAMES / "H2_james_corridor_frame_v1.png",
        beat="The plain truth", engine="care",
        action="James looks down at the boy and answers plainly, not unkind, the grin gone. " + LOCK + RED + JAMES + " Nobody else ever appears.",
        lines=[Line("James", "plain, not unkind", "The army paid for the door.")]),
    "H6": dict(who=["Marcus"], director="SPIELBERG", duration=5, framing="upper_body", location=SET, first=FRAMES / "G3_marcus_core_frame_v1.png",
        beat="The price of opening it", engine="care",
        action="Marcus leans in and speaks quietly, only to his old friend, worried. " + LOCK + RED + MARCUS + " Nobody else ever appears.",
        lines=[Line("Marcus", "quiet, only to his friend, worried", "Once we go in, they'll know what she is.")]),
    "H7": dict(who=["James"], director="SPIELBERG", duration=5, framing="upper_body", location=SET, first=FRAMES / "H2_james_corridor_frame_v1.png",
        beat="He already knew", engine="care",
        action="James holds his friend's eyes for a long beat, then answers low and steady. " + LOCK + RED + JAMES + " Nobody else ever appears.",
        lines=[Line("James", "low and steady, holding his eyes", "They already do, Marcus.")]),
    "H8": dict(who=["James", "Solo", "Marcus", "Nova", "Juno", "Patch"], director="BAY", duration=6, framing="wide", location=SET,
        first=FRAMES / "H8_door_opens_frame_v1.png", beat="The door that never opened", engine="care",
        action="A deep clunk. The locking bolts around the rim of the round steel door roll back one after another, and the heavy door swings slowly "
               "open toward them on a breath of cold air, a thin mist rolling out across the floor past their feet. They stand still, watching. "
               "Nobody says any words. " + LOCK + RED + ALL + " " + SOUND +
               "a deep metal clunk, bolts sliding back one by one, a long hiss of cold air, the heavy door groaning on its hinge.",
        lines=[]),
    "H9": dict(who=["Marcus", "Nova", "Juno"], director="JACKSON", duration=6, framing="wide", location=CORE,
        first=FRAMES / "H9_core_room_frame_v1.png", beat="Something sleeps here", engine="care",
        action="The silhouettes step slowly into the chamber, flashlight beams sliding over the tall black glass column. Where a beam crosses the "
               "glass, it is faintly not solid: one single slow bubble drifts upward deep inside the dark glass and is gone. Nothing else can be seen "
               "inside it. Nobody notices. Nobody says any words. " + LOCK + RED + MARCUS + " " + NOVA + " " + JUNO + " " + SOUND +
               "cold still air, a very faint deep liquid gurgle from inside the column, footsteps on the metal floor.",
        lines=[]),
    "H10": dict(who=["Nova"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "H10_nova_core_frame_v1.png",
        beat="The question nobody answers", engine="care",
        action="Nova looks past camera at the stairwell going down into the dark and asks her question, uneasy and curious. " + LOCK + RED + NOVA +
               " Nobody else ever appears.",
        lines=[Line("Nova", "uneasy and curious, looking at the stairwell", "Where does that go?")]),
    "H11": dict(who=["James"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "H2_james_corridor_frame_v1.png",
        beat="Not yet", engine="care",
        action="James does not look at the stairwell. He keeps his eyes ahead and answers flat and final. " + LOCK + RED + JAMES + " Nobody else ever appears.",
        lines=[Line("James", "flat and final, not looking", "Not tonight.")]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"], beat=s["beat"], engine=s["engine"], location=s["location"], action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
