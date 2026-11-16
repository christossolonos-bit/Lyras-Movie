#!/usr/bin/env python3
"""S11a OTS v8 — keep v7 look; Lyra performance like bay08 cabin (car) hologram."""
from __future__ import annotations

import base64
import io
import json
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

BASE = CLIPS / "S11a_ots_lyra_door_bridge_v7.jpg"
FACE = LOCK / "lyra_face_source_api.jpg"
CUT = CLIPS / "S11a_lyra_solid_cutout.jpg"
CABIN = REPO / "bay08_cabin_interior.png"
EXPR = LOCK / "lyra_cabin_expression.jpg"
BRIDGE = CLIPS / "S11a_ots_lyra_door_bridge_v8.jpg"
OUT = CLIPS / "S11a_ots_lyra_door_v8.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_v8_last.jpg"
DUR = 8


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


def data_url(path: Path, max_side: int = 1600, q: int = 94) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def http_json(url: str, key: str, payload: dict | None = None, timeout: int = 300) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers=headers(key), method="GET" if payload is None else "POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    key = load_key()
    LOCK.mkdir(exist_ok=True)
    cab = Image.open(CABIN).convert("RGB")
    w, h = cab.size
    cab.crop((int(w * 0.52), int(h * 0.12), int(w * 0.92), int(h * 0.62))).save(EXPR, quality=95)
    print(f"EXPR {EXPR.name}", flush=True)

    face = FACE if FACE.exists() else CUT
    bridge_prompt = (
        "OUTPUT 16:9 photoreal cinematic still. NO text. "
        "KEEP Image2 EXACTLY for composition: OTS Nova left / Solo right at table looking at frosted door, "
        "indoor cyan corridor. "
        "Lyra in doorway keeps SAME identity as Image1 (card face, chestnut wavy hair, teal top, "
        "soft cyan freefwalk aura, readable face — not featureless blue blob, no floor pad). "
        "CHANGE only PERFORMANCE to match Image3 (Lyra hologram in the vehicle cabin): "
        "brighter engaged smile, lively eyes, inviting warmth, slight head tilt, soft open-hand greeting gesture — "
        "more alive and expressive. Eyeline to Solo/Nova, never into camera."
    )
    print("STILL bridge v8", flush=True)
    body = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": bridge_prompt,
        "aspect_ratio": "16:9",
        "input_references": [
            {"type": "image_url", "image_url": {"url": data_url(face)}},
            {"type": "image_url", "image_url": {"url": data_url(BASE)}},
            {"type": "image_url", "image_url": {"url": data_url(EXPR)}},
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/images", key, body)
    item = (res.get("data") or [None])[0]
    if not item:
        raise SystemExit(str(res)[:600])
    raw = (
        base64.b64decode(item["b64_json"])
        if item.get("b64_json")
        else urllib.request.urlopen(item["url"]).read()
    )
    BRIDGE.write_bytes(raw)
    print(f"BRIDGE_OK {BRIDGE.stat().st_size}", flush=True)

    est = DUR * 0.13
    print(f"VIDEO H3 2K {DUR}s EST=${est:.2f}", flush=True)
    if OUT.exists():
        shutil.copy2(OUT, OUT.with_name(OUT.stem + "_prev.mp4"))
    video_prompt = (
        "CRITICAL: continue THIS exact first frame at high cinematic quality — sharp 2K, natural motion, no morphing. "
        "Same OTS Nova+Solo looking at freefwalk cyan Lyra in the doorway (card face readable, soft cyan aura, no pad). "
        "PERFORMANCE: Lyra warmly expressive like her vehicle-cabin hologram — bright inviting smile, lively eyes, "
        "slight greeting gesture, emotional presence while speaking; not stiff or blank. "
        "Eyeline to them, never camera. Indoor corridor only. No subtitles. "
        "CLEAR SPOKEN ENGLISH — only Lyra: "
        'LYRA: "Solo? Whenever you\'re ready… I\'d like to show you around." '
        "Hold with a soft smile after. Continuous 16:9."
    )
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": video_prompt,
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


if __name__ == "__main__":
    main()
