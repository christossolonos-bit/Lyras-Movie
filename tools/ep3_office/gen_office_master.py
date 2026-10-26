#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import json
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
REFS = ROOT / "assets" / "lyra-refs"
OFFICE = ROOT / "assets" / "office_clips"
ENV = Path(r"d:\movie maker\.env")


def load_env() -> dict:
    env = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def data_url(path: Path, max_side: int = 1400, q: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    OFFICE.mkdir(parents=True, exist_ok=True)
    key = load_env()["OPENROUTER_API_KEY"]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://moviemaker-cloud.local",
        "X-Title": "movieMaker Cloud",
    }
    prompt = (
        "Photoreal cinematic 16:9 still. MARCUS PRIVATE OFFICE inside a desert tech facility at night. "
        "Closed door. Dark desk with dual monitors showing soft facility camera feeds. "
        "Warm practical desk lamp vs cool cyan. Desert mountains through blinds. "
        "MARCUS (middle-aged, short salt-and-pepper hair, groomed beard, black leather jacket over grey shirt) "
        "stands camera-LEFT beside the desk, solid flesh, tense jaw, arms folded — NOT smiling. "
        "Match his face exactly from the Marcus reference crops. "
        "LYRA appears as a translucent CYAN full-body HOLOGRAM of a young woman with long wavy chestnut hair — "
        "FREE TO STAND AND WALK anywhere in the office, NOT stuck on a floor emitter or projector pad. "
        "No circular pad under her feet. She stands camera-RIGHT on the office floor as a mobile hologram "
        "(scanlines, soft particles, cyan glow) mid-step or planted as if she can pace. "
        "Match Lyra face and hologram look from refs. Calm but serious, not smiling wide. "
        "Intimate Spielberg two-shot across the desk, shallow DOF, pressure in a closed room. "
        "Single frame only. No collage, no turnaround sheet, no text, no subtitles, no watermark."
    )
    # Gemini Flash Image: max 3 input_references
    refs = [
        OFFICE / "marcus_mid_crop.jpg",
        REFS / "lyra_ref.png",
        REFS / "lh4_lyra_closeup.png",
    ]
    out = OFFICE / "office_master_twoshot.jpg"
    def ref_obj(path: Path) -> dict:
        return {"type": "image_url", "image_url": {"url": data_url(path)}}

    ref_list = [ref_obj(p) for p in refs if p.exists()][:4]

    def post(url: str, payload: dict) -> dict:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:2000]}") from e

    body = None
    for url, payload in (
        (
            "https://openrouter.ai/api/v1/images",
            {"model": "google/gemini-2.5-flash-image", "prompt": prompt, "input_references": ref_list},
        ),
        (
            "https://openrouter.ai/api/v1/images/generations",
            {"model": "google/gemini-2.5-flash-image", "prompt": prompt, "input_references": ref_list},
        ),
        (
            "https://openrouter.ai/api/v1/chat/completions",
            {
                "model": "google/gemini-2.5-flash-image",
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": prompt}]
                        + [{"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs if p.exists()][:4],
                    }
                ],
                "modalities": ["image", "text"],
            },
        ),
    ):
        try:
            print(f"TRY {url}", flush=True)
            body = post(url, payload)
            break
        except RuntimeError as e:
            print(f"FAIL {e}", flush=True)

    if body is None:
        raise SystemExit("all still endpoints failed")

    # generations / images shape
    data = (body.get("data") or [None])[0]
    b64 = None
    if data:
        if data.get("b64_json"):
            out.write_bytes(base64.b64decode(data["b64_json"]))
            cost = float((body.get("usage") or {}).get("cost") or 0)
            print(f"OK {out} bytes={out.stat().st_size} cost={cost}")
            return
        if data.get("url"):
            with urllib.request.urlopen(data["url"], timeout=120) as img:
                out.write_bytes(img.read())
            cost = float((body.get("usage") or {}).get("cost") or 0)
            print(f"OK {out} bytes={out.stat().st_size} cost={cost}")
            return

    # chat completions shape
    msg = (body.get("choices") or [{}])[0].get("message") or {}
    for image in msg.get("images") or []:
        url = (image.get("image_url") or {}).get("url") or image.get("url") or ""
        if url.startswith("data:image"):
            b64 = url.split(",", 1)[1]
            break
        if url.startswith("http"):
            with urllib.request.urlopen(url, timeout=120) as img:
                out.write_bytes(img.read())
            cost = float((body.get("usage") or {}).get("cost") or 0)
            print(f"OK {out} bytes={out.stat().st_size} cost={cost}")
            return
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") in ("image_url", "image"):
                url = (part.get("image_url") or {}).get("url") or part.get("url") or ""
                if url.startswith("data:image"):
                    b64 = url.split(",", 1)[1]
                    break
    if not b64:
        raise SystemExit("no image " + json.dumps(body)[:800])
    out.write_bytes(base64.b64decode(b64))
    cost = float((body.get("usage") or {}).get("cost") or 0)
    print(f"OK {out} bytes={out.stat().st_size} cost={cost}")


if __name__ == "__main__":
    main()
