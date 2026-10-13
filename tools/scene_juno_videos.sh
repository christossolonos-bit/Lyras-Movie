#!/bin/bash
# Animates the Juno introduction with MiniMax H3, audio OFF (Lyra narration added in edit).
# Straight cuts: each clip starts from its own ji still, no end frame. Clips are independent, so they run in parallel.
# Usage: bash tools/scene_juno_videos.sh [clip numbers...]   no args = 1..9
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot, smooth natural motion, consistent character. Juno is a woman around 30 with a tousled platinum-blonde shaggy bob, freckles, a black-and-grey tattoo sleeve on her right arm, olive tank top and grease-stained charcoal overalls. Her trike has one front wheel on a long raked fork and two fat rear wheels. No text overlays, no subtitles."
v(){ n=$1; d=$2; p=$3
  echo ">> $n  ${d}s"
  python tools/gen_video.py "$n" "$p $S" --model minimax/hailuo-3 --res 2K --duration "$d" --first "images/$n.png" > "logs_v_$n.txt" 2>&1 & }
run(){ [ $# -eq 0 ] && set -- 1 2 3 4 5 6 7 8 9; for c in "$@"; do case $c in
1) v ji1_workshop_floor 6 "Very slow push-in across the quiet workshop toward Juno sitting motionless on the floor against the trike, head down. Dust drifts through the shaft of sunlight. Almost nothing moves." ;;
2) v ji2_hands 6 "Close-up: her greasy fingers slowly turn the wrench over and over in her lap, restless. A tear drops onto the back of her hand. Static camera, shallow focus." ;;
3) v ji3_face 8 "Slow push-in on Juno's face as she sits against the trike staring at nothing, eyes wet, mascara streaked. She swallows hard, blinks, a tear runs down her cheek, her jaw tightens. The phone lies dark on the floor beside her." ;;
4) v ji4_phone_lights 7 "The phone on the concrete floor vibrates, buzzing slightly across the dust, its screen glowing with the notification. Dust motes drift in the sunlight. Very slow push-in." ;;
5) v ji5_picks_up 8 "Juno reads the phone, wipes her wet cheek with the back of her greasy wrist, takes a deep breath, and a small determined look breaks through the tears. She pushes herself up off the floor using the trike. Static camera." ;;
6) v ji6_highway_cam 6 "Fixed high-angle security camera footage: the trike rides along the desert highway from left to right through the frame, heat shimmer rising off the asphalt. The camera does not move." ;;
7) v ji7_singing 6 "Tracking shot alongside Juno riding the trike fast down the desert highway, hair whipping in the wind, goggles down, she sings out loud at the top of her lungs and laughs, the desert streaking past behind her." ;;
8) v ji8_aerial_approach 8 "High aerial shot: the tiny trike speeds down the long straight highway toward the massive white data center alone in the desert, a thin trail of dust behind it. The drone slowly tilts up and glides forward toward the complex." ;;
9) v ji9_gate_camera 6 "Juno sits on her idling trike at the closed gate, looking up at the security camera. The camera slowly pans and tilts to look directly at her, its lens glowing cyan. She tilts her head, curious. Slow push-in, quiet and mysterious." ;;
esac; done; wait; cat logs_v_*.txt; rm logs_v_*.txt; }
run "$@"
