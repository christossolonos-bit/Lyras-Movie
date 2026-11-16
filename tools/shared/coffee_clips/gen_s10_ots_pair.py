#!/usr/bin/env python3
"""S10 pair: (A) Solo OTS / Nova face from lock still; (B) Nova OTS / Solo face reverse."""
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

FIRST_A = CLIPS / "S10_ots_lock_from_s05.jpg"
OUT_A = CLIPS / "S10_solo_ots_nova_face.mp4"
LAST_A = CLIPS / "S10_solo_ots_nova_face_last.jpg"

BRIDGE_B = CLIPS / "S10_nova_ots_solo_face_bridge.jpg"
OUT_B = CLIPS / "S10_nova_ots_solo_face.mp4"
LAST_B = CLIPS / "S10_nova_ots_solo_face_last.jpg"

SOLO_CU = REFS / "coffee_a5_solo_closeup.jpg"
SOLO_FACE = CLIPS / "solo_face_lock_approved.jpg"
NOVA_CU = REFS / "coffee_a4_nova_closeup.jpg"
S05 = CLIPS / "S05_nova_cu_bridge.jpg"

DUR = 15

LINES = (
    "CLEAR SPOKEN ENGLISH — only the named speaker moves lips; the other is silent OS: "
    "SOLO: \"Can she even… does she actually feel things?\" "
    "NOVA: \"Ask her yourself. But I'd bet the building on it.\" "
    "SOLO: \"You mean you'd bet her.\" "
    "NOVA: \"…Yeah. Don't tell her I said that.\" "
    "LYRA (ceiling PA only — no body visible): \"I heard that.\" "
    "NOVA: \"Of course you did.\" "
    "Solo soft laugh. "
)

CRIT_A = (
    "CRITICAL: continue THIS exact first frame — tight OTS. "
    "EXACTLY TWO PEOPLE: Solo = soft FG camera-RIGHT (glasses + shoulder/ear only, maroon), "
    "Nova = sharp CU midground. NO third person, NO one outside any window, NO duplicate. "
    "Nova: TWO open nostrils, light freckles, messy bun, grey hoodie. Hold this OTS — do not reframe wide. "
    "No subtitles. "
)

CRIT_B = (
    "CRITICAL: continue THIS exact first frame — reverse OTS. "
    "EXACTLY TWO PEOPLE: Nova = soft FG camera-LEFT (messy bun / hoodie shoulder only), "
    "Solo = sharp CU midground (curly dark hair, thin glasses, maroon tee, olive skin). "
    "NO third person, NO window twin, NO woman as Solo. "
    "Hold reverse OTS — do not reframe wide. No subtitles. "
)

BRIDGE_B_PROMPT = (
    "OUTPUT 16:9 photoreal still. NO text, NO collage. "
    "EXACTLY TWO PEOPLE — Nova and Solo only. "
    "CAMERA: reverse over-the-shoulder — Nova soft FG (back of head / bun / grey hoodie shoulder on camera-LEFT). "
    "Solo sharp face CU midground: curly dark hair, thin metal glasses, maroon tee, match Solo refs. "
    "Same Vira break room cyan strip + soft bokeh; table implied below. "
    "FORBIDDEN: third person, reflection person, woman opposite Nova, empty Solo seat. "
    "Continuous live-action."
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


def data_url(path: Path, max_side: int = 1920, q: int = 90) -> str:
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


def bridge_b(key: str) -> None:
    refs = []
    for p in (SOLO_CU if SOLO_CU.exists() else SOLO_FACE, FIRST_A if FIRST_A.exists() else S05, NOVA_CU):
        if p and p.exists() and p not in refs:
            refs.append(p)
        if len(refs) >= 3:
            break
    print(f"BRIDGE_B refs={[p.name for p in refs]}", flush=True)
    body = http_json(
        "https://openrouter.ai/api/v1/images",
        key,
        {
            "model": "google/gemini-2.5-flash-image",
            "prompt": BRIDGE_B_PROMPT,
            "aspect_ratio": "16:9",
            "input_references": [
                {"type": "image_url", "image_url": {"url": data_url(p, 1400)}} for p in refs
            ],
        },
        timeout=300,
    )
    data = (body.get("data") or [None])[0]
    if not data:
        raise RuntimeError(f"bridge empty: {json.dumps(body)[:800]}")
    write_image(data, BRIDGE_B)
    print(f"BRIDGE_B_OK {BRIDGE_B.name} bytes={BRIDGE_B.stat().st_size}", flush=True)


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


def video(key: str, first: Path, out: Path, last: Path, crit: str) -> None:
    if not first.exists():
        raise SystemExit(f"missing {first}")
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_prev.mp4"))
    est = DUR * 0.13
    print(f"VIDEO {out.name} H3 2K {DUR}s EST=${est:.2f} first={first.name}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": crit + LINES + "Continuous 16:9.",
        "duration": DUR,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(first)},
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
    extract_last(out, last, float(DUR))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"DONE {out.name} last={last.name} cost={cost}", flush=True)


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    print("QUOTE ~$3.94 (2×15s H3) + ~$0.04 reverse bridge", flush=True)
    video(key, FIRST_A, OUT_A, LAST_A, CRIT_A)
    bridge_b(key)
    video(key, BRIDGE_B, OUT_B, LAST_B, CRIT_B)


if __name__ == "__main__":
    main()
