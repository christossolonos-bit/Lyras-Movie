"""Section A shots. Run: python shots_A.py A1 [--check]"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

SET = "an old dark concrete corridor deep underground with a giant round riveted steel door in the left wall, during a total power failure, lit only by red emergency lamps"
KEEP = ("Keep the first frame's set exactly: the same corridor, the round door, the two dead unlit glass strips on the wall either side of it, red emergency light, darkness. "
        "No cyan light anywhere. Solo keeps his face, curly hair, glasses, black puffer jacket and maroon t-shirt exactly as in the first frame. "
        "Nobody else ever appears.")
SHOTS = {
    "A1": dict(director="BAY", framing="wide_one", duration=6, model="minimax/hailuo-3", res="2K", first=FRAMES / "A1_frame_v1.png",
               beat="Solo is alone in the dark, the one he came for is gone", engine="care",
               action="The emergency power stutters: the red lamps flicker and cut out to near black, then with a heavy electrical clunk they come back on, "
                      "one after another down the corridor, and hold. Through it he stands alone before the round door, breathing hard, chest rising, staring at it. "
                      "CAMERA: completely locked off on a tripod, no push in, no zoom, no movement at all. He stays small in the wide frame, full length, "
                      "exactly as in the first frame, for the whole clip. " + KEEP, lines=[]),
    "A2": dict(director="SPIELBERG", framing="upper_body", duration=5, model="minimax/hailuo-3", res="2K", first=FRAMES / "A2_A4_frame_v1.png",
               beat="He calls for her and nothing answers", engine="care",
               action="He looks at the dead glass strip on the wall by the round door and calls once, quietly, his voice catching. Then he waits, listening, "
                      "and nothing answers: only his breathing and the hum of the red lamps. His eyes search the wall. "
                      "CAMERA: locked off, chest-up, exactly the first frame's framing, a faint handheld breath. " + KEEP,
               lines=[Line("Solo", "looks at the dead strip on the wall and calls quietly, scared", "Lyra?")]),
    "A3": dict(director="SPIELBERG", framing="knees_one", duration=5, model="minimax/hailuo-3", res="2K", first=FRAMES / "A3_frame_v1.png",
               beat="The doors only ever opened for her, and now they won't", engine="care",
               action="He presses his palm on the dead wall box, waits, presses it again harder. Nothing: the ring stays dark and the steel door stays shut. "
                      "He pushes against the door with his other hand, then speaks to it under his breath, frustrated. "
                      "CAMERA: locked off, knees-up, exactly the first frame's framing. Keep the first frame's set exactly: the sealed steel door, the dead "
                      "brushed-metal wall box with its dark ring, one caged red emergency lamp, darkness. No cyan light anywhere. He keeps his face, curly hair, "
                      "glasses, black puffer jacket and maroon t-shirt exactly as in the first frame. Nobody else ever appears.",
               lines=[Line("Solo", "presses the dead wall box again and pushes the door, frustrated, under his breath", "Come on. Open.")]),
    "A4": dict(director="SPIELBERG", framing="upper_body", duration=6, model="minimax/hailuo-3", res="2K", first=FRAMES / "A2_A4_frame_v1.png",
               beat="He refuses to leave her", engine="care",
               action="He steps to the round door at frame left and lays his palm flat on the cold steel, his forehead close to it. His breathing slows. "
                      "He speaks to the door softly, a promise, steady even though he is scared. Then he stays there, hand on the door, eyes closed for a moment. "
                      "CAMERA: chest-up, starting on the first frame's framing and drifting a little left with him as he moves to the door, gentle handheld. " + KEEP,
               lines=[Line("Solo", "palm flat on the round door, speaking softly to it, a quiet promise", "I'm here. I'm not going anywhere.")]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=["Solo"], beat=s["beat"], engine=s["engine"], location=SET, action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s["model"], resolution=s["res"])
