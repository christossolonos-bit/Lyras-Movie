#!/usr/bin/env python3
"""A08–A10 redo: richer Lyra lines; A10 end never looks at camera."""
from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
REFS = ROOT / "assets" / "lyra-refs"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

A07 = SB / "A08_first_from_a07.jpg"
SMILE = SB / "A10_sb_lyra_alone_smile.jpg"
LYRA_HOLO = REFS / "lh4_lyra_closeup.png"
LYRA_FACE = OFFICE / "ref_lyra_face_solid.jpg"

CLIPS = {
    "a08": {
        "out": OFFICE / "A08_big_thing_to_want.mp4",
        "last": OFFICE / "A08_big_thing_to_want_last.jpg",
        "dur": 10,
        "first": A07,
        "end": None,
        "prompt": (
            "CRITICAL: continue THIS exact first frame — Marcus + cyan-hologram Lyra on office couch, "
            "screen wall behind. Marcus late-40s LOCKED (salt-and-pepper, grey beard, crow's feet, leather jacket) — "
            "do NOT de-age. Lyra full-body CYAN aura + scanlines. Living performance, not flat. "
            "Lyra's eyes stay IN SCENE — on Marcus — NEVER into the camera. "
            "CLEAR SPOKEN ENGLISH, natural acting: "
            "MARCUS (firm, careful): \"You're not a kid. You've only been wanting things for a few weeks — "
            "and this is a big thing to want.\" "
            "LYRA (quiet steel, not a blank 'I know'): \"I know what it costs. I still want it.\" "
            "Only the speaker lipsyncs. No subtitles. Continuous 16:9."
        ),
    },
    "a09": {
        "out": OFFICE / "A09_deal_today.mp4",
        "last": OFFICE / "A09_deal_today_last.jpg",
        "dur": 12,
        "first": OFFICE / "A08_big_thing_to_want_last.jpg",
        "end": None,
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same couch two-shot, older Marcus, cyan Lyra. "
            "Eyelines on each other — NEVER into camera. Real conversation energy. "
            "CLEAR SPOKEN ENGLISH: "
            "MARCUS: \"No more surprises. You want something, you come to me first — not for permission, "
            "so I'm not last to find out. And you tell him everything. Today.\" "
            "LYRA (resolved, warm, not a flat echo): \"Today. No more half-truths.\" "
            "Only named speaker moves lips. No subtitles. Continuous 16:9."
        ),
    },
    "a10": {
        "out": OFFICE / "A10_guest_show_him.mp4",
        "last": OFFICE / "A10_guest_show_him_last.jpg",
        "dur": 12,
        "first": OFFICE / "A09_deal_today_last.jpg",
        "end": SMILE,
        "prompt": (
            "Begin on THIS first frame (couch two-shot). Marcus stands and walks toward the office door "
            "(SAME command office — not a bay/garage). Lyra cyan hologram stays. "
            "Eyelines stay in the scene — NEVER look into the camera lens. "
            "CLEAR SPOKEN ENGLISH: "
            "MARCUS: \"For the record — it is my facility.\" "
            "LYRA (steady, not cute): \"It's my body, Marcus.\" "
            "MARCUS: \"Then your body has a guest. Go show him around.\" "
            "He exits. Hold Lyra alone with a soft private smile looking TOWARD THE DOOR he left through — "
            "profile/three-quarter away from lens. FORBIDDEN: facing the camera / breaking fourth wall. "
            "End matching last-frame. No subtitles. Continuous 16:9."
        ),
    },
}


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


def still_smile(key: str) -> None:
    SB.mkdir(parents=True, exist_ok=True)
    if SMILE.exists():
        shutil.copy2(SMILE, SB / "A10_sb_lyra_alone_smile_tocamera.jpg")
    refs = [p for p in (A07, LYRA_HOLO, LYRA_FACE) if p.exists()][:3]
    prompt = (
        "OUTPUT 16:9. NO text. SAME office couch / blue screen wall. LYRA ONLY cyan hologram, "
        "full-body cyan aura, chestnut hair. Soft private smile. "
        "CRITICAL: looking TOWARD the office door / off toward where Marcus exited — "
        "three-quarter or profile. FORBIDDEN: looking into the camera, facing the viewer. "
        "Immersive. Empty couch beside her. No collage."
    )
    print(f"STILL smile refs={[p.name for p in refs]}", flush=True)
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
    if data.get("b64_json"):
        SMILE.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            SMILE.write_bytes(img.read())
    print(f"STILL_OK {SMILE.name}", flush=True)


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )


def video_one(key: str, name: str) -> None:
    spec = CLIPS[name]
    first: Path = spec["first"]
    if not first.exists():
        raise SystemExit(f"missing {first}")
    out: Path = spec["out"]
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_flat.mp4"))
    dur = int(spec["dur"])
    frames = [
        {
            "type": "image_url",
            "image_url": {"url": data_url(first, 1920)},
            "frame_type": "first_frame",
        }
    ]
    end = spec.get("end")
    if end and Path(end).exists():
        frames.append(
            {
                "type": "image_url",
                "image_url": {"url": data_url(Path(end), 1920)},
                "frame_type": "last_frame",
            }
        )
    est = dur * 0.13
    print(f"VIDEO {out.name} H3 2K {dur}s EST=${est:.2f}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": spec["prompt"],
        "duration": dur,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": frames,
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
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {name} {status}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, spec["last"], float(dur))
    print(f"OK {out} cost={float((res.get('usage') or {}).get('cost') or est)}", flush=True)


def main() -> None:
    key = load_env()["OPENROUTER_API_KEY"]
    still_smile(key)
    for n in ("a08", "a09", "a10"):
        video_one(key, n)


if __name__ == "__main__":
    main()
