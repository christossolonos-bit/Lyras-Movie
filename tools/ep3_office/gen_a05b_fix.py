#!/usr/bin/env python3
"""Redo A05b — Lyra look from OTS scarf ref + Marcus command office; then H3 2K."""
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

LYRA_LOOK = OFFICE / "ref_lyra_ots_scarf.png"
OFFICE_SET = OFFICE / "A05c_marcus_facelock_bridge.jpg"  # same office as Marcus A05
MARCUS_FACE = OFFICE / "ref_marcus_face.jpg"
STILL = SB / "A05b_lyra_listen_lock.jpg"
OUT = OFFICE / "A05b_lyra_never_lied.mp4"
LAST = OFFICE / "A05b_lyra_never_lied_last.jpg"
BAK = OFFICE / "A05b_lyra_never_lied_v1_wronglook.mp4"
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


def still(key: str) -> None:
    SB.mkdir(parents=True, exist_ok=True)
    # Lyra look + Marcus office + Marcus shoulder identity for OTS
    refs = [p for p in (LYRA_LOOK, OFFICE_SET, MARCUS_FACE) if p.exists()][:3]
    prompt = (
        "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO on-screen text. "
        "Photoreal cinematic OVER-THE-SHOULDER still — DIR:SPIELBERG dialogue coverage. "
        "SET LOCK: same command office as reference frame 2 (Marcus office) — glass desk, slanted city windows, "
        "server racks, daylight — NOT a dark wood-panel room. "
        "LYRA LOOK LOCK from reference frame 1: young woman, long wavy brown hair, serious face, "
        "white/cream long-sleeve top, patterned silk scarf (blue/gold/cream) at neck, "
        "soft CYAN hologram fringe/aura around her silhouette, slightly translucent. "
        "COMPOSITION like frame 1: Lyra mid-ground facing camera/Marcus, Marcus OTS shoulder+grey hair+beard "
        "in foreground right (face LOCKED to Marcus face reference), soft focus on his shoulder. "
        "Only these two. Lyra on the floor space, NOT on a desk pad. No collage. No watermark."
    )
    print(f"STILL refs={[p.name for p in refs]}", flush=True)
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
        raise SystemExit("still no data")
    if data.get("b64_json"):
        STILL.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            STILL.write_bytes(img.read())
    else:
        raise SystemExit("still no image")
    im = Image.open(STILL)
    w, h = im.size
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"STILL_OK {STILL.name} {w}x{h} ar={w/h:.3f} cost={cost}", flush=True)
    if w / h < 1.2:
        raise SystemExit("REJECTED non-16:9")


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )


def video(key: str) -> None:
    prompt = (
        "CRITICAL: continue THIS exact first frame — same Marcus command office, same Lyra look "
        "(white top, patterned scarf, cyan hologram fringe, long wavy hair), same OTS Marcus shoulder. "
        "Do NOT change Lyra's face or wardrobe. Do NOT change the office. "
        "No floor pad. No subtitles, no captions, no on-screen text. "
        "ONE ANGLE — Lyra speaks while Marcus stays soft in foreground. "
        "CLEAR SPOKEN ENGLISH, native audio, serious. "
        "ONLY LYRA speaks. LYRA says exactly: \"I never lied to him.\" "
        "Marcus does not speak. Continuous cinematic 16:9."
    )
    est = DURATION * 0.13
    print(f"VIDEO {OUT.name} H3 2K EST=${est:.2f}", flush=True)
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
                "image_url": {"url": data_url(STILL, max_side=1920)},
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


def main() -> None:
    if not LYRA_LOOK.exists() or not OFFICE_SET.exists():
        raise SystemExit("missing lyra look or office set ref")
    if OUT.exists():
        shutil.copy2(OUT, BAK)
    key = load_env()["OPENROUTER_API_KEY"]
    still(key)
    video(key)


if __name__ == "__main__":
    main()
