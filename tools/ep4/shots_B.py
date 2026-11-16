"""Section B shots: Marcus's office. Run: python shots_B.py B1 [v2] [--check]"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

SET = "a dark executive office at midnight during a power failure, a wall of data screens running on battery, one red emergency lamp, night city windows"
KEEP = ("Keep the first frame's set and light exactly: the office, the couch, the wall of data screens glowing pale blue-white, the red emergency lamp, night windows. "
        "No cyan hologram, nobody else ever appears. Marcus keeps his mature late-40s face, salt-and-pepper hair, grey-flecked beard, black leather jacket and grey henley "
        "exactly as in the first frame, never younger.")
SHOTS = {
    "B1": dict(director="SPIELBERG", framing="insert", duration=5, model="minimax/hailuo-3-max", res="768p", first=FRAMES / "B1_frame_v1.png",
               beat="The watch tells him something has never happened before", engine="care",
               action="The smartwatch on his wrist buzzes hard and its red warning screen pulses. His fingers tense, then the wrist turns slightly toward him "
                      "as he looks down at it. CAMERA: locked close-up on the wrist and watch, exactly the first frame's framing, the screens and red lamp soft behind. " + KEEP,
               lines=[]),
    "B2": dict(director="SPIELBERG", framing="upper_body", duration=5, model="minimax/hailuo-3", res="2K", first=FRAMES / "B2_B4_frame_v1.png",
               beat="For the first time she does not answer him", engine="care",
               action="He looks up from his watch at the room and says her name, the way he has a thousand times, expecting her voice back. "
                      "Nothing answers. He waits, eyes moving across the ceiling, his jaw tightening. "
                      "CAMERA: locked off, chest-up, exactly the first frame's framing, no cut. " + KEEP,
               lines=[Line("Marcus", "looks up at the room, calm but uneasy, expecting an answer", "Lyra?")]),
    "B3": dict(director="JACKSON", framing="wide_one", duration=5, model="minimax/hailuo-3-max", res="768p", first=FRAMES / "B_office_wide_v1.png",
               beat="The building goes dark around him", engine="care",
               action="Silence. Behind him the wall of data screens dies panel by panel, each one blinking out to black, until only the red emergency lamp lights the room. "
                      "As the last screen goes dark he rises slowly from the couch and stands, looking at the black wall. "
                      "CAMERA: completely locked off, exactly the first frame's wide framing, no push in, no cut. He stays small in the frame. " + KEEP.replace(
                      "the wall of data screens glowing pale blue-white, ", ""),
               lines=[]),
    "B4": dict(director="SPIELBERG", framing="upper_body", duration=5, model="minimax/hailuo-3", res="2K", first=FRAMES / "B2_B4_frame_v1.png",
               beat="He realises this has never happened before", engine="care",
               action="Still looking up at the silent room, it hits him. His brow knots, his eyes widen, he leans forward off the couch, one hand gripping "
                      "his knee, and he says it with real alarm, his voice dropping and breaking on the last word. His breathing quickens, his eyes dart across "
                      "the room. Expressive and human, a man suddenly afraid for someone he loves, never cartoonish. "
                      "CAMERA: chest-up, the first frame's framing, a slight handheld push as he leans in, no cut. " + KEEP,
               lines=[Line("Marcus", "leaning forward, alarmed, his voice dropping and breaking on the last word", "That's never happened before.")]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=["Marcus"], beat=s["beat"], engine=s["engine"], location=SET, action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s["model"], resolution=s["res"])
