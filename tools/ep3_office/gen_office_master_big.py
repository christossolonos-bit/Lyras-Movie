#!/usr/bin/env python3
"""Ep3 office master — bigger command office (scene 5/6/6.6) + Lyra cyan bloom birth."""
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
BACKUP = OFFICE / "office_master_twoshot_v4_ml8_ring.jpg"


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

    # Gemini max 3 refs: big office set + Lyra hologram + Marcus
    refs = [
        SET / "s5_first.jpg",
        REFS / "lh4_lyra_closeup.png",
        OFFICE / "marcus_mid_crop.jpg",
    ]

    prompt = (
        "Photoreal cinematic HORIZONTAL 16:9 landscape still. "
        "MATCH the BIG high-tech command office from the set reference: spacious dark room with OPEN FLOOR "
        "so two people can walk freely — long dark desk/console with monitors and blue data UI, "
        "grey ergonomic chairs, recessed ceiling light strips, glass partition into deep blue SERVER RACKS "
        "showing DEPTH (Jackson). NOT a tiny cluttered desk room. NOT a flat left-right posed tableau. "
        "DIR:JACKSON — deep wide frame: open mid-floor space, servers receding behind glass, room to move. "
        "DIR:BAY — a wall or console CYAN RING / panel emitter near Marcus blooms — cyan light SPREADS "
        "as a volumetric flare across the nearby floor. "
        "DIR:SPIELBERG — MARCUS (salt-and-pepper hair, beard, black leather jacket, solid flesh) mid-stride "
        "or turning in the open floor, tense. LYRA forms NEXT TO him from that spreading cyan light: "
        "translucent cyan full-body hologram, long wavy hair, free-walking (NOT stuck on a pad, NOT behind glass). "
        "Serious intimate beat as she materializes. Cool blues vs warm rim lights. "
        "Single landscape frame. No collage, no text, no subtitles, no watermark."
    )

    payload = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
        "input_references": [ref_obj(p) for p in refs if p.exists()][:3],
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
    print(f"OK {OUT} bytes={OUT.stat().st_size} cost={cost}", flush=True)


if __name__ == "__main__":
    main()
