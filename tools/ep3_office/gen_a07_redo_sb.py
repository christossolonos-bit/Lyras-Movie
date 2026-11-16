#!/usr/bin/env python3
"""A07 redo stills — from A06 last; screen wall only; eyeline; Lyra appear."""
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

A06 = SB / "A07_first_from_a06.jpg"
LYRA_FACE = OFFICE / "ref_lyra_face_solid.jpg"
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"
LYRA_LOOK = OFFICE / "ref_lyra_ots_scarf.png"
MARCUS = OFFICE / "ref_marcus_face.jpg"

FRAMES = {
    "sb01": {
        "out": "A07_sb01_marcus_screenwall.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO text. "
            "REFRAME the seated Marcus still: TIGHTER on Marcus on the charcoal couch. "
            "BACKGROUND = ONLY the dark wall with the large glowing BLUE DATA SCREENS behind the couch. "
            "FORBIDDEN: city WINDOW, desk area on the right, open office depth, wide room establishing. "
            "Marcus alone for now — salt-and-pepper, grey beard, brown/black leather jacket over grey shirt, "
            "same pose energy as the reference (seated, contemplative after his deep breath). "
            "Camera closer — medium / medium-wide on couch + screen wall only. No collage. No watermark."
        ),
        "refs": [A06, MARCUS, OFFICE / "A06_office_couch_screens.jpg" if False else A06],
    },
    "sb02": {
        "out": "A07_sb02_lyra_appears_eyeline.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO text. "
            "SAME tight couch framing against ONLY the screen wall (NO window, NO desk wing). "
            "Marcus seated on the couch in correct wardrobe (leather jacket, grey shirt). "
            "LYRA APPEARS as a living translucent CYAN hologram beside him on the couch — "
            "soft materialization, scanlines, NOT frozen poster still. "
            "WARDROBE: cream/white top + patterned silk scarf (blue/gold) matching Lyra look ref, cyan fringe. "
            "FACE LOCKED to Lyra face refs. "
            "They LOOK AT EACH OTHER (mutual eyeline) — intimate two-shot, faces readable. "
            "Marcus calmer, a little pity. Camera at their eye level, NOT a high wide room shot. "
            "No collage. No watermark."
        ),
        "refs": None,
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
        refs = [p for p in (A06, MARCUS, OFFICE / "ref_marcus_mid.jpg") if p.exists()][:3]
    else:
        prev = SB / "A07_sb01_marcus_screenwall.jpg"
        refs = [p for p in (prev if prev.exists() else A06, LYRA_LOOK if LYRA_LOOK.exists() else LYRA_FACE, LYRA_HOLO) if p.exists()][:3]
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
    print(f"OK {out} {im.size[0]}x{im.size[1]} cost={float((body.get('usage') or {}).get('cost') or 0)}", flush=True)


if __name__ == "__main__":
    main()
