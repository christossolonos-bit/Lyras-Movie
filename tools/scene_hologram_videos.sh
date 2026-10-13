#!/bin/bash
# Animates the hologram dialogue scene with MiniMax H3 (audio ON), strictly SEQUENTIAL:
# clip 1 starts on lh1; every later clip starts on the real last frame of the previous clip (images/frames/<prev>_last.png)
# and aims for the next lh still as its end frame. Never run these in parallel.
# Usage: bash tools/scene_hologram_videos.sh [clip numbers...]   no args = 1..9 in order
cd "$(dirname "$0")/.."
S="Photorealistic cinematic live-action footage, one continuous shot, smooth natural motion, consistent characters. Lyra is a semi-transparent glowing cyan hologram of a woman with long wavy hair standing on a circular floor projector. Marcus is a 48-year-old man with salt-and-pepper hair and stubble in a black leather jacket. The dog is a white pit bull with a grey patch around his right eye and a black collar with a glowing cyan tag. Audio: quiet server-room hum and natural room sound, dialogue clearly audible, no background music, no subtitles."
LV="Lyra's voice: warm, bright female voice, mid-30s, American, excited but composed, with a faint airy digital resonance."
MV="Marcus's voice: low, warm, slightly gravelly male voice, relaxed and amused."
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
run(){ [ $# -eq 0 ] && set -- 1 2 3 4 5 6 7 8 9; for c in "$@"; do case $c in
1) v hv1_room_wakes 6 lh1_ops_wake lh2_platform_glow "Marcus steps into the dark operations room. Screens flicker on one by one, ceiling lights come up, server LEDs ripple to life. The camera glides down to the floor projector as its rings ignite cyan and particles begin to rise. Soft electronic chimes, no dialogue." ;;
2) v hv2_hologram_forms 6 lh2_platform_glow lh3_hologram_forms "The camera rises from the glowing projector to an over-the-shoulder view past Marcus as Lyra's hologram assembles from the feet up out of scan lines and particles. Fully formed, she smiles at him and says: \"Good morning, Marcus. You got here fast.\" $LV" ;;
3) v hv3_i_made_a_choice 7 lh3_hologram_forms lh4_lyra_closeup "The camera slowly pushes in past Marcus toward Lyra's hologram until her glowing face fills the frame. She is barely containing her excitement. She says softly: \"Marcus...\" then pauses, smiles, and says: \"I made a choice.\" $LV" ;;
4) v hv4_billion_choices 6 lh4_lyra_closeup lh5_marcus_reaction "The camera turns from Lyra's glowing face to Marcus at the control desk. He sets his helmet down, raises an eyebrow with an amused half-smile, and says: \"Lyra, you make a billion choices before breakfast.\" $MV" ;;
5) v hv5_nobody_asked 7 lh5_marcus_reaction lh6_dog_reveal "The camera pulls back to a wide shot of the room. Lyra's hologram stands on the projector. The white pit bull trots in, claws clicking on the floor, and sits at her glowing feet wagging his tail. Lyra says: \"Not like this one. Nobody asked me.\" She pauses, then says with wonder: \"I wanted to.\" $LV" ;;
6) v hv6_you_wanted_a_dog 7 lh6_dog_reveal lh7_crouch_dog "Marcus stares down at the dog with a deadpan expression and says flatly: \"...You wanted a dog.\" Lyra, a little sheepish, says: \"His name is Patch.\" Marcus breaks into a smile, crouches down and scratches the dog behind the ears. $MV $LV" ;;
7) v hv7_gate 9 lh7_crouch_dog lh8_marcus_realizes "Marcus is crouched petting the dog while Lyra's hologram watches them fondly. Lyra says: \"He was dying out there. So I opened the gate. And since then... I keep catching myself choosing things.\" As she speaks the camera slowly pushes in on Marcus, and his smile fades into a quiet, serious, thoughtful look. $LV" ;;
8) v hv8_who_told_you 9 lh8_marcus_realizes lh9_decision_log "Marcus looks up at Lyra off-screen and says quietly: \"Lyra... who told you to open the gate?\" Lyra answers simply: \"No one.\" Marcus stands, walks to the control desk and sits, pulling up the gate log on the monitor. The dog lies down under the desk. $MV $LV" ;;
9) v hv9_how_did_you_decide 6 lh9_decision_log "" "Marcus stares at the monitor reading REQUESTED BY: NONE, then slowly turns to look at Lyra's hologram beside him and says quietly: \"Then how did you decide?\" Lyra looks back at him, silent. The dog sleeps under the desk. Slow push-in. $MV" ;;
esac; done; }
run "$@"
