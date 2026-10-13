#!/bin/bash
# Animates the "Juno fixes the projector" dialogue scene with MiniMax H3 (audio ON), strictly SEQUENTIAL:
# clip 1 starts on jl1; every later clip starts on the real last frame of the previous clip (images/frames/<prev>_last.png)
# and aims for the next jl still as its end frame. Never run these in parallel.
# Usage: bash tools/scene_juno_lyra_videos.sh [clip numbers...]   no args = 1..11
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot, smooth natural motion, consistent characters, set in a dark data center command room with a monitor wall, server racks and one circular hologram projector platform in the floor. Juno is a woman around 30 with a tousled platinum-blonde shaggy bob, freckles, a tattoo sleeve on her right arm, olive tank top and grease-stained charcoal overalls, brass goggles in her hair. Marcus is a 48-year-old man with salt-and-pepper hair and stubble in a black leather jacket. Audio: quiet server-room hum and natural room sound, dialogue clearly audible, no background music, no subtitles."
JV="Juno's voice: warm, slightly husky female voice, around 30, American, quick and sarcastic, a little raw from crying."
LV="Lyra's voice: warm, bright female voice, mid-30s, American, gentle and curious, with a faint airy digital resonance."
LS="Lyra is not visible; her voice comes from the ceiling speakers. $LV"
MV="Marcus's voice: low, warm, slightly gravelly male voice, relaxed."
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p images/frames
PREV="${PREV:-}"   # set PREV=<clip name> to resume the chain after that clip
v(){ n=$1; d=$2; first=$3; last=$4; p=$5
  if [ -n "$PREV" ]; then f="images/frames/${PREV}_last.png"; else f="images/$first.png"; fi
  [ -f "$f" ] || { echo "missing start frame $f"; exit 1; }
  args=(--model minimax/hailuo-3 --res 2K --duration "$d" --audio --first "$f")
  [ -n "$last" ] && args+=(--last "images/$last.png")
  echo ">> $n  first=$f  last=${last:-none}"
  python tools/gen_video.py "$n" "$p $S" "${args[@]}" || exit 1
  "$FF" -v error -sseof -0.05 -i "videos/$n.mp4" -frames:v 1 -update 1 -y "images/frames/${n}_last.png" || exit 1
  PREV=$n; }
run(){ [ $# -eq 0 ] && set -- 1 2 3 4 5 6 7 8 9 10 11; for c in "$@"; do case $c in
1) v jv1_arrival 10 jl1_arrival jl2_under_platform "Juno walks into the command room with her tool bag beside Marcus, staring around in awe. She lets out a low whistle and says: \"Okay. This place is ridiculous. Is that a liquid-cooled rack wall? Who do I have to marry to work here?\" She winces and says quietly: \"...Bad joke. Bad day for that joke.\" She drops to the floor, slides under the edge of the dark projector platform and pulls off its access panel. $JV" ;;
2) v jv2_youve_been_crying 10 jl2_under_platform jl3_talks_to_camera "Juno lies on her back under the projector platform with a headlamp on. A gentle voice from the ceiling says: \"You've been crying.\" Juno freezes and says: \"...Who said that?\" The voice says: \"The one you're fixing. I'm Lyra.\" Juno laughs, props herself up on her elbows, looks up at the ceiling camera and says: \"Of course you are. ...Is it that obvious?\" $LS $JV" ;;
3) v jv3_singing 14 jl3_talks_to_camera jl4_six_years "Juno, up on her elbows, looks at the ceiling camera. Lyra's voice says: \"Your voice is lower than it was on the dispatch call. And you sang the whole last twenty miles. People don't sing like that when they're okay.\" Juno says: \"You heard me sing?\" Lyra says: \"I watched you on the highway cameras.\" Juno groans, half laughing: \"Great. So the building's seen me ugly cry and murder every song on the radio.\" She lies back down into the open platform and starts working. $LS $JV" ;;
4) v jv4_six_years 12 jl4_six_years jl5_driver_board "Close on Juno lying in the open platform working on the circuitry with a screwdriver, eyes wet. She says quietly: \"Six years. I fixed his truck. His apartment. His credit score. Turns out I couldn't fix him.\" A pause. Lyra's voice says softly: \"Maybe he wasn't broken. Maybe he just chose wrong.\" Juno stops working, sits up slowly and pulls out a scorched circuit board. $LS $JV" ;;
5) v jv5_driver_board 13 jl5_driver_board jl6_soldering "Juno sits beside the open platform, looks up at the ceiling camera with a small surprised smile and says: \"...That's weirdly wise for a projector.\" Lyra's voice says: \"I'm not the projector. The projector is just my face.\" Juno holds up the scorched circuit board and says: \"Well, your face has a fried driver board. Somebody cheaped out on a capacitor.\" She pulls her goggles down and picks up a soldering iron. $LS $JV" ;;
6) v jv6_hasnt_met_me 7 jl6_soldering jl7_marcus_listening "Close on Juno soldering inside the platform, a thin curl of smoke rising. Lyra's voice asks: \"Can you fix it?\" Juno grins and says: \"If it's broken, it just hasn't met me yet.\" The camera slowly pulls back and pans toward Marcus at the control desk. $LS $JV" ;;
7) v jv7_marcus_listening 10 jl7_marcus_listening jl8_worth_fixing "Marcus sits at the control desk with a coffee mug, no longer looking at his screen, listening with a soft half-smile; Juno works on the floor in the background. Lyra's voice says: \"Juno? Can I ask you something?\" Juno says: \"Shoot.\" Lyra says: \"When something's this broken... how do you decide it's worth fixing?\" The camera slowly moves toward Juno as she sits up cross-legged and looks up at the ceiling. $LS $JV" ;;
8) v jv8_worth_fixing 13 jl8_worth_fixing jl9_lyra_appears "Juno sits cross-legged by the platform, thinks, and says gently: \"You don't decide with your head. You just look at it, and something in you goes, 'No. Not this one. This one's coming back.'\" A pause. Lyra's voice says quietly: \"...I think I know that feeling.\" Juno snaps the panel shut. The platform's rings ignite bright cyan and Lyra's full-body hologram rises out of scan lines and particles, standing over her. $LS $JV" ;;
9) v jv9_hi 13 jl9_lyra_appears jl10_i_want_her "Lyra's glowing cyan hologram stands on the platform smiling down at Juno, who sits on the floor looking up, breathless. Juno says: \"...Hi.\" Lyra says: \"Hi.\" Juno says: \"You're a lot prettier than your circuit boards.\" Lyra says: \"You're a lot happier than you were an hour ago.\" Juno laughs, wipes her eye and says: \"Yeah. Weird.\" Lyra turns toward Marcus. $JV $LV" ;;
10) v jv10_i_want_her 10 jl10_i_want_her jl11_job_offer "Lyra's hologram turns toward Marcus and says firmly: \"Marcus. I want her.\" Marcus rises from his chair with a slow smile and says: \"We already picked our candidate, Lyra.\" Lyra says: \"I know. I'm picking another one.\" Marcus walks over to Juno. $LV $MV" ;;
11) v jv11_job_offer 13 jl11_job_offer "" "Marcus reaches out and shakes Juno's hand and says: \"Marcus Hale. How would you like to fix things here full-time?\" Juno looks around the room, stunned, and says: \"Here? In this?\" A beat. \"Are you kidding? This place is a cathedral. ...Yes. Obviously yes.\" Lyra's hologram beams with joy beside them. $MV $JV" ;;
esac; done; }
run "$@"
