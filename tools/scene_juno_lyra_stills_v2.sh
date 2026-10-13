#!/bin/bash
# v2 keyframes for "Juno fixes the projector" (jk*), built around fixed camera setups so chained clips never jump angles.
# Setups: A = wide master from the door (jl1), B = low medium on Juno at the platform, C = Marcus at desk (jl7), D = close/inserts.
# Same-setup frames are generated FROM the previous frame of that setup (first --ref) so framing/geography stay locked.
# Chained joins: 2->3 (B), 8->9 (B tilt up), 10->11 (A). Everything else is a hard cut.
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, natural color grade, no text."
J="Juno from her character sheet (tousled platinum-blonde shaggy bob, freckles, mechanical tattoo sleeve on her right arm, olive tank top, grease-stained charcoal overalls, brass goggles in her hair, eyes a little red from crying) - match her face exactly."
L="Lyra from her character sheet as a hologram: semi-transparent glowing cyan light, scan lines, floating particles - match her face exactly."
M="Marcus from his reference (48, salt-and-pepper hair, stubble, black leather jacket over grey henley) - match his face exactly."
SAME="Keep the exact same camera position, lens, height, framing, room, lighting and character positions as the FIRST reference image; only change what is described."
PLAT="The projector platform is exactly the one in the wide reference: a single LOW circular brushed-steel disc only about shin height and two meters across, concentric rings on its top surface, sitting on the floor - NOT a tall block or pedestal. A curved access panel has been removed from its side, exposing circuit boards and cables inside the rim."
B="Camera setup B: low camera near floor level a few meters from the platform, looking across it toward the curved monitor wall; Juno is on the floor right beside the platform. $PLAT There is only ONE platform in the entire room - the floor behind and around Juno is empty open floor, no other discs or platforms anywhere."
g(){ n=$1; p=$2; shift 2; [ -f "images/$n.png" ] && return; python tools/gen_image.py "$n" "$p $S" --ref "$@" > "logs_$n.txt" 2>&1 & }
fin(){ wait; cat logs_*.txt 2>/dev/null; rm -f logs_*.txt; }
# reused frames
cp images/jl1_arrival.png images/jk1_walk_in.png
cp images/jl7_marcus_listening.png images/jk7_marcus.png
# wave 1: setup anchors
g jk2_under "$B In the command room from the room reference. Juno lies on her back on the floor with her head and shoulders right against the open side of the dark platform, reaching into the exposed circuitry, the removed curved panel lying beside her, headlamp on, tools on the floor, frozen mid-motion, eyes flicking up, startled by a voice. $J" images/juno_ref.png images/jk10_wide.png images/jk1_walk_in.png
g jk6_solder "Close-up insert at floor level: Juno, goggles down over her eyes, leans into the open side of the low round brushed-steel projector platform where a curved access panel has been removed, touching a soldering iron to a circuit board inside the rim; a thin curl of smoke rises, a tiny spark, her cocky grin lit by the work light. Only the platform rim, her hands and her face in frame, dark command room blurred behind. $J" images/juno_ref.png images/jk5_board.png
g jk4_close "Tight close-up of Juno's face as she lies on her back on the floor beside the open low round projector platform in the dark command room, the platform's brushed-steel rim and exposed circuitry blurred at the edge of frame, lit from below by her headlamp bounce and faint cyan from the ceiling, a small screwdriver in her hand at the edge of frame, eyes wet and far away, a sad tight smile. Dark ceiling and monitor glow softly out of focus behind, no other structures. $J" images/juno_ref.png images/jk10_wide.png
[ -f images/jk10_wide.png ] || g jk10_wide "Same room and same wide camera position as the first reference image (wide master from the door, monitor wall curving on the left, control desk on the left, the single projector platform in the center). The platform is lit cyan and Lyra's full-body hologram stands on it, turned toward the control desk speaking to Marcus; Juno sits on the floor at the edge of the platform looking between them; Marcus sits at the control desk on the left, starting to rise with a slow smile. $L $J $M" images/jk1_walk_in.png images/lyra_ref.png images/juno_ref.png images/char_ref.png
fin
# wave 2: derived from anchors
g jk3_elbows "$SAME Juno has slid out and propped herself up on her elbows beside the open platform, looking up toward the ceiling camera with a wry, embarrassed half-laugh. $J" images/jk2_under.png images/juno_ref.png
g jk5_board "$SAME Juno is now sitting up beside the open platform, holding up a scorched burnt circuit board between two fingers toward the ceiling camera, one eyebrow raised in a sarcastic grin. $J" images/jk2_under.png images/juno_ref.png
g jk8_answer "$SAME Juno now sits cross-legged on the floor beside the platform with the access panel back in her lap, tools beside her, looking up toward the ceiling camera with a thoughtful, honest, gentle expression. $J" images/jk2_under.png images/juno_ref.png
[ -f images/jk11_hand.png ] || g jk11_hand "$SAME Marcus has walked over and stands at the edge of the platform reaching down to offer Juno his hand; Juno, still sitting on the floor, is reaching up to take it, grinning; Lyra's hologram on the platform watches them, smiling. $M $J $L" images/jk10_wide.png images/char_ref.png images/juno_ref.png images/lyra_ref.png
fin
# wave 3: end states of chained shots
g jk3e_back_in "$SAME Juno has lain back down with her head and shoulders under the open platform edge again, working on the circuitry with a screwdriver, headlamp on, still talking. $J" images/jk3_elbows.png images/juno_ref.png
g jk8e_ignite "$SAME The access panel is now snapped back into place; the platform's concentric rings blaze bright cyan beside her, a column of glowing particles starting to rise, cyan light flooding Juno's upturned face, her mouth open in awe. $J" images/jk8_answer.png images/juno_ref.png
[ -f images/jk11e_shake.png ] || g jk11e_shake "$SAME Juno is now standing, pulled up off the floor, shaking Marcus's hand and beaming, looking around the room in delight; Lyra's hologram on the platform beside them clasps her hands, beaming with joy. $M $J $L" images/jk11_hand.png images/char_ref.png images/juno_ref.png images/lyra_ref.png
fin
# wave 4: end of the tilt-up
g jk9_two_shot "Same room, lighting and camera position as the first reference image, the camera tilted up slightly. Juno stays exactly where she is in the first reference - sitting cross-legged on the floor on the RIGHT side of frame, looking up. The single low round platform stays exactly where it is on the LEFT, its rings glowing cyan, and Lyra's full-body hologram now stands in the center of that same platform, smiling down toward Juno. There is only one platform and only one set of glowing rings. $L $J" images/jk8e_ignite.png images/lyra_ref.png images/juno_ref.png
fin
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
order=["jk1_walk_in","jk2_under","jk3_elbows","jk3e_back_in","jk4_close","jk5_board","jk6_solder","jk7_marcus","jk8_answer","jk8e_ignite","jk9_two_shot","jk10_wide","jk11_hand","jk11e_shake"]
tag={"jk1_walk_in":"1  A  start","jk2_under":"2  B  CUT","jk3_elbows":"2 end / 3 start  B  CHAIN","jk3e_back_in":"3 end  B","jk4_close":"4  D  CUT","jk5_board":"5  B  CUT","jk6_solder":"6  D  CUT","jk7_marcus":"7  C  CUT","jk8_answer":"8  B  CUT","jk8e_ignite":"8 end / 9 start  B  CHAIN","jk9_two_shot":"9 end  B tilt-up","jk10_wide":"10  A  CUT","jk11_hand":"10 end / 11 start  A  CHAIN","jk11e_shake":"11 end  A"}
W,H=640,360; rows=(len(order)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,n in enumerate(order):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(f"images/{n}.png").convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),f"{n}   [{tag[n]}]",fill="white",font=f)
s.save("storyboards/juno_lyra_v2.jpg",quality=88)
PY
