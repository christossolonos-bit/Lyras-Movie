#!/usr/bin/env python3
"""A07 storyboard — Lyra hologram appears beside Marcus on couch; calmer pity."""
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
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

MARCUS_SEAT = OFFICE / "A06_marcus_couch_breath_last.jpg"
COUCH = SB / "A06_sb02_marcus_sit_breath.jpg"
LYRA_SOLID = OFFICE / "ref_lyra_face_solid.jpg"
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"
MARCUS_FACE = OFFICE / "ref_marcus_face.jpg"

FRAMES = {
    "sb01": {
        "out": "A07_sb01_lyra_appears_couch.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "Photoreal cinematic MEDIUM of Marcus seated on the charcoal lounge couch in the command office "
            "(blue wall data SCREENS behind — match seated Marcus office refs). "
            "LYRA APPEARS as a translucent CYAN hologram sitting/standing close BESIDE him on the couch side — "
            "soft birth of presence, gentle scanlines, NOT a floor pad emitter. "
            "FACE LOCK: Lyra = original repo face (solid+holo refs); Marcus = salt-and-pepper, grey beard, leather jacket. "
            "Marcus looks at her a little CALMER than anger — quiet pity softening his eyes, still serious. "
            "Intimate two-shot, DIR:SPIELBERG. No collage. No watermark."
        ),
        "refs": [MARCUS_SEAT, LYRA_SOLID, LYRA_HOLO],
    },
    "sb02": {
        "out": "A07_sb02_pity_listen.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "SAME couch two-shot continuity: Marcus seated, Lyra cyan hologram beside him, wall screens behind. "
            "Marcus listening with calm pity — softer than the confrontation, not smiling wide. "
            "Lyra mid soft speech / earnest. FACE LOCK to character refs. "
            "He knows he must still research her actions, but in this beat he feels for her. "
            "No collage. No watermark."
        ),
        "refs": None,  # filled at runtime with sb01
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
        raise SystemExit("usage: sb01|sb02")
    name = sys.argv[1]
    spec = FRAMES[name]
    SB.mkdir(parents=True, exist_ok=True)
    out = SB / spec["out"]
    key = load_env()["OPENROUTER_API_KEY"]
    if name == "sb01":
        refs = [p for p in spec["refs"] if p.exists()]
        if MARCUS_FACE.exists() and len(refs) < 3:
            # prefer marcus face over missing
            pass
        if not MARCUS_SEAT.exists() and COUCH.exists():
            refs = [COUCH, LYRA_SOLID, LYRA_HOLO]
        refs = [p for p in refs if p.exists()][:3]
    else:
        prev = SB / "A07_sb01_lyra_appears_couch.jpg"
        refs = [p for p in (prev, LYRA_SOLID, MARCUS_FACE) if p.exists()][:3]
    print(f"{name} refs={[p.name for p in refs]} -> {out.name}", flush=True)
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": spec["prompt"],
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
        ],
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/images",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://moviemaker-cloud.local",
            "X-Title": "movieMaker Cloud",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode()[:2000]}") from e
    data = (body.get("data") or [None])[0]
    if not data:
        raise SystemExit("no data")
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
    print(f"OK {out} {w}x{h} cost={cost}", flush=True)


if __name__ == "__main__":
    main()
