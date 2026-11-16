#!/usr/bin/env python3
"""Download a finished OpenRouter video job by id.

  python fetch_openrouter_video.py <job_id> <out.mp4>
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ENV = Path(r"d:\movie maker\.env")


def load_key() -> str:
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OPENROUTER_API_KEY")


def main() -> None:
    job_id, out = sys.argv[1], Path(sys.argv[2])
    key = load_key()
    hdr = {"Authorization": f"Bearer {key}"}
    req = urllib.request.Request(f"https://openrouter.ai/api/v1/videos/{job_id}", headers=hdr)
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    print("STATUS", res.get("status"), "usage", res.get("usage"), flush=True)
    urls = res.get("unsigned_urls") or []
    if not urls:
        raise SystemExit(f"no urls: {json.dumps(res)[:600]}")
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=hdr), timeout=180) as resp:
        out.write_bytes(resp.read())
    last = out.with_name(out.stem + "_last.jpg")
    subprocess.run(
        ["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(out), "-frames:v", "1", "-q:v", "2", str(last)],
        capture_output=True,
    )
    print(f"SAVED {out} ({out.stat().st_size}) last={last.name}", flush=True)


if __name__ == "__main__":
    main()
