#!/usr/bin/env python3
"""Redo A05c — Gemini face-lock bridge (A05a last + Marcus repo face) then Max 768p."""
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

PREV = OFFICE / "A05a_marcus_stakes_last.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"
MARCUS_MID = OFFICE / "ref_marcus_mid.jpg"
BRIDGE = OFFICE / "A05c_marcus_facelock_bridge.jpg"
OUT = OFFICE / "A05c_marcus_what_you_are.mp4"
LAST = OFFICE / "A05c_marcus_what_you_are_last.jpg"
BAK = OFFICE / "A05c_marcus_what_you_are_v1_drift.mp4"
DURATION = 8
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


def bridge(key: str) -> None:
    refs = [p for p in (PREV, MARCUS, MARCUS_MID) if p.exists()][:3]
    prompt = (
        "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO on-screen text. "
        "Photoreal cinematic MEDIUM CLOSE-UP of MARCUS ONLY in the same command office as reference frame 1 "
        "(desk, city windows, servers). "
        "He has turned enough that we SEE HIS FACE clearly (three-quarter toward window), "
        "still at the desk, serious, about to speak. "
        "FACE LOCKED exactly to Marcus face reference — salt-and-pepper short hair, groomed grey beard, "
        "brown eyes, same nose/jaw. WARDROBE LOCKED — black leather jacket over grey henley (not quilted biker). "
        "NO Lyra, NO second person, NO hologram. Same office geography as frame 1. No collage. No watermark."
    )
    print(f"BRIDGE refs={[p.name for p in refs]}", flush=True)
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
        "CRITICAL: continue THIS exact first frame — SAME Marcus face already locked (salt-and-pepper, grey beard, "
        "leather jacket over grey henley). Do NOT change his face. ONLY Marcus — no Lyra. "
        "No subtitles, no captions, no on-screen text. ONE ANGLE — he speaks the knife line. "
        "CLEAR SPOKEN ENGLISH, native audio, intense controlled. "
        "MARCUS says exactly: \"You never told him what you are.\" "
        "Continuous cinematic 16:9."
    )
    est = DURATION * 0.08
    print(f"VIDEO {OUT.name} EST=${est:.2f}", flush=True)
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
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DURATION))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} last={LAST.exists()}", flush=True)


def main() -> None:
    if not PREV.exists() or not MARCUS.exists():
        raise SystemExit("missing A05a last or marcus face ref")
    if OUT.exists():
        shutil.copy2(OUT, BAK)
    key = load_env()["OPENROUTER_API_KEY"]
    bridge(key)
    video(key)


if __name__ == "__main__":
    main()
