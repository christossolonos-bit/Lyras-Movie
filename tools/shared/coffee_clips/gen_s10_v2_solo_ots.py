#!/usr/bin/env python3
"""S10 v2: bridge still (Nova + Solo OTS, both nostrils) then H3 15s Act B dialogue."""
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
ENV = Path(r"d:\movie maker\.env")

BRIDGE = CLIPS / "S10_solo_ots_bridge.jpg"
OUT = CLIPS / "S10_feel_things_bet_v2.mp4"
LAST = CLIPS / "S10_feel_things_bet_v2_last.jpg"
DUR = 15

# Identity / geography locks
NOVA_POSE = CLIPS / "S09_biggest_thing_v3_last.jpg"
NOVA_CARD = REFS / "nova_character_card.jpg"
SOLO_CU = REFS / "coffee_a5_solo_closeup.jpg"
SOLO_FACE = CLIPS / "solo_face_lock_approved.jpg"
SOLO_CARD = REFS / "solo_character_card.jpg"
TWOSHOT = REFS / "coffee_a1_twoshot.jpg"

BRIDGE_PROMPT = (
    "OUTPUT 16:9 cinematic still. NO text, NO watermark, NO collage, NO character sheet. "
    "Vira staff break room: grey panels, cyan waist LED, desert mountains + campus roofs in window, "
    "round white table with two mugs. "
    "CAMERA: over-the-shoulder toward Nova — Solo is soft-focus FOREGROUND on camera-RIGHT "
    "(back of head / shoulder / ear only). "
    "SOLO MUST BE THE MAN from the Solo refs: short curly dark hair, thin metal glasses, "
    "maroon/burgundy tee, olive skin, male. FORBIDDEN: any woman as the foreground person. "
    "NOVA (sharp, midground, camera-LEFT seat): messy dark bun, light freckles only, grey zip hoodie, "
    "layered necklaces, warm eyeline toward Solo. "
    "CRITICAL ANATOMY: Nova's nose has TWO clear open nostrils — left and right — "
    "do NOT fuse, cover, or erase either nostril. "
    "Same room light as the Nova pose ref. Photoreal live-action."
)

VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — same room, same seats "
    "(Nova camera-LEFT sharp, Solo camera-RIGHT soft OTS foreground), same clothes, mugs, window. "
    "Solo is the MAN with curly hair, glasses, maroon tee — NEVER replace him with a woman. "
    "Nova face: keep TWO open nostrils at all times — do not fuse or cover a nostril. "
    "Light freckles only. No hologram body. No subtitles. "
    "Cinematic OTS hold with micro push allowed. CLEAR SPOKEN ENGLISH — only named speaker lipsyncs: "
    "SOLO (vulnerable, his voice — FG may turn slightly): "
    "\"Can she even… does she actually feel things?\" "
    "NOVA (steady): \"Ask her yourself. But I'd bet the building on it.\" "
    "SOLO: \"You mean you'd bet her.\" "
    "NOVA (quiet, caught): \"…Yeah. Don't tell her I said that.\" "
    "LYRA (ceiling PA only — voice from above, no body): \"I heard that.\" "
    "NOVA (no beat, wry): \"Of course you did.\" "
    "Solo laughs softly. Hold. Continuous 16:9."
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


def data_url(path: Path, max_side: int = 1600, q: int = 90) -> str:
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
        raise RuntimeError(f"no image payload: {json.dumps(data)[:500]}")


def bridge_still(key: str) -> None:
    refs = []
    for p in (NOVA_POSE, SOLO_CU if SOLO_CU.exists() else SOLO_FACE, TWOSHOT, NOVA_CARD):
        if p.exists() and p not in refs:
            refs.append(p)
        if len(refs) >= 3:
            break
    if SOLO_FACE.exists() and SOLO_FACE not in refs and len(refs) < 3:
        refs.append(SOLO_FACE)
    print(f"BRIDGE refs={[p.name for p in refs]}", flush=True)
    body = http_json(
        "https://openrouter.ai/api/v1/images",
        key,
        {
            "model": "google/gemini-2.5-flash-image",
            "prompt": BRIDGE_PROMPT,
            "aspect_ratio": "16:9",
            "input_references": [
                {"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs
            ],
        },
        timeout=300,
    )
    data = (body.get("data") or [None])[0]
    if not data:
        raise RuntimeError(f"bridge empty: {json.dumps(body)[:800]}")
    write_image(data, BRIDGE)
    print(f"BRIDGE_OK {BRIDGE.name} bytes={BRIDGE.stat().st_size}", flush=True)


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


def video(key: str) -> None:
    if not BRIDGE.exists():
        raise SystemExit(f"missing bridge {BRIDGE}")
    if OUT.exists():
        shutil.copy2(OUT, OUT.with_name(OUT.stem + "_prev.mp4"))
    est = DUR * 0.13
    print(f"VIDEO {OUT.name} H3 2K {DUR}s EST=${est:.2f}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": VIDEO_PROMPT,
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
        print("POLL", OUT.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        OUT.write_bytes(resp.read())
    extract_last(OUT, LAST, float(DUR))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {OUT} last={LAST.name} cost={cost}", flush=True)


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    bridge_still(key)
    video(key)


if __name__ == "__main__":
    main()
