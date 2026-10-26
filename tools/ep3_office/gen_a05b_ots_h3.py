#!/usr/bin/env python3
"""A05b H3 2K from OTS-no-Marcus still."""
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

FIRST = SB / "A05b_sb_ots_nomarcus.jpg"
OUT = OFFICE / "A05b_lyra_never_lied.mp4"
LAST = OFFICE / "A05b_lyra_never_lied_last.jpg"
BAK = OFFICE / "A05b_lyra_never_lied_v4_cyanoffice.mp4"
DURATION = 8
MODEL = "minimax/hailuo-3"
RESOLUTION = "2K"


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


def data_url(path: Path, max_side: int = 1920, q: int = 92) -> str:
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
        [
            "ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4),
            "-frames:v", "1", "-update", "1", "-q:v", "2", str(last),
        ],
        check=False,
        capture_output=True,
    )


def main() -> None:
    if not FIRST.exists():
        raise SystemExit(f"missing {FIRST}")
    if OUT.exists():
        shutil.copy2(OUT, BAK)
        print(f"backup -> {BAK.name}", flush=True)
    key = load_env()["OPENROUTER_API_KEY"]
    prompt = (
        "CONTINUITY — Ep3 Marcus office Act A after his Security/Precedent/Or-break stakes. "
        "CRITICAL: continue THIS exact first frame — same Lyra face, cream top, patterned scarf, "
        "cyan hologram glow, same dark wood-panel office and camera angle. "
        "LYRA ONLY — no Marcus, no second person, no OTS silhouette. "
        "Do NOT change her face, wardrobe, or room. No floor pad. No subtitles or on-screen text. "
        "ONE ANGLE. Serious calm answer, not cute. "
        "CLEAR SPOKEN ENGLISH, native audio. ONLY LYRA speaks. "
        "LYRA says exactly: \"I never lied to him.\" "
        "Continuous cinematic 16:9."
    )
    est = DURATION * 0.13
    print(f"VIDEO {OUT.name} H3 2K {DURATION}s EST=${est:.2f} first={FIRST.name}", flush=True)
    payload = {
        "model": MODEL,
        "prompt": prompt,
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
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} last={LAST.exists()}", flush=True)


if __name__ == "__main__":
    main()
