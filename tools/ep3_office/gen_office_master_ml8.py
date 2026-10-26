#!/usr/bin/env python3
"""Ep3 office master — ml8 set depth + Lyra birth from wall cyan-ring device."""
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
BACKUP = OFFICE / "office_master_twoshot_v3_server_side_lyra.jpg"


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

    # Gemini max 3 refs: ml8 set + Lyra hologram look + Marcus face
    refs = [
        SET / "ml8_mid.jpg",
        REFS / "lh4_lyra_closeup.png",
        OFFICE / "marcus_mid_crop.jpg",
    ]

    prompt = (
        "Photoreal cinematic HORIZONTAL 16:9 still (landscape, not portrait). "
        "MATCH this exact late-night office from the reference: lived-in Marcus workspace — "
        "cluttered wooden desks with papers and coffee mugs in the FOREGROUND, "
        "Marcus seated in a black leather chair MID-GROUND (grey long-sleeve, salt-and-pepper hair, beard), "
        "triple monitors + warm desk lamp behind him, whiteboard with tech diagrams on the RIGHT, "
        "motorcycle helmet on wire shelf, LEFT glass wall into deep blue SERVER RACKS (background depth only). "
        "DIR:JACKSON — deep office: foreground clutter → Marcus + Lyra mid → servers far through glass. "
        "DIR:BAY — wall-mounted silver panel with CYAN RING on Marcus's OFFICE side of the glass "
        "(door/frame beside him, NOT inside the server cage). The ring is flaring — cyan light SPREADS "
        "across the nearby wall and floor like a bloom / volumetric wash. "
        "DIR:SPIELBERG — LYRA forms NEXT TO MARCUS in the office proper: translucent cyan full-body hologram "
        "young woman long wavy hair, materializing from that spreading ring-light into standing space "
        "beside his chair (same side of the glass as Marcus). Free-walk hologram, NOT behind glass, "
        "NOT stuck on a pad, NOT in the server room. Marcus turned toward her. Serious, intimate. "
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
