#!/usr/bin/env python3
"""A05b Lyra-only storyboard — REPO face cards only + Marcus office set.

  python gen_a05b_lyra_sb_repo.py sb01   # medium, about to speak / listening
  python gen_a05b_lyra_sb_repo.py sb02   # mid-speech
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
REFS = ROOT / "assets" / "lyra-refs"
OFFICE = ROOT / "assets" / "office_clips"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

# REPO character locks (never scarf/OTS as face source)
LYRA_SOLID = OFFICE / "ref_lyra_face_solid.jpg"  # from lyra_ref.png panel
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"  # from lyra_ref.png holo panel
LYRA_FACE = REFS / "lyra_face_source.png"
# Full character card (wardrobe + face). Do NOT pass Marcus office stills —
# they bias Gemini into OTS / second-person silhouettes.
LYRA_CARD = REFS / "lyra_ref.png"

FRAMES = {
    "sb01": {
        "out": "A05b_sb01_lyra_ready.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "EYELINE MEDIUM CLOSE-UP of LYRA ONLY — head, neck, upper chest. Camera is already "
            "facing her (Marcus has NOT turned yet — we do NOT see him at all). "
            "NO over-the-shoulder. NO silhouette. NO blurry head in foreground. NO second person. "
            "SET: high-tech command office (city windows, glass desk, servers) soft bokeh BEHIND her only. "
            "FACE LOCKED to Lyra solid + hologram face references — ORIGINAL repo face: long wavy chestnut hair, "
            "green-hazel eyes, same nose/mouth/jaw. "
            "Translucent CYAN hologram, deep teal long-sleeve top from character card. "
            "Listening / about to speak, serious. "
            "FORBIDDEN: Marcus, any male, OTS, scarf/white blouse unless on repo card, desk pad. "
            "No collage. No watermark."
        ),
    },
    "sb02": {
        "out": "A05b_sb02_lyra_speaking.jpg",
        "prompt": (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
            "SAME eyeline medium close-up — LYRA ONLY speaking (mouth slightly open). "
            "NO over-the-shoulder. NO silhouette. NO blurry head. NO Marcus. NO second person. "
            "FACE LOCKED to original Lyra repo face cards. Cyan hologram, teal top, long wavy chestnut hair. "
            "Office soft bokeh behind her only. Serious. "
            "FORBIDDEN: Marcus, OTS, scarf blouse look, desk pad. No collage. No watermark."
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
    # Repo face locks only — never scarf OTS / Marcus stills as face lead
    refs = []
    for p in (LYRA_SOLID, LYRA_HOLO, LYRA_CARD):
        if p.exists():
            refs.append(p)
        elif p == LYRA_SOLID and LYRA_FACE.exists():
            refs.append(LYRA_FACE)
    refs = refs[:3]
    if len(refs) < 2:
        raise SystemExit(f"missing lyra refs: {[LYRA_SOLID, LYRA_HOLO]}")
    print(f"STILL {name} refs={[p.name for p in refs]} -> {out.name}", flush=True)
    if name == "sb02":
        prev = SB / "A05b_sb01_lyra_ready.jpg"
        if prev.exists():
            refs = [prev, LYRA_SOLID if LYRA_SOLID.exists() else LYRA_FACE, LYRA_HOLO]
            refs = [p for p in refs if p and p.exists()][:3]
            print(f"STILL sb02 continuity refs={[p.name for p in refs]}", flush=True)
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
    if w / h < 1.2:
        raise SystemExit("REJECTED non-16:9")


if __name__ == "__main__":
    main()
