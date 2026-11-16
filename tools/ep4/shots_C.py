"""Section C shots: Nova and Juno lose her mid-sentence. Run: python shots_C.py C_nova [v2] [--check]"""
import sys
from ep4_lib import Shot, Line, FRAMES, CLIPS, build_prompt, clip

CUT = ("Mid-sentence, the power fails: the glowing cyan line on the wall dies instantly to black, the room lights cut out, and a red emergency lamp "
       "clunks on, washing everything in deep red. From that moment there is no cyan light anywhere. ")
SHOTS = {
    "C_nova": dict(who="Nova", director="SPIELBERG", duration=9, first=FRAMES / "C_nova_frame_v1.png",
        location="the staff break room of a desert data centre at midnight, a round table, a coffee machine, a black night window",
        beat="She loses the voice she talks to every day", engine="care",
        action="She laughs up at the glowing cyan line on the wall, teasing, mug in hand, and says her first line playfully. " + CUT +
               "She flinches hard, startled, a sharp breath in, coffee sloshing as she grips the mug. Her smile drops instantly, her eyes go wide and dart across "
               "the dead wall and the ceiling, her brow pulled up with alarm, she half rises from the chair. Then she calls to the dark wall, her voice "
               "catching, frightened and urgent. Expressive and human, real fear for a friend, never cartoonish. "
               "CAMERA: locked off, chest-up, exactly the first frame's framing, no cut. Keep the break room, the table, the mug and the black window. "
               "She keeps her face, dark messy bun, charcoal cardigan and necklaces exactly as in the first frame. Nobody else ever appears.",
        lines=[Line("Nova", "laughing up at the wall, teasing", "No, you tell him. He'll believe it from you."),
               Line("Nova", "half rising, calling to the dark wall, frightened and urgent", "Lyra?")]),
    "C_juno": dict(who="Juno", director="SPIELBERG", duration=9, first=FRAMES / "C_juno_frame_v1.png",
        location="Juno's cluttered repair workshop inside a desert data centre at midnight, workbench, gutted machines, hanging tools, an old radio, warm work lamps",
        beat="She loses the voice she works beside every day", engine="care",
        action="Soldering at her bench, grinning, she talks to the glowing cyan line on the wall beside her like a workmate, and says her first line, "
               "then laughs at her own joke. " + CUT +
               "The work lamps die too. She jolts, the soldering iron jerks away from the board, a sharp breath in. Her grin vanishes, her eyes go wide "
               "and snap to the dead wall line, she pushes her goggles up and leans toward it, brow pulled up with alarm. Then she calls to the dark wall, "
               "her voice catching, frightened. Expressive and human, real fear for a friend, never cartoonish. "
               "CAMERA: locked off, chest-up, exactly the first frame's framing, no cut. Keep the workshop, the bench, the radio and the clutter. "
               "She keeps her face, platinum-blonde shaggy bob, freckles, brass goggles, tattoo sleeve, olive tank top and charcoal overalls exactly as in "
               "the first frame. Nobody else ever appears.",
        lines=[Line("Juno", "grinning at the wall line while she solders", "Hold the light steady. Okay, you don't have hands."),
               Line("Juno", "leaning toward the dead wall, frightened", "Lyra?")]),
    "C5a": dict(who="Nova", director="SPIELBERG", duration=5, framing="wide_one", model="minimax/hailuo-3-max", res="768p",
        first=FRAMES / "C5a_nova_exit_frame_v2.png", location="the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, ceiling lights off, small red emergency lamps high on the walls, a glass door at the far end",
        beat="She goes looking for help", engine="care",
        action="Nova pushes the break room door wide and steps out into the red corridor, frightened, looks both ways down the empty corridor, "
               "then lets the door swing and hurries away down the corridor, away from the camera, glancing back once. "
               "CAMERA: completely locked off, exactly the first frame's wide framing, no push in, no cut. She stays small in the frame. "
               "There is no round door anywhere. She keeps her face, dark messy bun, charcoal cardigan and necklaces exactly as in the first frame. Nobody else ever appears.",
        lines=[]),
    "C5b": dict(who="Juno", director="SPIELBERG", duration=5, framing="wide_one", model="minimax/hailuo-3-max", res="768p",
        first=FRAMES / "C5b_juno_exit_frame_v2.png", location="the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, ceiling lights off, small red emergency lamps high on the walls, a glass door at the far end",
        beat="She goes looking for help", engine="care",
        action="Juno shoulders the heavy workshop door open and squeezes out into the red corridor, her small flashlight beam sweeping the dark walls, frightened, "
               "then she hurries away down the corridor, away from the camera, the beam bobbing ahead of her. "
               "CAMERA: completely locked off, exactly the first frame's wide framing, no push in, no cut. She stays small in the frame. "
               "There is no round door anywhere. She keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, "
               "olive tank top and charcoal overalls exactly as in the first frame. Nobody else ever appears.",
        lines=[]),
    "C5c": dict(who=["Nova", "Juno"], director="SPIELBERG", duration=5, framing="two_react", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "C5c_scare_frame_v2.png",
        location="a blind corner where two staff-level corridors of a desert data centre meet, midnight, power failure, pale concrete wall panels, a dead unlit strip along the walls, small red emergency lamps",
        beat="In the dark they frighten each other", engine="care",
        action="Nova hurries round the corner from the left and Juno from the right with her flashlight, and they almost walk straight into each other. "
               "Both jump back and give one short startled scream at the same moment, the flashlight beam swinging across Nova's face. "
               "A beat, they recognise each other, Nova clutches her chest, Juno lets out a shaky breath and half laughs from nerves, then fear returns to both faces. "
               "No words, only the scream and breathing. Expressive and human, never cartoonish. "
               "CAMERA: locked off, knees-up, exactly the first frame's framing, no cut. Keep the corner, the pale wall panels and the red wall lamps. There is no round door anywhere. "
               "Nova keeps her face, dark messy bun, charcoal cardigan and necklaces; Juno keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, "
               "tattoo sleeve, olive tank top and charcoal overalls, exactly as in the first frame. Nobody else ever appears.",
        lines=[]),
    "C7a": dict(who=["Nova", "Juno"], director="SPIELBERG", duration=5, framing="two_shot", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "C7_run_twoshot_frame_v1.png", location="the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, ceiling lights off, small red emergency lamps high on the walls", beat="Running, they check what happened", engine="care",
        action="Nova and Juno run side by side straight toward the camera down the red corridor, breathless and frightened, arms pumping. Nova glances across at Juno and asks her line between breaths. Juno keeps running beside her, listening, her mouth closed. CAMERA: tracks backward ahead of them at their speed, exactly the first frame's waist-up framing, never closer, no cut. LIGHT: from the first frame to the last the corridor stays exactly as dark and deep red as the first frame; nothing switches on, the pale walls never turn grey or white, faces stay lit only by red. Keep the pale wall panels and the dead wall strip. There is no round door anywhere. Nova keeps her face, dark messy bun, charcoal cardigan and necklaces; Juno keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, olive tank top and charcoal overalls, exactly as in the first frame. Nobody else ever appears.",
        lines=[Line("Nova", "glancing across while running, breathless", "Did she go quiet on you too?")]),
    "C7b": dict(who=["Nova", "Juno"], director="SPIELBERG", duration=6, framing="two_shot", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "C7_run_twoshot_frame_v1.png", location="the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, ceiling lights off, small red emergency lamps high on the walls", beat="Running, they check what happened", engine="care",
        action="Nova and Juno run side by side straight toward the camera down the red corridor, breathless and frightened, arms pumping. Juno answers fast and breathless while running, upset, shaking her head, waving the flashlight in her hand, her voice cracking on the last words. Nova keeps running beside her, listening, her mouth closed. CAMERA: tracks backward ahead of them at their speed, exactly the first frame's waist-up framing, never closer, no cut. LIGHT: from the first frame to the last the corridor stays exactly as dark and deep red as the first frame; nothing switches on, the pale walls never turn grey or white, faces stay lit only by red. Keep the pale wall panels and the dead wall strip. There is no round door anywhere. Nova keeps her face, dark messy bun, charcoal cardigan and necklaces; Juno keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, olive tank top and charcoal overalls, exactly as in the first frame. Nobody else ever appears.",
        lines=[Line("Juno", "running, fast and breathless, shaking her head, voice cracking at the end", "Mid-joke, Nova! She just stopped. She's never stopped.")]),
    "C7c": dict(who=["Nova", "Juno"], director="SPIELBERG", duration=5, framing="two_shot", model="minimax/hailuo-3", res="2K",
        first=FRAMES / "C7_run_twoshot_frame_v1.png", location="the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, ceiling lights off, small red emergency lamps high on the walls", beat="Running, she pushes them on", engine="care",
        action="Nova and Juno run side by side straight toward the camera down the red corridor, breathless and frightened, arms pumping. Nova pushes ahead a little, determined, and says her line, waving Juno on. Juno keeps running beside her, listening, her mouth closed. CAMERA: tracks backward ahead of them at their speed, exactly the first frame's waist-up framing, never closer, no cut. LIGHT: from the first frame to the last the corridor stays exactly as dark and deep red as the first frame; nothing switches on, the pale walls never turn grey or white, faces stay lit only by red. Keep the pale wall panels and the dead wall strip. There is no round door anywhere. Nova keeps her face, dark messy bun, charcoal cardigan and necklaces; Juno keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, olive tank top and charcoal overalls, exactly as in the first frame. Nobody else ever appears.",
        lines=[Line("Nova", "pushing ahead, determined, waving her on", "Marcus will know. Come on.")]),
    "C6": dict(who=["Nova", "Juno"], director="BAY", duration=6, framing="wide", model="minimax/hailuo-3-max", res="768p",
        first=FRAMES / "C6_meet_frame_v2.png",
        location="the staff-level corridor of a desert data centre at midnight during a power failure, pale concrete wall panels, a dead unlit strip along both walls, ceiling lights off, small red emergency lamps high on the walls, a glass door at the far end",
        beat="Together they run for help", engine="care",
        action="Nova and Juno have just met in the red corridor. They glance at each other, frightened, and Juno gives one quick nod. Then both break into a full run "
               "side by side straight toward the camera, arms pumping, red lamp light streaking over them as they pass each wall lamp. Urgent, breathless, real fear for a friend. "
               "CAMERA: tracks backward ahead of them at the same speed, so they stay the same size in frame as in the first frame, never closer; no push in, no cut. "
               "Keep the corridor, the pale wall panels and the red wall lamps. There is no round door anywhere. Nova keeps her face, dark messy bun, charcoal cardigan and necklaces; "
               "Juno keeps her face, platinum-blonde shaggy bob, freckles, brass goggles up on her head, tattoo sleeve, tank top and charcoal overalls, exactly as in the first frame. "
               "Nobody else ever appears.",
        lines=[]),
}
cid = sys.argv[1]; s = SHOTS[cid]
shot = Shot(id=cid, director=s["director"], characters=s["who"] if isinstance(s["who"], list) else [s["who"]], beat=s["beat"], engine=s["engine"], location=s["location"], action=s["action"],
            duration=s["duration"], framing=s.get("framing", "upper_body"), lines=s["lines"], first_frame=s["first"])
if "--check" in sys.argv:
    p = build_prompt(shot); print(p); print("chars:", len(p)); raise SystemExit
ver = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "v1"
clip(shot, CLIPS / f"{cid}_{ver}.mp4", model=s.get("model", "minimax/hailuo-3"), resolution=s.get("res", "2K"))
