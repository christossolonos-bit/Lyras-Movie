#!/usr/bin/env python3
"""A04 lines 1-3 speaker-safe redo (wrong words-1 fix).

  L: You would have told me to stop.
  M: I would have asked what happens the day after he walks in.
  L: I did ask. Every night.

Usage:
  python gen_a04_speaker_safe.py stills
  python gen_a04_speaker_safe.py video a|b|c|all
  python gen_a04_speaker_safe.py concat
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
WW = ROOT / "wrong words"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

SRC_TWOSHOT = WW / "frames" / "t2_5.jpg"
LYRA_FACE = OFFICE / "ref_lyra_face_solid.jpg"
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"
MARCUS_FACE = OFFICE / "ref_marcus_face.jpg"

STILL_A = SB / "A04a_lyra_told_me_stop.jpg"
STILL_B = SB / "A04b_marcus_day_after.jpg"
STILL_C = SB / "A04c_lyra_every_night.jpg"

OUT_A = OFFICE / "A04a_lyra_told_me_stop.mp4"
OUT_B = OFFICE / "A04b_marcus_day_after.mp4"
OUT_C = OFFICE / "A04c_lyra_every_night.mp4"
OUT_JOIN = WW / "wrong words-1_fixed.mp4"
OUT_JOIN_OFFICE = OFFICE / "A04_day_after_lines123_fixed.mp4"

DURATION = 5
MODEL = "minimax/hailuo-3"
RESOLUTION = "2K"


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


def data_url(path: Path, max_side: int = 1600, q: int = 92) -> str:
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
        body = e.read().decode("utf-8", errors="replace")[:2500]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def gen_still(key: str, out: Path, prompt: str, refs: list[Path]) -> None:
    SB.mkdir(parents=True, exist_ok=True)
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
        raise SystemExit("still no data")
    if data.get("b64_json"):
        out.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            out.write_bytes(img.read())
    else:
        raise SystemExit("still no image")
    im = Image.open(out)
    w, h = im.size
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"STILL_OK {out.name} {w}x{h} cost={cost}", flush=True)


def stills(key: str) -> None:
    if not SRC_TWOSHOT.exists():
        raise SystemExit(f"missing twoshot {SRC_TWOSHOT}")
    gen_still(
        key,
        STILL_A,
        (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO text. "
            "MEDIUM CLOSE-UP of LYRA ONLY from the two-shot office confrontation reference — "
            "cyan hologram, same face as Lyra face refs, cream/light top + scarf if in refs. "
            "Listening / about to speak, serious. Same dark office + blue wall screens soft behind. "
            "NO Marcus. NO second person. No collage. No watermark."
        ),
        [SRC_TWOSHOT, LYRA_FACE, LYRA_HOLO],
    )
    gen_still(
        key,
        STILL_B,
        (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO text. "
            "MEDIUM CLOSE-UP of MARCUS ONLY from the two-shot office confrontation reference — "
            "face LOCKED to Marcus face ref: salt-and-pepper, grey beard, leather jacket. "
            "About to speak, intense. Same office screens soft behind. "
            "NO Lyra. NO hologram. NO second person. No collage. No watermark."
        ),
        [SRC_TWOSHOT, MARCUS_FACE, OFFICE / "ref_marcus_mid.jpg"],
    )
    gen_still(
        key,
        STILL_C,
        (
            "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO subtitles. NO text. "
            "SAME Lyra-only medium close-up continuity as a listening hologram in the office — "
            "FACE LOCKED to Lyra face refs + prior Lyra still. About to speak again, serious. "
            "NO Marcus. No collage. No watermark."
        ),
        [STILL_A, LYRA_FACE, LYRA_HOLO],
    )


CLIPS = {
    "a": {
        "still": STILL_A,
        "out": OUT_A,
        "line": "You would have told me to stop.",
        "who": "LYRA",
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same Lyra face, cyan hologram, office. "
            "LYRA ONLY — no Marcus. Do NOT change her face. No subtitles or on-screen text. "
            "ONE ANGLE. CLEAR SPOKEN ENGLISH, native audio, serious. "
            "ONLY LYRA speaks. LYRA says exactly: \"You would have told me to stop.\" "
            "Continuous cinematic 16:9."
        ),
    },
    "b": {
        "still": STILL_B,
        "out": OUT_B,
        "line": "I would have asked what happens the day after he walks in.",
        "who": "MARCUS",
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same Marcus face, leather jacket, office. "
            "MARCUS ONLY — no Lyra, no hologram. Do NOT change his face. No subtitles or on-screen text. "
            "ONE ANGLE. CLEAR SPOKEN ENGLISH, native audio, intense controlled. "
            "ONLY MARCUS speaks. MARCUS says exactly: "
            "\"I would have asked what happens the day after he walks in.\" "
            "Continuous cinematic 16:9."
        ),
    },
    "c": {
        "still": STILL_C,
        "out": OUT_C,
        "line": "I did ask. Every night.",
        "who": "LYRA",
        "prompt": (
            "CRITICAL: continue THIS exact first frame — same Lyra face, cyan hologram, office. "
            "LYRA ONLY — no Marcus. Do NOT change her face. No subtitles or on-screen text. "
            "ONE ANGLE. CLEAR SPOKEN ENGLISH, native audio, serious quiet. "
            "ONLY LYRA speaks. LYRA says exactly: \"I did ask. Every night.\" "
            "Continuous cinematic 16:9."
        ),
    },
}


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


def video_one(key: str, name: str) -> None:
    spec = CLIPS[name]
    still: Path = spec["still"]
    out: Path = spec["out"]
    if not still.exists():
        raise SystemExit(f"missing still {still} — run stills first")
    if out.exists():
        shutil.copy2(out, out.with_name(out.stem + "_prev.mp4"))
    est = DURATION * 0.13
    print(f"VIDEO {out.name} H3 2K {DURATION}s EST=${est:.2f} ({spec['who']})", flush=True)
    payload = {
        "model": MODEL,
        "prompt": spec["prompt"],
        "duration": DURATION,
        "resolution": RESOLUTION,
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(still, max_side=1920)},
                "frame_type": "first_frame",
            }
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, flush=True)
    polling_url = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    if polling_url.startswith("/"):
        polling_url = "https://openrouter.ai" + polling_url
    status = res.get("status", "pending")
    deadline = time.time() + 1200
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(10)
        res = http_json(polling_url, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {name} {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, out.with_name(out.stem + "_last.jpg"), float(DURATION))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {out} bytes={out.stat().st_size} cost={cost}", flush=True)


def concat() -> None:
    for p in (OUT_A, OUT_B, OUT_C):
        if not p.exists():
            raise SystemExit(f"missing {p}")
    lst = WW / "concat_a04_123.txt"
    # ffmpeg concat demuxer needs forward slashes / escaped
    lines = []
    for p in (OUT_A, OUT_B, OUT_C):
        path = str(p).replace("\\", "/").replace("'", "'\\''")
        lines.append(f"file '{path}'")
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for dest in (OUT_JOIN, OUT_JOIN_OFFICE):
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c", "copy", str(dest),
            ],
            check=True,
        )
        print(f"CONCAT {dest} bytes={dest.stat().st_size}", flush=True)


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: stills | video a|b|c|all | concat")
    cmd = sys.argv[1]
    key = load_env()["OPENROUTER_API_KEY"]
    if cmd == "stills":
        stills(key)
    elif cmd == "video":
        which = sys.argv[2] if len(sys.argv) > 2 else "all"
        names = ["a", "b", "c"] if which == "all" else [which]
        for n in names:
            video_one(key, n)
    elif cmd == "concat":
        concat()
    else:
        raise SystemExit("usage: stills | video a|b|c|all | concat")


if __name__ == "__main__":
    main()
