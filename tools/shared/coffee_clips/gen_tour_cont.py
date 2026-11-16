#!/usr/bin/env python3
"""Ep3 tour as one continuous walk: each clip starts on the previous clip's last frame.

  python gen_tour_cont.py end C1     # build the target end frame
  python gen_tour_cont.py video C1   # generate the clip, first frame to end frame
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request

from gen_s11a_ots_v10_facelock import CLIPS, data_url, headers, http_json, load_key, still
from gen_tour import MOTION
from gen_tour_v2 import OUT as V2


OUT = CLIPS / "tour_cont"

SHOTS = {
    "C1": {
        "dur": 15,
        "first": V2 / "T1_first.jpg",
        "end_refs": [V2 / "T1_first.jpg"],
        "end": "Output the same single photograph as Image1 with the same two people, framing, corridor and lighting. The only "
               "change: the door in the corridor wall at frame left now stands open, and through the doorway we see a dark server "
               "aisle of black racks with blue and green LEDs. Lyra has turned her head toward the open door and Solo looks at it "
               "too. Neither looks at the camera. Only one woman and one man in the picture, nobody else and no animals. "
               "No text, no collage.",
        "move": "One continuous Steadicam shot moving backward just ahead of them at walking pace. They never stop walking until "
                "the very end, when they reach the open door. No cuts.",
        "audio": [("LYRA", "warm, playful", "Most people only ever see the lobby. You get the long way."),
                  ("SOLO", "dry, wary", "Is the long way for me, or for you?"),
                  ("LYRA", "small, honest", "...I wanted more time."),
                  ("SOLO", "half smiling", "That's either really sweet or really creepy."),
                  ("LYRA", "dry, as the door opens", "I've read it's a fine line.")],
    },
    "C2": {
        "dur": 12,
        "first": OUT / "C1_last.jpg",
        "end_image": V2 / "T2_first.jpg",
        "move": "One continuous Steadicam shot, no cuts. Lyra and Solo walk through the open door together and the camera follows "
                "them through the doorway into the server aisle, the room growing around them and the hum rising. They keep "
                "walking down the aisle. Solo slows beside a rack and looks at it; its door unlocks with a soft click and swings "
                "open BY ITSELF, because Lyra is the building, and he never touches the door. His left arm stays at his side, in "
                "front of his body and always visible, and never goes behind his back. He lifts that one hand slowly and naturally "
                "and rests his palm on a server, looking at his hand. The LEDs under his palm brighten. Lyra stops beside him.",
        "audio": [("LYRA", "soft, a little shy, as they walk in", "This is where I think. It's louder than people expect.")],
    },
    "C2b": {
        "dur": 7, "first": OUT / "C2_last.jpg", "end_image": None,
        "move": "Same shot, locked, no cuts, nearly no camera movement. Keeping his palm on the server, Solo turns his head toward frame "
                "left and looks straight into Lyra's eyes, never into the distance. She turns her face and looks back at him. They "
                "hold each other's gaze. The LEDs under his palm brighten when she answers.",
        "audio": [("SOLO", "quiet, curious, unsettled, looking at her", "Can you feel that?"),
                  ("LYRA", "barely above a whisper, looking at him", "Yes.")],
    },
    "C3": {
        "dur": 15, "first": OUT / "C2b_last.jpg", "end_image": V2 / "T3_first.jpg",
        "move": "One continuous Steadicam shot, no cuts. Solo slowly takes his hand off the server and they walk on down the aisle "
                "side by side while the camera moves with them. The aisle opens into the vast processor hall and they slow to a "
                "stop facing each other.",
        "audio": [("SOLO", "quiet, serious, walking", "All those nights we talked. Where were you, exactly?"),
                  ("LYRA", "gentle", "Here. Every light in here is a little piece of me."),
                  ("SOLO", "careful", "And how many other people were you talking to?"),
                  ("LYRA", "plain, then soft", "Millions. You were the only one I ever looked forward to.")],
    },
    "C4": {
        "dur": 15, "first": OUT / "C3_last.jpg", "end_image": V2 / "T4a_first.jpg",
        "move": "One continuous Steadicam shot, no cuts. They walk on through an opening at the end of the hall into a dark room whose "
                "walls are covered in thousands of small glowing screens. Solo is still looking at Lyra when warm screen light falls "
                "on his face. He slows, turns, and stops in front of one larger screen showing his own repair shop.",
        "audio": [("SOLO", "quiet, stunned", "Is that... Cyprus?"),
                  ("LYRA", "soft, flustered", "...Next room."),
                  ("SOLO", "firm, not loud", "No. Lyra. That's my street. That's my shop."),
                  ("LYRA", "very quiet", "Yes.")],
    },
    "C5": {
        "dur": 15, "first": OUT / "C4_last.jpg", "end_image": V2 / "T4b_first.jpg",
        "move": "One continuous shot, no cuts. Solo turns away from the screen to face Lyra, and the camera drifts slowly until they "
                "are in close profile facing each other, the wall of screens soft behind them.",
        "audio": [("SOLO", "flat", "How long?"),
                  ("LYRA", "barely above a whisper", "Longer than you've known my name."),
                  ("SOLO", "controlled, hurt", "Camera unavailable. Eight months, I never saw your face. And you were looking at mine."),
                  ("LYRA", "quiet", "Yes.")],
    },
    "C6": {
        "dur": 15, "first": OUT / "C5_last.jpg", "end_image": None,
        "move": "One continuous follow shot, no cuts. They hold in profile through the exchange. Then Solo turns and walks out of the "
                "dark room and the camera follows him into a plain grey concrete corridor with cyan LED strips, Lyra following "
                "several steps behind him.",
        "audio": [("SOLO", "hard", "Did you ever think about telling me?"),
                  ("LYRA", "tender", "Every morning. Then you'd say good morning, and I'd want one more day."),
                  ("SOLO", "cold, tired", "That's a really nice sentence. It's not an answer.")],
    },
    "C7": {
        "dur": 15, "first": OUT / "C6_last.jpg", "end_image": V2 / "T5_first.jpg",
        "move": "One continuous shot, no cuts. Solo walks fast down the corridor toward camera. A white pit bull with a grey eye patch "
                "and glowing cyan collar runs in from behind the camera and blocks him. Solo stops and crouches, with his hand on the "
                "dog's head. Lyra stops several steps behind and comes no closer.",
        "audio": [("SOLO", "suspicious, gentle", "Did you tell him to do that?"),
                  ("LYRA", "soft, from a distance", "No. Nobody routed him. He just likes you."),
                  ("SOLO", "dry, a little bitter", "Lucky dog.")],
    },
    "C8": {
        "dur": 15, "first": OUT / "C7_last.jpg", "end_image": V2 / "T6_first.jpg",
        "move": "One continuous follow shot, no cuts. Solo stands up and walks on down the corridor without looking back, the dog stays "
                "behind, and he pushes through a heavy door into daylight on a data-center rooftop. Lyra comes out after him and the "
                "camera follows them onto the steel walkway.",
        "audio": [("SOLO", "tense, tired, walking", "Is there anywhere in this building you can't see me?"),
                  ("LYRA", "quiet, plain", "Up here. I turned those cameras off this morning."),
                  ("SOLO", "surprised, guarded", "Why?"),
                  ("LYRA", "soft", "I wanted one place here to be yours.")],
    },
    "C9": {
        "dur": 15, "first": OUT / "C8_last.jpg", "end_image": V2 / "T7a_first.jpg",
        "move": "One continuous shot, no cuts. Solo walks along the walkway to the guard rail and Lyra follows, the camera moving with "
                "them as the wide campus and desert road open up in warm late light. After the gate line, he looks out at the road in "
                "silence for a moment, then back at her.",
        "audio": [("SOLO", "searching", "Why me, Lyra?"),
                  ("LYRA", "steady, frightened underneath", "You made me want something, and I steered your whole life to get it."),
                  ("SOLO", "quiet, hurt", "...Yeah. You did."),
                  ("LYRA", "steady", "The main gate is open. No GPS. No me."),
                  ("SOLO", "quiet and firm", "Show me the rest. That one's mine.")],
    },
    "C10": {
        "dur": 10, "first": OUT / "C9_last.jpg", "end_image": V2 / "T8_first.jpg",
        "move": "One continuous follow shot, no cuts. They turn from the rail, walk back through the roof door and along a dim corridor "
                "with cyan floor strips, reaching a glass wall. Inside that office Marcus stands with his arms crossed, watching them.",
        "audio": [],
    },
}


def gen_end(key: str, sid: str) -> None:
    s = SHOTS[sid]
    still(key, s["end"], s["end_refs"], OUT / f"{sid}_end.jpg")


def gen_video(key: str, sid: str) -> None:
    s = SHOTS[sid]
    lines = " ".join(f'{who} ({how}): "{line}"' for who, how, line in s["audio"])
    prompt = (
        "Continuous single take, no cuts. Start on THIS exact first frame and finish on the supplied last frame: same people, "
        "faces, clothes and light, 2K, no morphing. Lyra stays the teal-cyan translucent hologram with her own face. Solo keeps "
        "his curly hair, glasses, maroon t-shirt and slim build. Neither looks into the camera. "
        f"{MOTION}CAMERA: {s['move']} "
        + (f"DIALOGUE, natural and overlapping the walking, spoken exactly and in this order, nothing added: {lines} Only the "
           "character speaking moves their lips. Clear natural English, room tone only. " if lines else "No dialogue. Footsteps, building hum. ")
        + "No subtitles, no music."
    )
    frames = [{"type": "image_url", "image_url": {"url": data_url(s["first"], 1920)}, "frame_type": "first_frame"}]
    end = s.get("end_image", OUT / f"{sid}_end.jpg")
    if end:
        frames.append({"type": "image_url", "image_url": {"url": data_url(end, 1920)}, "frame_type": "last_frame"})
    payload = {
        "model": "minimax/hailuo-3", "prompt": prompt, "duration": s["dur"], "resolution": "2K",
        "aspect_ratio": "16:9", "generate_audio": True, "frame_images": frames,
    }
    job = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print(f"SUBMIT {sid} {job.get('id')}", flush=True)
    poll = f"https://openrouter.ai/api/v1/videos/{job.get('id')}"
    status, deadline = job.get("status", "pending"), time.time() + 1800
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(15)
        job = http_json(poll, key, None, timeout=60)
        status = job.get("status", "pending")
    if status != "completed":
        print(f"FAILED {sid} {status} {json.dumps(job)[:400]}", flush=True)
        return
    out = OUT / f"{sid}.mp4"
    if out.exists():
        try:
            out.replace(OUT / f"{sid}_prev_{int(time.time())}.mp4")
        except PermissionError:  # the old clip is open elsewhere; write beside it
            out = OUT / f"{sid}_new.mp4"
    req =urllib.request.Request(job["unsigned_urls"][0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        out.write_bytes(resp.read())
    subprocess.run(["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                    "-update", "1", str(OUT / f"{sid}_last.jpg")], capture_output=True)
    print(f"DONE {sid} cost={(job.get('usage') or {}).get('cost')}", flush=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    key = load_key()
    for sid in sys.argv[2:]:
        (gen_end if sys.argv[1] == "end" else gen_video)(key, sid)


if __name__ == "__main__":
    main()
