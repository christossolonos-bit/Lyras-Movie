"""Episode 4 helpers: balance check, GPT Image 2 stills, and video clips through production_lock.

Follows PIPELINE_EFFICIENCY.md: approve a still per setup, then make each clip from that still.
Dialogue on minimax/hailuo-3 (2K). Silent shots may use minimax/hailuo-3-max (768p).
"""
from __future__ import annotations

import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(R), str(R / "assets" / "coffee_clips")]
from production_lock import Shot, Line, _image, build_prompt, submit, video_payload  # noqa: E402,F401
from gen_s11a_ots_v10_facelock import load_key  # noqa: E402

E4 = R / "Episode 4"
FRAMES = E4 / "Frames"
CLIPS = E4 / "Clips"
API = "https://openrouter.ai/api/v1"


def balance() -> float:
    req = urllib.request.Request(f"{API}/credits", headers={"Authorization": f"Bearer {load_key()}"})
    d = json.load(urllib.request.urlopen(req, timeout=30))["data"]
    return d["total_credits"] - d["total_usage"]


def need(dollars: float) -> None:
    left = balance()
    print(f"balance ${left:.2f}, this call about ${dollars:.2f}", flush=True)
    if left < dollars + 0.5:
        raise SystemExit("not enough balance; top up first")


def still(out: Path, prompt: str, refs: list[Path]) -> Path:
    """One GPT Image 2 still, 1536x864, up to 3 refs. About $0.07."""
    need(0.10)
    try:
        res = submit(f"{API}/images", load_key(), {"model": "openai/gpt-image-2", "prompt": prompt, "aspect_ratio": "16:9",
                                                   "input_references": [_image(p) for p in refs[:3]]})
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} {e.read().decode('utf-8', 'replace')[:1500]}")
    from PIL import Image
    item = res["data"][0]
    raw = base64.b64decode(item["b64_json"]) if item.get("b64_json") else urllib.request.urlopen(item["url"]).read()
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.open(io.BytesIO(raw)).convert("RGB").save(out)
    print("SAVED", out, "cost:", (res.get("usage") or {}).get("cost"), flush=True)
    return out


def clip(shot: Shot, out: Path, model: str = "minimax/hailuo-3", resolution: str = "2K") -> Path:
    rate = {"minimax/hailuo-3": 0.13, "minimax/hailuo-3-max": 0.08}[model]
    payload = video_payload(shot, model=model, resolution=resolution)
    if model == "minimax/hailuo-3-max":
        payload["generate_audio"] = False  # H3 Max has no audio pricing; silent cover only (PRODUCTION_RULES 8)
    need(rate * shot.duration)
    print("prompt chars:", len(payload["prompt"]), flush=True)
    key = load_key()
    try:
        res = submit(f"{API}/videos", key, payload)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} {e.read().decode('utf-8', 'replace')[:1500]}")
    poll = res.get("polling_url") or f"{API}/videos/{res.get('id')}"
    if poll.startswith("/"):
        poll = "https://openrouter.ai" + poll
    auth = {"Authorization": f"Bearer {key}"}
    status, deadline = res.get("status", "pending"), time.time() + 1500
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(12)
        with urllib.request.urlopen(urllib.request.Request(poll, headers=auth), timeout=60) as r:
            res = json.loads(r.read().decode("utf-8"))
        status = res.get("status", "pending")
        print("POLL", status, flush=True)
    if status != "completed":
        raise SystemExit(f"FAILED {status} {json.dumps(res)[:800]}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(res["unsigned_urls"][0], headers=auth), timeout=180) as r:
        out.write_bytes(r.read())
    print("SAVED", out, "cost:", (res.get("usage") or {}).get("cost"), flush=True)
    with (E4 / "Scripts" / "prompts_sent.md").open("a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n## {out.name} ({model} {resolution})\n\n```text\n{payload['prompt']}\n```\n")
    return out
