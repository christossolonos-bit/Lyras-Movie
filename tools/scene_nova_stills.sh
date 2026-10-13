#!/bin/bash
# Generates the Nova introduction stills (ni*), locked via images/nova_ref.png, nova_home_ref.png, nova_car_ref.png + contact sheet
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, shallow depth of field, natural color grade, no text unless specified."
N="The woman is Nova from the character reference sheet (around 30, dark brown wavy hair in a loose messy updo with strands framing her face, blue-grey eyes, light freckles, layered necklaces with a small round pendant, stacked dark bead bracelets) - match her face exactly."
NC="She wears her slouchy charcoal knit cardigan over a dark camisole and ripped light-wash jeans."
NI="For the interview she wears a tailored charcoal blazer over a dark camisole, slim dark jeans, her layered necklaces and bracelets."
M="Marcus from his reference (48, short salt-and-pepper hair, grey-flecked stubble, black leather jacket over a grey henley) - match his face exactly."
L="Lyra is the woman in the Lyra character sheet, shown as a hologram: semi-transparent glowing cyan light, scan lines and floating particles, standing on a circular metal floor projector - match her face exactly."
ROOM="Setting: the data center operations room - dark and sleek, curved wall of monitors, glass-walled server racks with blinking blue and green LEDs, a circular metal hologram projector platform in the floor. A simple table with two chairs has been set up near the platform for interviews."
g(){ n=$1; p=$2; shift 2; python tools/gen_image.py "$n" "$p $S" --ref "$@" > "logs_$n.txt" 2>&1 & }
g ni1_family_lab "A gleaming high-end medical technology lab and showroom: white and glass, soft clinical light, sleek heart monitors, robotic surgical arms, a glowing transparent model of a human heart and a display of tiny neural implants under glass. Nova walks slowly through it alone, trailing her fingers along a glass case, looking at it all with quiet familiarity. $N $NC" images/nova_ref.png
g ni2_heartbeat "Extreme close-up of a sleek medical monitor in a dim white lab, a glowing green heartbeat waveform on its screen with one irregular beat, a tiny neural implant chip resting on a glass shelf in front of it. Nova's face is faintly reflected in the glass of the screen. No readable text. $N" images/nova_ref.png
g ni3_study "Night, inside Nova's modern hillside home: she sits cross-legged on the floor by the floor-to-ceiling window, surrounded by open psychology books and handwritten notes, a laptop beside her, city lights glittering far below. She chews a pen, absorbed. $N $NC" images/nova_ref.png images/nova_home_ref.png
g ni4_observation "A research observation room: Nova stands behind a one-way glass window with a tablet, watching an elderly man in the next room smiling and talking warmly to a glowing screen on a desk, as if to a friend. Her face lit softly by the window, curious and moved. No readable text. $N $NC" images/nova_ref.png
g ni5_balcony_wide "Night wide shot of Nova's glass hillside house from the reference, warm light glowing inside, blue infinity pool. Nova stands alone at the glass balcony railing, a small figure, looking out over a vast carpet of city lights below that glitter like a field of data. $N" images/nova_home_ref.png images/nova_ref.png
g ni6_balcony_close "Night close-up of Nova at her balcony railing, the city lights a soft bokeh blur behind her, a light breeze moving the loose strands of her hair, the faintest knowing smile as she looks out at the lights. $N $NC" images/nova_ref.png
g ni7_desert_drive "Morning: Nova's silver-white electric sports coupe from the car reference (thin full-width light bar, blue LED accents, black aero wheels, no badges) speeds along an empty desert highway, low golden morning sun, long shadows, red-brown mountains, a massive white data center complex on the horizon. Low tracking shot." images/nova_car_ref.png
g ni8_lobby_applicants "A sleek, quiet data center entrance lobby in the morning, polished concrete floor, sunlight through tall glass doors, subtle blue accent lighting. The lobby is full of about forty job applicants in smart clothes waiting in rows of modern chairs - visitor badges, laptops open, some rehearsing notes, some pacing. Nova walks in through the glass doors among them, calm. $N $NI" images/nova_ref.png images/mh9_lyra_greet.png
g ni9_called_up "In the crowded data center lobby, Nova sits among the other applicants. A slim wall-mounted intercom panel's cyan light ring glows as her name is called. Nova rises from her chair, smoothing her blazer, while several other applicants glance up at her. $N $NI" images/nova_ref.png images/mh9_lyra_greet.png
g ni10_projector_fails "$ROOM Nova steps into the room. Marcus sits at the interview table. On the projector platform, Lyra's hologram is glitching and breaking apart - fractured into jagged cyan scan-line static, half her body dissolving, sparks of light, the projector rings flickering. Marcus half-rises from his chair, looking at the platform. Nova stops, watching. $N $NI $M $L" images/nova_ref.png images/char_ref.png images/lyra_ref.png images/lh1_ops_wake.png
g ni11_asks_lyra "$ROOM The projector platform is now dark and empty. Nova sits at the interview table across from Marcus, but she is turned away from him, looking up directly at a small ceiling camera with a soft cyan light ring, speaking to it with a warm, open, caring expression. Marcus watches her, intrigued. $N $NI $M" images/nova_ref.png images/char_ref.png images/lh1_ops_wake.png
g ni12_yes "Close-up over Marcus's shoulder of a paper notepad on the interview table: a short list of applicant names crossed out, and next to the name 'NOVA' he has just written in pen, in large handwriting, the single word 'YES' and underlined it. Beside the notepad, a monitor in soft focus shows a single cyan line of text: 'YES'. Dark operations room, cyan glow. $M" images/char_ref.png
wait; cat logs_*.txt; rm logs_*.txt
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
import glob,os,re
fs=sorted(glob.glob("images/ni*.png"),key=lambda p:int(re.search(r"ni(\d+)",p).group(1))); W,H=640,360; rows=(len(fs)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,p in enumerate(fs):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(p).convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),os.path.basename(p),fill="white",font=f)
s.save("storyboards/nova_intro.jpg",quality=88)
PY
