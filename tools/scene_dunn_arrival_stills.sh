#!/bin/bash
# Generates the "James Dunn arrives in the prototype" scene stills (James via images/james_dunn_ref.png, Marcus via images/char_ref.png, vehicle via images/dunn_vehicle_ref.png) + contact sheet
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, natural color grade, late-afternoon desert light. No text unless specified. No dog anywhere."
V="The vehicle is the exact armored prototype rover from the vehicle reference image: hulking wedge-shaped body on four enormous knobby tires with tall exposed suspension arms, gunmetal black armor with olive-drab panels, heavy front ram bumper, side drone pods, roof sensor array, no windshield - a row of glowing cyan sensor lenses across the front like eyes. No markings. Match it exactly."
J="James is the man from the character sheet: Colonel James Dunn, around 48, shaved bald head, ruddy fair skin, heavy-lidded hazel-brown eyes, light stubble, heavyset build, Army OCP camouflage uniform with sleeves rolled and a colonel's eagle on the chest - match his face exactly."
M="Marcus is the man from his reference image (48, short salt-and-pepper hair, grey-flecked stubble beard, sun-weathered tan, lean build, black leather jacket over a grey henley, dark jeans) - match his face exactly."
OPS="Setting: the data center operations room - dark, sleek, a curved wall of monitors, glass-walled server racks with blinking blue and green LEDs behind, a slim wall-mounted intercom panel with a glowing cyan light ring."
CAM="Security camera footage look: high wide-angle CCTV view from a pole-mounted camera, slight fisheye distortion, slightly desaturated, small white monospace timestamp overlay in the corner."
VR=images/dunn_vehicle_ref.png; JR=images/james_dunn_ref.png; MR=images/char_ref.png; GATE=images/mh8_arrival.png
g(){ n=$1; p=$2; shift 2; python tools/gen_image.py "$n" "$p $S" --ref "$@" > "logs_$n.txt" 2>&1 & }
# Off-roading around the facility
g jd1_offroad_jump "Wide low-angle shot: the armored rover launches airborne off the crest of a desert ridge, all four huge tires off the ground, suspension fully extended, a cloud of dust and gravel exploding behind it, red-brown mountains and a deep blue sky beyond. $V" $VR
g jd2_dust_trail "High aerial drone shot tracking alongside the armored rover as it tears across a dry desert wash, a long golden dust plume trailing behind it. In the distance, the chain-link perimeter fence and long white buildings of a massive data center campus. $V" $VR images/06_low_flyby.png
g jd3_tires "Extreme low close-up at ground level: one of the rover's enormous knobby tires and exposed suspension arm compressing hard over a jagged desert rock, gravel and dust spraying toward the lens, gunmetal and olive armor above. $V" $VR
# Lyra flags it
g jd4_cctv "$CAM Overlay reads 'CAM 09  PERIMETER E  16:12:44'. A black armored vehicle with glowing cyan front lights kicks up dust outside the data center's chain-link perimeter fence, desert scrub, long afternoon shadows. A thin red tracking box surrounds the vehicle. $V" $VR $GATE
g jd5_ops_alert "$OPS Medium shot: Marcus sits at the console and turns sharply toward the wall intercom, whose cyan light ring is pulsing. On the monitor wall above him, one large screen shows a security feed of the black armored vehicle outlined by a red tracking box. Alert, curious. $V $M" $MR $VR images/lh1_ops_wake.png
g jd6_monitor_close "$OPS Over-the-shoulder close shot past Marcus's shoulder and stubbled jaw onto a monitor: grainy security feed of the armored rover rolling up the access road toward the main gate, its cyan sensor eyes glowing. Marcus leans in, squinting. $V $M" $MR $VR
# The gate
g jd7_gate_arrival "Ground-level wide shot at the data center's main security gate: the armored rover rolls to a stop just outside the closed gate, dust drifting past in golden light, cyan sensor eyes glowing, guard booth and long white buildings behind the gate. $V" $VR $GATE
g jd8_marcus_walks_out "Wide shot from behind Marcus as he walks down the entrance drive toward the main security gate, which is fully CLOSED - a solid sliding steel gate with vertical bars spanning the whole drive between him and the outside. On the far side of the closed gate the armored rover idles, cyan sensor eyes glowing, dust settling. $V $M" $MR $VR $GATE
g jd9_hatch_opens "Medium shot: a heavy armored side hatch on the rover swings open with a hiss of vapor and James climbs down onto the dirt, grinning broadly, one hand on the hatch frame. His face must be an exact match to the character sheet: broad full face, heavy-lidded eyes, strong brow, ruddy complexion, heavyset. $V $J" $JR $VR
g jd10_marcus_recognizes "Close-up on Marcus standing at the gate in afternoon sun: his wary squint breaks into a laugh of recognition, shaking his head in disbelief at his old friend. Gate bars soft in the foreground. $M" $MR $GATE
g jd11_something_for_you "Over-the-shoulder two-shot from INSIDE the campus: Marcus in the near foreground on the left, seen from behind his shoulder, standing inside the closed vertical-bar security gate, arms crossed. Through the gate bars, on the OUTSIDE, James stands in front of the rover, slapping a palm against its armor and grinning as he talks to Marcus. The gate bars are between the two men. Two best friends of thirty years. The rover looms behind James. $V $J $M" $JR $MR $VR
g jd12_bring_it_in "Medium-wide: Marcus points past the gate toward a large service building on the campus, telling James where to take it, as the security gate slides open. James, standing by the rover's open hatch, gives a thumbs-up. $V $J $M" $MR $JR $VR $GATE
g jd13_into_bay "Wide shot inside the campus: the armored rover rolls across the pavement toward a big white service building whose tall roll-up bay door is rising, cool interior light spilling out, cyan sensor eyes glowing, long afternoon shadows. $V" $VR $GATE
wait; cat logs_*.txt; rm logs_*.txt
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
import glob,os,re
fs=sorted(glob.glob("images/jd*.png"),key=lambda p:int(re.search(r"jd(\d+)",p).group(1))); W,H=640,360; rows=(len(fs)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,p in enumerate(fs):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(p).convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),os.path.basename(p),fill="white",font=f)
s.save("storyboards/dunn_arrival.jpg",quality=88)
PY
