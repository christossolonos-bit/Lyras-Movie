#!/usr/bin/env python3
"""A05b H3 2K 8s, history-rich continuity prompt, from repo-face Lyra-only SB02.

Also collects the earlier thin 5s job as a versioned backup.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gen_a05b_h3_from_sb as g  # noqa: E402

OLD_JOB = "gen-vid-1793009661-mkdUEaOOC2zfEuCygJUg"
OLD_OUT = g.OFFICE / "A05b_lyra_never_lied_v3_thin5s.mp4"
OUT = g.OUT
LAST = g.LAST
DURATION = 8

PROMPT = (
    "CRITICAL: continue THIS exact first frame — same Lyra face, same cyan free-walk hologram with "
    "scanlines, same teal top, same Marcus command office: open floor, server racks, glass desk, "
    "night city windows behind her. Keep her original face exactly; do not morph or restyle it. "
    "STORY CONTEXT: this is the same late-night confrontation in Marcus's office. Lyra asked him to "
    "close the door, told him about Cyprus and the Solo name, the eight months at the gate, the day "
    "after, every night — that it was about him, not the rest of them. Marcus has just turned and laid "
    "out the stakes coldly: security, precedent, or break. Now Lyra answers him. "
    "LYRA ONLY in frame — Marcus is off-screen, has not fully turned to face her; no second person, "
    "no over-the-shoulder silhouette, no hands or shoulders in foreground. "
    "Medium close-up, one steady angle, slow subtle push-in. She holds his off-screen gaze, a small "
    "breath, jaw set, eyes steady and wounded but unflinching; hologram flickers faintly with emotion. "
    "Serious, quiet conviction — not cute, not smiling. "
    "CLEAR SPOKEN ENGLISH, native audio, low calm voice, office room tone and faint server hum. "
    "ONLY LYRA speaks. LYRA says exactly: \"I never lied to him.\" Then she holds the silence. "
    "No floor pad, no emitter, no subtitles, no captions, no on-screen text. Cinematic 16:9."
)


def poll(url: str, key: str) -> dict:
    return g.http_json(url, key, None, timeout=60)


def download(res: dict, key: str, dest: Path) -> None:
    urls = res.get("unsigned_urls") or []
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=g.headers(key)), timeout=300) as r:
        dest.write_bytes(r.read())


def main() -> None:
    key = g.load_env()["OPENROUTER_API_KEY"]
    payload = {
        "model": g.MODEL,
        "prompt": PROMPT,
        "duration": DURATION,
        "resolution": g.RESOLUTION,
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "frame_images": [
            {"type": "image_url", "image_url": {"url": g.data_url(g.FIRST)}, "frame_type": "first_frame"}
        ],
    }
    res = g.http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    new_id = res.get("id")
    print("SUBMIT NEW", new_id, res.get("status"), flush=True)
    new_url = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{new_id}"
    if new_url.startswith("/"):
        new_url = "https://openrouter.ai" + new_url
    old_url = f"https://openrouter.ai/api/v1/videos/{OLD_JOB}"

    done = {"new": None, "old": None}
    terminal = ("completed", "failed", "cancelled", "expired")
    deadline = time.time() + 1800
    while time.time() < deadline and (done["new"] is None or done["old"] is None):
        time.sleep(15)
        for name, url in (("new", new_url), ("old", old_url)):
            if done[name] is not None:
                continue
            try:
                r = poll(url, key)
            except Exception as e:  # transient network error
                print("POLL ERR", name, e, flush=True)
                continue
            st = r.get("status", "pending")
            print("POLL", name, st, flush=True)
            if st in terminal:
                done[name] = r

    old = done["old"]
    if old and old.get("status") == "completed":
        download(old, key, OLD_OUT)
        print(f"OLD OK {OLD_OUT.name} bytes={OLD_OUT.stat().st_size} "
              f"cost={(old.get('usage') or {}).get('cost')}", flush=True)
    else:
        print("OLD NOT COMPLETED", json.dumps(old)[:500] if old else "timeout", flush=True)

    new = done["new"]
    if not new or new.get("status") != "completed":
        raise SystemExit(f"NEW FAILED {new_id} {json.dumps(new)[:800] if new else 'timeout'}")
    download(new, key, OUT)
    g.extract_last(OUT, LAST, float(DURATION))
    print(f"NEW OK id={new_id} {OUT} bytes={OUT.stat().st_size} "
          f"cost={(new.get('usage') or {}).get('cost')} last={LAST.exists()} "
          f"last_mtime={time.ctime(LAST.stat().st_mtime) if LAST.exists() else None}", flush=True)


if __name__ == "__main__":
    main()
