#!/usr/bin/env python3
"""S11a video from v12a bridge.

  python gen_s11a_v12_video.py h3        # minimax/hailuo-3 2K 8s
  python gen_s11a_v12_video.py seedance  # bytedance/seedance-2.0 1080p 8s
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request

from gen_s11a_ots_v10_facelock import CLIPS, data_url, headers, http_json, load_key

BRIDGE = CLIPS / "S11a_ots_lyra_door_bridge_v12a.jpg"
DUR = 8
LINE = "Solo? Whenever you're ready... I'd like to show you around."
MODELS = {
    "h3": ("minimax/hailuo-3", "2K"),
    "seedance": ("bytedance/seedance-2.0", "1080p"),
}

PROMPT = (
    "DIR:SPIELBERG. Continue THIS exact first frame — same tight over-the-shoulder framing, camera locked "
    "with a very slow push toward the door. Nova left and Solo right stay soft-focus in the foreground, still. "
    "Lyra stays IN the doorway — she does not walk into the room. Her face stays identical to the first frame "
    "the whole clip. She remains a teal-cyan AI hologram: fine scanlines, soft edge glow, faint translucency. "
    "Her left hand drops gently to her side; her right hand stays resting on the door frame rim. "
    "She turns her eyes to Solo (frame right) and keeps them there — she never looks into the camera. "
    "A small hopeful smile, slight shyness, brows lifting as she speaks. "
    "Clear spoken English, warm and soft, only Lyra speaks: "
    f'LYRA: "{LINE}" '
    "Then a quiet one-second hold on her smile. No subtitles, no text, no music swell."
)


def main() -> None:
    model, res = MODELS[sys.argv[1]]
    out = CLIPS / f"S11a_ots_lyra_door_v12_{sys.argv[1]}.mp4"
    key = load_key()
    payload = {
        "model": model,
        "prompt": PROMPT,
        "duration": DUR,
        "resolution": res,
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {"type": "image_url", "image_url": {"url": data_url(BRIDGE, 1920)}, "frame_type": "first_frame"}
        ],
    }
    job = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", job.get("id"), job.get("status"), flush=True)
    poll = f"https://openrouter.ai/api/v1/videos/{job.get('id')}"
    status = job.get("status", "pending")
    deadline = time.time() + 1800
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        job = http_json(poll, key, None, timeout=60)
        status = job.get("status", "pending")
        print("POLL", status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(job)[:800]}")
    req = urllib.request.Request(job["unsigned_urls"][0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        out.write_bytes(resp.read())
    last = out.with_name(out.stem + "_last.jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(out), "-frames:v", "1", "-q:v", "2", str(last)],
        capture_output=True,
    )
    print(f"DONE {out.name} cost={(job.get('usage') or {}).get('cost')}", flush=True)


if __name__ == "__main__":
    main()
