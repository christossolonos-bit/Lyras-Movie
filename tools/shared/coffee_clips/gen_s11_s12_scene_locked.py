#!/usr/bin/env python3
"""S11/S12 from MOVIE plates — not generic rooms.

S11: coffee freefwalk bridge / v2 continuity — tight dialogue; Lyra NEVER looks at camera.
S12: break-room door → facility CORRIDOR (pb8 server aisle language) — not outdoors.
"""
from __future__ import annotations

import base64
import io
import json
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
LOCK = CLIPS / "lyra_lock"
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
ENV = Path(r"d:\movie maker\.env")

# Movie plates
BREAK_ROOM = REFS / "vira_staff_break_room.jpg"
CORRIDOR = REPO / "pb8_server_aisle.png"  # facility aisle / corridor language
S11_BRIDGE = CLIPS / "S11_lyra_freefwalk_bridge.jpg"
S11_V2_LAST = CLIPS / "S11_lyra_appear_ready_v2_last.jpg"
S10_NOVA = CLIPS / "S10_solo_ots_nova_face_last.jpg"
S10_SOLO = CLIPS / "S10_nova_ots_solo_face_v2_last.jpg"

LYRA_HOLO = LOCK / "ref_lyra_face_holo.jpg" if (LOCK / "ref_lyra_face_holo.jpg").exists() else REPO / "ep3_office" / "ref_lyra_face_holo.jpg"
LYRA_REF = LOCK / "lyra_ref.png" if (LOCK / "lyra_ref.png").exists() else REPO / "lyra_ref.png"
LH4 = LOCK / "lh4_lyra_closeup.png" if (LOCK / "lh4_lyra_closeup.png").exists() else REFS / "lh4_lyra_closeup.png"
NOVA_CU = REFS / "coffee_a4_nova_closeup.jpg"

BRIDGE_S11 = CLIPS / "S11_eyeline_scene_bridge.jpg"
OUT_S11 = CLIPS / "S11_lyra_appear_ready_v3.mp4"
LAST_S11 = CLIPS / "S11_lyra_appear_ready_v3_last.jpg"

BRIDGE_S12 = CLIPS / "S12_corridor_scene_bridge.jpg"
OUT_S12 = CLIPS / "S12_corridor_exit.mp4"
LAST_S12 = CLIPS / "S12_corridor_exit_last.jpg"

DUR_S11 = 12
DUR_S12 = 10

S11_BRIDGE_PROMPT = (
    "OUTPUT 16:9. Continue THIS coffee break-room MOVIE scene (same table, chairs, cyan strip, door). "
    "EXACTLY three: Nova seated LEFT (bun, grey hoodie), Solo seated RIGHT (glasses, maroon), "
    "cyan freefwalk hologram Lyra standing BESIDE Solo's chair — chestnut wavy middle-part face from Lyra holo refs, "
    "full cyan body aura, NO floor pad. "
    "CRITICAL EYELINE: Lyra looks at SOLO or NOVA — NEVER into the camera lens. "
    "Solo and Nova look at each other / Lyra — NEVER into camera. "
    "No text. Photoreal. Match the room plate."
)

S11_VIDEO = (
    "CRITICAL: continue THIS exact first-frame MOVIE still. Same coffee break room. Same three. "
    "Lyra freefwalk cyan hologram — eyes stay ON SOLO (or Nova) — FORBIDDEN: looking into the camera / breaking fourth wall. "
    "PACING: almost no silence. Lyra's invite starts immediately; the second it ends Solo stands and looks down at Nova; "
    "Nova answers AT ONCE with no long pause: "
    "LYRA: \"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Solo stands, looks down at Nova. "
    "NOVA (immediate): \"Go on. Don't keep the building waiting.\" "
    "CLEAR ENGLISH, only named speaker lipsyncs. No subtitles. Continuous 16:9."
)

S12_BRIDGE_PROMPT = (
    "OUTPUT 16:9. COMPOSITE from these MOVIE plates: coffee break room (door on the right) + "
    "facility server/corridor aisle beyond the doorway (raised floor, rack lights, industrial hall — indoor). "
    "EXACTLY three: Nova still in the break room looking toward the door; "
    "Solo (glasses, maroon) and cyan freefwalk Lyra (aura, no pad) stepping through the break-room door "
    "INTO the facility CORRIDOR — hallway recedes inside the building. "
    "FORBIDDEN: desert, mountains, outdoor campus, sky as the exit. "
    "Lyra and Solo face INTO the corridor / each other — NEVER into the camera. "
    "No text. Photoreal continuity."
)

S12_VIDEO = (
    "CRITICAL: continue THIS exact first-frame MOVIE still. "
    "Solo and cyan freefwalk Lyra walk from the break room INTO the indoor facility corridor "
    "(server-aisle / cyan-strip hall language). Nova watches from inside the break room. "
    "FORBIDDEN: exiting outdoors, desert, mountains. "
    "Eyelines never into camera. Silent soft hold. No subtitles. Continuous 16:9."
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
    print(f"VIDEO {out.name} H3 2K {dur}s EST=${est:.2f} first={first.name}", flush=True)
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
    print(
        f"QUOTE scene-locked: S11 {DUR_S11}s=${DUR_S11*0.13:.2f} + S12 {DUR_S12}s=${DUR_S12*0.13:.2f} + bridges ~$0.08",
        flush=True,
    )
    # S11 bridge: coffee movie still + Lyra face lock (not invent room)
    room = S11_BRIDGE if S11_BRIDGE.exists() else (S11_V2_LAST if S11_V2_LAST.exists() else BREAK_ROOM)
    still(key, S11_BRIDGE_PROMPT, [room, LYRA_HOLO, LYRA_REF], BRIDGE_S11)
    video(key, BRIDGE_S11, OUT_S11, LAST_S11, S11_VIDEO, DUR_S11)

    # S12: break room door plate + corridor aisle movie plate + S11 last
    still(
        key,
        S12_BRIDGE_PROMPT,
        [BREAK_ROOM if BREAK_ROOM.exists() else LAST_S11, CORRIDOR, LAST_S11],
        BRIDGE_S12,
    )
    video(key, BRIDGE_S12, OUT_S12, LAST_S12, S12_VIDEO, DUR_S12)


if __name__ == "__main__":
    main()
