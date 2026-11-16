#!/usr/bin/env python3
"""S10b redo: Solo face sharp; Nova OTS FG must be Nova (bun+hoodie), NOT a Solo twin."""
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
LOCK = CLIPS / "nova_lock"
ENV = Path(r"d:\movie maker\.env")

BRIDGE = CLIPS / "S10_nova_ots_solo_face_bridge_v2.jpg"
OUT = CLIPS / "S10_nova_ots_solo_face_v2.mp4"
LAST = CLIPS / "S10_nova_ots_solo_face_v2_last.jpg"
DUR = 15

# Prefer assembled lock folder, fall back to lyra-refs / repo copies
NOVA_CARD = LOCK / "nova_character_card.jpg" if (LOCK / "nova_character_card.jpg").exists() else REFS / "nova_character_card.jpg"
NOVA_REF = LOCK / "nova_ref.png" if (LOCK / "nova_ref.png").exists() else REFS / "nova_ref.png"
NOVA_CU = LOCK / "coffee_a4_nova_closeup.jpg" if (LOCK / "coffee_a4_nova_closeup.jpg").exists() else REFS / "coffee_a4_nova_closeup.jpg"
SOLO_CU = REFS / "coffee_a5_solo_closeup.jpg"
SOLO_FACE = CLIPS / "solo_face_lock_approved.jpg"
SOLO_GOOD = CLIPS / "S10_nova_ots_solo_face_last.jpg"  # Solo face was good — reuse pose if needed

BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage, NO character sheet. "
    "EXACTLY TWO PEOPLE: Nova and Solo. "
    "CAMERA: reverse over-the-shoulder toward Solo. "
    "FOREGROUND (camera-LEFT, soft blur): MUST be NOVA only — back/side of her head. "
    "Nova identity LOCK from refs: dark hair in a MESSY BUN with loose strands, "
    "grey zip hoodie over dark top, layered cord/pendant necklaces if shoulder visible. "
    "FORBIDDEN for foreground: curly short male hair, glasses, maroon tee, Solo's head — "
    "if the FG looks like Solo, the image is WRONG. "
    "MIDGROUND (sharp): SOLO face CU — curly dark hair, thin metal glasses, maroon/burgundy tee, "
    "olive skin, male — match Solo refs. Looking toward Nova. "
    "Same Vira break room cyan strip bokeh. No third person. No window twin."
)

VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame for all 15s. "
    "EXACTLY two people. Soft FG camera-LEFT is NOVA (messy bun + grey hoodie) — "
    "NEVER turn the FG into Solo, a man, glasses, or curly short hair. "
    "Sharp midground is SOLO face (curly hair, glasses, maroon) — keep his face lock. "
    "Hold reverse OTS — do not reframe wide. No subtitles. No third person. "
    "CLEAR SPOKEN ENGLISH — only named speaker lipsyncs: "
    "SOLO: \"Can she even… does she actually feel things?\" "
    "NOVA (OS — her voice only; FG bun may nod slightly): "
    "\"Ask her yourself. But I'd bet the building on it.\" "
    "SOLO: \"You mean you'd bet her.\" "
    "NOVA OS: \"…Yeah. Don't tell her I said that.\" "
    "LYRA (ceiling PA only — no body): \"I heard that.\" "
    "NOVA OS: \"Of course you did.\" "
    "Solo soft laugh. Continuous 16:9."
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


def bridge(key: str) -> None:
    # Order: Nova identity first (card + CU), then Solo face — max 3 refs for Gemini
    refs = []
    for p in (NOVA_CU, NOVA_CARD if NOVA_CARD.exists() else NOVA_REF, SOLO_CU if SOLO_CU.exists() else SOLO_FACE):
        if p.exists() and p not in refs:
            refs.append(p)
        if len(refs) >= 3:
            break
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
        raise SystemExit(f"missing {BRIDGE}")
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
    bridge(key)
    # Stop after bridge so user can approve FG=Nova before spending H3 — set RUN_VIDEO=1 to continue
    import os
    if os.environ.get("RUN_VIDEO", "1") == "1":
        video(key)
    else:
        print("BRIDGE_ONLY — set RUN_VIDEO=1 to generate video", flush=True)


if __name__ == "__main__":
    main()
