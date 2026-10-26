#!/usr/bin/env python3
"""Ep3 office A01 REDO — sharper dialogue, drama performance. hailuo-3-max 768p 15s."""
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
FIRST = OFFICE / "office_master_twoshot.jpg"
OUT = OFFICE / "A01_sit_talking.mp4"
LAST = OFFICE / "A01_sit_talking_last.jpg"
BAK = OFFICE / "A01_sit_talking_v2_simple.mp4"
DURATION = 15
MODEL = "minimax/hailuo-3-max"
RESOLUTION = "768p"

PROMPT = (
    "CRITICAL: continue THIS exact first frame — same 16:9 spacious command office from scene 6.6, "
    "same Marcus (salt-and-pepper hair, beard, black leather jacket) and cyan free-walking hologram Lyra "
    "(long wavy hair, white top, patterned scarf). No floor pad, no wall emitter. "
    "No subtitles, no captions, no on-screen text. "
    "DRAMA SERIES LOGIC: this is the START of a confrontation — Marcus initiates with quiet authority, "
    "Lyra answers with calm literal honesty that lands as defiance, Marcus sharpens without shouting. "
    "DIR:SPIELBERG faces + DIR:JACKSON room depth — camera FOLLOWS their small moves; not a frozen left-right pose. "
    "EMOTIONAL PERFORMANCE: Marcus tense jaw, controlled anger under care; Lyra soft but steady cyan glow, "
    "slight hurt recognition on his last line. CLEAR SPOKEN ENGLISH, native audio, unhurried, weight between lines. "
    "MARCUS says exactly: \"Close the door. We're talking.\" "
    "LYRA says exactly: \"There is no door for me.\" "
    "MARCUS says exactly: \"You know what I mean.\" "
    "Natural walk/turn/gesture. Continuous cinematic 16:9."
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
    im = Image.open(FIRST)
    w, h = im.size
    if w / h < 1.2:
        raise SystemExit(f"first frame not 16:9: {w}x{h}")
    if OUT.exists():
        shutil.copy2(OUT, BAK)
    key = load_env()["OPENROUTER_API_KEY"]
    est = DURATION * 0.08
    print(f"VIDEO {OUT.name} REDO model={MODEL} {RESOLUTION} {DURATION}s EST=${est:.2f}", flush=True)
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
