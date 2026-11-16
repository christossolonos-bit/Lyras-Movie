#!/usr/bin/env python3
"""S11: cyan Lyra hologram appears by Solo's seat → Solo stands, looks to Nova → Nova line.
S12: Nova watches Solo + Lyra hologram walk out the door.
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
ENV = Path(r"d:\movie maker\.env")

BRIDGE_S11 = CLIPS / "S11_lyra_appear_bridge.jpg"
OUT_S11 = CLIPS / "S11_lyra_appear_ready.mp4"
LAST_S11 = CLIPS / "S11_lyra_appear_ready_last.jpg"

BRIDGE_S12 = CLIPS / "S12_exit_watch_bridge.jpg"
OUT_S12 = CLIPS / "S12_nova_watches_exit.mp4"
LAST_S12 = CLIPS / "S12_nova_watches_exit_last.jpg"

NOVA_CU = REFS / "coffee_a4_nova_closeup.jpg"
NOVA_CARD = REFS / "nova_character_card.jpg"
SOLO_CU = REFS / "coffee_a5_solo_closeup.jpg"
S10_NOVA = CLIPS / "S10_solo_ots_nova_face_last.jpg"
S10_SOLO = CLIPS / "S10_nova_ots_solo_face_v2_last.jpg"
TWOSHOT = REFS / "coffee_a1_twoshot.jpg"
MASTER = CLIPS / "coffee_master_room_positions.jpg"
LH3 = REFS / "lh3_hologram_forms.png"
LH4 = REFS / "lh4_lyra_closeup.png"
LYRA_REF = REFS / "lyra_ref.png"

DUR_S11 = 15
DUR_S12 = 10

S11_BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage. "
    "Vira staff break room. EXACTLY THREE FIGURES: Nova (human), Solo (human), Lyra (cyan HOLOGRAM). "
    "GEOGRAPHY: Nova seated camera-LEFT at round white table (messy dark bun, grey zip hoodie, necklaces, light freckles). "
    "Solo seated camera-RIGHT (curly dark hair, thin glasses, maroon tee) — still sitting. "
    "CYAN TRANSLUCENT hologram LYRA standing/appearing NEXT TO Solo's seat (his right / outer side of chair) — "
    "chestnut wavy hair, full-body CYAN aura/fringe + soft scanlines, match Lyra hologram refs. "
    "NOT solid flesh. Table + two mugs between Nova and Solo. Grey walls; window as side light OK. "
    "FORBIDDEN: fourth person, Marcus, window twin, Lyra without cyan aura. "
    "Medium two-shot favoring the table so all three read."
)

S11_VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — same room, same three: Nova LEFT seated, Solo RIGHT seated, "
    "cyan hologram Lyra beside Solo's chair. Hold continuity — do not invent extras. "
    "ACTION: Lyra hologram fully present/stabilizes by Solo's seat and speaks; "
    "then Solo stands up from his chair and looks DOWN toward seated Nova; "
    "Nova looks up at him and speaks while tipping/gesturing toward the door. "
    "Lyra stays cyan translucent + body aura. Solo stays curly hair/glasses/maroon. "
    "Nova stays bun/grey hoodie. No subtitles. "
    "CLEAR SPOKEN ENGLISH — only named speaker lipsyncs: "
    "LYRA (warm, from the hologram by his seat): "
    "\"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Solo stands, looks down at Nova. "
    "NOVA (encouraging): \"Go on. Don't keep the building waiting.\" "
    "Continuous 16:9."
)

S12_BRIDGE_PROMPT = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage. "
    "Same Vira break room. EXACTLY THREE FIGURES only: "
    "Nova seated camera-LEFT / nearer camera at the table (messy bun, grey hoodie) — "
    "she looks toward the frosted/glass exit door. "
    "Solo (curly hair, glasses, maroon) and cyan hologram Lyra (full cyan aura) are midground "
    "walking toward / at the door to leave — backs or three-quarter away from Nova. "
    "Table with mugs in FG or mid. Empty chairs behind them OK. "
    "FORBIDDEN: fourth person, Lyra solid/non-holo, Solo looking like Nova."
)

S12_VIDEO_PROMPT = (
    "CRITICAL: continue THIS exact first frame — Nova watches; Solo + cyan hologram Lyra exit. "
    "EXACTLY these three — no extras. "
    "ACTION: Solo and cyan Lyra walk out through the break-room door together; "
    "Nova stays seated, watching them go (soft reaction / optional sip). Silent or near-silent. "
    "Lyra remains cyan translucent with body aura. No subtitles. Continuous 16:9."
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
        raise RuntimeError(f"still empty {out.name}: {json.dumps(body)[:800]}")
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
    print("QUOTE ~$3.25–$4.00 (15s+10s H3) + bridges", flush=True)

    still(
        key,
        S11_BRIDGE_PROMPT,
        [
            TWOSHOT if TWOSHOT.exists() else MASTER,
            LH4 if LH4.exists() else LH3,
            NOVA_CU if NOVA_CU.exists() else SOLO_CU,
        ],
        BRIDGE_S11,
    )
    video(key, BRIDGE_S11, OUT_S11, LAST_S11, S11_VIDEO_PROMPT, DUR_S11)

    still(
        key,
        S12_BRIDGE_PROMPT,
        [LAST_S11, NOVA_CU if NOVA_CU.exists() else NOVA_CARD, LH4 if LH4.exists() else LH3],
        BRIDGE_S12,
    )
    video(key, BRIDGE_S12, OUT_S12, LAST_S12, S12_VIDEO_PROMPT, DUR_S12)


if __name__ == "__main__":
    main()
