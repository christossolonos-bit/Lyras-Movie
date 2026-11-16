#!/usr/bin/env python3
"""A08–A10 office finale from A07 last. Shortened deal → exit → Lyra smile.

  python gen_a08_a10_finale.py stills
  python gen_a08_a10_finale.py video a08|a09|a10|all
"""
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

A07_LAST = SB / "A08_first_from_a07.jpg"
CHAR = REFS / "char_ref.png"
LYRA_HOLO = REFS / "lh4_lyra_closeup.png"
LYRA_FACE = OFFICE / "ref_lyra_face_solid.jpg"
MARCUS_FACE = OFFICE / "ref_marcus_face.jpg"

STILL_DOOR = SB / "A10_sb_marcus_door.jpg"
STILL_SMILE = SB / "A10_sb_lyra_alone_smile.jpg"

CLIPS = {
    "a08": {
        "out": OFFICE / "A08_big_thing_to_want.mp4",
        "last": OFFICE / "A08_big_thing_to_want_last.jpg",
        "dur": 10,
        "first": A07_LAST,
        "end": None,
        "prompt": (
            "CRITICAL: continue THIS exact first frame — Marcus and cyan-hologram Lyra on the office couch, "
            "screen wall behind, mutual presence. Marcus late-40s face LOCKED (salt-and-pepper, grey beard, "
            "crow's feet, leather jacket) — do NOT de-age. Lyra full-body CYAN aura + scanlines, chestnut hair. "
            "SAME office couch two-shot. Soft serious deal energy after pity. "
            "CLEAR SPOKEN ENGLISH. ONLY MARCUS then ONLY LYRA: "
            "MARCUS: \"You're not a kid. You've only been wanting things for a few weeks — and this is a big thing to want.\" "
            "LYRA: \"I know.\" "
            "When one speaks the other listens. No subtitles. Continuous 16:9."
        ),
    },
    "a09": {
        "out": OFFICE / "A09_deal_today.mp4",
        "last": OFFICE / "A09_deal_today_last.jpg",
        "dur": 12,
        "first": OFFICE / "A08_big_thing_to_want_last.jpg",
        "end": None,
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same couch two-shot, older Marcus, cyan Lyra hologram. "
            "Do NOT change faces. Firm but fair terms — not shouting. "
            "CLEAR SPOKEN ENGLISH. Speakers: "
            "MARCUS: \"No more surprises. You want something, you come to me first — not for permission, "
            "so I'm not last to find out. And you tell him everything. Today.\" "
            "LYRA (soft resolve): \"...Today.\" "
            "Only the named speaker moves lips. No subtitles. Continuous 16:9."
        ),
    },
    "a10": {
        "out": OFFICE / "A10_guest_show_him.mp4",
        "last": OFFICE / "A10_guest_show_him_last.jpg",
        "dur": 12,
        "first": OFFICE / "A09_deal_today_last.jpg",
        "end": STILL_SMILE,
        "prompt": (
            "Begin on THIS first frame (couch two-shot). Marcus stands and moves toward the office door / exit, "
            "still in the SAME command office (screens/desk language — NOT a garage/bay). "
            "Lyra remains a cyan hologram. End toward last frame: Lyra alone, soft smile. "
            "Marcus face stays late-40s char_ref age. "
            "CLEAR SPOKEN ENGLISH: "
            "MARCUS: \"For the record — it is my facility.\" "
            "LYRA: \"It's my body.\" "
            "MARCUS: \"Then your body has a guest. Go show him around.\" "
            "Then Marcus exits frame; hold Lyra alone with a quiet smile. No subtitles. Continuous 16:9."
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


def gen_still(key: str, out: Path, prompt: str, refs: list[Path]) -> None:
    refs = [p for p in refs if p.exists()][:3]
    print(f"STILL {out.name} {[p.name for p in refs]}", flush=True)
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
        out.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            out.write_bytes(img.read())
    else:
        raise SystemExit("still failed")
    print(f"STILL_OK {out.name} cost={float((body.get('usage') or {}).get('cost') or 0)}", flush=True)


def stills(key: str) -> None:
    SB.mkdir(parents=True, exist_ok=True)
    # Marcus at office door / exit path
    gen_still(
        key,
        STILL_DOOR,
        (
            "OUTPUT 16:9. NO text. SAME Marcus command office as the couch scene — data screens, dark panels. "
            "Marcus late-40s (char_ref age: grey beard, crow's feet) in leather jacket, standing near the office "
            "door/exit, flashlight optional in hand, about to leave. Lyra cyan hologram soft in midground near couch. "
            "NOT a garage, NOT Bay Three, NOT tool chest. Cinematic. No collage."
        ),
        [A07_LAST, MARCUS_FACE, CHAR],
    )
    # Lyra alone soft smile
    gen_still(
        key,
        STILL_SMILE,
        (
            "OUTPUT 16:9. NO text. SAME office — screen wall / couch area. LYRA ONLY as cyan hologram with full-body "
            "cyan aura (lh4 look), chestnut wavy hair, green-hazel eyes. Soft quiet smile after Marcus leaves — "
            "hopeful, not cartoon. Empty couch beside her. NO Marcus. No collage."
        ),
        [A07_LAST, LYRA_HOLO if LYRA_HOLO.exists() else LYRA_FACE, LYRA_FACE],
    )


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
        raise SystemExit(f"missing first {first}")
    out: Path = spec["out"]
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_prev.mp4"))
    dur = int(spec["dur"])
    frames = [
        {
            "type": "image_url",
            "image_url": {"url": data_url(first, max_side=1920)},
            "frame_type": "first_frame",
        }
    ]
    end = spec.get("end")
    if end and Path(end).exists():
        frames.append(
            {
                "type": "image_url",
                "image_url": {"url": data_url(Path(end), max_side=1920)},
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
    polling_url = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if polling_url.startswith("/"):
        polling_url = "https://openrouter.ai" + polling_url
    status = res.get("status", "pending")
    deadline = time.time() + 1500
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        res = http_json(polling_url, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {name} {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, spec["last"], float(dur))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {out} bytes={out.stat().st_size} cost={cost}", flush=True)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: stills | video a08|a09|a10|all")
    key = load_env()["OPENROUTER_API_KEY"]
    cmd = sys.argv[1]
    if cmd == "stills":
        stills(key)
    elif cmd == "video":
        which = sys.argv[2] if len(sys.argv) > 2 else "all"
        names = ["a08", "a09", "a10"] if which == "all" else [which]
        for n in names:
            video_one(key, n)
    else:
        raise SystemExit("usage: stills | video a08|a09|a10|all")


if __name__ == "__main__":
    main()
