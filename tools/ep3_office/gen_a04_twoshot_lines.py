#!/usr/bin/env python3
"""A04 lines 1-3 from LOCKED two-shot (same look as wrong words-1).

One speaker per take so Marcus keeps line 2; Lyra face stays the original hologram.
"""
from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
WW = ROOT / "wrong words"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

FIRST = SB / "A04_twoshot_lock.jpg"
DURATION = 5
MODEL = "minimax/hailuo-3"
RESOLUTION = "2K"

CLIPS = {
    "a": {
        "out": OFFICE / "A04a_twoshot_lyra_stop.mp4",
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same tight PROFILE TWO-SHOT: "
            "Lyra cyan hologram left, Marcus salt-and-pepper/beard/leather jacket right, "
            "blue map screen soft between them. Do NOT change faces, wardrobe, or camera angle. "
            "Do NOT cut away. Do NOT make Lyra solid/human. Keep her translucent cyan scanlines. "
            "AUDIO + LIPS: ONLY LYRA speaks. Marcus stays silent, mouth closed, listening. "
            "CLEAR SPOKEN ENGLISH. LYRA says exactly: \"You would have told me to stop.\" "
            "No subtitles, no captions, no on-screen text. Continuous cinematic 16:9."
        ),
    },
    "b": {
        "out": OFFICE / "A04b_twoshot_marcus_day.mp4",
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same tight PROFILE TWO-SHOT: "
            "Lyra cyan hologram left, Marcus right, blue map screen between. "
            "Do NOT change faces or angle. Keep Lyra as cyan hologram (not solid). "
            "AUDIO + LIPS: ONLY MARCUS speaks. Lyra stays silent — mouth closed, listening, "
            "NO lip movement on Lyra. "
            "CLEAR SPOKEN ENGLISH. MARCUS says exactly: "
            "\"I would have asked what happens the day after he walks in.\" "
            "No subtitles or on-screen text. Continuous cinematic 16:9."
        ),
    },
    "c": {
        "out": OFFICE / "A04c_twoshot_lyra_night.mp4",
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same tight PROFILE TWO-SHOT: "
            "Lyra cyan hologram left, Marcus right, blue map screen between. "
            "Do NOT change faces or angle. Keep Lyra translucent cyan. "
            "AUDIO + LIPS: ONLY LYRA speaks. Marcus silent, mouth closed, listening. "
            "CLEAR SPOKEN ENGLISH. LYRA says exactly: \"I did ask. Every night.\" "
            "No subtitles or on-screen text. Continuous cinematic 16:9."
        ),
    },
}


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


def video_one(key: str, name: str) -> None:
    spec = CLIPS[name]
    out: Path = spec["out"]
    if not FIRST.exists():
        raise SystemExit(f"missing {FIRST}")
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_prev.mp4"))
    est = DURATION * 0.13
    print(f"VIDEO {out.name} H3 2K {DURATION}s EST=${est:.2f}", flush=True)
    payload = {
        "model": MODEL,
        "prompt": spec["prompt"],
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
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {name} {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {out} bytes={out.stat().st_size} cost={cost}", flush=True)


def concat() -> None:
    outs = [CLIPS[n]["out"] for n in ("a", "b", "c")]
    for p in outs:
        if not p.exists():
            raise SystemExit(f"missing {p}")
    lst = WW / "concat_a04_twoshot.txt"
    lines = [f"file '{str(p).replace(chr(92), '/')}'" for p in outs]
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    dests = [
        WW / "wrong words-1_fixed.mp4",
        OFFICE / "A04_day_after_lines123_fixed.mp4",
    ]
    # backup previous fixed
    prev = WW / "wrong words-1_fixed_singles.mp4"
    if dests[0].exists():
        shutil.copy2(dests[0], prev)
    for dest in dests:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(dest)],
            check=True,
        )
        print(f"CONCAT {dest} bytes={dest.stat().st_size}", flush=True)


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which == "concat":
        concat()
        return
    names = ["a", "b", "c"] if which == "all" else [which]
    for n in names:
        video_one(key, n)
    if which == "all":
        concat()


if __name__ == "__main__":
    main()
