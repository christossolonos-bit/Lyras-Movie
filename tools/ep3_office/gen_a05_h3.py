#!/usr/bin/env python3
"""A05: face-lock bridge (A04 last + refs) then hailuo-3 2K from that frame only.

MiniMax rejects frame_images + input_references in the same request.
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

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
REFS = ROOT / "assets" / "lyra-refs"
OFFICE = ROOT / "assets" / "office_clips"
ENV = Path(r"d:\movie maker\.env")
PREV = OFFICE / "A04_day_after_last.jpg"
BRIDGE = OFFICE / "A05_h3_bridge.jpg"
OUT = OFFICE / "A05_stakes.mp4"
LAST = OFFICE / "A05_stakes_last.jpg"
BAK = OFFICE / "A05_stakes_v2_max.mp4"
DURATION = 15
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


def data_url(path: Path, max_side: int = 1400, q: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def ref_obj(path: Path) -> dict:
    return {"type": "image_url", "image_url": {"url": data_url(path)}}


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


def bridge(key: str) -> None:
    prompt = (
        "OUTPUT MUST BE WIDESCREEN 16:9 landscape (~1920x1080). NEVER portrait. "
        "Photoreal cinematic still. Continue EXACTLY from the first reference (A04 last frame): "
        "same office, same Marcus position at desk/window with back/side to Lyra, same distance. "
        "LOCK Marcus face to Marcus reference crop (salt-and-pepper hair, groomed beard, leather jacket). "
        "LOCK Lyra to hologram reference: translucent CYAN full-body free-walking hologram, long wavy hair, "
        "scanlines — no floor pad. Serious confrontation. Single landscape frame. No text, no collage."
    )
    refs = [PREV, OFFICE / "marcus_cu_crop.jpg", REFS / "lh4_lyra_closeup.png"]
    refs = [p for p in refs if p.exists()][:3]
    print("BRIDGE A04+refs…", flush=True)
    body = http_json(
        "https://openrouter.ai/api/v1/images",
        key,
        {
            "model": "google/gemini-2.5-flash-image",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "input_references": [ref_obj(p) for p in refs],
        },
        timeout=300,
    )
    data = (body.get("data") or [None])[0]
    if not data:
        raise SystemExit("no bridge data")
    if data.get("b64_json"):
        BRIDGE.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            BRIDGE.write_bytes(img.read())
    else:
        raise SystemExit("no bridge image")
    im = Image.open(BRIDGE)
    w, h = im.size
    print(f"BRIDGE_OK {w}x{h} ar={w/h:.3f} cost={(body.get('usage') or {}).get('cost')}", flush=True)
    if w / h < 1.2:
        raise SystemExit("bridge not 16:9")


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )


def video(key: str) -> None:
    prompt = (
        "CRITICAL: continue THIS exact first frame — faces already locked (Marcus + cyan hologram Lyra). "
        "Do NOT change faces. Same 16:9 office. No floor pad. No subtitles, no captions, no text. "
        "BLOCKING: Marcus paces/turns with stakes; Lyra listens; glance back on last line. "
        "DIR:SPIELBERG. CLEAR SPOKEN ENGLISH, native audio. "
        "MARCUS says exactly: \"You don't see it yet. You opened something you can't close with a pretty sentence. "
        "Security. Precedent. A person who can leave. Or stay. Or break.\" "
        "LYRA says exactly: \"I never lied to him.\" "
        "MARCUS says exactly: \"You never told him what you are.\" "
        "Preserve face identity entire clip. Continuous cinematic 16:9."
    )
    est = DURATION * 0.13
    print(f"VIDEO H3 2K EST=${est:.2f}", flush=True)
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
                "image_url": {"url": data_url(BRIDGE, max_side=1920)},
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
        raise SystemExit("no urls")
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DURATION))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} last={LAST.exists()}", flush=True)


def main() -> None:
    if not PREV.exists():
        raise SystemExit(f"missing {PREV}")
    if OUT.exists():
        shutil.copy2(OUT, BAK)
    key = load_env()["OPENROUTER_API_KEY"]
    bridge(key)
    video(key)


if __name__ == "__main__":
    main()
