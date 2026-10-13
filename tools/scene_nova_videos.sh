#!/bin/bash
# Animates the Nova introduction with MiniMax H3, audio OFF (Lyra narration added in edit).
# Straight cuts: each clip starts from its own ni still, no end frame. Clips are independent, so they run in parallel.
# Usage: bash tools/scene_nova_videos.sh [clip numbers...]   no args = 1..12
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot, smooth natural motion, consistent character. Nova is a woman around 30 with dark brown wavy hair in a loose messy updo, blue-grey eyes, light freckles, layered necklaces and dark bead bracelets. No text overlays, no subtitles."
v(){ n=$1; d=$2; p=$3
  echo ">> $n  ${d}s"
  python tools/gen_video.py "$n" "$p $S" --model minimax/hailuo-3 --res 2K --duration "$d" --first "images/$n.png" > "logs_v_$n.txt" 2>&1 & }
run(){ [ $# -eq 0 ] && set -- 1 2 3 4 5 6 7 8 9 10 11 12; for c in "$@"; do case $c in
1) v ni1_family_lab 5 "Nova walks slowly through the gleaming medical technology lab, trailing her fingers along a glass display case, glancing at the glowing heart model with quiet familiarity. Slow tracking shot." ;;
2) v ni2_heartbeat 5 "The green heartbeat waveform pulses across the monitor, one beat stuttering. Nova's reflection in the screen watches it. Very slow push-in." ;;
3) v ni3_study 5 "Nova sits cross-legged among her books by the night window, taps the pen against her lip, then leans in and writes a quick note, absorbed. City lights twinkle below. Static camera." ;;
4) v ni4_observation 5 "Through the one-way glass, the elderly man laughs and talks warmly to the glowing screen. Nova watches him, her expression softening, and slowly lowers her tablet. Slow push-in on Nova." ;;
5) v ni5_balcony_wide 5 "Night. The camera slowly drifts toward the glowing glass house above the vast field of glittering city lights, the pool rippling softly." ;;
6) v ni6_balcony_close 5 "Nova leans on the balcony rail, a breeze moving loose strands of her hair; she looks out over the city lights and a faint knowing smile forms. Shallow focus, slow push-in." ;;
7) v ni7_desert_drive 5 "The silver-white coupe speeds along the desert highway in the low golden morning sun, dust lifting behind it, the data center on the horizon. Smooth low tracking shot." ;;
8) v ni8_lobby_applicants 5 "Nova walks calmly through the crowded lobby between the rows of waiting applicants, some looking up from laptops and notes as she passes. Slow backward tracking shot ahead of her." ;;
9) v ni9_called_up 5 "The wall intercom's cyan light ring pulses. Nova rises from her chair, smoothing her blazer, while nearby applicants glance up at her. Static camera." ;;
10) v ni10_projector_fails 5 "Lyra's hologram on the projector flickers violently, breaks apart into jagged cyan static and sparks, and collapses into darkness as the platform rings die. Marcus rises from his chair. Nova stops and watches." ;;
11) v ni11_asks_lyra 6 "With the projector dark, Nova turns away from Marcus and looks up at the small ceiling camera with a warm, caring expression, speaking softly to it. Marcus watches her, intrigued, and slowly leans back. Slow push-in." ;;
12) v ni12_yes 5 "Marcus's hand finishes underlining the word YES on the notepad and sets the pen down. On the monitor behind, the cyan word YES glows softly. Static close-up." ;;
esac; done; wait; cat logs_v_*.txt; rm logs_v_*.txt; }
run "$@"
