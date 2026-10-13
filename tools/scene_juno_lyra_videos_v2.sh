#!/bin/bash
# v2 animation of "Juno fixes the projector" with MiniMax H3 (audio ON), from the jk* keyframes.
# Hard cuts start from their own still. Only same-setup pairs are chained (2->3, 8->9, 10->11): the second clip
# starts from the REAL last frame of the first. Independent groups run in parallel; each chain runs in order.
# Usage: bash tools/scene_juno_lyra_videos_v2.sh [group names...]   no args = all groups (c1 c23 c4 c5 c6 c7 c89 c1011)
# Resume a chain's second clip alone (needs images/frames/<first clip>_last.png): c3, c9, c11
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot with NO camera cuts, smooth natural motion, consistent characters, dark data center command room with a monitor wall, server racks and a single low round brushed-steel hologram projector platform on the floor. Juno is a woman around 30 with a tousled platinum-blonde shaggy bob, freckles, a tattoo sleeve on her right arm, olive tank top and grease-stained charcoal overalls, brass goggles. Marcus is a 48-year-old man with salt-and-pepper hair and stubble in a black leather jacket. Audio: quiet server-room hum and natural room sound, dialogue clearly audible, no background music, no subtitles."
JV="Juno's voice: warm, slightly husky female voice, around 30, American, quick and sarcastic, a little raw from crying."
LV="Lyra's voice: warm, bright female voice, mid-30s, American, gentle and curious, with a faint airy digital resonance."
LS="Lyra is not visible; her voice comes from the ceiling speakers. $LV"
MV="Marcus's voice: low, warm, slightly gravelly male voice, relaxed."
FF=$(python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p images/frames
# v name dur first(still name or frames/<clip>_last) last(still name or "") prompt
v(){ n=$1; d=$2; first=$3; last=$4; p=$5
  args=(--model minimax/hailuo-3 --res 2K --duration "$d" --audio --first "images/$first.png")
  [ -n "$last" ] && args+=(--last "images/$last.png")
  echo ">> $n  first=$first  last=${last:-none}"
  python tools/gen_video.py "$n" "$p $S" "${args[@]}" || return 1
  "$FF" -v error -sseof -0.05 -i "videos/$n.mp4" -frames:v 1 -update 1 -y "images/frames/${n}_last.png"; }
c1(){ v jw1_arrival 10 jk1_walk_in "" "Juno walks into the command room with her tool bag beside Marcus, staring around in awe. She lets out a low whistle and says: \"Okay. This place is ridiculous. Is that a liquid-cooled rack wall? Who do I have to marry to work here?\" She winces and says quietly: \"...Bad joke. Bad day for that joke.\" She drops her bag and kneels at the edge of the low round platform. Static wide camera. $JV"; }
c2(){ v jw2_youve_been_crying 10 jk2_under jk3_elbows "Static low camera. Juno lies on her back on the floor beside the platform, reaching into its open side, headlamp on. A gentle voice from the ceiling says: \"You've been crying.\" Juno freezes and says: \"...Who said that?\" The voice says: \"The one you're fixing. I'm Lyra.\" Juno laughs, props herself up on her elbows, looks up toward the ceiling and says: \"Of course you are. ...Is it that obvious?\" $LS $JV"; }
c3(){ v jw3_singing 14 frames/jw2_youve_been_crying_last jk3e_back_in "Same static low camera, very slow push-in. Juno, up on her elbows, looks toward the ceiling. Lyra's voice says: \"Your voice is lower than it was on the dispatch call. And you sang the whole last twenty miles. People don't sing like that when they're okay.\" Juno says: \"You heard me sing?\" Lyra says: \"I watched you on the highway cameras.\" Juno groans, half laughing: \"Great. So the building's seen me ugly cry and murder every song on the radio.\" She lies back down and reaches into the open side of the platform again. $LS $JV"; }
c4(){ v jw4_six_years 12 jk4_close "" "Static close-up on Juno's face as she lies on the floor working inside the platform with a screwdriver, eyes wet. She says quietly: \"Six years. I fixed his truck. His apartment. His credit score. Turns out I couldn't fix him.\" A pause. Lyra's voice says softly: \"Maybe he wasn't broken. Maybe he just chose wrong.\" Juno stops working and blinks. $LS $JV"; }
c5(){ v jw5_driver_board 13 jk5_board "" "Static low camera. Juno sits beside the open platform holding up a scorched circuit board, looks toward the ceiling with a small surprised smile and says: \"...That's weirdly wise for a projector.\" Lyra's voice says: \"I'm not the projector. The projector is just my face.\" Juno waggles the burnt board and says: \"Well, your face has a fried driver board. Somebody cheaped out on a capacitor.\" She pulls her goggles down over her eyes. $LS $JV"; }
c6(){ v jw6_hasnt_met_me 7 jk6_solder "" "Static close-up insert. Juno solders a circuit board inside the open side of the platform, a thin curl of smoke rising, tiny sparks. Lyra's voice asks: \"Can you fix it?\" Juno grins and says: \"If it's broken, it just hasn't met me yet.\" $LS $JV"; }
c23(){ c2 && c3; }
c89(){ c8 && c9; }
c1011(){ c10 && c11; }
c7(){ v jw7_marcus_listening 10 jk7_marcus "" "Static medium shot. Marcus sits at the control desk holding a coffee mug, no longer looking at his screen, listening with a soft half-smile; Juno works on the floor at the platform in the soft-focus background. Lyra's voice says: \"Juno? Can I ask you something?\" Juno says: \"Shoot.\" Lyra says: \"When something's this broken... how do you decide it's worth fixing?\" Marcus slowly sets his mug down. $LS $JV"; }
c8(){ v jw8_worth_fixing 13 jk8_answer jk8e_ignite "Static low camera. Juno sits cross-legged beside the platform holding the curved panel, thinks, and says gently: \"You don't decide with your head. You just look at it, and something in you goes, 'No. Not this one. This one's coming back.'\" A pause. Lyra's voice says quietly: \"...I think I know that feeling.\" Juno snaps the curved panel back onto the side of the platform. The platform's rings ignite bright cyan and a column of glowing particles begins to rise. Juno stays seated, looking up in awe. $LS $JV"; }
c9(){ v jw9_hi 13 frames/jw8_worth_fixing_last jk9_two_shot "Same static low camera. The rising particles on the platform assemble into Lyra's full-body glowing cyan hologram, standing on the platform and smiling down at Juno, who stays sitting cross-legged on the floor to the right. Juno says breathlessly: \"...Hi.\" Lyra says: \"Hi.\" Juno says: \"You're a lot prettier than your circuit boards.\" Lyra says: \"You're a lot happier than you were an hour ago.\" Juno laughs, wipes her eye and says: \"Yeah. Weird.\" $JV $LV"; }
c10(){ v jw10_i_want_her 10 jk10_wide jk11_hand "Static wide camera. Lyra's hologram on the platform turns toward Marcus at the control desk and says firmly: \"Marcus. I want her.\" Marcus rises from his chair with a slow smile and says: \"We already picked our candidate, Lyra.\" Lyra says: \"I know. I'm picking another one.\" Marcus walks over to the platform and reaches down to offer Juno his hand. $LV $MV"; }
c11(){ v jw11_job_offer 13 frames/jw10_i_want_her_last jk11e_shake "Same static wide camera. Marcus pulls Juno up off the floor and shakes her hand and says: \"Marcus Hale. How would you like to fix things here full-time?\" Juno looks around the room, stunned, and says: \"Here? In this?\" A beat. \"Are you kidding? This place is a cathedral. ...Yes. Obviously yes.\" Lyra's hologram clasps her hands, beaming with joy. $MV $JV"; }
[ $# -eq 0 ] && set -- c1 c23 c4 c5 c6 c7 c89 c1011
for gname in "$@"; do $gname > "logs_v_$gname.txt" 2>&1 & done
wait; cat logs_v_*.txt; rm logs_v_*.txt
