#!/bin/bash
# Generates the "Juno fixes the projector" dialogue scene stills (jl*), locked via juno_ref, lyra_ref, char_ref and the ops room from ni11 + contact sheet
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, shallow depth of field, natural color grade, no text unless specified."
ROOM="Setting: the data center operations room from the room reference - dark and sleek, curved wall of monitors, glass-walled server racks with blinking blue and green LEDs, exactly ONE circular metal hologram projector platform set into the floor in the middle of the room (there is only one platform in the whole room), a control desk, a small interview table with two chairs nearby."
J="Juno from the character reference sheet (around 30, tousled platinum-blonde shaggy bob, hazel-green eyes, freckles, black-and-grey mechanical tattoo sleeve on her right arm, olive tank top, grease-stained charcoal work overalls, brass welding goggles pushed up in her hair), eyes still a little red from crying - match her face exactly."
L="Lyra from the Lyra character sheet as a hologram: semi-transparent glowing cyan light, scan lines and floating particles, long wavy hair, fitted long-sleeve top and slim pants, standing on the projector platform - match her face exactly."
M="Marcus from his reference (48, short salt-and-pepper hair, grey-flecked stubble, black leather jacket over a grey henley) - match his face exactly."
CAM="a small ceiling-mounted camera dome with a soft glowing cyan light ring (Lyra's eye and voice while the projector is down)"
g(){ n=$1; p=$2; shift 2; python tools/gen_image.py "$n" "$p $ROOM $S" --ref "$@" > "logs_$n.txt" 2>&1 & }
g jl1_arrival "Juno walks into the operations room carrying a heavy canvas tool bag, staring around in open-mouthed awe at the monitor wall and server racks. Marcus walks beside her pointing toward the dark, dead projector platform. $J $M" images/juno_ref.png images/char_ref.png images/ni11_asks_lyra.png
g jl2_under_platform "Juno lies on her back on the floor half under the edge of the dark projector platform, its access panel pulled off and leaning beside her, a headlamp on, cables and circuit boards exposed above her face, tools scattered on the floor. She has just frozen mid-motion, eyes darting up, startled by a voice. $J" images/juno_ref.png images/ni11_asks_lyra.png
g jl3_talks_to_camera "Juno props herself up on her elbows beside the open projector platform and looks up at $CAM on the ceiling, giving it a wry, embarrassed half-laugh. Low angle from the floor, the cyan camera glow visible above. $J" images/juno_ref.png images/ni11_asks_lyra.png
g jl4_six_years "Intimate close-up: Juno lying on her back inside the open projector platform, working on the exposed circuitry with a small screwdriver, lit by her headlamp and the faint cyan glow from above, her eyes wet and far away, a sad tight smile as she talks about something painful. $J" images/juno_ref.png
g jl5_driver_board "Juno sits up on the floor beside the open projector platform holding up a scorched, burnt circuit board between two fingers toward $CAM, one eyebrow raised in a sarcastic grin. $J" images/juno_ref.png images/ni11_asks_lyra.png
g jl6_soldering "Close-up: Juno bent over the open projector platform with a soldering iron, a thin curl of smoke rising, tongue in the corner of her mouth, goggles down over her eyes, a confident cocky grin, tiny sparks of light. $J" images/juno_ref.png
g jl7_marcus_listening "Medium shot of Marcus sitting at the control desk, a coffee mug forgotten in his hand, no longer looking at his monitor, turned slightly and listening intently with a soft, moved half-smile. In the soft-focus background Juno is visible on the floor working at the open projector platform. $M $J" images/char_ref.png images/juno_ref.png images/ni11_asks_lyra.png
g jl8_worth_fixing "Juno sits cross-legged on the floor beside the projector platform, tools in her lap, looking up at $CAM with a thoughtful, honest, gentle expression, as if answering a deep question. Warm and quiet. $J" images/juno_ref.png images/ni11_asks_lyra.png
g jl9_lyra_appears "There is exactly one projector platform in the shot. Juno sits on the floor right at the edge of the projector platform as it ignites: the concentric rings blaze cyan and Lyra's full-body hologram has just formed, standing over her, smiling down at her warmly. Juno looks up at Lyra, breathless and amazed, a teary laugh on her face, cyan light washing over her. $J $L" images/juno_ref.png images/lyra_ref.png images/jl8_worth_fixing.png
g jl10_i_want_her "There is exactly one projector platform in the shot, and Lyra stands on it. Wide shot: Lyra's hologram on the projector platform turned toward the control desk, speaking with a determined, hopeful look; Juno still sitting on the floor at her feet looking between them; Marcus rising from his chair at the control desk with a slow smile. $L $J $M" images/lyra_ref.png images/juno_ref.png images/char_ref.png images/jl8_worth_fixing.png
g jl11_job_offer "Marcus stands at the projector platform reaching down to offer Juno a hand up off the floor; Juno takes his hand, beaming and looking around the room in wide-eyed delight; Lyra's hologram stands beside them, beaming with joy. $M $J $L" images/char_ref.png images/juno_ref.png images/lyra_ref.png images/ni11_asks_lyra.png
wait; cat logs_*.txt; rm logs_*.txt
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
import glob,os,re
fs=sorted(glob.glob("images/jl*.png"),key=lambda p:int(re.search(r"jl(\d+)",p).group(1))); W,H=640,360; rows=(len(fs)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,p in enumerate(fs):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(p).convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),os.path.basename(p),fill="white",font=f)
s.save("storyboards/juno_lyra.jpg",quality=88)
PY
