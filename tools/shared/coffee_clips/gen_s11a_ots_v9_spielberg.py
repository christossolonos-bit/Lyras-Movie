#!/usr/bin/env python3
"""S11a OTS v9 — DIR:SPIELBERG
Lyra = AI hologram from lyra_ref card (cyan + readable face).
Hand holds the door rim. Warmer invite line.
"""
from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image

CLIPS = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\coffee_clips")
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
LOCK = CLIPS / "lyra_lock"
ENV = Path(r"d:\movie maker\.env")

BASE = CLIPS / "S11a_ots_lyra_door_bridge_v7.jpg"  # approved OTS geography
FACE = LOCK / "lyra_face_source_api.jpg"
CARD = REPO / "lyra_ref.png"
CUT = CLIPS / "S11a_lyra_solid_cutout.jpg"
HOLO_FACE = LOCK / "card_q1_holo_face.jpg"
BRIDGE = CLIPS / "S11a_ots_lyra_door_bridge_v9.jpg"
OUT = CLIPS / "S11a_ots_lyra_door_v9.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_v9_last.jpg"
DUR = 8

# Warmer than flat PA — personal, inviting (Spielberg intimacy)
LINE = 'Solo… whenever you\'re ready. I\'d love to show you around.'


def load_key() -> str:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env["OPENROUTER_API_KEY"]


def headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }


def data_url(path: Path, max_side: int = 1600, q: int = 94) -> str:
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
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ensure_holo_panel() -> Path:
    LOCK.mkdir(exist_ok=True)
    if HOLO_FACE.exists():
        return HOLO_FACE
    card = Image.open(CARD).convert("RGB")
    w, h = card.size
    cw, ch = w // 2, h // 2
    # top-right = holo face panel on 2x2 card
    card.crop((cw, 0, w, ch)).save(HOLO_FACE, quality=95)
    return HOLO_FACE


def main() -> None:
    key = load_key()
    holo = ensure_holo_panel()
    face = FACE if FACE.exists() else CUT

    bridge_prompt = (
        "DIR:SPIELBERG — photoreal 16:9 cinematic still. NO text, NO 4-panel sheet visible. "
        "KEEP Image2 OTS composition: Nova left (bun, grey hoodie) and Solo right (curly hair, glasses, maroon) "
        "at the round table with mugs, looking toward the open frosted-glass door and indoor cyan corridor. "
        "Lyra stands IN the doorway as a free-walking AI HOLOGRAM matching her character card (Image1 face + Image3 holo look): "
        "long wavy chestnut hair middle part, green-hazel eyes clearly readable, soft warm smile, "
        "full-body translucent CYAN hologram with scanlines and edge glow (like lyra_ref holo panels) — "
        "NOT a featureless blue mannequin; face and hair must stay recognizable. "
        "CRITICAL POSE: her LEFT hand rests on / lightly holds the metal DOOR RIM (door jamb / frame edge) "
        "as she leans a little into the room — intimate presence, not stiff. "
        "NO circular floor projector pad. Eyeline to Solo — never into the camera. "
        "Spielberg: wonder + human intimacy — longer face-readable beat, warm invite energy. "
        "Forbidden: outdoor desert, wrong face, hand not on door, looking at lens."
    )
    print("STILL v9 Spielberg door-rim", flush=True)
    body = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": bridge_prompt,
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(face)}},
            {"type": "image_url", "image_url": {"url": data_url(BASE)}},
            {"type": "image_url", "image_url": {"url": data_url(holo)}},
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/images", key, body)
    item = (res.get("data") or [None])[0]
    if not item:
        raise SystemExit(str(res)[:600])
    raw = (
        base64.b64decode(item["b64_json"])
        if item.get("b64_json")
        else urllib.request.urlopen(item["url"]).read()
    )
    BRIDGE.write_bytes(raw)
    print(f"BRIDGE_OK {BRIDGE} ({BRIDGE.stat().st_size})", flush=True)

    est = DUR * 0.13
    print(f"VIDEO H3 2K {DUR}s EST=${est:.2f}", flush=True)
    if OUT.exists():
        shutil.copy2(OUT, OUT.with_name(OUT.stem + "_prev.mp4"))

    video_prompt = (
        "DIR:SPIELBERG. CRITICAL: continue THIS exact first frame — high cinematic quality, sharp 2K, "
        "natural subtle motion, no morphing. "
        "Same OTS Nova+Solo looking at freefwalk CYAN AI hologram Lyra in the doorway "
        "(character-card face readable under cyan scanlines/glow; soft aura; NO floor pad). "
        "Her hand stays on the door rim as she speaks — intimate lean into the room. "
        "Warm expressive eyes and smile; wonder + invitation, not stiff PA. Eyeline to Solo, never camera. "
        "Indoor corridor only. No subtitles. "
        "CLEAR SPOKEN ENGLISH — only Lyra, soft and personal: "
        f'LYRA: "{LINE}" '
        "Quiet hold after the line (Spielberg beat). Continuous 16:9."
    )
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": video_prompt,
        "duration": DUR,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(BRIDGE, 1920)},
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
        print("POLL", status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    req = urllib.request.Request(urls[0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        OUT.write_bytes(resp.read())
    ss = max(0.1, DUR - 0.3)
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(ss), "-i", str(OUT),
            "-frames:v", "1", "-update", "1", "-q:v", "2", str(LAST),
        ],
        capture_output=True,
    )
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"DONE {OUT.name} cost={cost} LINE={LINE}", flush=True)


if __name__ == "__main__":
    main()
