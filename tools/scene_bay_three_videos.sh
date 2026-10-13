#!/bin/bash
# Animates the Bay Three scene (James's rover) with self-hosted MiniMax H3 on the RunPod pod (audio ON, 768p).
# Every shot is its own camera setup -> all hard cuts, each clip starts from its own bay still, no end frame.
# Clips are submitted together; ComfyUI renders them one after another on the single GPU. Existing clips are skipped.
# Usage: bash tools/scene_bay_three_videos.sh [clip numbers...]   no args = 1..12
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot with no cuts, smooth natural motion, consistent characters, a large industrial vehicle bay at a desert data center, the big bay door open onto desert mountains at golden hour. Marcus is a 48-year-old man with salt-and-pepper hair and stubble in a black leather jacket. James is a bald, broad 48-year-old man in US Army camouflage fatigues. The rover is a black and olive armored four-wheel prototype with glowing cyan sensor lights. Lyra is a glowing cyan hologram of a woman with long wavy hair. Audio: large echoing hangar ambience, dialogue clearly audible, no background music, no subtitles."
MV="Marcus's voice: low, warm, slightly gravelly male voice, dry humor."
JV="James's voice: big, hearty male voice, around 48, American, a little gravelly, easy confidence of a career officer."
LV="Lyra's voice: warm, bright female voice, mid-30s, American, playful and curious, with a faint airy digital resonance."
v(){ n=$1; d=$2; p=$3
  [ -f "videos/$n.mp4" ] && { echo "skip $n (exists)"; return; }
  python tools/gen_video_runpod.py "$n" "$p $S" --first "images/$n.png" --duration "$d" --audio > "logs_v_$n.txt" 2>&1 & }
run(){ [ $# -eq 0 ] && set -- 1 2 3 4 5 6 7 8 9 10 11 12; for c in "$@"; do case $c in
1) v bay01_establishing 7 "Marcus and James walk across the hangar floor toward the rover while Lyra's hologram watches from her platform on the left. Marcus says: \"You drove this thing across the desert? On public roads?\" James grins and says: \"Mostly public.\" Slow tracking shot from behind. $MV $JV" ;;
2) v bay02_front_threequarter 8 "Slow push-in on the rover. Its cyan sensor lights swivel toward Lyra's hologram. Lyra's voice says: \"James, your vehicle has scanned me eleven times since you parked.\" James says: \"It's curious.\" Lyra says: \"So am I.\" A soft electronic scanning tone. $LV $JV" ;;
3) v bay03_lyra_briefing 9 "Lyra's hologram gestures through a glowing schematic of the rover while Marcus and James watch from behind. Lyra says: \"Autonomous recon platform. Independent drive on all four wheels. And a decision engine that's been arguing with itself all morning.\" James turns to her and says: \"...You got all that from the parking lot?\" $LV $JV" ;;
4) v bay04_marcus_walkaround 7 "Marcus crouches beside the huge front wheel, running his hand over the armor. He says: \"That's a hell of a suspension.\" James's voice from off-screen says: \"Took a forty-foot drop off a ridge on the way in. Didn't spill my coffee.\" Marcus smirks. $MV $JV" ;;
5) v bay05_james_explains 6 "James gestures into the open access panel full of wiring while Marcus listens with his hand on his chin. James says: \"Armor, power, sensors. The hardware's perfect.\" Marcus says: \"So what's wrong with it?\" $JV $MV" ;;
6) v bay06_sensor_closeup 9 "Extreme close-up of the rover's cyan sensor lights slowly sweeping back and forth, soft servo whine. James's voice from off-screen says: \"The brain. Give it a clear order, it's brilliant. Give it something nobody planned for...\" A pause. \"...it freezes.\" The sensors stop and hold still. $JV" ;;
7) v bay07_side_hatch 9 "James hauls the armored electronics compartment open wider and points at the hardware inside while Marcus stands beside him. James says: \"Eighteen months. The best engineers in the country. It still can't make a single call on its own.\" Marcus says quietly, half to himself: \"...It can't decide.\" $JV $MV" ;;
8) v bay08_cabin_interior 7 "Inside the rover's cabin, the screens flicker awake one by one and Lyra appears across the main display. She says gently: \"It isn't broken, Marcus. Nobody ever let it want anything.\" The instrument lights glow cyan. Slow push-in. $LV" ;;
9) v bay09_suspension_close 7 "Marcus crouches by the suspension, studying it, then glances up. He says: \"James. Tell me you didn't promise the Pentagon we'd fix their toy.\" James's voice from off-screen says: \"I promised them I'd ask.\" Marcus shakes his head with a tired smile. $MV $JV" ;;
10) v bay10_holo_overlay 8 "Lyra's hologram spreads a detailed glowing wireframe of the rover through the air as Marcus and James watch. Lyra says: \"Its architecture is remarkably close to mine. Like a little brother who never learned to talk.\" Marcus turns toward her. $LV" ;;
11) v bay11_shared_reaction 8 "Marcus and James stand side by side, arms folded, exchanging a knowing smile. Marcus says: \"You knew she'd want to get her hands on it.\" James says: \"Thirty years, Marcus. I know that look.\" He glances toward Lyra off-screen and adds: \"On both of you.\" $MV $JV" ;;
12) v bay12_wide_wrap 7 "Wide shot. Lyra's hologram steps off her platform toward the rover and its cyan sensors brighten, as if answering her. Lyra says: \"Gentlemen...\" A pause. \"...may I take it for a drive?\" Marcus and James turn to look at her. $LV" ;;
esac; done; wait; cat logs_v_*.txt 2>/dev/null; rm -f logs_v_*.txt; }
run "$@"
