#!/usr/bin/env python3
"""Ep3 office master — exact set from lyra movie scene 6.6.mp4."""
from __future__ import annotations

import base64
import io
import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
REFS = ROOT / "assets" / "lyra-refs"
OFFICE = ROOT / "assets" / "office_clips"
SET = OFFICE / "set_refs"
ENV = Path(r"d:\movie maker\.env")
OUT = OFFICE / "office_master_twoshot.jpg"
BACKUP = OFFICE / "office_master_twoshot_v6_portrait.jpg"


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


def ref_obj(path: Path) -> dict:
    return {"type": "image_url", "image_url": {"url": data_url(path)}}


def main() -> None:
    if OUT.exists():
        shutil.copy2(OUT, BACKUP)

    key = load_env()["OPENROUTER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }

    # Only LANDSCAPE refs — a portrait Marcus crop biases Gemini to 9:16 output
    refs = [
        SET / "s66_mid.jpg",
        SET / "s66_first.jpg",
        REFS / "lh4_lyra_closeup.png",
    ]
    refs = [p for p in refs if p.exists()][:3]

    prompt = (
        "OUTPUT MUST BE WIDESCREEN LANDSCAPE 16:9 (wider than tall), like a TV series frame — "
        "approximately 1920x1080. NEVER portrait. NEVER vertical phone frame. "
        "Photoreal cinematic still. EXACTLY match the office from the scene 6.6 reference: "
        "spacious dark high-tech command office, polished dark floor with OPEN walking space, "
        "long modern desk with under-glow and blue data monitors, ergonomic chairs, "
        "large wall data screens, glass partitions, recessed linear ceiling lights. "
        "DIR:JACKSON — wide DEPTH: show left and right of the room so they can walk. "
        "MARCUS (salt-and-pepper hair, beard, black leather jacket) solid, mid-stride. "
        "LYRA cyan translucent full-body hologram, long wavy hair, white top + patterned scarf — "
        "FREE-WALKING on the open floor. NO floor pad, NO wall emitter, NO birth VFX. "
        "Serious mood. One landscape image only. No collage, no text, no watermark."
    )

    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "input_references": [ref_obj(p) for p in refs][:3],
    }
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
        raise SystemExit("no data " + json.dumps(body)[:800])
    if data.get("b64_json"):
        OUT.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            OUT.write_bytes(img.read())
    else:
        raise SystemExit("no image " + json.dumps(data)[:500])
    cost = float((body.get("usage") or {}).get("cost") or 0)
    im = Image.open(OUT)
    w, h = im.size
    ar = w / h
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost} size={w}x{h} ar={ar:.3f}", flush=True)
    if ar < 1.2:
        raise SystemExit(f"REJECTED portrait/non-16:9 output {w}x{h} — redo needed")


if __name__ == "__main__":
    main()
