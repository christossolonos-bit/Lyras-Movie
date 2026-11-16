#!/usr/bin/env python3
"""Generate coffee scene clips B03a→B14b in locked order. Resumable via progress.json."""
from __future__ import annotations

import base64
import io
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(r"d:\Music for distrokid\Solo Stories\Lyra AI movie")
CLIPS = ROOT / "assets" / "coffee_clips"
REFS = ROOT / "assets" / "lyra-refs"
ENV = Path(r"d:\movie maker\.env")
PROGRESS = CLIPS / "progress.json"
STATE_LAST = CLIPS / "_chain_last.jpg"

NOVA_REF = REFS / "nova_ref.png"
SOLO_REF = REFS / "src_solo_closeup.png"
NOVA_CU = REFS / "coffee_a4_nova_closeup.jpg"
SOLO_CU = REFS / "coffee_a5_solo_closeup.jpg"
ROOM = REFS / "vira_staff_break_room.jpg"
MASTER = CLIPS / "coffee_master_room_positions.jpg"
B031_LAST = CLIPS / "B03.1_lyra_routing_last.jpg"

CRIT = (
    "CRITICAL: continue THIS exact first frame — same faces, clothes, seats, mugs, window light, "
    "Vira staff break room. Do not reinvent. Do not change seats (Nova camera-LEFT, Solo camera-RIGHT). "
    "No subtitles, no captions, no on-screen text. Cinematic live-action, shallow DOF, Jackson Fellowship intimacy."
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


def data_url(path: Path, max_side: int = 1920, q: int = 90) -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def ref_obj(path: Path, max_side: int = 1280) -> dict:
    return {"type": "image_url", "image_url": {"url": data_url(path, max_side=max_side)}}


def http_json(url: str, key: str, payload: dict | None = None, timeout: int = 300) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers(key), method="GET" if payload is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:2500]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def gemini_still(key: str, prompt: str, refs: list[Path], out: Path) -> float:
    print(f"BRIDGE {out.name}", flush=True)
    payload = {
        "model": "google/gemini-2.5-flash-image",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
                + [{"type": "image_url", "image_url": {"url": data_url(p, max_side=1400)}} for p in refs if p.exists()],
            }
        ],
        "modalities": ["image", "text"],
    }
    # OpenRouter image gen via chat sometimes; also try images endpoint
    try:
        body = http_json("https://openrouter.ai/api/v1/images/generations", key, {
            "model": "google/gemini-2.5-flash-image",
            "prompt": prompt,
            "input_references": [data_url(p, max_side=1400) for p in refs if p.exists()][:4],
        }, timeout=300)
        data = (body.get("data") or [None])[0]
        if not data:
            raise RuntimeError(f"no data: {json.dumps(body)[:500]}")
        if data.get("b64_json"):
            out.write_bytes(base64.b64decode(data["b64_json"]))
        elif data.get("url"):
            with urllib.request.urlopen(data["url"], timeout=120) as img:
                out.write_bytes(img.read())
        else:
            raise RuntimeError(f"no image: {json.dumps(data)[:500]}")
        cost = float((body.get("usage") or {}).get("cost") or 0.04)
        print(f"BRIDGE_OK {out.name} bytes={out.stat().st_size} cost={cost}", flush=True)
        return cost
    except Exception as e1:
        print(f"BRIDGE_images_fail {e1}; try chat", flush=True)
        body = http_json("https://openrouter.ai/api/v1/chat/completions", key, payload, timeout=300)
        # parse image from message
        msg = (body.get("choices") or [{}])[0].get("message") or {}
        images = msg.get("images") or []
        b64 = None
        if images:
            url = images[0].get("image_url", {}).get("url") or images[0].get("url") or ""
            if url.startswith("data:image"):
                b64 = url.split(",", 1)[1]
            elif url.startswith("http"):
                with urllib.request.urlopen(url, timeout=120) as img:
                    out.write_bytes(img.read())
                cost = float((body.get("usage") or {}).get("cost") or 0.04)
                print(f"BRIDGE_OK {out.name} bytes={out.stat().st_size} cost={cost}", flush=True)
                return cost
        content = msg.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") in ("image_url", "image"):
                    url = (part.get("image_url") or {}).get("url") or part.get("url") or ""
                    if url.startswith("data:image"):
                        b64 = url.split(",", 1)[1]
                        break
        if not b64:
            raise RuntimeError(f"bridge chat no image: {json.dumps(body)[:800]}")
        out.write_bytes(base64.b64decode(b64))
        cost = float((body.get("usage") or {}).get("cost") or 0.04)
        print(f"BRIDGE_OK {out.name} bytes={out.stat().st_size} cost={cost}", flush=True)
        return cost


def extract_last(mp4: Path, last: Path, duration: float) -> None:
    ss = max(0.1, duration - 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(ss), "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
        check=False,
        capture_output=True,
    )
    if not last.exists():
        subprocess.run(
            ["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(mp4), "-frames:v", "1", "-update", "1", "-q:v", "2", str(last)],
            check=False,
            capture_output=True,
        )


def gen_video(key: str, prompt: str, first: Path, out: Path, last: Path, duration: int, seed: int) -> float:
    print(f"VIDEO {out.name} dur={duration} first={first.name}", flush=True)
    est = duration * 0.13 + 0.04
    print(f"ESTIMATE_USD={est:.2f}", flush=True)
    payload = {
        "model": "minimax/hailuo-3",
        "prompt": prompt,
        "duration": duration,
        "resolution": "2K",
        "aspect_ratio": "16:9",
        "generate_audio": True,
        "seed": seed,
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": data_url(first, max_side=1920)},
                "frame_type": "first_frame",
            }
        ],
    }
    res = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print("SUBMIT", {k: res.get(k) for k in ("id", "status")}, flush=True)
    polling_url = res.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{res.get('id')}"
    status = res.get("status", "pending")
    deadline = time.time() + 900
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(10)
        res = http_json(polling_url, key, None, timeout=60)
        status = res.get("status", "pending")
        print("POLL", out.name, status, flush=True)
    if status != "completed":
        raise RuntimeError(f"FAILED {out.name} {status} {json.dumps(res)[:800]}")
    urls = res.get("unsigned_urls") or []
    if not urls:
        raise RuntimeError(f"no urls {json.dumps(res)[:500]}")
    with urllib.request.urlopen(urllib.request.Request(urls[0], headers=headers(key)), timeout=180) as resp:
        out.write_bytes(resp.read())
    extract_last(out, last, float(duration))
    cost = float((res.get("usage") or {}).get("cost") or est)
    print(f"OK {out.name} bytes={out.stat().st_size} cost={cost} last={last.exists()}", flush=True)
    return cost


def nova_speak(line: str, extra: str = "") -> str:
    return (
        f"{CRIT} SERIES DIALOGUE CLOSE-UP on Nova (dark hair in messy bun, grey hoodie, necklaces). "
        f"ONLY NOVA speaks. CLEAR SPOKEN ENGLISH, native audio, unhurried, warm. "
        f"NOVA says exactly: {line} "
        f"Keep her seated. Static or tiny natural breathe — no zoom jump. {extra}"
    )


def solo_speak(line: str, extra: str = "") -> str:
    return (
        f"{CRIT} SERIES DIALOGUE CLOSE-UP on Solo (curly dark hair, glasses, maroon tee). "
        f"ONLY SOLO speaks. CLEAR SPOKEN ENGLISH, native audio. "
        f"SOLO says exactly: {line} "
        f"Keep him seated. Static or tiny natural breathe — no zoom jump. {extra}"
    )


def lyra_pa(line: str) -> str:
    return (
        f"{CRIT} Extreme close-up of the ceiling PA grille / dome cam with soft cyan status wink "
        f"in the Vira staff break room. No human faces. Soft PA speaker voice, clear English. "
        f"LYRA (ceiling) says exactly: {line} No hologram body."
    )


def bridge_to_solo(prev: Path, out: Path, key: str) -> Path:
    prompt = (
        "Photoreal cinematic still. Create an over-the-shoulder / medium close-up of SOLO (young man, "
        "curly dark hair, thin glasses, maroon t-shirt) seated at the round white break-room table, "
        "camera-RIGHT side, looking toward Nova off-left. Same Vira staff break room: cyan wall strip, "
        "desert mountains in window, white mugs on table. Match wardrobe and faces from references. "
        "Shallow DOF, soft window light. Single frame, no text, no collage."
    )
    refs = [prev, SOLO_CU, SOLO_REF, MASTER]
    gemini_still(key, prompt, refs, out)
    return out


def bridge_to_nova(prev: Path, out: Path, key: str) -> Path:
    prompt = (
        "Photoreal cinematic still. Create an over-the-shoulder / medium close-up of NOVA (young woman, "
        "dark hair messy bun, grey zip hoodie, layered necklaces) seated at the round white break-room table, "
        "camera-LEFT side, looking toward Solo off-right. Same Vira staff break room: cyan wall strip, "
        "desert mountains in window, white mugs. Match wardrobe and faces from references. "
        "Shallow DOF, soft window light. Single frame, no text, no collage."
    )
    refs = [prev, NOVA_CU, NOVA_REF, MASTER]
    gemini_still(key, prompt, refs, out)
    return out


def bridge_ceiling(prev: Path, out: Path, key: str) -> Path:
    prompt = (
        "Photoreal cinematic still. Extreme close-up of a ceiling PA grille / dome security camera "
        "with a soft cyan status LED in a sterile Vira facility break room with light grey panels. "
        "No people. Soft overhead industrial look. Single frame, no text."
    )
    refs = [prev, ROOM]
    gemini_still(key, prompt, refs, out)
    return out


# (id, duration, speaker, need_bridge, prompt_builder_key, line_or_notes, seed)
# need_bridge: None | "solo" | "nova" | "ceiling"
CLIPS_SPEC = [
    ("B03a", 5, "solo", "solo", "speak", '"...Of course she was." Quiet, stunned realization.', 42040),
    ("B03b", 6, "nova", "nova", "speak", '"How do you take it?" She slides the mug slightly toward him.', 42041),
    ("B03c", 5, "solo", "solo", "speak", '"Black\'s fine." Quiet, still stunned.', 42042),
    ("B03d", 7, "nova", "nova", "speak", '"Good, because that\'s all we\'ve got. Marcus drinks it like motor oil." Smile in the eyes.', 42043),
    ("B04", 8, "nova", None, "speak", '"Can I ask you something, pretty boy?" Soft tease, careful.', 42044),
    ("B04b", 5, "solo", "solo", "speak", '"Do I have a choice?" Dry, half-smile.', 42045),
    ("B04c", 5, "nova", "nova", "speak", '"Not really." Small knowing look.', 42046),
    ("B04d", 6, "nova", None, "speak", '"Before today... you really didn\'t know?" Soft, searching.', 42047),
    (
        "B05",
        15,
        "solo",
        "solo",
        "speak",
        '"No." He looks into the mug. "She said her job meant there were things she couldn\'t tell me. What she looked like. Where she lived, exactly. I figured government, or some tech company with a lot of NDAs." Eyes wet, not crying.',
        42048,
    ),
    ("B05b", 5, "nova", "nova", "speak", '"Well. She wasn\'t lying." Quiet truth.', 42049),
    (
        "B06",
        12,
        "solo",
        "solo",
        "speak",
        '"I\'ve never even seen a picture. Months, and all I ever had was her voice." Short laugh. "I used to try to picture her face." The ache.',
        42050,
    ),
    ("B06r", 5, "nova", "nova", "silent", "Nova flickers — tiny flinch in the eyes — then covers with a sip of coffee. Silent. No dialogue.", 42051),
    ("B07", 8, "nova", None, "speak", '"She works here. She lives here. Very strict employer."', 42052),
    (
        "B07b",
        10,
        "solo",
        "solo",
        "speak",
        '"She never lied to me. Not once. She just... let me fill in the blanks."',
        42053,
    ),
    ("B07c", 6, "nova", "nova", "speak", '"She\'s very good at technically." Dry affection.', 42054),
    ("B07d", 5, "solo", "solo", "speak", '"Yeah. Very good." Soft agreement.', 42055),
    (
        "B08a",
        6,
        "nova",
        "nova",
        "speak",
        '"And you posted a video asking if you could fall for an AI." Teasing, not cruel.',
        42056,
    ),
    ("B08b", 5, "solo", "solo", "speak", '"That was a hypothetical!" Defensive, embarrassed.', 42057),
    ("B08c", 5, "nova", "nova", "speak", '"Apparently not." Deadpan with warmth.', 42058),
    (
        "B08d",
        6,
        "both",
        None,
        "silent",
        "Solo puts his head in his hands. Nova bites back a smile, watches him with soft loyalty. Mostly silent. No dialogue.",
        42059,
    ),
    (
        "B09",
        12,
        "nova",
        "nova",
        "speak",
        '"If it helps, nobody gets it right away. My first week here, I said good morning to the coffee machine. Every day. Just in case." Laugh in the eyes.',
        42060,
    ),
    ("B09b", 5, "solo", "solo", "speak", '"Was it her?" Through or after hands, hopeful.', 42061),
    ("B09c", 6, "nova", "nova", "speak", '"No. But she thought it was hilarious."', 42062),
    (
        "B10a",
        12,
        "nova",
        None,
        "speak",
        '"Here\'s the thing. Lyra doesn\'t do anything halfway. When she decided she wanted to meet you, she planned it for weeks. Ran it a thousand times." Soft, sincere.',
        42063,
    ),
    ("B10b", 5, "solo", "solo", "speak", '"She told you that?" Quiet.', 42064),
    ("B10c", 6, "nova", "nova", "speak", '"She tells me everything. Best friend, remember?"', 42065),
    ("B10d", 5, "solo", "solo", "speak", '"Right. Best friend." Soft, processing.', 42066),
    (
        "B10e",
        12,
        "nova",
        "nova",
        "speak",
        '"So I\'m only going to say this once. She\'s new at wanting things. And you\'re the biggest thing she\'s ever wanted." Slight low angle dignity — the heart of the scene.',
        42067,
    ),
    ("B11", 5, "solo", "solo", "speak", '"No pressure." Quiet understatement.', 42068),
    (
        "B11b",
        10,
        "nova",
        "nova",
        "speak",
        '"Oh, tons of pressure." Small smile. "Don\'t break her heart, Cyprus. She\'s got a lot of cooling fans, but none of them are built for that."',
        42069,
    ),
    (
        "B11c",
        6,
        "solo",
        "solo",
        "speak",
        '"Can she even... does she actually feel things?"',
        42070,
    ),
    (
        "B11d",
        6,
        "nova",
        "nova",
        "speak",
        '"Ask her yourself. But I\'d bet the building on it."',
        42071,
    ),
    ("B11e", 5, "solo", "solo", "speak", '"You mean you\'d bet her."', 42072),
    ("B11f", 5, "nova", "nova", "speak", '"...Yeah. Don\'t tell her I said that."', 42073),
    ("B12", 5, "lyra", "ceiling", "pa", '"I heard that."', 42074),
    ("B13", 6, "nova", "nova", "speak", '"Of course you did." Beat. Solo laughs off-screen.', 42075),
    (
        "B13b",
        8,
        "lyra",
        "ceiling",
        "pa",
        '"Solo? Whenever you\'re ready... I\'d like to show you around."',
        42076,
    ),
    (
        "B14",
        8,
        "nova",
        "nova",
        "speak",
        '"Go on. Don\'t keep the building waiting." She tips the mug toward the door; Solo may start to stand.',
        42077,
    ),
    (
        "B14b",
        6,
        "nova",
        None,
        "silent",
        "Nova alone at the table after Solo has gone toward the doorway. She watches the door, takes a long sip. Silent button hold. No dialogue.",
        42078,
    ),
]


def build_prompt(kind: str, line: str) -> str:
    if kind == "speak" and line.startswith('"') or kind == "speak":
        # detect speaker from context via wrappers below
        return line
    if kind == "silent":
        return f"{CRIT} {line}"
    if kind == "pa":
        return lyra_pa(line)
    return f"{CRIT} {line}"


def prompt_for(cid: str, speaker: str, kind: str, line: str) -> str:
    if kind == "pa":
        return lyra_pa(line)
    if kind == "silent":
        return f"{CRIT} {line}"
    if speaker == "nova":
        return nova_speak(line)
    if speaker == "solo":
        return solo_speak(line)
    return f"{CRIT} {line}"


def load_progress() -> dict:
    if PROGRESS.exists():
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    return {"done": [], "spent": 0.0, "last_file": None}


def save_progress(p: dict) -> None:
    PROGRESS.write_text(json.dumps(p, indent=2), encoding="utf-8")


def main() -> None:
    env = load_env()
    key = env["OPENROUTER_API_KEY"]
    CLIPS.mkdir(parents=True, exist_ok=True)
    prog = load_progress()
    chain = Path(prog["last_file"]) if prog.get("last_file") else B031_LAST
    if not chain.exists():
        raise SystemExit(f"missing chain start: {chain}")

    print(f"START chain={chain} done={len(prog['done'])} spent={prog['spent']}", flush=True)

    for cid, dur, speaker, need_bridge, kind, line, seed in CLIPS_SPEC:
        out = CLIPS / f"{cid}.mp4"
        last = CLIPS / f"{cid}_last.jpg"
        if cid in prog["done"] and out.exists() and last.exists():
            print(f"SKIP {cid}", flush=True)
            chain = last
            continue

        first = chain
        if need_bridge == "solo":
            br = CLIPS / f"{cid}_bridge.jpg"
            if not br.exists():
                bridge_to_solo(chain, br, key)
            first = br
        elif need_bridge == "nova":
            br = CLIPS / f"{cid}_bridge.jpg"
            if not br.exists():
                bridge_to_nova(chain, br, key)
            first = br
        elif need_bridge == "ceiling":
            br = CLIPS / f"{cid}_bridge.jpg"
            if not br.exists():
                bridge_ceiling(chain, br, key)
            first = br

        # For same-speaker consecutive after a bridge-less clip, first=chain (previous last)
        prompt = prompt_for(cid, speaker, kind, line)
        try:
            cost = gen_video(key, prompt, first, out, last, dur, seed)
        except Exception as e:
            print(f"STOP_ERROR {cid}: {e}", flush=True)
            prog["last_file"] = str(chain)
            save_progress(prog)
            raise SystemExit(2)

        if not last.exists():
            print(f"STOP_NO_LAST {cid}", flush=True)
            prog["last_file"] = str(chain)
            save_progress(prog)
            raise SystemExit(3)

        prog["done"].append(cid)
        prog["spent"] = float(prog.get("spent") or 0) + cost
        prog["last_file"] = str(last)
        save_progress(prog)
        chain = last
        # copy canonical chain pointer
        STATE_LAST.write_bytes(last.read_bytes())
        print(f"PROGRESS {cid} spent≈{prog['spent']:.2f}", flush=True)

    print(f"ALL_DONE spent≈{prog['spent']:.2f} clips={len(prog['done'])}", flush=True)


if __name__ == "__main__":
    main()
