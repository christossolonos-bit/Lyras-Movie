#!/usr/bin/env python3
"""S10 bridge: ONLY Solo + Nova. Side window, walls behind, table middle, OTS."""
from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
CLIPS = ROOT / "assets" / "coffee_clips"
REFS = ROOT / "assets" / "lyra-refs"
ENV = Path(r"d:\movie maker\.env")

OUT = CLIPS / "S10_two_only_bridge.jpg"

NOVA = REFS / "coffee_a4_nova_closeup.jpg"
SOLO = REFS / "coffee_a5_solo_closeup.jpg"
TWOSHOT = REFS / "coffee_a1_twoshot.jpg"

PROMPT = (
    "OUTPUT one 16:9 photoreal cinematic still. NO text, NO watermark, NO collage. "
    "EXACTLY TWO PEOPLE IN THE ENTIRE IMAGE — count them: 1) Nova 2) Solo. "
    "ZERO extras. FORBIDDEN: third person, silhouette, reflection, person outside window, "
    "duplicate Solo, anyone in the glass, background diner, hallway figure. "
    "Empty desert campus through the side window only — no humans outdoors. "
    "GEOGRAPHY: Nova and Solo sit opposite at a round white table; TWO mugs on the table between them. "
    "Large window is on their SIDE (lateral light). GREY WALLS behind both backs — "
    "do NOT put the window as a backdrop behind their heads. "
    "CAMERA: over-the-shoulder looking at Nova. Solo is soft FG camera-RIGHT — "
    "ONLY the back/side of ONE male head (short curly dark hair, thin glasses, maroon tee). "
    "Nova sharp camera-LEFT midground: messy dark bun, light freckles, grey zip hoodie, necklaces, "
    "TWO clear open nostrils. Eyeline to Solo. "
    "Coffee machine on interior wall left edge OK. Continuous single room, live-action."
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


def data_url(path: Path, max_side: int = 1400, q: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    refs = [p for p in (SOLO, NOVA, TWOSHOT) if p.exists()][:3]
    print(f"BRIDGE refs={[p.name for p in refs]}", flush=True)
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": PROMPT,
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/images", data=data, headers=headers(key), method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:2000]}")
    img = (body.get("data") or [None])[0]
    if not img:
        raise SystemExit(json.dumps(body)[:800])
    if img.get("b64_json"):
        OUT.write_bytes(base64.b64decode(img["b64_json"]))
    elif img.get("url"):
        with urllib.request.urlopen(img["url"], timeout=120) as r:
            OUT.write_bytes(r.read())
    else:
        raise SystemExit(json.dumps(img)[:500])
    print(f"OK {OUT} bytes={OUT.stat().st_size}", flush=True)


if __name__ == "__main__":
    main()
