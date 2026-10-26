#!/usr/bin/env python3
"""A05 still storyboard — frame-accurate locks for MiniMax H3.

Usage:
  python gen_a05_storyboard.py sb01   # continuity from A04 last
  python gen_a05_storyboard.py sb02   # mid stakes / Marcus turns
  python gen_a05_storyboard.py sb03   # last-line glance / two-shot
"""
from __future__ import annotations

import base64
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
ENV = Path(r"d:\movie maker\.env")
A04 = OFFICE / "A04_day_after_last.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"
SB_DIR = OFFICE / "a05_storyboard"

FRAMES = {
    "sb01": {
        "out": "A05_sb01_open.jpg",
        "refs": [A04, MARCUS, LYRA_HOLO],
        "prompt": (
            "OUTPUT MUST BE WIDESCREEN 16:9 landscape (~1920x1080). NEVER portrait. "
            "Photoreal cinematic STILL — exact continuity from reference frame 1 (A04 last). "
            "ONLY TWO CHARACTERS TOTAL — no third person. "
            "FOREGROUND LEFT: over-the-shoulder of LYRA only — she is a translucent CYAN HOLOGRAM "
            "(soft scanlines, cyan glow). The blurred hair/shoulder IS Lyra, not a separate human blonde. "
            "MID/RIGHT: MARCUS at the glass desk, back mostly to camera, hands on desk, looking toward window/servers — "
            "same pose/position as frame 1. "
            "LOCK Marcus face identity to Marcus face reference (salt-and-pepper hair, groomed grey beard, black leather jacket, grey henley). "
            "LOCK Lyra face identity to Lyra hologram face reference (young woman, long wavy chestnut hair as cyan hologram, teal top look). "
            "Lyra stands on the OFFICE FLOOR free-walking — NOT on the desk, NO floor pad, NO second Lyra. "
            "Same office architecture as frame 1. Serious mood. Single landscape frame. No text, no collage, no watermark."
        ),
    },
    "sb02": {
        "out": "A05_sb02_lyra_listen.jpg",
        # Face card first — do NOT lead with SB01 wide or model copies backs
        "refs": [LYRA_HOLO, OFFICE / "ref_lyra_face_solid.jpg", SB_DIR / "A05_sb01_open.jpg"],
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "CAMERA: MEDIUM CLOSE-UP on LYRA'S FACE — head, neck, and upper shoulders only, with space around the head. "
            "She faces roughly toward camera / slight three-quarter, looking off toward Marcus (listening). "
            "FORBIDDEN: shot from behind, forbidden: wide two-shot, forbidden: only back of head. "
            "Lyra is translucent CYAN hologram — face LOCKED to the Lyra hologram + solid face references "
            "(same eyes, nose, mouth, long wavy chestnut hair under cyan hologram treatment, scanlines). "
            "Serious listening expression, NOT smiling. Soft blurred office bokeh behind (desk/window hint). "
            "Marcus not in frame. No third person. No collage. No watermark."
        ),
    },
    "sb03": {
        "out": "A05_sb03_marcus_window.jpg",
        "refs": [SB_DIR / "A05_sb01_open.jpg", MARCUS, LYRA_HOLO],
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox bars. NO subtitles. NO captions. NO on-screen text. "
            "DIR:SPIELBERG — SAME desk/office as SB01. "
            "MARCUS at the glass desk LOOKING OUT THE WINDOW at the city while speaking. "
            "He does NOT turn to look at Lyra — gaze stays toward the glass / outside. "
            "Profile or three-quarter beside the desk: talking, intense, controlled. "
            "Face LOCKED to Marcus face reference — salt-and-pepper hair, grey beard, black leather jacket, grey henley. "
            "Hands on desk. Lyra not in frame. Medium close (face+torso), not extreme CU. "
            "No third person. No collage. No watermark."
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


def data_url(path: Path, max_side: int = 1400, q: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in FRAMES:
        raise SystemExit("usage: gen_a05_storyboard.py sb01|sb02|sb03")
    key_name = sys.argv[1]
    spec = FRAMES[key_name]
    SB_DIR.mkdir(parents=True, exist_ok=True)
    out = SB_DIR / spec["out"]
    key = load_env()["OPENROUTER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }
    refs = [p for p in spec["refs"] if p.exists()][:3]
    if len(refs) < 3:
        raise SystemExit(f"missing refs: {spec['refs']}")
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": spec["prompt"],
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
        ],
    }
    print(f"STILL {key_name} -> {out.name} refs={[p.name for p in refs]}", flush=True)
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/images",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:2000]}") from e
    data = (body.get("data") or [None])[0]
    if not data:
        raise SystemExit("no data " + json.dumps(body)[:600])
    if data.get("b64_json"):
        out.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            out.write_bytes(img.read())
    else:
        raise SystemExit("no image")
    im = Image.open(out)
    w, h = im.size
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"OK {out} {w}x{h} ar={w/h:.3f} cost={cost}", flush=True)
    if w / h < 1.2:
        raise SystemExit("REJECTED non-16:9")


if __name__ == "__main__":
    main()
