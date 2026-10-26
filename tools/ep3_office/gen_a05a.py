#!/usr/bin/env python3
"""A05a — H3 2K: SB01 open → SB02 Lyra face. Marcus stakes; end on her listening."""
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

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")
FIRST = SB / "A05_sb01_open.jpg"
LAST_F = SB / "A05_sb02_lyra_listen.jpg"
OUT = OFFICE / "A05a_stakes_to_lyra.mp4"
LAST = OFFICE / "A05a_stakes_to_lyra_last.jpg"
DURATION = 15
MODEL = "minimax/hailuo-3"
RESOLUTION = "2K"

PROMPT = (
    "CRITICAL: start on the exact first frame — wide from behind, cyan hologram Lyra left, Marcus at desk right. "
    "End on the exact last frame — MEDIUM on Lyra's cyan hologram FACE (same face identity), listening. "
    "ONLY these two characters. No third person. No floor pad. No subtitles, no captions, no on-screen text. "
    "COVERAGE: hold open beat, then reframe/cut to Lyra's face medium (head+shoulders) as she listens. "
    "Do NOT change Lyra's face from the last-frame guide. Marcus may be off-camera or soft when on her CU. "
    "CLEAR SPOKEN ENGLISH, native audio. Marcus speaks the stakes (we can be on her face for part of it). "
    "MARCUS says exactly: \"You don't see it yet. You opened something you can't close with a pretty sentence. "
    "Security. Precedent. A person who can leave. Or stay. Or break.\" "
    "Lyra listens — she does not speak in this clip. Continuous cinematic 16:9."
)


def load_env() -> dict:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }


def data_url(path: Path, max_side: int = 1920, q: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def http_json(url: str, key: str, payload: dict | None = None, timeout: int = 300) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers(key), method="GET" if payload is None else "POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:2500]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    est = DURATION * 0.13
    print(f"VIDEO {OUT.name} first={FIRST.name} last={LAST_F.name} EST=${est:.2f}", flush=True)
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "duration": DURATION,
        "resolution": RESOLUTION,
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {"type": "image_url", "image_url": {"url": data_url(FIRST)}, "frame_type": "first_frame"},
            {"type": "image_url", "image_url": {"url": data_url(LAST_F)}, "frame_type": "last_frame"},
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, flush=True)
    polling_url = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if polling_url.startswith("/"):
        polling_url = "https://openrouter.ai" + polling_url
    status = res.get("status", "pending")
    deadline = time.time() + 1200
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(10)
        res = http_json(polling_url, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", OUT.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DURATION))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} cost={cost} last={LAST.exists()}", flush=True)


if __name__ == "__main__":
    main()
