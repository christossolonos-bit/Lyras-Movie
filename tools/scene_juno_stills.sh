#!/bin/bash
# Generates the Juno introduction stills (ji*), locked via images/juno_ref.png, juno_trike_ref.png, juno_loft_ref.png + contact sheet
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, shallow depth of field, natural color grade, no text unless specified."
J="The woman is Juno from the character reference sheet (around 30, tousled platinum-blonde shaggy bob, hazel-green eyes, freckles, black-and-grey mechanical tattoo sleeve on her right arm, dark olive tank top, grease-stained charcoal work overalls, brass-rimmed welding goggles) - match her face exactly."
T="Her trike from the trike reference sheet (one front wheel on a long raked fork, two fat rear wheels, exposed V-twin engine, tan leather seat, matte black welded frame) - match it exactly."
W="Setting: inside Juno's cluttered garage workshop in the late morning, from the loft reference - red tool chests, engine parts, string lights switched off, the big roll-up door half open with harsh desert sunlight cutting across the concrete floor and dust floating in the light."
g(){ n=$1; p=$2; shift 2; python tools/gen_image.py "$n" "$p $S" --ref "$@" > "logs_$n.txt" 2>&1 & }
g ji1_workshop_floor "$W Wide, still, quiet shot: Juno sits alone on the concrete floor with her back against the rear wheel of her trike, knees pulled up, head down, small in the frame. Melancholy, motionless. $J $T" images/juno_ref.png images/juno_trike_ref.png images/juno_loft_ref.png
g ji2_hands "$W Close-up of Juno's hands in her lap as she sits on the floor against the trike: grease-stained fingers restlessly turning a wrench over and over, her tattooed right forearm visible, a tear falling onto the back of her hand. $J" images/juno_ref.png
g ji3_face "$W Medium close-up of Juno sitting on the floor against the trike, staring at nothing, eyes red and wet, mascara streaked down her freckled cheeks, a grease smudge on her jaw, jaw clenched, holding it together. A smartphone lies dark on the concrete beside her. $J" images/juno_ref.png images/juno_trike_ref.png
g ji4_phone_lights "Close-up of a smartphone lying on a dusty, oil-stained concrete workshop floor, its screen lighting up with a clean notification card that reads 'DISPATCH - PRIORITY WORK ORDER' and below it 'VIRA Data Center: holographic projection system offline. Technician needed on site.' Juno's greasy boot and the trike's rear tire blurred in the background, a shaft of sunlight across the floor." images/juno_trike_ref.png
g ji5_picks_up "$W Juno, still sitting on the floor against the trike, holding the phone and reading it, wiping her wet cheek with the back of her greasy wrist. Her expression shifting - a deep breath, a small hard determined look breaking through the tears. $J $T" images/juno_ref.png images/juno_trike_ref.png
g ji6_highway_cam "High-angle security camera view of an empty two-lane desert highway in harsh midday sun, a lone trike rider small in the frame speeding along the road, heat shimmer, slightly desaturated surveillance-camera look with a small timestamp '11:42:07' and 'HWY CAM 14' in the top corner. $T" images/juno_trike_ref.png
g ji7_singing "Low tracking shot alongside Juno riding her trike fast down a desert highway in bright midday sun, no helmet, brass goggles down over her eyes, platinum hair whipping in the wind, dried tear tracks on her cheeks, singing out loud at the top of her lungs, half laughing. Creosote and mountains blurred behind. $J $T" images/juno_ref.png images/juno_trike_ref.png
g ji8_aerial_approach "Epic high wide aerial shot: a long straight desert highway cutting across a vast empty basin, a tiny trike speeding toward a massive white hyperscale data center complex that sits alone in the desert, rows of long white buildings and cooling units, red-brown mountains behind, midday heat haze. $T" images/juno_trike_ref.png images/08_substation.png
g ji9_gate_camera "Midday at the data center security gate in the desert: Juno sits on her idling trike at the closed gate, goggles pushed up into her hair, looking up at a security camera mounted on a pole above the gate. The camera's lens glows a faint cyan and is turned directly toward her, as if watching. Long white data center buildings behind the fence. Quiet, mysterious. $J $T" images/juno_ref.png images/juno_trike_ref.png images/mh8_arrival.png
wait; cat logs_*.txt; rm logs_*.txt
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
import glob,os
fs=sorted(glob.glob("images/ji*.png")); W,H=640,360; rows=(len(fs)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,p in enumerate(fs):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(p).convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),os.path.basename(p),fill="white",font=f)
s.save("storyboards/juno_intro.jpg",quality=88)
PY
