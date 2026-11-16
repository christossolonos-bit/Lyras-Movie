#!/usr/bin/env python3
"""S11 redo: free-walk cyan Lyra (repo face) appears by Solo's seat — NO floor emitter pad.
Then S12: Nova watches Solo + Lyra exit.
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
LOCK = CLIPS / "lyra_lock"
REFS = ROOT / "assets" / "lyra-refs"
REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images")
ENV = Path(r"d:\movie maker\.env")

BRIDGE_S11 = CLIPS / "S11_lyra_freefwalk_bridge.jpg"
OUT_S11 = CLIPS / "S11_lyra_appear_ready_v2.mp4"
LAST_S11 = CLIPS / "S11_lyra_appear_ready_v2_last.jpg"

BRIDGE_S12 = CLIPS / "S12_exit_watch_bridge_v2.jpg"
OUT_S12 = CLIPS / "S12_nova_watches_exit_v2.mp4"
LAST_S12 = CLIPS / "S12_nova_watches_exit_v2_last.jpg"

LYRA_REF = LOCK / "lyra_ref.png" if (LOCK / "lyra_ref.png").exists() else REPO / "lyra_ref.png"
LYRA_HOLO_FACE = LOCK / "ref_lyra_face_holo.jpg" if (LOCK / "ref_lyra_face_holo.jpg").exists() else REPO / "ep3_office" / "ref_lyra_face_holo.jpg"
LH4 = LOCK / "lh4_lyra_closeup.png" if (LOCK / "lh4_lyra_closeup.png").exists() else REFS / "lh4_lyra_closeup.png"
LH3 = LOCK / "lh3_hologram_forms.png" if (LOCK / "lh3_hologram_forms.png").exists() else REFS / "lh3_hologram_forms.png"
TWOSHOT = REFS / "coffee_a1_twoshot.jpg"
NOVA_CU = REFS / "coffee_a4_nova_closeup.jpg"
SOLO_CU = REFS / "coffee_a5_solo_closeup.jpg"

DUR_S11 = 15
DUR_S12 = 10

S11_BRIDGE = (
    "OUTPUT 16:9 photoreal cinematic still. NO text, NO collage, NO character sheet. "
    "Vira staff break room. EXACTLY THREE: human Nova, human Solo, hologram Lyra. "
    "Nova seated camera-LEFT: messy dark bun, grey zip hoodie, light freckles, necklaces. "
    "Solo seated camera-RIGHT: curly dark hair, thin glasses, maroon tee. Round table + two mugs between them. "
    "LYRA: free-walking CYAN TRANSLUCENT hologram standing NEXT TO Solo's chair (outer side). "
    "Face LOCKED to Lyra refs — long wavy CHESTNUT hair, middle part, green-hazel eyes, heart-shaped face. "
    "FULL-BODY cyan aura/fringe + soft scanlines around her whole body. Teal-top silhouette under the cyan. "
    "CRITICAL: NO floor emitter, NO circular hologram pad, NO pedestal under her feet — she free-stands on the floor like office Act A. "
    "FORBIDDEN: wrong Lyra face, solid flesh Lyra, fourth person, pad/disc under Lyra. "
    "Medium table shot so all three read."
)

S11_VIDEO = (
    "CRITICAL: continue THIS exact first frame. Same three only. "
    "Lyra stays free-walk cyan hologram (aura + scanlines) beside Solo's seat — "
    "NEVER spawn a floor emitter/pad under her. Keep Lyra face = chestnut wavy middle-part. "
    "ACTION: Lyra speaks the invite; Solo stands and looks DOWN at seated Nova; "
    "Nova looks up and speaks, tipping him toward the door. "
    "No subtitles. CLEAR SPOKEN ENGLISH — only named speaker lipsyncs: "
    "LYRA (holo by his seat): \"Solo? Whenever you're ready… I'd like to show you around.\" "
    "Solo stands, looks down at Nova. "
    "NOVA: \"Go on. Don't keep the building waiting.\" "
    "Continuous 16:9."
)

S12_BRIDGE = (
    "OUTPUT 16:9 photoreal still. NO text. Same break room. EXACTLY THREE: "
    "Nova seated (messy bun, grey hoodie) watching the exit door. "
    "Solo (glasses, maroon, curly hair) and free-walk CYAN hologram Lyra (chestnut face lock, "
    "full cyan body aura, NO floor pad) walking toward / through the door together. "
    "FORBIDDEN: emitter pad, fourth person, wrong Lyra face."
)

S12_VIDEO = (
    "CRITICAL: continue THIS exact first frame. "
    "Solo and cyan free-walk Lyra hologram (no pad) exit through the door; "
    "Nova stays seated watching them. Silent button. No extras. No subtitles. Continuous 16:9."
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
    print("QUOTE ~$3.25 (15s+10s) + bridges — freefwalk Lyra, repo face", flush=True)
    # Lyra identity heavy: face holo + lyra_ref + room/people
    still(
        key,
        S11_BRIDGE,
        [LYRA_HOLO_FACE, LYRA_REF, TWOSHOT if TWOSHOT.exists() else NOVA_CU],
        BRIDGE_S11,
    )
    video(key, BRIDGE_S11, OUT_S11, LAST_S11, S11_VIDEO, DUR_S11)
    still(
        key,
        S12_BRIDGE,
        [LAST_S11, LYRA_HOLO_FACE, NOVA_CU if NOVA_CU.exists() else LH4],
        BRIDGE_S12,
    )
    video(key, BRIDGE_S12, OUT_S12, LAST_S12, S12_VIDEO, DUR_S12)


if __name__ == "__main__":
    main()
