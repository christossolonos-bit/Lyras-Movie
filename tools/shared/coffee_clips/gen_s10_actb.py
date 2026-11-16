#!/usr/bin/env python3
"""Act B coffee S10 — feel things → bet her → Lyra PA 'I heard that'. Chain from S09 last."""
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
CLIPS = ROOT / "assets" / "coffee_clips"
ENV = Path(r"d:\movie maker\.env")

FIRST = CLIPS / "S09_biggest_thing_v3_last.jpg"
OUT = CLIPS / "S10_feel_things_bet.mp4"
LAST = CLIPS / "S10_feel_things_bet_last.jpg"
DUR = 15

PROMPT = (
    "CRITICAL: continue THIS exact first frame — Nova close-up in Vira staff break room, "
    "same face, light freckles (do NOT densify), messy dark bun, grey zip hoodie, layered necklaces, "
    "cyan LED strip + desert window bokeh. Camera mostly on Nova; Solo may be OS or soft FG on camera-RIGHT. "
    "Seats lock: Nova camera-LEFT, Solo camera-RIGHT. No hologram body. No subtitles. "
    "Cinematic live-action, shallow DOF. CLEAR SPOKEN ENGLISH, natural acting — only the named speaker lipsyncs: "
    "SOLO (OS or soft FG, vulnerable): \"Can she even… does she actually feel things?\" "
    "NOVA (steady, soft certainty): \"Ask her yourself. But I'd bet the building on it.\" "
    "SOLO: \"You mean you'd bet her.\" "
    "NOVA (quiet, a little caught): \"…Yeah. Don't tell her I said that.\" "
    "LYRA (ceiling PA only — voice from above, no body): \"I heard that.\" "
    "NOVA (no beat missed, wry): \"Of course you did.\" "
    "Solo laughs OS. Hold Nova. Continuous 16:9."
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
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:2500]}") from e


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
        raise SystemExit(f"missing first frame {FIRST}")
    key = load_env()["OPENROUTER_API_KEY"]
    est = DUR * 0.13
    print(f"VIDEO {OUT.name} H3 2K {DUR}s EST=${est:.2f} first={FIRST.name}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": PROMPT,
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
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
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
        print("POLL", OUT.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DUR))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} last={LAST.name} cost={cost}", flush=True)


if __name__ == "__main__":
    main()
