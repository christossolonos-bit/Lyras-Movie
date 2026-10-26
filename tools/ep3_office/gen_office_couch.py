#!/usr/bin/env python3
"""Office couch set still — wall screens behind; empty (no people)."""
from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
SET = OFFICE / "set_refs"
ENV = Path(r"d:\movie maker\.env")
OUT = OFFICE / "a05_storyboard" / "A06_office_couch_screens.jpg"


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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    key = load_env()["OPENROUTER_API_KEY"]
    refs = [
        p
        for p in (
            SET / "s66_mid.jpg",
            SET / "s66_first.jpg",
            OFFICE / "office_master_twoshot.jpg",
        )
        if p.exists()
    ][:3]
    prompt = (
        "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text overlays. "
        "Photoreal cinematic EMPTY SET still of Marcus's high-tech command office "
        "(same architecture/materials/lighting language as the reference frames). "
        "HERO: a modern dark low lounge COUCH / sofa in the midground, inviting someone to sit — "
        "leather or fabric, sleek, executive. "
        "BEHIND the couch: large WALL SCREENS / data monitors mounted on dark panel walls, "
        "glowing cool blue UI maps and telemetry (like the office wall displays in the refs). "
        "Polished dark floor, recessed ceiling lights, optional city window soft in frame edge. "
        "WIDE enough for a walk-to-sit shot. Depth like DIR:JACKSON. "
        "NO people. NO Marcus. NO Lyra. NO hologram. NO collage. No watermark."
    )
    print(f"refs={[p.name for p in refs]} -> {OUT.name}", flush=True)
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
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
        OUT.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            OUT.write_bytes(img.read())
    else:
        raise SystemExit("no image")
    im = Image.open(OUT)
    w, h = im.size
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"OK {OUT} {w}x{h} ar={w/h:.3f} cost={cost}", flush=True)
    if w / h < 1.2:
        raise SystemExit("REJECTED non-16:9")


if __name__ == "__main__":
    main()
