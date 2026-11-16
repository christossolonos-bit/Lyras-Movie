#!/usr/bin/env python3
"""S11a face A/B — Seedance 2.0 from approved v10a solid bridge.
Compare to H3 face melt. Quote: ~$0.07/s × 8s ≈ $0.54 (OpenRouter Seedance 2.0).
"""
from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

CLIPS = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\coffee_clips")
ENV = Path(r"d:\movie maker\.env")
FIRST = CLIPS / "S11a_ots_lyra_door_bridge_v10a_solid.jpg"
OUT = CLIPS / "S11a_ots_lyra_door_seedance.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_seedance_last.jpg"
MODEL = "bytedance/seedance-2.0"
DUR = 8
# Seedance commonly wants 720p; try 1080p then fall back
RESOLUTIONS = ["1080p", "720p"]
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:2500]}") from e


def main() -> None:
    key = load_key()
    if not FIRST.exists():
        raise SystemExit(f"missing {FIRST}")
    if OUT.exists():
        shutil.copy2(OUT, OUT.with_name(OUT.stem + "_prev.mp4"))

    prompt = (
        "DIR:SPIELBERG. Continue THIS exact first frame — preserve Lyra's face identity exactly "
        "(cafe/card Lyra: chestnut wavy middle-part hair, green-hazel eyes). Do not morph her face. "
        "Same OTS: Nova left / Solo right looking at the door. "
        "Lyra is a freefwalk cyan AI hologram with soft scanlines/aura; hand on the door rim; "
        "warm inviting expression. Eyeline to Solo, never into camera. No floor pad. Indoor corridor only. "
        "No subtitles. "
        "CLEAR SPOKEN ENGLISH — only Lyra: "
        f'LYRA: "{LINE}" '
        "Quiet hold after. Continuous 16:9."
    )

    last_err = None
    res = None
    used_res = None
    for resolution in RESOLUTIONS:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "duration": DUR,
            "resolution": resolution,
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
        print(f"TRY {MODEL} {resolution} {DUR}s from {FIRST.name}", flush=True)
        try:
            res = http_json("https://openrouter.ai/api/v1/videos", key, payload)
            used_res = resolution
            break
        except RuntimeError as e:
            last_err = e
            print(f"REJECT {resolution}: {e}", flush=True)
            continue
    if res is None:
        raise SystemExit(f"all resolutions failed: {last_err}")

    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, "res=", used_res, flush=True)
    poll = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    status = res.get("status", "pending")
    deadline = time.time() + 1800
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        res = http_json(poll, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:1000]}")
    urls = res.get("unsigned_urls") or []
    if not urls:
        raise SystemExit(f"no urls: {json.dumps(res)[:800]}")
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
    cost = float((res.get("usage") or {}).get("cost") or (0.067 * DUR))
    print(f"DONE {OUT.name} last={LAST.name} cost={cost} resolution={used_res}", flush=True)


if __name__ == "__main__":
    main()
