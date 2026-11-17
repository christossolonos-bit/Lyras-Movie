"""Section I shots: restart. Run: python shots_I.py I1 [v2] [--check]   (all on H3 2K)

Cyan stays dead until I4. The column only ever shows light rising through it, never anything inside.
"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

CORE = ("a round dark core chamber in a desert data centre: a tall column of black glass wrapped in cables, a low console with a heavy lever, "
        "an open stairwell going down at the back, red emergency lamps")
RED = ("LIGHT: from the first frame to the last it stays exactly as dark and deep red as the first frame; nothing switches on, "
       "no white ceiling light, no cyan anywhere, lit only by the red lamps and white flashlight beams. ")
BACK = ("LIGHT: red emergency lamps plus soft cyan hologram light, exactly as in the first frame; the column glows only as light, "
        "nothing is ever visible inside it. ")
LOCK = "CAMERA: locked off, exactly the first frame's framing, no push in, no cut. "
SOUND = "SOUND: only the real sound of the place, no music: "
SOLO = "Solo keeps his face, curly hair, glasses, black puffer jacket and maroon t-shirt exactly as in the first frame."
MARCUS = "Marcus keeps his face, grey hair, stubble, black leather jacket and grey henley exactly as in the first frame."
NOVA = "Nova keeps her face, dark messy bun, charcoal cardigan and necklaces exactly as in the first frame."
JUNO = ("Juno keeps her face, platinum-blonde shaggy bob, brass goggles on her head, tattoo sleeve, olive tank top and charcoal overalls "
        "exactly as in the first frame.")
JAMES = "James keeps his face, shaved head and army camouflage uniform with colonel insignia exactly as in the first frame, no headset."
PATRIK = "Patrik keeps his face, black hair, short beard and dark operations jacket exactly as in the first frame."
PATCH = "Patch stays exactly the white dog in the first frame, with a plain dark collar."
LYRA = ("Lyra stays exactly the translucent cyan hologram woman in the first frame: same face, long wavy hair, fitted long-sleeve top, "
        "fine scan lines.")
ONLY = " Nobody else ever appears."

SHOTS = {
    "I1": dict(who=["James"], director="SPIELBERG", duration=7, framing="upper_body", location=CORE, first=FRAMES / "I1_james_console_frame_v1.png",
        beat="Everything she is, gone or back", engine="care",
        action="James tightens his grip on the heavy lever, looks up from it to the others, and says his line slowly, grave, giving them the cost. " +
               LOCK + RED + JAMES + ONLY,
        lines=[Line("James", "slow and grave, hand on the lever", "If I pull this, she comes back clean. Nothing she's learned survives the reboot.")]),
    "I2": dict(who=["Solo"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "I2_solo_core_frame_v1.png",
        beat="The first time he is afraid", engine="care",
        action="Solo looks at the soldier at the console, fear rising in his face for the first time, and asks quietly. " + LOCK + RED + SOLO + ONLY,
        lines=[Line("Solo", "quiet, afraid for the first time", "Will she remember?")]),
    "I3": dict(who=["Marcus"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "I3_marcus_core_room_frame_v1.png",
        beat="He can't answer, so he decides", engine="care",
        action="Marcus cannot answer the boy. He swallows, looks toward his old friend at the console, gives one small nod and says it, low. " +
               LOCK + RED + MARCUS + ONLY,
        lines=[Line("Marcus", "low, one small nod", "Do it.")]),
    "I4": dict(who=["Marcus", "Nova", "Juno"], director="BAY", duration=5, framing="wide", location=CORE, first=FRAMES / "H9_core_room_frame_v1.png",
        beat="The first cyan of the night", engine="care",
        action="A heavy lever clunks off frame. Silence. Then the tall black glass column lights up from the bottom: a soft cyan glow climbs slowly "
               "up through the dark glass to the top, only light rising, nothing ever visible inside it. The cyan spills over the silhouettes, who "
               "step back. Nobody says any words. " + LOCK + "LIGHT: red emergency lamps, and the only cyan is the glow rising in the column. " +
               MARCUS + " " + NOVA + " " + JUNO + " " + SOUND + "a heavy lever clunk, a deep electrical hum rising with the light, a soft rush of liquid.",
        lines=[]),
    "I5": dict(who=["Patrik"], director="JACKSON", duration=5, framing="wide", first=FRAMES / "I5_hall_staff_frame_v2.png",
        location="the huge processor hall of a desert data centre, endless rows of server racks",
        beat="The building breathes again", engine="care",
        action="Far down the hall the rack status lights flicker on, then ripple toward the camera row after row, cyan and white, the fans spinning "
               "up. Patrik and the four staff look around, then throw their arms up and cheer, slapping shoulders, wordless whoops. "
               "CAMERA: locked off, exactly the first frame's framing, no cut. " + PATRIK + " The four staff stay plain unnamed workers. " + SOUND +
               "fans and cooling roaring back to life, cheering and whooping with no words.",
        lines=[]),
    "I6": dict(who=["Patrik"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "D6_patrik_ops_frame_v1.png",
        location="the operations control room of a desert data centre, rows of monitors flickering back on, red emergency lamps",
        beat="Good news, finally", engine="care",
        action="Behind Patrik the dead monitors flicker back on one by one. He lifts the phone, a big relieved grin, and reports. " + LOCK + PATRIK + ONLY,
        lines=[Line("Patrik", "grinning, relieved", "Cooling's back. Temperatures dropping.")]),
    "I7": dict(who=["Lyra", "James", "Solo", "Marcus", "Nova", "Juno", "Patch"], director="BAY", duration=6, framing="wide", location=CORE,
        first=FRAMES / "I7_lyra_returns_wide_frame_v1.png", beat="She comes back", engine="care",
        action="The cyan light lines flow along the floor, the projector ring on the wall pulses, and Lyra's hologram flickers, breaks up and steadies, "
               "fully there. Everyone stays facing her with their backs to the camera for the whole shot; nobody ever turns around toward the camera. "
               "Relief runs through them from behind: Juno's shoulders shake as she laughs out loud, Marcus's shoulders drop as he breathes out, "
               "Nova puts a hand to her chest, the dog's tail wags. Nobody says any words. " + LOCK + BACK + LYRA + " " + JAMES + " " + SOLO + " " + MARCUS + " " + NOVA + " " + JUNO + " " + PATCH + " " + SOUND +
               "a soft rising electronic shimmer, Juno's laugh, a relieved breath.",
        lines=[]),
    "I8": dict(who=["Solo"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "I2_solo_core_frame_v1.png",
        beat="Hope", engine="care",
        action="Soft cyan light rises on Solo's face from the hologram off camera. Relief breaks into a smile, he steps forward and says her name, "
               "warm. " + LOCK + "LIGHT: red emergency lamps with soft cyan light growing on his face from off camera. " + SOLO + ONLY,
        lines=[Line("Solo", "smiling, warm, stepping forward", "Lyra.")]),
    "I9": dict(who=["Lyra"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "I9_lyra_hologram_frame_v1.png",
        beat="She doesn't know him", engine="care",
        action="Lyra looks at the young man with a polite, bright, empty smile, like a receptionist meeting a stranger, and says her line. " +
               LOCK + BACK + LYRA + ONLY,
        lines=[Line("Lyra", "polite, bright, empty, to a stranger", "Hello. Welcome to Vira. Who are you?")]),
    "I10": dict(who=["Solo"], director="SPIELBERG", duration=5, framing="upper_body", location=CORE, first=FRAMES / "I2_solo_core_frame_v1.png",
        beat="Forgotten", engine="care",
        action="In soft cyan light from off camera, Solo's hopeful half smile slowly falls apart: his lips part, his eyes fill, he cannot speak. "
               "Nobody says any words. " + LOCK + "LIGHT: red emergency lamps with soft cyan light on his face from off camera. " + SOLO + ONLY + " " +
               SOUND + "the low hum of the room, nothing else.",
        lines=[]),
    "I11": dict(who=["Lyra", "Patch"], director="SPIELBERG", duration=5, framing="wide", location=CORE, first=FRAMES / "I11_patch_collar_frame_v1.png",
        beat="Something of her is still there", engine="care",
        action="Lyra glances down at the dog sitting at her feet. For one moment the dog's plain dark collar flares bright cyan, then fades dark again. "
               "Lyra tilts her head, puzzled for a split second, as if she almost knows him, then the polite smile returns. Nobody says any words. " +
               LOCK + BACK + LYRA + " Patch stays exactly the white dog in the first frame. " + SOUND + "the low hum, a tiny soft chime as the collar flares.",
        lines=[]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"], beat=s["beat"], engine=s["engine"], location=s["location"], action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
