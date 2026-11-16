#!/usr/bin/env python3
"""S11a OTS v10 — hard face lock from lyra_face_source + lyra_ref solid.
Pass A: solid Lyra (correct face) hand on door rim in OTS.
Pass B: cyan hologram treatment WITHOUT changing her face.
Bridge only unless RUN_VIDEO=1.
"""
from __future__ import annotations

import base64
import io
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from PIL import Image

CLIPS = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\coffee_clips")
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
LOCK = CLIPS / "lyra_lock"
ENV = Path(r"d:\movie maker\.env")

OTS = CLIPS / "S11a_ots_lyra_door_bridge_v7.jpg"
FACE_SRC = REPO / "lyra_face_source.png"
CARD = REPO / "lyra_ref.png"
CUT = CLIPS / "S11a_lyra_solid_cutout.jpg"
SOLID_PANEL = LOCK / "card_q0_solid.jpg"
HOLO_PANEL = LOCK / "card_q1_holo_face.jpg"

PASS_A = CLIPS / "S11a_ots_lyra_door_bridge_v10a_solid.jpg"
BRIDGE = CLIPS / "S11a_ots_lyra_door_bridge_v10.jpg"
OUT = CLIPS / "S11a_ots_lyra_door_v10.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_v10_last.jpg"
DUR = 8
LINE = "Solo… whenever you're ready. I'd love to show you around."


def load_key() -> str:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env["OPENROUTER_API_KEY"]


def headers(key: str) -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }


def data_url(path: Path, max_side: int = 1600, q: int = 95) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def http_json(url: str, key: str, payload: dict | None = None, timeout: int = 300) -> dict:
    if payload is not None:
        raise SystemExit("REFUSED: new generation must go through production_lock.py (see PRODUCTION_RULES.md)")
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers(key), method="GET" if payload is None else "POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def still(key: str, prompt: str, refs: list[Path], out: Path) -> None:
    refs = [p for p in refs if p.exists()][:3]
    print(f"STILL {out.name} ← {[p.name for p in refs]}", flush=True)
    body = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/images", key, body)
    item = (res.get("data") or [None])[0]
    if not item:
        raise SystemExit(f"empty still: {json.dumps(res)[:600]}")
    raw = (
        base64.b64decode(item["b64_json"])
        if item.get("b64_json")
        else urllib.request.urlopen(item["url"]).read()
    )
    out.write_bytes(raw)
    print(f"OK {out.name} {out.stat().st_size}", flush=True)


def ensure_panels() -> None:
    LOCK.mkdir(exist_ok=True)
    # face source api jpg
    Image.open(FACE_SRC).convert("RGB").save(LOCK / "lyra_face_source_api.jpg", quality=95)
    card = Image.open(CARD).convert("RGB")
    w, h = card.size
    cw, ch = w // 2, h // 2
    card.crop((0, 0, cw, ch)).save(SOLID_PANEL, quality=95)
    card.crop((cw, 0, w, ch)).save(HOLO_PANEL, quality=95)
    # tight face from cafe source
    fs = Image.open(FACE_SRC).convert("RGB")
    fw, fh = fs.size
    fs.crop((int(fw * 0.28), int(fh * 0.05), int(fw * 0.72), int(fh * 0.55))).save(
        LOCK / "lyra_face_tight.jpg", quality=95
    )


def video(key: str) -> None:
    if OUT.exists():
        shutil.copy2(OUT, OUT.with_name(OUT.stem + "_prev.mp4"))
    est = DUR * 0.13
    print(f"VIDEO H3 2K {DUR}s EST=${est:.2f}", flush=True)
    prompt = (
        "DIR:SPIELBERG. CRITICAL: continue THIS exact first frame — high quality 2K, no face morph. "
        "Same OTS Nova+Solo. Same Lyra: her FACE must stay identical to this still "
        "(lyra_face_source identity — chestnut wavy middle-part, green-hazel eyes). "
        "She is a cyan AI hologram with scanlines/aura but face stays hers. Hand on door rim. "
        "Eyeline to Solo, never camera. No pad. No subtitles. "
        "CLEAR SPOKEN ENGLISH — only Lyra, soft personal: "
        f'LYRA: "{LINE}" '
        "Quiet hold after. Continuous 16:9."
    )
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": prompt,
        "duration": DUR,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(BRIDGE, 1920)},
                "frame_type": "first_frame",
            }
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, flush=True)
    poll = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    status = res.get("status", "pending")
    deadline = time.time() + 1500
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        res = http_json(poll, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    req = urllib.request.Request(urls[0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        OUT.write_bytes(resp.read())
    ss = max(0.1, DUR - 0.3)
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(ss), "-i", str(OUT),
            "-frames:v", "1", "-update", "1", "-q:v", "2", str(LAST),
        ],
        capture_output=True,
    )
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"DONE {OUT.name} cost={cost}", flush=True)


def main() -> None:
    key = load_key()
    ensure_panels()
    face_tight = LOCK / "lyra_face_tight.jpg"
    face_api = LOCK / "lyra_face_source_api.jpg"

    # Pass A — SOLID photoreal identity (no hologram word) so face locks to cafe source
    still(
        key,
        (
            "OUTPUT 16:9 photoreal. NO text. NO collage. "
            "KEEP Image2 OTS exactly: Nova left / Solo right at table looking at open frosted door, indoor corridor. "
            "REPLACE doorway person with the EXACT woman from Image1 (cafe portrait) and Image3 (full-body teal top): "
            "SAME face — heart-shaped, green-hazel eyes, long wavy chestnut-brunette middle-part hair, soft smile. "
            "Fair natural skin. Deep teal scoop long-sleeve top, dark slim pants. "
            "POSE: standing in doorway, ONE hand resting on the metal door rim/frame, slight lean into the room. "
            "Looking at Solo (not camera). Photoreal human — NO cyan hologram yet, NO blue body, NO scanlines, NO pad. "
            "If her face does not match Image1, the image is wrong."
        ),
        [face_tight if face_tight.exists() else face_api, OTS, CUT if CUT.exists() else SOLID_PANEL],
        PASS_A,
    )

    # Pass B — hologram treatment only; face frozen from Pass A
    still(
        key,
        (
            "OUTPUT 16:9 photoreal. NO text. "
            "KEEP Image1 EXACTLY — same OTS, same Lyra pose with hand on door rim, SAME FACE (do not redesign her face). "
            "Only add AI-hologram treatment from Image2 style: soft cyan translucent glow, light scanlines, edge fringe "
            "around her body — skin/hair/eyes from Image1 must remain clearly her (cafe Lyra), not a different woman, "
            "not a featureless blue silhouette. No floor projector pad. "
            "Image3 is identity backup — match that face if anything drifts."
        ),
        [PASS_A, HOLO_PANEL, face_api],
        BRIDGE,
    )

    print(f"QUOTE H3 2K {DUR}s ≈ ${DUR * 0.13:.2f} — approve FACE on {BRIDGE.name} then RUN_VIDEO=1", flush=True)
    if os.environ.get("RUN_VIDEO", "").strip() != "1":
        print(f"BRIDGE_ONLY → {BRIDGE}", flush=True)
        return
    video(key)


if __name__ == "__main__":
    main()
