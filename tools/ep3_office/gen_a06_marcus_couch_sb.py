#!/usr/bin/env python3
"""A06 storyboard — Marcus window→couch, deep breath. sb01 walk / sb02 sit breath."""
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

COUCH = SB / "A06_office_couch_screens.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"
MARCUS_MID = OFFICE / "ref_marcus_mid.jpg"
MASTER = OFFICE / "office_master_twoshot.jpg"

FRAMES = {
    "sb01": {
        "out": "A06_sb01_marcus_from_window.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "Photoreal cinematic still — SAME office as references: charcoal lounge couch midground, "
            "large blue wall data screens behind/ beside the couch, polished dark floor, city WINDOW "
            "visible on the right (or edge) so we feel he is leaving that window. "
            "MARCUS ONLY — salt-and-pepper hair, grey beard, black leather jacket over dark henley "
            "(face LOCKED to Marcus face refs). He is mid-WALK away from the window toward the couch, "
            "body angled to sit, heavy thoughtful energy — the weight of the confrontation. "
            "DIR:SPIELBERG coverage, natural depth. "
            "NO Lyra, NO second person, NO hologram. No collage. No watermark."
        ),
    },
    "sb02": {
        "out": "A06_sb02_marcus_sit_breath.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "SAME office couch set as reference frame 1 — couch + glowing wall screens behind. "
            "MARCUS ONLY seated on the couch, face LOCKED to Marcus face refs "
            "(salt-and-pepper, grey beard, leather jacket). "
            "He has just sat; taking a DEEP BREATH — chest rising, eyes soft/heavy, "
            "absorbing everything he feels after the fight with Lyra. Quiet, not shouting. "
            "City window soft in background or side. Medium-wide enough to see couch + screens. "
            "NO Lyra. NO second person. No collage. No watermark."
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
        raise SystemExit("usage: sb01|sb02")
    name = sys.argv[1]
    spec = FRAMES[name]
    SB.mkdir(parents=True, exist_ok=True)
    out = SB / spec["out"]
    key = load_env()["OPENROUTER_API_KEY"]
    if name == "sb01":
        refs = [p for p in (COUCH, MARCUS if MARCUS.exists() else MARCUS_MID, MASTER) if p.exists()][:3]
    else:
        prev = SB / "A06_sb01_marcus_from_window.jpg"
        refs = [p for p in (prev if prev.exists() else COUCH, MARCUS, COUCH) if p and p.exists()]
        # dedupe preserve order
        seen = set()
        uniq = []
        for p in refs:
            if p.resolve() not in seen:
                seen.add(p.resolve())
                uniq.append(p)
        refs = uniq[:3]
        if MARCUS_MID.exists() and len(refs) < 3:
            refs.append(MARCUS_MID)
        refs = refs[:3]
    if not refs:
        raise SystemExit("missing refs")
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
    print(f"OK {out} {w}x{h} ar={w/h:.3f} cost={cost}", flush=True)


if __name__ == "__main__":
    main()
