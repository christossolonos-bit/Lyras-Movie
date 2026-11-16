#!/usr/bin/env python3
"""S11a only — Lyra freefwalk hologram APPEARS at break-room door → indoor corridor.
Invite line only. No Nova/Solo dialogue in this clip. No floor pad. Never look at camera.

  python gen_s11a_door_lyra.py              # bridge still only
  set RUN_VIDEO=1 && python gen_s11a_door_lyra.py
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
REFS = ROOT / "assets" / "lyra-refs"
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
GAME_REFS = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\game\assets\refs")
ENV = Path(r"d:\movie maker\.env")

BRIDGE = CLIPS / "S11a_lyra_door_bridge.jpg"
OUT = CLIPS / "S11a_lyra_door_ready.mp4"
LAST = CLIPS / "S11a_lyra_door_ready_last.jpg"

ROOM = REFS / "vira_staff_break_room.jpg"
CORRIDOR = GAME_REFS / "pb7_lobby_cool.png"
if not CORRIDOR.exists():
    CORRIDOR = REPO / "pb7_lobby_cool.png"
AISLE = GAME_REFS / "pb8_server_aisle.png"
if not AISLE.exists():
    AISLE = REPO / "pb8_server_aisle.png"

LYRA_REF = REFS / "lyra_ref.png"
if not LYRA_REF.exists():
    LYRA_REF = REPO / "lyra_ref.png"
LH4 = REFS / "lh4_lyra_closeup.png"
if not LH4.exists():
    LH4 = REPO / "lh4_lyra_closeup.png"
LH3 = REFS / "lh3_hologram_forms.png"
if not LH3.exists():
    LH3 = REPO / "lh3_hologram_forms.png"

DUR = 8  # invite only — no dead air packing

BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage, NO character sheet. "
    "CAMERA: medium shot FROM INSIDE the Vira staff break room, aimed at the FROSTED GLASS DOOR "
    "on the interior wall (same room as the coffee plate — grey concrete panels, cyan waist LED strip). "
    "The frosted door is OPEN / ajar. Beyond the doorway: INDOOR facility corridor only — "
    "polished grey floor, concrete + white panels, cyan LED strips, cool industrial light "
    "(match lobby/corridor language). FORBIDDEN beyond the door: desert, sky, mountains, outdoor campus. "
    "SUBJECT: Lyra as a FREE-WALKING CYAN TRANSLUCENT hologram standing IN THE DOORWAY, facing into the room "
    "(toward Solo off-camera at the table). "
    "Face LOCK: long wavy CHESTNUT hair, middle part, green-hazel eyes, soft smile — match Lyra face refs. "
    "FULL-BODY cyan glow + soft horizontal scanlines; teal-top silhouette under the cyan. "
    "CRITICAL: NO circular floor emitter pad, NO pedestal, NO projection disc under her feet. "
    "Eyeline toward the table / Solo — NEVER into the camera lens. "
    "Optional soft out-of-focus edge of table/chairs in FG — do NOT invent a third person in focus. "
    "FORBIDDEN: solid flesh Lyra, wrong face, outdoor exit, looking into camera."
)

VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — same doorway, same indoor cyan corridor beyond, "
    "same freefwalk cyan hologram Lyra (chestnut face, scanlines, NO floor pad). Do not reinvent. "
    "ACTION: Lyra materializes / firms up in the doorway a beat, then speaks to Solo at the table "
    "(eyeline into the room — NEVER into camera). Soft cyan particle fringe OK. "
    "No other speakers. No Nova dialogue. No Solo walking yet. No outdoor cut. No subtitles. "
    "CLEAR SPOKEN ENGLISH — only Lyra lipsyncs: "
    "LYRA: \"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Hold on her after the line. Continuous 16:9 2K."
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
    if not first.exists():
        raise SystemExit(f"missing {first}")
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
    est = DUR * 0.13
    print(f"S11a door plate — bridge refs: room + pb7 corridor + Lyra face", flush=True)
    print(f"QUOTE video: H3 2K {DUR}s ≈ ${est:.2f} (+ bridge still ~$0.04) — RUN_VIDEO=1 to spend", flush=True)

    # Prefer face lock + room + corridor (not lh3 pad plate as Image1)
    still(key, BRIDGE_PROMPT, [LH4 if LH4.exists() else LYRA_REF, ROOM, CORRIDOR], BRIDGE)

    if os.environ.get("RUN_VIDEO", "").strip() != "1":
        print(f"BRIDGE_ONLY → {BRIDGE}", flush=True)
        print("Approve cost in chat, then: set RUN_VIDEO=1 && python gen_s11a_door_lyra.py", flush=True)
        return

    video(key, BRIDGE, OUT, LAST, VIDEO_PROMPT, DUR)


if __name__ == "__main__":
    main()
