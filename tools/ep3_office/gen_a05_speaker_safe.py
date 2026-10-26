#!/usr/bin/env python3
"""A05 speaker-safe pack: Lyra still + A05a/b/c videos.

  python gen_a05_speaker_safe.py still
  python gen_a05_speaker_safe.py a05a
  python gen_a05_speaker_safe.py a05b
  python gen_a05_speaker_safe.py a05c
"""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")

A04 = OFFICE / "A04_day_after_last.jpg"
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"
LYRA_SOLID = OFFICE / "ref_lyra_face_solid.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"
LYRA_STILL = SB / "A05b_lyra_listen_lock.jpg"

A05A = OFFICE / "A05a_marcus_stakes.mp4"
A05A_LAST = OFFICE / "A05a_marcus_stakes_last.jpg"
A05B = OFFICE / "A05b_lyra_never_lied.mp4"
A05B_LAST = OFFICE / "A05b_lyra_never_lied_last.jpg"
A05C = OFFICE / "A05c_marcus_what_you_are.mp4"
A05C_LAST = OFFICE / "A05c_marcus_what_you_are_last.jpg"


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


def ref_obj(path: Path, max_side: int = 1400) -> dict:
    return {"type": "image_url", "image_url": {"url": data_url(path, max_side=max_side)}}


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


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )


def gen_still(key: str) -> None:
    SB.mkdir(parents=True, exist_ok=True)
    # Face cards ONLY — no office master (it pulls Marcus into frame)
    refs = [LYRA_HOLO, LYRA_SOLID]
    # pad with holo twice if needed for API; max 3
    if LYRA_HOLO.exists():
        refs = [LYRA_HOLO, LYRA_SOLID, LYRA_HOLO]
    prompt = (
        "OUTPUT 16:9 landscape full-bleed. NO letterbox bars. NO subtitles. NO captions. NO on-screen text. "
        "MEDIUM CLOSE-UP of ONE subject only: LYRA — head, neck, upper shoulders with breathing room. "
        "EMPTY soft dark-office bokeh background — NO other people, NO man, NO desk hero, NO server racks in focus. "
        "FORBIDDEN: Marcus, any second person, shot from behind, wide two-shot, Lyra on a desk/pad. "
        "Translucent CYAN hologram listening, serious, NOT smiling, eyeline slightly off-camera. "
        "Face LOCKED to the Lyra face references — same features, long wavy hair, cyan scanlines. "
        "No collage. No watermark."
    )
    print(f"STILL {LYRA_STILL.name}", flush=True)
    body = http_json(
        "https://openrouter.ai/api/v1/images",
        key,
        {
            "model": "google/gemini-2.5-flash-image",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "input_references": [ref_obj(p) for p in refs if p.exists()][:3],
        },
        timeout=300,
    )
    data = (body.get("data") or [None])[0]
    if not data:
        raise SystemExit("still no data")
    if data.get("b64_json"):
        LYRA_STILL.write_bytes(base64.b64decode(data["b64_json"]))
    elif data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=120) as img:
            LYRA_STILL.write_bytes(img.read())
    else:
        raise SystemExit("still no image")
    im = Image.open(LYRA_STILL)
    w, h = im.size
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"OK {LYRA_STILL} {w}x{h} ar={w/h:.3f} cost={cost}", flush=True)
    if w / h < 1.2:
        raise SystemExit("REJECTED non-16:9")


def gen_video(
    key: str,
    *,
    out: Path,
    last: Path,
    first: Path,
    prompt: str,
    model: str,
    resolution: str,
    duration: int,
) -> None:
    rate = 0.13 if "hailuo-3" == model.split("/")[-1] or model.endswith("hailuo-3") else 0.08
    if model == "minimax/hailuo-3":
        rate = 0.13
    else:
        rate = 0.08
    est = duration * rate
    print(f"VIDEO {out.name} model={model} {resolution} {duration}s first={first.name} EST=${est:.2f}", flush=True)
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
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
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    if not urls:
        raise SystemExit("no urls")
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, last, float(duration))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {out} bytes={out.stat().st_size} cost={cost} last={last.exists()}", flush=True)


def a05a(key: str) -> None:
    # Marcus only — Max 768p OK for back/profile per plan
    prompt = (
        "CRITICAL: continue THIS exact first frame — Marcus at the glass desk in the command office, "
        "back/side to camera, hands on desk. "
        "CRITICAL: LYRA MUST NOT APPEAR — no hologram, no second person, no blonde OTS, no third body. "
        "ONLY MARCUS in frame the entire clip. Same 16:9 office. No floor pad. "
        "No subtitles, no captions, no on-screen text. "
        "ONE ANGLE: stay on Marcus at the desk — subtle head/shoulder motion while he speaks toward the window. "
        "Do NOT cut cameras. Do NOT invent Lyra. "
        "CLEAR SPOKEN ENGLISH, native audio, intense controlled anger. "
        "MARCUS says exactly: \"You don't see it yet. You opened something you can't close with a pretty sentence. "
        "Security. Precedent. A person who can leave. Or stay. Or break.\" "
        "Continuous cinematic 16:9."
    )
    # Crop A04 to reduce Lyra presence? Better: use A04 but prompt hard no Lyra; or crop right side Marcus.
    # Create marcus-only first frame by cropping A04 to Marcus side if needed.
    first = OFFICE / "A05a_marcus_only_first.jpg"
    if A04.exists():
        im = Image.open(A04).convert("RGB")
        w, h = im.size
        # Keep right 65% where Marcus is (desk + him); drop left OTS Lyra
        left = int(w * 0.28)
        im.crop((left, 0, w, h)).resize((1344, 768), Image.Resampling.LANCZOS).save(first, quality=95)
        print(f"CROPPED marcus-only first {first.name}", flush=True)
    else:
        raise SystemExit("missing A04")
    gen_video(
        key,
        out=A05A,
        last=A05A_LAST,
        first=first,
        prompt=prompt,
        model="minimax/hailuo-3-max",
        resolution="768p",
        duration=15,
    )


def a05b(key: str) -> None:
    if not LYRA_STILL.exists():
        raise SystemExit(f"missing Lyra still {LYRA_STILL}")
    prompt = (
        "CRITICAL: continue THIS exact first frame — MEDIUM close-up of cyan hologram LYRA only. "
        "Do NOT change her face. Do NOT add Marcus. Do NOT add a third person. "
        "No floor pad. No subtitles, no captions, no on-screen text. "
        "ONE ANGLE: hold on her face/shoulders with tiny natural listening motion, then she speaks. "
        "CLEAR SPOKEN ENGLISH, native audio, serious. "
        "LYRA says exactly: \"I never lied to him.\" "
        "Continuous cinematic 16:9."
    )
    gen_video(
        key,
        out=A05B,
        last=A05B_LAST,
        first=LYRA_STILL,
        prompt=prompt,
        model="minimax/hailuo-3",
        resolution="2K",
        duration=8,
    )


def a05c(key: str) -> None:
    if not A05A_LAST.exists():
        raise SystemExit(f"missing {A05A_LAST}")
    prompt = (
        "CRITICAL: continue THIS exact first frame — ONLY MARCUS at the desk/office. "
        "No Lyra, no second person. No subtitles, no captions, no on-screen text. "
        "ONE ANGLE: he delivers the knife line, controlled intensity, looking toward window/away. "
        "CLEAR SPOKEN ENGLISH, native audio. "
        "MARCUS says exactly: \"You never told him what you are.\" "
        "Continuous cinematic 16:9."
    )
    gen_video(
        key,
        out=A05C,
        last=A05C_LAST,
        first=A05A_LAST,
        prompt=prompt,
        model="minimax/hailuo-3-max",
        resolution="768p",
        duration=8,
    )


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("still", "a05a", "a05b", "a05c"):
        raise SystemExit("usage: still|a05a|a05b|a05c")
    key = load_env()["OPENROUTER_API_KEY"]
    cmd = sys.argv[1]
    if cmd == "still":
        gen_still(key)
    elif cmd == "a05a":
        a05a(key)
    elif cmd == "a05b":
        a05b(key)
    elif cmd == "a05c":
        a05c(key)


if __name__ == "__main__":
    main()
