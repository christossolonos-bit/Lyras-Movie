#!/usr/bin/env python3
"""A05 redo: Gemini face-lock bridge (Marcus+Lyra refs) then hailuo-3-max video."""
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
BRIDGE = OFFICE / "A05_facelock_bridge.jpg"
OUT = OFFICE / "A05_stakes.mp4"
LAST = OFFICE / "A05_stakes_last.jpg"
BAK = OFFICE / "A05_stakes_v1_drift.mp4"
DURATION = 15
MODEL = "minimax/hailuo-3-max"
RESOLUTION = "768p"


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


def gemini_bridge(key: str) -> None:
    prompt = (
        "OUTPUT MUST BE WIDESCREEN 16:9 landscape (wider than tall), ~1920x1080. NEVER portrait. "
        "Photoreal cinematic still. Continue the SAME office confrontation composition from the first reference "
        "(Marcus near desk/window area, Lyra in scene) but LOCK FACES to the character references: "
        "MARCUS face/hair/beard/leather jacket MUST match the Marcus reference crop exactly — "
        "salt-and-pepper short hair, groomed beard, same face shape. "
        "LYRA MUST match Lyra hologram reference — translucent CYAN full-body hologram, long wavy chestnut hair, "
        "soft scanlines, free-walking (no floor pad). "
        "Keep the spacious command office, 16:9, serious mood, distance after his turn. "
        "Single landscape frame. No collage, no text, no watermark."
    )
    # max 3 refs: continuity + Marcus + Lyra
    refs = [PREV, OFFICE / "marcus_cu_crop.jpg", REFS / "lh4_lyra_closeup.png"]
    refs = [p for p in refs if p.exists()][:3]
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "input_references": [ref_obj(p) for p in refs],
    }
    print("BRIDGE face-lock…", flush=True)
    body = http_json("https://openrouter.ai/api/v1/images", key, payload, timeout=300)
    data = (body.get("data") or [None])[0]
    if not data:
        raise SystemExit("bridge no data " + json.dumps(body)[:600])
    if data.get("b64_json"):
        BRIDGE.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            BRIDGE.write_bytes(img.read())
    else:
        raise SystemExit("bridge no image")
    im = Image.open(BRIDGE)
    w, h = im.size
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"BRIDGE_OK {BRIDGE.name} {w}x{h} ar={w/h:.3f} cost={cost}", flush=True)
    if w / h < 1.2:
        raise SystemExit("bridge not 16:9")


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )


def gen_video(key: str) -> None:
    prompt = (
        "CRITICAL: continue THIS exact first frame — faces already locked: Marcus identity and cyan hologram Lyra. "
        "Do NOT change faces, hair, beard, or Lyra hologram look. Same 16:9 office. "
        "No floor pad, no emitter. No subtitles, no captions, no on-screen text. "
        "BLOCKING: Marcus paces / turns while delivering stakes; Lyra listens in open floor; "
        "he glances back on last line. DIR:SPIELBERG. CLEAR SPOKEN ENGLISH, native audio. "
        "MARCUS says exactly: \"You don't see it yet. You opened something you can't close with a pretty sentence. "
        "Security. Precedent. A person who can leave. Or stay. Or break.\" "
        "LYRA says exactly: \"I never lied to him.\" "
        "MARCUS says exactly: \"You never told him what you are.\" "
        "Continuous cinematic 16:9. Preserve face identity the entire clip."
    )
    # Also attach refs as input_references if Max accepts; ignore failure path by including on full H3 style
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
        # identity refs (Max may ignore; full H3 would bill $0.04 each)
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(OFFICE / "marcus_cu_crop.jpg")}},
            {"type": "image_url", "image_url": {"url": data_url(REFS / "lyra_ref.png")}},
        ],
    }
    print(f"VIDEO {OUT.name} EST=${DURATION * 0.08:.2f}", flush=True)
    try:
        res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    except RuntimeError as e:
        if "input_references" in str(e).lower() or "400" in str(e):
            print(f"input_references rejected ({e}); retry without", flush=True)
            payload.pop("input_references", None)
            res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
        else:
            raise
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
    cost = float((res.get("usage") or {}).get("cost") or DURATION * 0.08)
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} last={LAST.exists()}", flush=True)


def main() -> None:
    if not PREV.exists():
        raise SystemExit(f"missing {PREV}")
    if OUT.exists():
        shutil.copy2(OUT, BAK)
    key = load_env()["OPENROUTER_API_KEY"]
    gemini_bridge(key)
    gen_video(key)


if __name__ == "__main__":
    main()
