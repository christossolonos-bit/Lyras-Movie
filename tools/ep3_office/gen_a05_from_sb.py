#!/usr/bin/env python3
"""A05 video — hailuo-3 2K from storyboard first/last frames."""
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
LAST_GUIDE = SB / "A05_sb03_marcus_window.jpg"
OUT = OFFICE / "A05_stakes.mp4"
LAST = OFFICE / "A05_stakes_last.jpg"
BAK = OFFICE / "A05_stakes_v3_bad.jpg"
DURATION = 15
MODEL = "minimax/hailuo-3"
RESOLUTION = "2K"

PROMPT = (
    "CRITICAL: start on THIS exact first frame — same 16:9 office, cyan hologram Lyra camera-left from behind, "
    "Marcus at glass desk camera-right leaning on desk looking toward window. Only these two. "
    "NO floor pad. NO third person. No subtitles, no captions, no on-screen text. "
    "SERIES COVERAGE (Spielberg): "
    "1) Hold the opening wide beat briefly. "
    "2) Cut/reframe to a MEDIUM on Lyra's face (head+shoulders, not extreme CU) — cyan hologram listening, serious. "
    "3) Cut/reframe to Marcus at the desk speaking his stakes while oriented toward the window/city — "
    "end matching the last-frame guide: Marcus at desk talking. "
    "Preserve Marcus and Lyra face identity from the frames. "
    "CLEAR SPOKEN ENGLISH, native audio. "
    "MARCUS says exactly: \"You don't see it yet. You opened something you can't close with a pretty sentence. "
    "Security. Precedent. A person who can leave. Or stay. Or break.\" "
    "LYRA says exactly: \"I never lied to him.\" "
    "MARCUS says exactly: \"You never told him what you are.\" "
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


def main() -> None:
    if not FIRST.exists() or not LAST_GUIDE.exists():
        raise SystemExit("missing storyboard frames")
    if OUT.exists():
        # keep prior mp4 backup name
        bak_mp4 = OFFICE / "A05_stakes_v3_prior.mp4"
        shutil.copy2(OUT, bak_mp4)
    key = load_env()["OPENROUTER_API_KEY"]
    est = DURATION * 0.13
    print(f"VIDEO {OUT.name} H3 2K first={FIRST.name} last={LAST_GUIDE.name} EST=${est:.2f}", flush=True)
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
            },
            {
                "type": "image_url",
                "image_url": {"url": data_url(LAST_GUIDE)},
                "frame_type": "last_frame",
            },
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
    if not urls:
        raise SystemExit("no urls")
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DURATION))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} last={LAST.exists()}", flush=True)


if __name__ == "__main__":
    main()
