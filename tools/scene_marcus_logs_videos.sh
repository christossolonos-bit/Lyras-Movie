#!/bin/bash
# Animates the "Marcus reads the logs" scene with MiniMax H3, audio OFF (Lyra narration added in edit).
# Straight cuts: each clip starts from its own ml still, no end frame. Clips are independent, so they run in parallel.
# Usage: bash tools/scene_marcus_logs_videos.sh [clip numbers...]   no args = 1..12
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot, smooth natural motion, consistent character. Marcus is a 48-year-old man with short salt-and-pepper hair and grey-flecked stubble in a rumpled grey henley, in his small office with a glass wall onto a server hall. No text overlays, no subtitles."
v(){ n=$1; d=$2; p=$3
  echo ">> $n  ${d}s"
  python tools/gen_video.py "$n" "$p $S" --model minimax/hailuo-3 --res 2K --duration "$d" --first "images/$n.png" > "logs_v_$n.txt" 2>&1 & }
run(){ [ $# -eq 0 ] && set -- 1 2 3 4 5 6 7 8 9 10 11 12; for c in "$@"; do case $c in
1) v ml1_late_night 5 "Night. Marcus sits hunched at his desk, scrolling and reading intently, the server hall LEDs blinking through the glass. Very slow push-in." ;;
2) v ml2_scrolling_logs 5 "Over his shoulder, dense log data scrolls steadily up all three monitors as Marcus reads, his eyes tracking line by line. Static camera." ;;
3) v ml3_gate_log 6 "Close on the monitor: the man's finger rests under the amber line on the screen, then taps it twice, slowly. The rest of the screen stays still. Very slow push-in." ;;
4) v ml4_printouts 6 "Marcus drags a yellow highlighter down a printed log page, flips to the next page, keeps reading with intense focus. Papers shift on the crowded desk." ;;
5) v ml5_never_found 5 "In harsh daylight, Marcus presses the heels of his hands into his eyes, then drops his hands and stares at the ceiling, exhausted and baffled. Static camera." ;;
6) v ml6_cold_coffee 5 "Marcus takes a sip of coffee while staring at his monitor, pauses, grimaces at how cold it is, and sets the mug down among the others." ;;
7) v ml7_whiteboard 5 "Marcus wipes half of the diagram off the whiteboard with the side of his fist, takes the marker cap from his teeth, and immediately starts drawing it again." ;;
8) v ml8_three_am 5 "Late at night, Marcus leans back and laughs out loud at nothing, shaking his head, exhausted and a little giddy, then rubs his face. Static camera." ;;
9) v ml9_glass_wall 6 "Marcus stands at the glass wall with his hands in his pockets, staring out at the endless rows of blinking server racks, perfectly still and thoughtful. Very slow push-in." ;;
10) v ml10_looks_up 5 "Night. Marcus leans far back in his chair, rubs his stubble, and slowly turns his gaze up to the cyan-lit intercom by the door." ;;
11) v ml11_cant_alone 7 "Close on Marcus in his chair at night, looking up at the intercom off-screen, he speaks a few quiet, honest words, humble and a little vulnerable, then waits. Slow push-in." ;;
12) v ml12_yes 6 "Just before dawn, pale blue light growing in the window: the intercom's cyan ring brightens, and Marcus breaks into a slow, relieved, tired smile toward it. Static wide shot." ;;
esac; done; wait; cat logs_v_*.txt; rm logs_v_*.txt; }
run "$@"
