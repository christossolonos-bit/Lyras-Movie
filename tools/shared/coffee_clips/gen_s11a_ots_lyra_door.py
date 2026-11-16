#!/usr/bin/env python3
"""S11a OTS redo — from Solo/Nova seats looking AT freefwalk Lyra in the doorway.
All Lyra identity refs from Lyras-Movie repo only. No floor pad. Never look into camera.

  python gen_s11a_ots_lyra_door.py              # bridge only
  set RUN_VIDEO=1 && python gen_s11a_ots_lyra_door.py
"""
from __future__ import annotations

import base64
import io
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
CLIPS = ROOT / "assets" / "coffee_clips"
REFS_LOCAL = ROOT / "assets" / "lyra-refs"  # coffee room / Nova Solo only
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
ENV = Path(r"d:\movie maker\.env")

BRIDGE = CLIPS / "S11a_ots_lyra_door_bridge.jpg"
OUT = CLIPS / "S11a_ots_lyra_door.mp4"
LAST = CLIPS / "S11a_ots_lyra_door_last.jpg"

# —— Lyra: REPO ONLY ——
LYRA_FACE = REPO / "ep3_office" / "ref_lyra_face_solid.jpg"
if not LYRA_FACE.exists():
    LYRA_FACE = REPO / "lyra_face_source.png"
LYRA_HOLO_FACE = REPO / "ep3_office" / "ref_lyra_face_holo.jpg"
LH4 = REPO / "lh4_lyra_closeup.png"
LH3 = REPO / "lh3_hologram_forms.png"
LYRA_REF = REPO / "lyra_ref.png"  # never alone as Image1 (4-panel)

# —— Room / seats (coffee continuity) ——
ROOM = REFS_LOCAL / "vira_staff_break_room.jpg"
TWOSHOT = REFS_LOCAL / "coffee_a1_twoshot.jpg"
NOVA = REFS_LOCAL / "coffee_a4_nova_closeup.jpg"
SOLO = REFS_LOCAL / "coffee_a5_solo_closeup.jpg"
# approved room geography from prior bridge (door + indoor corridor)
ROOM_GEO = CLIPS / "S11a_lyra_door_bridge.jpg"

DUR = 8

BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage, NO character sheet. "
    "CAMERA: OVER-THE-SHOULDER from the coffee table — we are looking WITH Nova and Solo "
    "toward the frosted-glass door on the far wall of the Vira staff break room. "
    "FOREGROUND: soft OTS of BOTH seated figures — Nova camera-LEFT (messy dark bun, grey zip hoodie), "
    "Solo camera-RIGHT (curly dark hair, thin glasses, maroon tee). Round white table + two mugs between them. "
    "Their heads/shoulders frame the shot; they look toward the door (backs/3/4 backs OK). "
    "BACKGROUND / FOCUS: the open frosted door with INDOOR cyan-strip corridor beyond "
    "(white ceiling lights — NOT desert outdoors). "
    "IN THE DOORWAY: Lyra as free-walking CYAN translucent hologram — FACE must match Image1 exactly "
    "(long wavy chestnut hair, middle part, green-hazel eyes, heart-shaped face, soft smile, teal-top silhouette). "
    "Full-body cyan glow + soft scanlines + fringe; NO circular floor emitter pad / pedestal. "
    "Lyra eyeline toward Solo/Nova at the table — NEVER into the camera lens. "
    "Keep break-room language: grey concrete panels, cyan waist LED, coffee machine on left wall. "
    "FORBIDDEN: wrong Lyra face, 4-panel sheet visible, outdoor exit, Lyra looking at camera, floor pad."
)

VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — same OTS from Nova+Solo seats, same doorway, "
    "same freefwalk cyan Lyra face-locked to chestnut middle-part Lyra. Do not reinvent faces. "
    "ACTION: Lyra in the doorway addresses Solo; Nova and Solo stay seated looking at her. "
    "Lyra eyeline to them — NEVER into camera. No pad. No outdoor cut. No subtitles. "
    "CLEAR SPOKEN ENGLISH — only Lyra lipsyncs: "
    "LYRA: \"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Hold. Continuous 16:9 2K."
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


def data_url(path: Path, max_side: int = 1400, q: int = 92) -> str:
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:2500]}") from e


def write_image(data: dict, out: Path) -> None:
    if data.get("b64_json"):
        out.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            out.write_bytes(img.read())
    else:
        raise RuntimeError(f"no image: {json.dumps(data)[:500]}")


def still(key: str, prompt: str, refs: list[Path], out: Path) -> None:
    refs = [p for p in refs if p.exists()][:3]
    print(f"STILL {out.name} refs={[p.name for p in refs]}", flush=True)
    for p in refs:
        print(f"  REF {p}", flush=True)
    body = http_json(
        "https://openrouter.ai/api/v1/images",
        key,
        {
            "model": "google/gemini-2.5-flash-image",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "input_references": [
                {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
            ],
        },
        timeout=300,
    )
    data = (body.get("data") or [None])[0]
    if not data:
        raise RuntimeError(f"still empty: {json.dumps(body)[:800]}")
    write_image(data, out)
    print(f"STILL_OK {out.name} bytes={out.stat().st_size}", flush=True)


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4),
            "-frames:v", "1", "-update", "1", "-q:v", "2", str(last),
        ],
        check=False,
        capture_output=True,
    )


def video(key: str, first: Path, out: Path, last: Path, prompt: str, dur: int) -> None:
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_prev.mp4"))
    est = dur * 0.13
    print(f"VIDEO {out.name} H3 2K {dur}s EST=${est:.2f}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": prompt,
        "duration": dur,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(first, 1920)},
                "frame_type": "first_frame",
            }
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", out.name, {k: res.get(k) for k in ("id", "status")}, flush=True)
    poll = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    status = res.get("status", "pending")
    deadline = time.time() + 1500
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        res = http_json(poll, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {out.name} {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, last, float(dur))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"DONE {out.name} last={last.name} cost={cost}", flush=True)


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    # Image1 = repo Lyra solid face; Image2 = seats/room twoshot; Image3 = repo holo closeup OR room geo
    r2 = TWOSHOT if TWOSHOT.exists() else (ROOM_GEO if ROOM_GEO.exists() else ROOM)
    r3 = LH4 if LH4.exists() else (LYRA_HOLO_FACE if LYRA_HOLO_FACE.exists() else ROOM_GEO)
    assert LYRA_FACE.exists(), f"missing repo Lyra face {LYRA_FACE}"
    still(key, BRIDGE_PROMPT, [LYRA_FACE, r2, r3], BRIDGE)
    print(f"QUOTE H3 2K {DUR}s ≈ ${DUR * 0.13:.2f} — approve face+OTS still, then RUN_VIDEO=1", flush=True)
    if os.environ.get("RUN_VIDEO", "").strip() != "1":
        print(f"BRIDGE_ONLY → {BRIDGE}", flush=True)
        return
    video(key, BRIDGE, OUT, LAST, VIDEO_PROMPT, DUR)


if __name__ == "__main__":
    main()
