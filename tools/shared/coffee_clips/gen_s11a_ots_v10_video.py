#!/usr/bin/env python3
"""S11a OTS video from approved v10a solid face-lock bridge."""
from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image

CLIPS = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\coffee_clips")
ENV = Path(r"d:\movie maker\.env")
FIRST = CLIPS / "S11a_ots_lyra_door_bridge_v10a_solid.jpg"
OUT = CLIPS / "S11a_ots_lyra_door_v10.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_v10_last.jpg"
DUR = 8
LINE = "Solo… whenever you're ready. I'd love to show you around."


def load_key() -> str:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env["OPENROUTER_API_KEY"]


def headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }


def data_url(path: Path, max_side: int = 1920, q: int = 95) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def http_json(url: str, key: str, payload: dict | None = None, timeout: int = 180) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers(key), method="GET" if payload is None else "POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    key = load_key()
    if not FIRST.exists():
        raise SystemExit(f"missing {FIRST}")
    if OUT.exists():
        shutil.copy2(OUT, OUT.with_name(OUT.stem + "_prev.mp4"))
    est = DUR * 0.13
    print(f"VIDEO {OUT.name} from {FIRST.name} H3 2K {DUR}s EST=${est:.2f}", flush=True)
    prompt = (
        "DIR:SPIELBERG. CRITICAL: continue THIS exact first frame — high cinematic quality, sharp 2K, "
        "no face morph. Same OTS Nova left / Solo right. Same Lyra in the doorway — "
        "KEEP her exact face from this still (cafe/card Lyra: chestnut wavy middle-part, green-hazel eyes). "
        "She is an AI hologram: add soft cyan glow, light scanlines, translucent fringe around her body "
        "WITHOUT changing her facial identity into a different woman or a blue blob. "
        "Hand stays on the door rim. Warm expressive invite. Eyeline to Solo, never camera. No floor pad. "
        "Indoor corridor only. No subtitles. "
        "CLEAR SPOKEN ENGLISH — only Lyra, soft and personal: "
        f'LYRA: "{LINE}" '
        "Quiet hold after the line. Continuous 16:9."
    )
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": prompt,
        "duration": DUR,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(FIRST)},
                "frame_type": "first_frame",
            }
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload)
    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, flush=True)
    poll = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    status = res.get("status", "pending")
    deadline = time.time() + 1500
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        res = http_json(poll, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    req = urllib.request.Request(urls[0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        OUT.write_bytes(resp.read())
    ss = max(0.1, DUR - 0.3)
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(ss), "-i", str(OUT),
            "-frames:v", "1", "-update", "1", "-q:v", "2", str(LAST),
        ],
        capture_output=True,
    )
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"DONE {OUT.name} last={LAST.name} cost={cost}", flush=True)


if __name__ == "__main__":
    main()
