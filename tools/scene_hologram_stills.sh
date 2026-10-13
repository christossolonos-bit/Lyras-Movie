#!/bin/bash
# Generates the "Lyra appears as a hologram" scene stills (Lyra locked via images/lyra_ref.png, Marcus via images/char_ref.png, dog via images/dog_ref.png) + contact sheet
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, shallow depth of field, natural color grade, no text unless specified."
ROOM="Setting: the data center operations room in the morning - a dark, sleek control room with a curved wall of monitors, glass-walled rows of server racks with blinking blue and green LEDs behind, a circular metal hologram projector platform set into the floor in the middle of the room, a grey dog bed and water bowl near the racks."
L="Lyra is the woman in the character sheet reference, shown as a hologram: semi-transparent glowing cyan light, faint horizontal scan lines and floating particles, long wavy hair, fitted long-sleeve top and slim pants - match her face exactly to the sheet."
M="The man is Marcus from the reference image (48, short salt-and-pepper hair, grey-flecked stubble beard, sun-weathered tan, lean build, black leather jacket over a grey henley, dark jeans) - match his face exactly."
D="The dog is the white pit bull from the reference image: a single grey patch around his own right eye only, natural floppy ears, now wearing a simple black collar with a small glowing cyan tag - match him exactly."
g(){ n=$1; p=$2; shift 2; python tools/gen_image.py "$n" "$p $ROOM $S" --ref "$@" > "logs_$n.txt" 2>&1 & }
g lh1_ops_wake "Wide shot from behind Marcus as he steps into the dark operations room, helmet under his arm. The room is waking up around him: the monitor wall flickering on screen by screen, ceiling strip lights coming up, server LEDs rippling to life down the aisles. $M" images/char_ref.png images/pb9_home.png
g lh2_platform_glow "Low close-up of the circular metal hologram projector platform in the floor: its concentric rings igniting in bright cyan light, a column of glowing particles beginning to rise from it into the dim air, Marcus's boots and jeans visible at the edge of frame. $M" images/char_ref.png images/lyra_ref.png
g lh3_hologram_forms "Over-the-shoulder shot past Marcus (back of his head and leather jacket soft in the foreground) toward the projector platform, where Lyra's full-body hologram is materializing - assembling from the feet up out of scan lines and particles, her face already formed, smiling at him. $L $M" images/lyra_ref.png images/char_ref.png
g lh4_lyra_closeup "Close-up of Lyra's hologram face and shoulders, glowing cyan against the dark room, eyes bright, an excited smile she's barely holding back, as if she's about to burst with news. Monitor wall softly out of focus behind her. $L" images/lyra_ref.png
g lh5_marcus_reaction "Medium close-up of Marcus setting his helmet down on a control desk, looking up at a glowing cyan light source off-screen, one eyebrow raised, an amused curious half-smile - 'all right, let's hear it'. Cyan light on his face, monitors behind him. $M" images/char_ref.png
g lh6_dog_reveal "Comedic wide shot: Lyra's full-body hologram stands on the projector platform looking proud and a little sheepish, and sitting right at her glowing feet is the white pit bull, tail wagging, looking up at Marcus. Marcus stands facing them, helmet in hand, staring down at the dog with a deadpan expression. $L $M $D" images/lyra_ref.png images/char_ref.png images/dog_ref.png
g lh7_crouch_dog "Marcus crouches down scratching the white pit bull behind the ears, the dog leaning happily into his hand, while Marcus looks up at Lyra's hologram standing over them, who watches the dog fondly with her hands clasped. Warm, funny, tender moment. $L $M $D" images/lyra_ref.png images/char_ref.png images/dog_ref.png
g lh8_marcus_realizes "Medium close-up of Marcus, crouched with one hand resting on the white pit bull's back; the dog sits beside him fully in frame, head and grey eye patch clearly visible, looking up too. Marcus's smile is fading into a quiet, intense, thoughtful look as he stares up at Lyra off-screen, cyan light on both their faces - realizing this is something far bigger than a dog. $M $D" images/char_ref.png images/dog_ref.png
g lh9_decision_log "Marcus sits at the control desk leaning toward a large monitor showing a single clean dark alert panel with just two lines of large, crisp, legible white text: '13:51:22  MAIN GATE - OPENED' and below it in amber 'REQUESTED BY: NONE'. Nothing else on that screen. Lyra's hologram stands on the projector platform beside his chair, looking at the screen with him, curious. The white pit bull is asleep under the desk. $L $M $D" images/lyra_ref.png images/char_ref.png images/dog_ref.png
wait; cat logs_*.txt; rm logs_*.txt
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
import glob,os
fs=sorted(glob.glob("images/lh*.png")); W,H=640,360; rows=(len(fs)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,p in enumerate(fs):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(p).convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),os.path.basename(p),fill="white",font=f)
s.save("storyboards/lyra_hologram.jpg",quality=88)
PY
