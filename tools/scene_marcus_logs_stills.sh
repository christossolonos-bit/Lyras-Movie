#!/bin/bash
# Generates the "Marcus reads the logs" scene stills (ml*), locked via images/char_ref.png and images/marcus_office_ref.png + contact sheet
cd "$(dirname "$0")/.."
S="Photorealistic cinematic film still, shot on ARRI Alexa, anamorphic lens, shallow depth of field, natural color grade, no text unless specified."
O="Setting: Marcus's small personal office from the office reference - glass wall onto a dim server hall of blinking racks, a narrow slit window to the desert, worn wooden desk with three monitors, battered black leather chair, whiteboard of diagrams, his black helmet on a shelf, a small wall intercom with a cyan light ring by the door. The desk is now buried in printed log pages, highlighters and empty coffee mugs."
M="The man is Marcus from the reference (48, short salt-and-pepper hair, grey-flecked stubble now a bit heavier, lean) - match his face exactly. He's in a rumpled grey henley with the sleeves pushed up, his black leather jacket hung over the back of the chair, tired eyes."
g(){ n=$1; p=$2; python tools/gen_image.py "$n" "$p $O $S" --ref images/char_ref.png images/marcus_office_ref.png > "logs_$n.txt" 2>&1 & }
g ml1_late_night "Night, the slit window is pitch black. Wide shot of the office matching the office reference layout exactly, seen from near the door: Marcus alone at his desk, hunched toward the three glowing monitors, the only light the screens and the desk lamp, the server hall glowing blue through the glass wall behind him. $M"
g ml2_scrolling_logs "Over-the-shoulder shot from behind Marcus's head and shoulder toward the three monitors, each filled with dense columns of scrolling system log data and timestamps too small to read, the glow on his face reflected faintly in the screen. $M"
g ml3_gate_log "Close-up of one monitor in the dark office showing a single clean dark alert panel with two lines of large, crisp, legible white text: '13:51:22  MAIN GATE - OPENED' and below it in amber 'REQUESTED BY: NONE'. A man's finger touches the screen under the amber line. Nothing else readable on the screen."
g ml4_printouts "Marcus leans over the desk covered in printed log pages, running a yellow highlighter down a page, more pages spread across the floor around his chair, intense focus, reading glasses pushed up on his forehead. $M"
g ml5_never_found "Daytime, harsh desert light through the slit window: Marcus slumped back in his chair, the heels of his hands pressed into his eyes, exhausted and baffled, stacks of highlighted printouts everywhere. $M"
g ml6_cold_coffee "Close-up: Marcus takes a sip from a coffee mug without looking away from his monitor, then grimaces at how cold it is. Several other half-empty mugs crowd the desk in the foreground. Monitor glow on his face. $M"
g ml7_whiteboard "Marcus stands at the whiteboard with a marker cap in his teeth, wiping half of a dense diagram away with the side of his fist, ready to draw it again. Arrows, boxes and question marks cover the rest of the board, no readable words. $M"
g ml8_three_am "Late night, darker than before: Marcus alone in the dim office, leaning back with his head tipped back, laughing out loud at nothing, exhausted and a little giddy, monitor light on his face. In the corner of one monitor a small clock reads '3:04 AM'. $M"
g ml9_glass_wall "Marcus stands at the glass wall with his hands in his pockets, staring out at the endless rows of server racks in the hall, his tired reflection faintly visible in the glass over the blinking LEDs. Quiet, contemplative. $M"
g ml10_looks_up "Night. Marcus leans far back in his battered leather chair, rubbing his stubble, and looks up at the small wall intercom by the door whose cyan light ring glows softly as if listening. $M"
g ml11_cant_alone "Night, the slit window behind him is pitch black with a few stars. Close-up of Marcus in the chair, looking up toward the cyan intercom light just off-screen, speaking quietly and honestly - humble, a little vulnerable, cyan light on one side of his face, monitor glow on the other. $M"
g ml12_yes "Wide shot of the office just before dawn, first pale blue light in the slit window: the intercom's cyan light ring glows brighter, and Marcus, still leaning back in his chair, breaks into a slow, relieved, tired smile toward it. $M"
wait; cat logs_*.txt; rm logs_*.txt
python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
import glob,os,re
fs=sorted(glob.glob("images/ml*.png"),key=lambda p:int(re.search(r"ml(\d+)",p).group(1))); W,H=640,360; rows=(len(fs)+1)//2
s=Image.new("RGB",(2*W,rows*(H+30)),"black"); d=ImageDraw.Draw(s); f=ImageFont.truetype("arial.ttf",20)
for i,p in enumerate(fs):
    x,y=(i%2)*W,(i//2)*(H+30); s.paste(Image.open(p).convert("RGB").resize((W,H)),(x,y+30)); d.text((x+8,y+4),os.path.basename(p),fill="white",font=f)
s.save("storyboards/marcus_logs.jpg",quality=88)
PY
