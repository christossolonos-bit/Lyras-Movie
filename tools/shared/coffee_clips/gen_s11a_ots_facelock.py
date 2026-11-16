#!/usr/bin/env python3
"""S11a OTS — keep approved OTS plate; replace doorway Lyra with FACE from card.

Identity (mandatory):
  Lyras-Movie images/lyra_face_source.png
  Lyras-Movie images/lyra_ref.png  (use single-panel crops — never 4-panel alone as Image1)

  python gen_s11a_ots_facelock.py
  set RUN_VIDEO=1 && python gen_s11a_ots_facelock.py
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
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
ENV = Path(r"d:\movie maker\.env")

# User-approved OTS geography (Nova+Solo backs → door)
OTS_GEO = CLIPS / "S11a_ots_lyra_door_bridge.jpg"
BRIDGE = CLIPS / "S11a_ots_lyra_door_bridge_v3.jpg"
OUT = CLIPS / "S11a_ots_lyra_door_v3.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_v3_last.jpg"

FACE_SRC = REPO / "lyra_face_source.png"
LYRA_CARD = REPO / "lyra_ref.png"
# single panels cropped from card
PANEL_SOLID = LOCK / "card_q0_solid.jpg"   # face+teal top
PANEL_HOLO = LOCK / "card_q1_holo_face.jpg"  # cyan face (same bones)

DUR = 8


def ensure_card_crops() -> None:
    LOCK.mkdir(exist_ok=True)
    card = Image.open(LYRA_CARD).convert("RGB")
    w, h = card.size
    cw, ch = w // 2, h // 2
    # q0 top-left solid close, q1 top-right holo close (on 2x2 card)
    q0 = card.crop((0, 0, cw, ch))
    q1 = card.crop((cw, 0, w, ch))
    # if top row is two portraits side-by-side inside q0 (some exports), keep full q0
    q0.save(PANEL_SOLID, quality=95)
    q1.save(PANEL_HOLO, quality=95)
    # also save face_source jpg for API friendliness
    Image.open(FACE_SRC).convert("RGB").save(LOCK / "lyra_face_source_api.jpg", quality=95)
    print(f"CARD_CROPS {PANEL_SOLID.name} {PANEL_HOLO.name} from {LYRA_CARD}", flush=True)


BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage, NO character-sheet grid visible. "
    "CRITICAL COMPOSITION LOCK from Image2: keep the EXACT over-the-shoulder shot — "
    "Nova (messy bun, grey hoodie) LEFT and Solo (curly hair, glasses, maroon tee) RIGHT at the round table "
    "with two mugs, backs toward camera, looking at the open frosted door and indoor cyan corridor beyond. "
    "Do not change their seats, clothes, or the room architecture. "
    "REPLACE ONLY the figure in the doorway. "
    "NEW Lyra must be the SAME PERSON as Image1 (lyra_face_source) and the solid panels of her character card: "
    "long wavy CHESTNUT/brunette hair with middle part, green-hazel eyes, heart-shaped face, soft closed-mouth smile, "
    "fair skin readable — NOT a featureless blue silhouette. "
    "She is a free-walking hologram: soft CYAN glow, light scanlines, translucent fringe around her body and teal long-sleeve top + slim pants, "
    "but her FACE and HAIR must stay clearly recognizable as Image1 under a light cyan wash (eyes, brows, mouth, hairline visible). "
    "NO circular floor projector pad. Eyeline to Solo/Nova — NEVER into camera. "
    "FORBIDDEN: anonymous blue mannequin, wrong face, blonde, short hair, outdoor desert beyond door, showing the 4-panel card."
)

VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — same OTS Nova+Solo, same doorway, "
    "same freefwalk cyan Lyra whose face matches lyra_face_source / character card (chestnut wavy middle-part, green-hazel). "
    "Do not melt her into a blue blob. No pad. Eyeline to them, not camera. No subtitles. "
    "CLEAR SPOKEN ENGLISH — only Lyra: "
    "LYRA: \"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Hold. Continuous 16:9 2K."
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


def data_url(path: Path, max_side: int = 1400, q: int = 93) -> str:
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
    for p in refs:
        print(f"  {p}", flush=True)
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
    assert FACE_SRC.exists() and LYRA_CARD.exists() and OTS_GEO.exists()
    ensure_card_crops()
    face = LOCK / "lyra_face_source_api.jpg"
    # Image1 = face source (identity), Image2 = approved OTS, Image3 = solid card panel (teal wardrobe bones)
    still(key, BRIDGE_PROMPT, [face, OTS_GEO, PANEL_SOLID], BRIDGE)
    print(f"QUOTE H3 2K {DUR}s ≈ ${DUR * 0.13:.2f} — approve face, then RUN_VIDEO=1", flush=True)
    if os.environ.get("RUN_VIDEO", "").strip() != "1":
        print(f"BRIDGE_ONLY → {BRIDGE}", flush=True)
        return
    video(key, BRIDGE, OUT, LAST, VIDEO_PROMPT, DUR)


if __name__ == "__main__":
    main()
