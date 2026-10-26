#!/usr/bin/env python3
"""Ep3 office A02 REDO — sharper dialogue, chain from A01 last. hailuo-3-max 768p 15s."""
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
ENV = Path(r"d:\movie maker\.env")
FIRST = OFFICE / "A01_sit_talking_last.jpg"
OUT = OFFICE / "A02_cyprus_solo.mp4"
LAST = OFFICE / "A02_cyprus_solo_last.jpg"
BAK = OFFICE / "A02_cyprus_solo_v1_simple.mp4"
DURATION = 15
MODEL = "minimax/hailuo-3-max"
RESOLUTION = "768p"

PROMPT = (
    "CRITICAL: continue THIS exact first frame — same 16:9 command office, same Marcus face/wardrobe, "
    "same Lyra as cyan translucent free-walking hologram (restore clear cyan hologram look with soft scanlines "
    "if she drifted solid — she is AI hologram, not a solid blonde woman). No floor pad, no emitter. "
    "No subtitles, no captions, no on-screen text. "
    "DRAMA SERIES LOGIC: Marcus lays the charge (a real person is inside his facility because of her); "
    "Lyra answers with a name — humanizing him; Marcus rejects the soft landing and plants the real stake: presence. "
    "Escalate intensity without shouting. DIR:SPIELBERG — hold faces, follow micro-moves; not a left-right freeze. "
    "EMOTIONAL PERFORMANCE: Marcus controlled anger + protective fear; Lyra steady then slightly stung on his last line. "
    "CLEAR SPOKEN ENGLISH, native audio, weight between lines. "
    "MARCUS says exactly: \"There's a man from Cyprus walking my halls. Because you invited him.\" "
    "LYRA says exactly: \"His name is Solo.\" "
    "MARCUS says exactly: \"I don't care what he calls himself. I care that he's here.\" "
    "Natural gesture/turn while speaking. Continuous cinematic 16:9."
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
    if OUT.exists():
        shutil.copy2(OUT, BAK)
    key = load_env()["OPENROUTER_API_KEY"]
    est = DURATION * 0.08
    print(f"VIDEO {OUT.name} REDO first={FIRST.name} EST=${est:.2f}", flush=True)
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
