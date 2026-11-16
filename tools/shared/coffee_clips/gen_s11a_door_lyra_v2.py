#!/usr/bin/env python3
"""S11a v2 — KEEP approved break-room door plate; REPLACE Lyra with locked face.
Refs: face crop / solid panel + good room bridge. No floor pad. Eyeline into room.

  python gen_s11a_door_lyra_v2.py
  set RUN_VIDEO=1 && python gen_s11a_door_lyra_v2.py
"""
from __future__ import annotations

import base64
import io
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
CLIPS = ROOT / "assets" / "coffee_clips"
LOCK = CLIPS / "lyra_lock"
ENV = Path(r"d:\movie maker\.env")

# Keep room geography from v1 (user approved room)
ROOM_LOCK = CLIPS / "S11a_lyra_door_bridge.jpg"
BRIDGE = CLIPS / "S11a_lyra_door_bridge_v2.jpg"
OUT = CLIPS / "S11a_lyra_door_ready_v2.mp4"
LAST = CLIPS / "S11a_lyra_door_ready_v2_last.jpg"

FACE = LOCK / "lyra_face_crop.jpg"
PANEL = LOCK / "lyra_panel_solid.jpg"
HOLO_FACE = LOCK / "lyra_panel_holo_face.jpg"
FACE_SRC = LOCK / "lyra_face_source.jpg"
FACE_HOLO = LOCK / "ref_lyra_face_holo.jpg"

DUR = 8

BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage, NO character sheet. "
    "CRITICAL ROOM LOCK: keep Image2 EXACTLY — same Vira break room, coffee machine left, "
    "round table + mugs FG soft-focus, frosted glass door open center, indoor bright corridor beyond "
    "(white ceiling lights). Do NOT change architecture, props, or outdoor desert. "
    "REPLACE only the person in the doorway. "
    "NEW FIGURE = Lyra free-walk CYAN hologram whose FACE is an exact match to Image1: "
    "same heart-shaped face, long wavy CHESTNUT hair with MIDDLE PART, green-hazel eyes, soft closed-mouth smile, "
    "same proportions as Image1 — do not invent a different woman. "
    "Whole body translucent cyan with soft scanlines and edge glow, including a cyan wash on face/hair "
    "(still recognizably Image1's face under the cyan). Teal long-sleeve top + slim pants silhouette. "
    "NO circular floor emitter pad, NO pedestal, NO projection disc. "
    "Eyeline toward the table / into the room — NEVER into the camera. "
    "FORBIDDEN: wrong face, different hairline, blonde, short hair, looking at lens, outdoor beyond door."
)

VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — same room, same door, same indoor corridor, "
    "same freefwalk cyan Lyra whose face matches the locked chestnut middle-part Lyra. Do not reinvent her face. "
    "ACTION: she firms up in the doorway, then speaks to Solo at the table "
    "(eyeline into the room — NEVER into camera). No pad. No other speakers. No subtitles. "
    "CLEAR SPOKEN ENGLISH — only Lyra: "
    "LYRA: \"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Hold after the line. Continuous 16:9 2K."
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


def data_url(path: Path, max_side: int = 1400, q: int = 92) -> str:
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


def write_image(data: dict, out: Path) -> None:
    if data.get("b64_json"):
        out.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            out.write_bytes(img.read())
    else:
        raise RuntimeError(f"no image: {json.dumps(data)[:500]}")


def still(key: str, prompt: str, refs: list[Path], out: Path) -> None:
    refs = [p for p in refs if p.exists()][:3]
    print(f"STILL {out.name} refs={[p.name for p in refs]}", flush=True)
    body = http_json(
        "https://openrouter.ai/api/v1/images",
        key,
        {
            "model": "google/gemini-2.5-flash-image",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "input_references": [
                {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
            ],
        },
        timeout=300,
    )
    data = (body.get("data") or [None])[0]
    if not data:
        raise RuntimeError(f"still empty: {json.dumps(body)[:800]}")
    write_image(data, out)
    print(f"STILL_OK {out.name} bytes={out.stat().st_size}", flush=True)


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


def video(key: str, first: Path, out: Path, last: Path, prompt: str, dur: int) -> None:
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_prev.mp4"))
    est = dur * 0.13
    print(f"VIDEO {out.name} H3 2K {dur}s EST=${est:.2f}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": prompt,
        "duration": dur,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(first, 1920)},
                "frame_type": "first_frame",
            }
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", out.name, {k: res.get(k) for k in ("id", "status")}, flush=True)
    poll = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    status = res.get("status", "pending")
    deadline = time.time() + 1500
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        res = http_json(poll, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {out.name} {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, last, float(dur))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"DONE {out.name} last={last.name} cost={cost}", flush=True)


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    if not ROOM_LOCK.exists():
        raise SystemExit(f"missing room lock {ROOM_LOCK}")
    face = FACE if FACE.exists() else PANEL
    if not face.exists():
        raise SystemExit("run crop_lyra_face_lock.py first")
    # Image1 = identity face, Image2 = approved room, Image3 = holo look hint (single face panel)
    r3 = HOLO_FACE if HOLO_FACE.exists() else (FACE_HOLO if FACE_HOLO.exists() else FACE_SRC)
    still(key, BRIDGE_PROMPT, [face, ROOM_LOCK, r3], BRIDGE)
    print(f"QUOTE H3 2K {DUR}s ≈ ${DUR * 0.13:.2f} — set RUN_VIDEO=1 only after you approve face", flush=True)
    if os.environ.get("RUN_VIDEO", "").strip() != "1":
        print(f"BRIDGE_ONLY → {BRIDGE}", flush=True)
        return
    video(key, BRIDGE, OUT, LAST, VIDEO_PROMPT, DUR)


if __name__ == "__main__":
    main()
