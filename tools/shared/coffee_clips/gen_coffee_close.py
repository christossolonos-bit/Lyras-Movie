#!/usr/bin/env python3
"""Coffee Act B close: S11b Nova, S11c Solo, S12b Nova button (B6–B7 locked lines).

  python gen_coffee_close.py S11b S11c S12b
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request

from gen_s11a_ots_v10_facelock import CLIPS, data_url, headers, http_json, load_key
from gen_tour import MOTION

SHOTS = {
    "S11b": {
        "first": CLIPS / "S10_solo_ots_nova_face_last.jpg", "dur": 6,
        "prompt": "DIR:SPIELBERG. Continue THIS exact frame: over Solo's blurred shoulder onto Nova at the break-room table. "
                  "Nova glances toward the doorway off frame right where Lyra's cyan light spills in, then back to Solo; "
                  "she lifts her mug and tips it toward the door with a knowing half-smile. "
                  'NOVA (dry, warm): "Go on. Don\'t keep the building waiting." '
                  "Solo's shoulder starts to rise out of frame as he stands. Locked camera, tiny push in.",
    },
    "S11c": {
        "first": CLIPS / "S10_nova_ots_solo_face_v2_last.jpg", "dur": 8,
        "prompt": "DIR:SPIELBERG. Continue THIS exact frame: over Nova's blurred shoulder onto Solo, smiling. "
                  "Solo pushes his chair back and stands with real weight, chair scraping; he looks down at Nova. "
                  'SOLO (warm, a little shy): "Sure, let\'s go. See you, Nova. Was nice talking to you." '
                  "He gives a small nod, turns and walks out of frame toward the doorway, cyan light on his face as he goes. "
                  "Camera tilts up with him as he rises, then holds on the empty window.",
    },
    "S12b": {
        "first": CLIPS / "S10_solo_ots_nova_face_last.jpg", "dur": 6,
        "prompt": "DIR:SPIELBERG. Same break-room table, Solo's chair now EMPTY and pushed back, foreground clear. "
                  "Nova sits alone, watching the doorway off frame right where cyan light fades away. A private smile. "
                  "She takes a long slow sip of her coffee, eyes still on the doorway. No dialogue. "
                  "Room tone, distant footsteps fading down the corridor. Slow push in on Nova.",
    },
}


def gen(key: str, sid: str) -> None:
    s = SHOTS[sid]
    out = CLIPS / f"{sid}_final.mp4"
    prompt = (
        s["prompt"] + " Same faces, wardrobe and light as the first frame, 2K, no morphing. Nobody looks into the camera. "
        + MOTION + "Clear natural English. No subtitles, no music swell."
    )
    payload = {
        "model": "minimax/hailuo-3", "prompt": prompt, "duration": s["dur"], "resolution": "2K",
        "aspect_ratio": "16:9", "generate_audio": True,
        "frame_images": [{"type": "image_url", "image_url": {"url": data_url(s["first"], 1920)}, "frame_type": "first_frame"}],
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
    req = urllib.request.Request(job["unsigned_urls"][0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        out.write_bytes(resp.read())
    subprocess.run(["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                    str(out.with_name(out.stem + "_last.jpg"))], capture_output=True)
    print(f"DONE {sid} cost={(job.get('usage') or {}).get('cost')}", flush=True)


def main() -> None:
    key = load_key()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(lambda sid: gen(key, sid), sys.argv[1:] or list(SHOTS)))


if __name__ == "__main__":
    main()
