#!/usr/bin/env python3
"""A05b still — keep OTS scarf image angle+background; remove Marcus."""
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
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

BASE = OFFICE / "ref_lyra_ots_scarf.png"
OUT = SB / "A05b_sb_ots_nomarcus.jpg"


def load_env() -> dict:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def data_url(path: Path, max_side: int = 1600, q: int = 92) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    if not BASE.exists():
        raise SystemExit(f"missing {BASE}")
    SB.mkdir(parents=True, exist_ok=True)
    key = load_env()["OPENROUTER_API_KEY"]
    prompt = (
        "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO captions. NO text. "
        "EDIT this exact still: KEEP the same camera angle, framing height, lens feel, lighting, "
        "and the SAME background room (dark wood/stone wall panels, glass door/window on the left, "
        "moody cinematic office). "
        "KEEP Lyra exactly as she appears — same face, long wavy brown hair, cream/white long-sleeve top, "
        "patterned silk scarf (blue/gold/cream), soft cyan hologram glow/aura. "
        "REMOVE the man in the foreground completely (grey hair/beard shoulder on the right) — "
        "inpaint clean empty space so only Lyra remains. No silhouette, no blurry head, no second person. "
        "Lyra stays in the same position in frame. Photoreal. No collage. No watermark."
    )
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(BASE)}}
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
        raise SystemExit("no data " + json.dumps(body)[:600])
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


if __name__ == "__main__":
    main()
