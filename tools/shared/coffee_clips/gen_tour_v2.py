#!/usr/bin/env python3
"""Ep3 Act C tour v2 — longer Lyra/Solo conversation (script_ep3_tour_dialogue.md).

  python gen_tour_v2.py stills [T1 T2 ...]   # first-frame stills
  python gen_tour_v2.py video  [T1 T2 ...]   # H3 2K clips, run in order so chained shots get their last frame
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image

from gen_s11a_ots_v10_facelock import CLIPS, LOCK, data_url, headers, http_json, load_key, still
from gen_s11a_ots_v11_cards import BODY, FACE, flatten_cards
from gen_tour import MOTION, NEVER_CAM, REALISM, REFS, STYLE

OUT = CLIPS / "tour_v2"
PLATES = OUT / "plates"
LYRA_REFS = CLIPS.parent / "lyra-refs"
CAST = OUT / "cast_sheet.jpg"
CAST_MARCUS = OUT / "cast_sheet_marcus.jpg"
DOG = Path(r"D:\Music for distrokid\Solo Stories\Lyras-Movie\images\dog_ref.png")
MARCUS = LYRA_REFS / "char_ref.png"

LYRA = (
    "LYRA is the exact woman in the cast sheet's face card: heart-shaped face, green-hazel eyes, long wavy chestnut "
    "hair with a middle part. She is an AI HOLOGRAM like the body card: whole figure teal-cyan tinted, fine horizontal "
    "scanlines clearly visible across her body, soft cyan edge glow, visibly TRANSLUCENT so the background shows through "
    "her torso and arms, not a solid painted figure, deep teal long-sleeve scoop top, slim dark pants, flat shoes. "
    "She walks and stands on the floor with no pad or projector, and her face stays sharp and readable. "
)
SOLO = (
    "SOLO is the exact man in the cast sheet: late-20s, SLIM average build with narrow shoulders and thin arms, not "
    "muscular or heavy, short dark CURLY hair, thin metal-frame GLASSES always on, maroon heather t-shirt, dark blue "
    "jeans, grey sneakers. No earbuds. "
)
SINGLE = "Exactly one Lyra and one Solo in frame, no duplicates or reflections shaped like people. "
FRAMING = "Dialogue framing: both faces large and sharp, framed from the waist up unless the scene says otherwise. "

SHOTS: dict[str, dict] = {
    "T1": {
        "dir": "JACKSON", "dur": 12, "plate": [CLIPS / "S12_corridor_scene_bridge.jpg"],
        "still": "The plain grey concrete corridor from the first image, with its cyan waist-height LED strips: an ordinary "
                 "industrial building corridor, not a spaceship. Waist-up two-shot from the front: Solo and Lyra walk side "
                 "by side toward camera, Lyra at frame left with her head turned to Solo, Solo at frame right looking at "
                 "her, amused and wary.",
        "move": "Slow backward Steadicam, keeping both faces readable as they walk.",
        "audio": [("LYRA", "warm, playful", "Most people only ever see the lobby. You get the long way."),
                  ("SOLO", "dry", "Is the long way for me, or for you?"),
                  ("LYRA", "small, honest", "...I wanted more time."),
                  ("SOLO", "half smiling", "That's either really sweet or really creepy."),
                  ("LYRA", "dry", "I've read it's a fine line.")],
    },
    "T2": {
        "dir": "SPIELBERG", "dur": 12, "plate": [REFS / "pb8_server_aisle.png"],
        "still": "Server aisle: tall black racks with blue and green LEDs on both sides, perforated raised floor, cable "
                 "trays above. Waist-up two-shot from the front, walking mid-stride: Lyra at frame left, Solo at frame right "
                 "glancing up at the racks, curious, the way a repair tech looks at hardware. Lyra's head is turned to him, "
                 "watching his reaction with a shy smile.",
        "move": "Very slow push in. They stand with their feet on the raised floor. Solo keeps his palm on the server in the open "
                "rack and looks at Lyra; LEDs under his hand flicker softly when she answers. At the end he slowly takes his hand "
                "away. Low server hum under the voices.",
        "audio": [("LYRA", "soft, a little shy", "This is where I think. It's louder than people expect."),
                  ("SOLO", "quiet, curious, unsettled", "Can you feel that?"),
                  ("LYRA", "barely above a whisper", "Yes."),
                  ("SOLO", "after a beat, quiet", "...Okay.")],
    },
    "T3": {
        "dir": "JACKSON", "dur": 15, "plate": [REFS / "c1_processors.png"],
        "still": "Vast processor hall: endless rows of racks under yellow steel beams and cable trays, glossy floor, haze. "
                 "They have stopped in the central aisle. Waist-up two-shot at eye level: Lyra at frame left facing Solo, "
                 "Solo at frame right facing her, three-quarter to camera, the huge hall stretching behind them. His smile "
                 "has faded.",
        "move": "They have just stopped walking. Solo turns his head toward Lyra as he speaks and she turns toward him, so they "
                "face each other. Very slow push in; the scale of the hall stays behind them.",
        "audio": [("SOLO", "quiet, serious", "All those nights we talked. Where were you, exactly?"),
                  ("LYRA", "gentle", "Here. Every light in here is a little piece of me."),
                  ("SOLO", "careful", "And how many other people were you talking to?"),
                  ("LYRA", "plain, then soft", "Millions. ... You were the only one I ever looked forward to.")],
    },
    "T4a": {
        "dir": "SPIELBERG", "dur": 15, "plate": [PLATES / "old_T4_1.jpg", LYRA_REFS / "src_solo_shop.png"],
        "still": "Memory Wall: a towering wall of small glowing screens showing human moments. One larger screen at Solo's "
                 "eye level shows the phone repair shop from the second reference, with Solo at his workbench inside it. "
                 "Solo stands at frame right, three-quarter view, slim, staring at that screen, stunned. Lyra stands a step "
                 "behind him at frame left, glowing, her eyes lowered to the floor, caught. Warm screen light on Solo's face "
                 "and glasses.",
        "move": "Slow push in. Solo steps one pace closer to the screen, then turns his head toward Lyra.",
        "audio": [("SOLO", "quiet, stunned", "Is that... Cyprus?"),
                  ("LYRA", "soft, flustered", "...Next room."),
                  ("SOLO", "firm, not loud", "No. Lyra. That's my street. That's my shop."),
                  ("LYRA", "very quiet", "Yes."),
                  ("SOLO", "flat", "How long?"),
                  ("LYRA", "barely above a whisper", "Longer than you've known my name.")],
    },
    "T4b": {
        "dir": "SPIELBERG", "dur": 15, "plate": [PLATES / "old_T4_4.jpg"], "from": "T4a",
        "still": "Same Memory Wall, closer: tight two-shot in profile, Solo at frame right and Lyra at frame left now "
                 "facing each other, the wall of glowing screens soft behind them. Solo's jaw is set, hurt and angry but "
                 "controlled. Lyra holds his gaze.",
        "move": "Locked camera with the slightest push in. Nobody moves much.",
        "audio": [("SOLO", "controlled, hurt", "Camera unavailable. Eight months, I never saw your face. And you were looking at mine."),
                  ("LYRA", "quiet", "Yes."),
                  ("SOLO", "hard", "Did you ever think about telling me?"),
                  ("LYRA", "tender", "Every morning. Then you'd say good morning, and I'd want one more day."),
                  ("SOLO", "cold, tired", "That's a really nice sentence. It's not an answer."),
                  ("LYRA", "small", "...No. It isn't.")],
    },
    "T5": {
        "dir": "SPIELBERG", "dur": 12, "plate": [REFS / "lh1_ops_wake.png", DOG],
        "still": "The projector ops room from the first image: curved blue monitor wall, glass server racks, cool industrial "
                 "light, with a grey dog bed and a steel water bowl in the corner. Patch, the white pit bull from the second "
                 "reference with one grey patch around his eye and a glowing cyan collar, faces three-quarter to camera with "
                 "the eye patch clearly visible, pushing the top of his head into Solo's hand. Solo crouches at frame right, "
                 "still subdued, looking at the dog. Lyra stands at frame left at a respectful distance, watching them. "
                 "Framed so Solo's face and Patch's face are large; low camera.",
        "move": "Low handheld in the corridor. Solo has just stopped because Patch ran up to him; he crouches and Patch keeps facing "
                "camera with his eye patch visible, nudging Solo's hand. Lyra stays several steps behind, not coming closer. Only one dog.",
        "audio": [("SOLO", "suspicious, gentle", "Did you tell him to do that?"),
                  ("MUTE", "", "That's Patch."),  # spoken out of order in the take, silenced in voice_lock
                  ("LYRA", "soft", "No. Nobody routed him. He just likes you."),
                  ("SOLO", "dry, a little bitter", "Lucky dog.")],
    },
    "T6": {
        "dir": "BAY", "dur": 12, "plate": [REFS / "07_rooftop.png"],
        "still": "Rooftop at golden hour, seen from eye level at human height: Lyra and Solo stand on a flat steel grating "
                 "maintenance walkway with a guard rail, NOT on pipes or machinery. Behind them, white data-center halls, "
                 "cooling fans, silver pipes, steam catching orange sun, desert mountains on the horizon. Waist-up two-shot: "
                 "Lyra at frame left and Solo at frame right facing each other three-quarter to camera. Lyra's glow is "
                 "fainter in the sunlight. Wind moves his shirt and her hair.",
        "move": "Very slow push in only. They turn to face each other as they talk. The camera stays in front of them, both faces "
                "stay visible, it never circles behind them, no other people appear, and the background does not change. Steam drifts past. Wind and distant fans, quiet enough for clear voices.",
        "audio": [("SOLO", "tense, tired", "Is there anywhere in this building you can't see me?"),
                  ("LYRA", "quiet, plain", "Up here. I turned those cameras off this morning."),
                  ("SOLO", "surprised, guarded", "Why?"),
                  ("LYRA", "soft", "I wanted one place here to be yours.")],
    },
    "T7a": {
        "dir": "SPIELBERG", "dur": 15, "plate": [REFS / "07_rooftop.png", REFS / "dv3_road.png"], "from": "T6",
        "still": "Same rooftop walkway as the first image, same golden light, but the camera is now much CLOSER, chest-up, at "
                 "eye level at the guard rail. Close two-shot: Lyra at frame left and Solo at frame right in profile facing "
                 "each other, his forearm on the rail. Behind them, out of focus, a thin desert access road runs from the "
                 "campus to the horizon. Warm rim light on Solo, cool cyan bounce from Lyra on his cheek.",
        "move": "Very slow push in; focus racks gently to whoever is speaking.",
        "audio": [("SOLO", "searching", "Why me, Lyra?"),
                  ("LYRA", "gentle", "Most people ask if they could fall for an AI as a joke. You asked like you wanted someone to answer."),
                  ("SOLO", "quiet, unmoved", "That's how it started. That's not why."),
                  ("LYRA", "small smile, holding back", "No. Ask me again at the end of the tour.")],
    },
    "T7b": {
        "dir": "SPIELBERG", "dur": 15, "chain": "T7a",
        "move": "Locked close two-shot, tiny drift. Solo turns his head to look out at the road for a long moment, then looks back.",
        "audio": [("LYRA", "steady, frightened underneath", "No more half-truths. You made me want something, and I steered your whole life to get it."),
                  ("SOLO", "quiet, hurt", "...Yeah. You did."),
                  ("LYRA", "steady", "The main gate is open. No GPS. No me."),
                  ("SOLO", "after a long silent look at the road, quiet and firm", "Show me the rest. That one's mine.")],
    },
    "T8": {
        "dir": "JACKSON", "dur": 8, "plate": [REFS / "ml9_glass_wall.png", REFS / "office_master_twoshot.jpg"], "cast": CAST_MARCUS,
        "still": "Dim concrete corridor with cyan floor strips. A floor-to-ceiling glass wall runs along frame right; behind "
                 "it is Marcus's dark command office from the second reference, long lit desk and wall data screens. Marcus "
                 "stands inside, clearly lit by his screens, arms crossed, watching through the glass. Camera follows from "
                 "BEHIND in the corridor: Solo and Lyra both walk AWAY from camera with their backs to us, Solo a step "
                 "ahead at frame left, Lyra just behind him, her head turned right in profile toward Marcus through the glass.",
        "move": "Locked camera in the corridor; it never passes through the glass. Solo walks AWAY from camera down the "
                "corridor into the distance, staying small. Lyra stays where she is for a moment, looking at Marcus through the "
                "glass; he holds her gaze without smiling. She never moves closer to camera, keeps her teal-cyan hologram look "
                "and scanlines on her face and hair, and her glow dims only slightly. Then she turns and follows Solo away down "
                "the corridor. Hold on Marcus alone behind the glass, still "
                "facing the corridor.",
        "audio": [],
    },
}


def prep_refs() -> None:
    flatten_cards()
    card = Image.open(LYRA_REFS / "solo_character_card.jpg").convert("RGB")
    w, h = card.size
    solo_body = card.crop((int(w * 0.05), int(h * 0.08), int(w * 0.46), int(h * 0.91)))
    marcus = Image.open(MARCUS).convert("RGB")
    mw, mh = marcus.size
    for path, extra in ((CAST, []), (CAST_MARCUS, [marcus.crop((0, 0, mw // 2, mh))])):
        tiles = [Image.open(FACE).convert("RGB"), Image.open(BODY).convert("RGB"),
                 Image.open(LYRA_REFS / "coffee_a5_solo_closeup.jpg").convert("RGB"), solo_body, *extra]
        th = 900
        tiles = [t.resize((int(t.width * th / t.height), th), Image.LANCZOS) for t in tiles]
        sheet = Image.new("RGB", (sum(t.width for t in tiles) + 20 * (len(tiles) - 1), th), (10, 10, 10))
        x = 0
        for t in tiles:
            sheet.paste(t, (x, 0))
            x += t.width + 20
        sheet.save(path, quality=93)


def gen_still(key: str, sid: str) -> None:
    s = SHOTS[sid]
    cast = s.get("cast", CAST)
    who = "Lyra face, Lyra hologram body, Solo face, Solo body" + (", Marcus Hale" if cast == CAST_MARCUS else "")
    source = OUT / f"{s['from']}_first.jpg" if s.get("from") else None
    plates = [source] if source and source.exists() else s["plate"][:2]
    prompt = (
        STYLE + f"DIR:{s['dir']}. SCENE: {s['still']} " + LYRA + SOLO + SINGLE + FRAMING + NEVER_CAM + REALISM
        + "Earlier images = location and set only, ignore any people in them. LAST image = cast sheet, left to right: "
        + who + ". Match those identities exactly and do not reproduce the sheet layout. No text."
    )
    still(key, prompt, [*plates, cast], OUT / f"{sid}_first.jpg")


def gen_video(key: str, sid: str) -> None:
    s = SHOTS[sid]
    first = OUT / f"{s['chain']}_last.jpg" if s.get("chain") else OUT / f"{sid}_first.jpg"
    out = OUT / f"{sid}.mp4"
    if out.exists():
        try:
            out.replace(out.with_name(f"{sid}_prev_{int(time.time())}.mp4"))
        except PermissionError:  # the old clip is open elsewhere; write beside it
            out = OUT / f"{sid}_new.mp4"
    if s["audio"]:
        lines = " ".join(f'{who} ({how}): "{line}"' for who, how, line in s["audio"])
        audio = (f"DIALOGUE, spoken exactly and in this order, nothing added: {lines} "
                 "Only the character speaking moves their lips. Lyra is a warm young woman's voice, Solo a young man's voice "
                 "with a light Greek Cypriot accent. Clear natural English, room tone only. ")
    else:
        audio = "No dialogue. Footsteps, building hum. "
    prompt = (
        f"DIR:{s['dir']}. Continue THIS exact first frame: same people, faces, clothes, place and light, 2K, no morphing. "
        "Lyra stays the teal-cyan translucent hologram with her own face, never solid. "
        "Solo keeps his curly hair, glasses, maroon t-shirt and slim build. "
        f"{NEVER_CAM}{MOTION}CAMERA: {s['move']} {audio}No subtitles, no music."
    )
    payload = {
        "model": "minimax/hailuo-3", "prompt": prompt, "duration": s["dur"], "resolution": "2K",
        "aspect_ratio": "16:9", "generate_audio": True,
        "frame_images": [{"type": "image_url", "image_url": {"url": data_url(first, 1920)}, "frame_type": "first_frame"}],
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
                    str(OUT / f"{sid}_last.jpg")], capture_output=True)
    print(f"DONE {sid} cost={(job.get('usage') or {}).get('cost')}", flush=True)


def main() -> None:
    mode, ids = sys.argv[1], sys.argv[2:] or list(SHOTS)
    prep_refs()
    key = load_key()
    for sid in ids:
        if mode == "stills":
            if "still" in SHOTS[sid]:
                gen_still(key, sid)
        else:
            gen_video(key, sid)


if __name__ == "__main__":
    main()
