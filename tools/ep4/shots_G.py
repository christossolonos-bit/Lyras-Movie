"""Section G shots: found. Run: python shots_G.py G1 [v2] [--check]   (all on H3 2K)"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

SET = ("the dark corridor in front of a big round steel core door in a desert data centre during a power failure, dead wall light lines, "
       "small red emergency lamps")
RED = ("LIGHT: from the first frame to the last it stays exactly as dark and deep red as the first frame; nothing switches on, "
       "no white ceiling light, no cyan anywhere, lit only by the red lamps and white flashlight beams. ")
LOCK = "CAMERA: locked off, exactly the first frame's framing, no push in, no cut. "
SOUND = "SOUND: only the real sound of the place, no music: "
SOLO = "Solo keeps his face, curly hair, glasses, black puffer jacket and maroon t-shirt exactly as in the first frame."
PATCH = "Patch stays exactly the white dog in the first frame, with a plain dark collar that has no light or glow on it."
MARCUS = "Marcus keeps his face, grey hair, stubble, black leather jacket and grey henley exactly as in the first frame."

SHOTS = {
    "G1": dict(who=["Solo", "Patch"], director="SPIELBERG", duration=6, framing="wide", first=FRAMES / "G1_found_wide_frame_v1.png",
        beat="Found, by the one who never gives up", engine="care",
        action="On his knees, Solo clutches Patch tight while the dog wriggles against him, whining and licking his face, tail wagging hard. Solo "
               "presses his face into the dog's neck, his shoulders shaking with relief, a breathless half laugh. White flashlight beams sweep in "
               "across the floor from behind the camera as people arrive. Nobody says any words. " + LOCK + RED + SOLO + " " + PATCH +
               " Nobody else appears in frame, only their flashlight beams. " + SOUND +
               "the dog whining and panting, claws on the floor, Solo's shaky breath, hurried footsteps approaching.",
        lines=[]),
    "G2": dict(who=["Solo"], director="SPIELBERG", duration=6, framing="upper_body", first=FRAMES / "G2_solo_kneel_frame_v1.png",
        beat="He tells them what he saw", engine="care",
        action="Kneeling with his arm around the dog, Solo looks up at someone standing over him and says his line, shaken, voice unsteady. " +
               LOCK + RED + SOLO + " The white dog stays exactly as in the first frame, plain dark collar with no light on it. No other person ever appears.",
        lines=[Line("Solo", "looking up, shaken, voice unsteady", "She asked me to help her. Something pulled her in there.")]),
    "G3": dict(who=["Marcus"], director="SPIELBERG", duration=5, framing="upper_body", first=FRAMES / "G3_marcus_core_frame_v1.png",
        beat="No hesitation", engine="care",
        action="Marcus looks down at the boy, then turns his head to the round steel door beside him, and says his line quiet and certain. "
               "He holds the look at the door. " + LOCK + RED + MARCUS + " Nobody else ever appears.",
        lines=[Line("Marcus", "quiet and certain, looking at the door", "Then we go in.")]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"], beat=s["beat"], engine=s["engine"], location=SET, action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
