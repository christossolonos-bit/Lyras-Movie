#!/usr/bin/env python3
"""Ep3 Act C — Lyra gives Solo the facility tour (T1–T8).

  python gen_tour.py stills [T1 T2 ...]   # bridge stills (Gemini)
  python gen_tour.py video  [T1 T2 ...]   # H3 2K clips from approved stills
"""
from __future__ import annotations

import base64
import io
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

from gen_s11a_ots_v10_facelock import CLIPS, LOCK, data_url, headers, http_json, load_key
from gen_s11a_ots_v11_cards import BODY, FACE, flatten_cards

REPO = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie")
REFS = REPO / "tools" / "facility_3d" / "refs"
TOUR = CLIPS / "tour"
SOLO_FACE = LOCK / "solo_face.jpg"
SOLO_BODY = REPO / "images" / "src" / "solo_seafront_source.png"

LYRA = (
    "LYRA is the exact woman in the Lyra face card (heart-shaped face, green-hazel eyes, long wavy chestnut hair "
    "with a middle part, warm soft smile) rendered as an AI HOLOGRAM exactly like the Lyra body card: whole figure "
    "teal-cyan tinted, fine horizontal scanlines, soft cyan edge glow, faintly translucent; deep teal scoop "
    "long-sleeve top, slim dark pants. She walks freely — no floor pad, no projector beam. Her face stays readable. "
)
SOLO = (
    "SOLO is the exact man in the Solo refs: late-20s, short dark curly hair, thin metal-frame glasses, "
    "maroon heather t-shirt, dark jeans, sneakers. No earbuds, no headphones. "
)
STYLE = "Photoreal 35mm cinema, 16:9, anamorphic depth, no text, no subtitles, no collage. "
NEVER_CAM = "Neither of them looks into the camera. "
REALISM = (
    "REALISM: shot on location, not a composite. Same lens perspective and horizon for people and set; correct "
    "real-world scale (Solo ~1.80 m, Lyra ~1.70 m against door frames, racks ~2.2 m). Feet planted on the actual "
    "walkable floor with contact shadows and weight in the stance. Solo is lit by the set's own lights — color, "
    "direction and falloff match (LED spill, sun rim light, screen glow on skin and glasses). Lyra is a light "
    "source: her cyan glow spills onto the floor, nearby surfaces, and Solo's arm and face; reflections in glossy "
    "floors and glass. Her feet touch the floor lightly. Natural mid-motion body language, relaxed hands, clothes "
    "folding with movement, atmospheric haze and depth of field shared by everyone in frame. "
)
MOTION = (
    "PHYSICS: real walking gait with weight transfer and heel strike, natural arm swing, inertia when stopping, "
    "cloth and hair react to movement and wind, camera has real inertia; Lyra moves like a person (no sliding or "
    "floating) while her light flickers subtly; consistent scale and parallax as the camera moves. "
)

SHOTS: dict[str, dict] = {
    "T1": {
        "dir": "JACKSON", "dur": 8, "plate": [CLIPS / "S12_corridor_exit_last.jpg"],
        "still": "Long grey concrete corridor with cyan waist-height LED strips and glowing cyan access rings on doors, "
                 "receding far into depth. Wide tracking shot from behind and slightly low: Solo and Lyra walk side by side "
                 "away from camera, small against the long corridor, Lyra glowing softly, half a step ahead, turning her head "
                 "toward Solo as she talks.",
        "move": "Smooth Steadicam follow behind them down the corridor; cyan rings ignite one by one ahead of Lyra as she passes.",
        "audio": 'LYRA (warm, a little playful): "Most people only ever see the lobby. You get the long way."',
    },
    "T2": {
        "dir": "SPIELBERG", "dur": 8, "plate": [REFS / "pb8_server_aisle.png"],
        "still": "Server aisle: tall black server racks with blue and green LEDs both sides, perforated raised floor tiles, "
                 "cable trays above. Medium two-shot walking toward camera: Solo looks up at the racks in quiet awe, "
                 "Lyra walks beside him with her head turned toward Solo, watching his reaction with a shy smile. "
                 "Only ONE Lyra in the frame — no reflections or copies of her on the racks; just a soft cyan light spill.",
        "move": "Slow backward dolly as they walk toward camera; the LEDs ripple in a soft wave down the aisle as Lyra passes.",
        "audio": 'LYRA (soft, almost shy): "This is where I think. It\'s louder than people expect." Low server hum.',
    },
    "T3": {
        "dir": "JACKSON", "dur": 8, "plate": [REFS / "c1_processors.png"],
        "still": "Vast processor hall: endless rows of server racks under yellow steel beams and cable trays, glossy floor "
                 "reflecting blue LEDs, haze. Extreme wide high angle: Solo and the glowing cyan Lyra are two small figures "
                 "standing in the central aisle, Solo turning slowly to take it in.",
        "move": "Slow crane up and back revealing the full scale of the hall; tiny figures hold center.",
        "audio": 'LYRA (gentle, from the figure below): "Every light in here… is a little piece of me." Deep hum, airflow.',
    },
    "T3b": {
        "dir": "JACKSON", "dur": 8, "plate": [REFS / "c1_processors.png"],
        "still": "",
        "move": "Starts high above the aisle looking down its length; slow crane DOWN and forward toward the two small "
                "figures as Solo stops and turns a full slow circle taking in the endless racks; Lyra waits, glowing.",
        "audio": 'LYRA (gentle, echoing faintly): "Every light in here… is a little piece of me." Deep hum, airflow.',
    },
    "T4": {
        "dir": "SPIELBERG", "dur": 8, "plate": [REFS / "st4_memory_wall.png", SOLO_BODY],
        "still": "Memory Wall: a towering wall of small glowing screens showing human moments — birthdays, weddings, "
                 "sunsets, families. Solo stands in the foreground right in PROFILE facing the wall (frame right), "
                 "still, arms at his sides, lips parted, stunned — face lit warm by the screens. He stares at one larger "
                 "screen at his eye level that shows the seafront photo from the second reference image (Solo smiling on a "
                 "palm-lined Cyprus promenade) — that photo appears ONLY inside the screen. "
                 "Lyra stands a step behind him at left, glowing cyan, eyes lowered to the floor, caught and embarrassed.",
        "move": "Slow push in past Lyra onto Solo's face as he recognizes himself.",
        "audio": 'SOLO (quiet, stunned): "Is that… Cyprus?" Beat. LYRA (soft, flustered): "…Next room."',
    },
    "T5": {
        "dir": "SPIELBERG", "dur": 6, "plate": [REFS / "pb9_home.png", REFS / "lh1_ops_wake.png"],
        "still": "Projector Ops corner: wall data screens, glass server cabinets, a grey dog bed and steel water bowl, a cyan "
                 "wall speaker. Patch — white pit bull with grey patch over one eye and a cyan-light collar — has just lifted "
                 "his head from the bed, tail mid-wag, looking at Solo. Solo crouches down offering his hand, grinning. "
                 "Lyra stands beside, glowing, smiling down at the dog.",
        "move": "Low handheld at dog height; Patch gets up and trots to sniff Solo's hand, licks it.",
        "audio": 'LYRA (proud, warm): "This is Patch. He chose me first." Solo laughs softly.',
    },
    "T6": {
        "dir": "BAY", "dur": 8, "plate": [REFS / "07_rooftop.png"],
        "still": "Rooftop at golden hour: endless white data-center halls, giant cooling fan units, silver pipe runs, "
                 "steam plumes catching orange sun, desert mountains on the horizon. Low hero angle: a roof access door "
                 "swung open, Solo stepping out into wind and light, Lyra beside him — her cyan hologram flickering and "
                 "shimmering in the hard sunlight, hair lifting slightly.",
        "move": "Sweeping low orbit around them as steam rolls past and lens flares bloom; epic but quiet.",
        "audio": 'LYRA (awed, quiet under the wind): "And this is where I come to watch the world." Wind, fans.',
    },
    "T7": {
        "dir": "SPIELBERG", "dur": 8, "plate": [REFS / "07_rooftop.png"],
        "still": "Rooftop edge at sunset, close two-shot in profile: Solo at left and Lyra at right facing each other at the "
                 "rail, desert and steam soft behind them, warm orange backlight on Solo, cool cyan glow from Lyra mixing "
                 "between their faces. Solo looks at her searching; Lyra looks out at the horizon, then back to him.",
        "move": "Very slow push in; shallow focus racks from Solo to Lyra on her answer.",
        "audio": 'SOLO (gentle): "Why me, Lyra?" LYRA (small smile, holding something back): "Ask me again… at the end of the tour."',
    },
    "T8": {
        "dir": "JACKSON", "dur": 8, "plate": [REFS / "marcus_office_ref.png", REFS / "lh1_ops_wake.png"],
        "still": "Camera stands in a dim concrete CORRIDOR. A floor-to-ceiling glass wall runs across the back of the frame; "
                 "BEHIND the glass is Marcus's office (desk with three monitors, papers pinned up, whiteboard, desk lamp — "
                 "from the first reference). Marcus — grey hair, black leather jacket (second reference) — stands INSIDE "
                 "the office by his desk, arms crossed, watching through the glass. In the FOREGROUND corridor, in front of "
                 "the glass, Solo and the glowing Lyra walk past from right to left in profile, Solo talking, Lyra's eyes "
                 "flicking toward Marcus through the glass.",
        "move": "Lateral tracking with them; Lyra turns her head toward Marcus through the glass and her cyan glow softens "
                "a little (still clearly a bright cyan hologram), then she keeps walking. "
                "Camera stops and holds on Marcus alone behind the glass.",
        "audio": "No dialogue. Footsteps, building hum, a soft low tone as Lyra's glow dims.",
    },
}


CAST = LOCK / "tour_cast_sheet.jpg"


def prep_refs() -> None:
    flatten_cards()
    src = Image.open(REPO / "images" / "src" / "solo_closeup_source.png").convert("RGB")
    w, h = src.size
    src.crop((int(w * 0.52), 0, w, int(h * 0.85))).save(SOLO_FACE, quality=95)
    sea = Image.open(SOLO_BODY).convert("RGB")
    sw, sh = sea.size
    tiles = [
        Image.open(FACE).convert("RGB"),
        Image.open(BODY).convert("RGB"),
        Image.open(SOLO_FACE).convert("RGB"),
        sea.crop((int(sw * 0.3), 0, int(sw * 0.66), sh)),
    ]
    th = 900
    tiles = [t.resize((int(t.width * th / t.height), th), Image.LANCZOS) for t in tiles]
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + 20 * 3, th), (10, 10, 10))
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 20
    sheet.save(CAST, quality=93)
    TOUR.mkdir(exist_ok=True)


def gen_still(key: str, sid: str) -> Path:
    s = SHOTS[sid]
    refs = [*s["plate"][:2], CAST]
    prompt = (
        STYLE + f"DIR:{s['dir']}. SCENE: {s['still']} " + LYRA + SOLO + NEVER_CAM + REALISM
        + "References: first image(s) = location/set. LAST image = cast sheet, left to right: Lyra face card, "
        "Lyra hologram body card, Solo face, Solo body. Match those identities exactly; do NOT reproduce the sheet layout."
    )
    out = TOUR / f"{sid}_bridge.jpg"
    print(f"STILL {out.name} ← {[p.name for p in refs]}", flush=True)
    body = {
        "model": "google/gemini-2.5-flash-image",
        "prompt": prompt,
        "aspect_ratio": "16:9",
        "input_references": [{"type": "image_url", "image_url": {"url": data_url(p)}} for p in refs],
    }
    res = http_json("https://openrouter.ai/api/v1/images", key, body)
    item = (res.get("data") or [None])[0]
    if not item:
        raise SystemExit(f"empty still {sid}: {json.dumps(res)[:600]}")
    raw = base64.b64decode(item["b64_json"]) if item.get("b64_json") else urllib.request.urlopen(item["url"]).read()
    out.write_bytes(raw)
    print(f"OK {out.name}", flush=True)
    return out


def gen_video(key: str, sid: str) -> None:
    s = SHOTS[sid]
    bridge = TOUR / f"{sid}_bridge.jpg"
    out = TOUR / f"{sid}.mp4"
    prompt = (
        f"DIR:{s['dir']}. Continue THIS exact first frame — same people, same faces, same place, 2K, no morphing. "
        f"Lyra stays the teal-cyan glowing hologram with her own face throughout — never turns into a solid or dark figure. "
        f"Solo keeps his exact face from the first frame: short dark CURLY hair, thin metal-frame GLASSES, maroon t-shirt. "
        f"{NEVER_CAM}{MOTION}"
        f"CAMERA: {s['move']} AUDIO: {s['audio']} Clear natural English voices. No subtitles, no music swell."
    )
    payload = {
        "model": "minimax/hailuo-3", "prompt": prompt, "duration": s["dur"], "resolution": "2K",
        "aspect_ratio": "16:9", "generate_audio": True,
        "frame_images": [{"type": "image_url", "image_url": {"url": data_url(bridge, 1920)}, "frame_type": "first_frame"}],
    }
    job = http_json("https://openrouter.ai/api/v1/videos", key, payload, timeout=180)
    print(f"SUBMIT {sid} {job.get('id')}", flush=True)
    poll = f"https://openrouter.ai/api/v1/videos/{job.get('id')}"
    status, deadline = job.get("status", "pending"), time.time() + 1800
    while status not in ("completed", "failed", "cancelled", "expired") and time.time() < deadline:
        time.sleep(15)
        job = http_json(poll, key, None, timeout=60)
        status = job.get("status", "pending")
    if status != "completed":
        print(f"FAILED {sid} {status} {json.dumps(job)[:400]}", flush=True)
        return
    req = urllib.request.Request(job["unsigned_urls"][0], headers=headers(key))
    with urllib.request.urlopen(req, timeout=180) as resp:
        out.write_bytes(resp.read())
    subprocess.run(["ffmpeg", "-y", "-sseof", "-0.3", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                    str(TOUR / f"{sid}_last.jpg")], capture_output=True)
    print(f"DONE {sid} cost={(job.get('usage') or {}).get('cost')}", flush=True)


def main() -> None:
    mode, ids = sys.argv[1], sys.argv[2:] or list(SHOTS)
    prep_refs()
    key = load_key()
    if mode == "stills":
        for sid in ids:
            gen_still(key, sid)
    elif mode == "video":
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as ex:
            list(ex.map(lambda sid: gen_video(key, sid), ids))
    total = sum(SHOTS[i]["dur"] for i in ids)
    print(f"H3 2K total {total}s ≈ ${total * 0.13:.2f}", flush=True)


if __name__ == "__main__":
    main()
