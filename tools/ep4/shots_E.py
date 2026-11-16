"""Section E shots: the rover. Run: python shots_E.py E1 [v2] [--check]

E1 and E2 show only the vehicle. The lock needs a character, so James is listed as the unseen driver;
with a first frame, MiniMax gets no ref images, only the frame, so no face is pushed into the shot.
"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

ROVER = ("the armoured army prototype rover exactly as in the first frame: gunmetal-black and olive-drab armour panels, four huge knobby tyres on "
         "long-travel suspension, a ram bumper, side drone pods, a roof sensor turret, no windscreen, a row of glowing cyan sensor eyes across the front")
UNSEEN = " James drives it from inside and is never visible; no person appears anywhere in the shot."
SOUND = " SOUND: only the real sound of the scene, no music, no voices: "

SHOTS = {
    "E1": dict(who=["James"], director="JACKSON", duration=6, framing="wide_one", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "E1_ridge_frame_v1.png",
        location="the open desert at night under a starry sky, low rocky mountains on the horizon, moonlight",
        beat="Help is coming, fast", engine="care",
        action=f"Over the crest of the sandy ridge, {ROVER}, tips its nose down and charges down the slope toward the camera at speed, "
               "suspension compressing and rebounding, tyres throwing sand, a long dust plume rising behind it in the moonlight, the cyan sensor eyes "
               "growing larger. CAMERA: locked low on the ground, exactly the first frame's wide framing, no cut; the rover ends larger in frame "
               "but never fills it. Keep the stars, the ridge and the mountains." + UNSEEN +
               SOUND + "a heavy diesel-electric engine growling and rising to a roar as it charges, tyres crunching and spraying sand, suspension thumping, desert wind.",
        lines=[]),
    "E2": dict(who=["James"], director="BAY", duration=5, framing="wide_one", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "E2_gate_frame_v1.png",
        location="the entrance gate of a desert data centre at night during a total power failure, chain-link fence, an empty dark guard booth, "
                 "a yellow post, a red-and-white barrier arm down across the road, long dark buildings behind, a full moon",
        beat="The dead gate doesn't stop him", engine="care",
        action=f"Down the access road, {ROVER}, races straight at the gate without slowing. The barrier arm stays down. The rover's ram bumper hits it "
               "and the arm snaps clean off and spins away into the dark, the rover thundering through the gap past the booth and out of frame on "
               "the left, dust swirling in the moonlight behind it. CAMERA: locked low by the booth, exactly the first frame's framing, no cut. "
               "Every light in the buildings and the booth stays dark." + UNSEEN +
               SOUND + "the engine roaring louder as it races in at full speed, a loud crack as the barrier arm snaps, the broken arm clattering on the road, "
                       "the engine thundering past and fading, gravel and dust.",
        lines=[]),
    "E3": dict(who=["James"], director="BAY", duration=5, framing="upper_body", first=FRAMES / "D10_james_rover_frame_v1.png",
        location="the dark cabin of an army prototype rover at night, glowing cyan dashboard screens, a large external camera screen showing the desert",
        beat="A soldier's apology to an old friend", engine="care",
        action="The cabin jolts hard as if something just snapped against the front, James's body rocking in the seat. He winces a little, half a "
               "guilty smile, and says his line to the dark air, gently, as if she could hear him. The camera screen behind him shows the dark facility "
               "rushing closer. CAMERA: locked off, exactly the first frame's chest-up framing, no cut. "
               "He keeps his face, shaved head, headset and army camouflage uniform exactly as in the first frame. Nobody else ever appears.",
        lines=[Line("James", "wincing, half a guilty smile, gently", "Sorry, Lyra. I'll pay for the fence.")]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"], beat=s["beat"], engine=s["engine"], location=s["location"], action=s["action"],
            duration=s["duration"], framing=s["framing"], lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
