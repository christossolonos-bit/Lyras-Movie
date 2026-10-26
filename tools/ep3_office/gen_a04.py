#!/usr/bin/env python3
"""Ep3 office A04 — close fight then Marcus turns away. hailuo-3-max 768p 15s."""
from __future__ import annotations

import base64
import io
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
ENV = Path(r"d:\movie maker\.env")
FIRST = OFFICE / "A03_eight_months_last.jpg"
OUT = OFFICE / "A04_day_after.mp4"
LAST = OFFICE / "A04_day_after_last.jpg"
DURATION = 15
MODEL = "minimax/hailuo-3-max"
RESOLUTION = "768p"

PROMPT = (
    "CRITICAL: continue THIS exact first frame — same 16:9 command office, same close face-to-face, "
    "Marcus (salt-and-pepper hair, beard, leather jacket) and Lyra as translucent CYAN free-walking hologram "
    "with soft scanlines. No floor pad, no emitter. No subtitles, no captions, no on-screen text. "
    "BLOCKING (drama series): KEEP them face-to-face for the first three lines — intimate confrontation. "
    "Lyra may half-step back then step slightly toward him on her second line. "
    "On Marcus's FINAL line only: he BREAKS — turns away from her, hands on hips (or grips desk), "
    "looks toward window/servers, frustrated, can't look at her. Lyra left facing his back / empty space. "
    "DIR:SPIELBERG faces then DIR:JACKSON slight widen as he turns. "
    "CLEAR SPOKEN ENGLISH, native audio, weight between lines. "
    "LYRA says exactly: \"You would have told me to stop.\" "
    "MARCUS says exactly: \"I would have asked what happens the day after he walks in.\" "
    "LYRA says exactly: \"I did ask. Every night.\" "
    "MARCUS says exactly: \"You asked about him. Not about the rest of us.\" "
    "Continuous cinematic 16:9."
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
    if not last.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
            check=False,
            capture_output=True,
        )


def main() -> None:
    if not FIRST.exists():
        raise SystemExit(f"missing first frame: {FIRST}")
    key = load_env()["OPENROUTER_API_KEY"]
    est = DURATION * 0.08
    print(f"VIDEO {OUT.name} first={FIRST.name} EST=${est:.2f}", flush=True)
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "duration": DURATION,
        "resolution": RESOLUTION,
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
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, flush=True)
    polling_url = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if polling_url.startswith("/"):
        polling_url = "https://openrouter.ai" + polling_url
    status = res.get("status", "pending")
    deadline = time.time() + 900
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(10)
        res = http_json(polling_url, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", OUT.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    if not urls:
        raise SystemExit(f"no urls {json.dumps(res)[:500]}")
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DURATION))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} last={LAST.exists()}", flush=True)


if __name__ == "__main__":
    main()
