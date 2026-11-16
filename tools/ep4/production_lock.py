#!/usr/bin/env python3
"""Refuses any Lyra shot that breaks PRODUCTION_RULES.md. All new generation goes through here.

  from production_lock import Shot, build_prompt, video_payload, still_payload, submit
  python production_lock.py   # self-test; makes no API calls
"""
from __future__ import annotations

import base64
import json
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REFS = ROOT / "assets" / "lyra-refs"

DIRECTORS = {
    "BAY": "DIR:BAY. Low angles on machines, chrome and cyan highlights, motion-forward, short dialogue punches.",
    "SPIELBERG": "DIR:SPIELBERG. Longer take on faces, warm practicals against the cool hologram, wonder in the eyes, "
                 "quiet after a big line, handheld-intimate when emotional.",
    "JACKSON": "DIR:JACKSON. Wide cathedral frame, group blocking, earnest dialogue, the scale of the facility.",
}

ENGINE = ("care", "deny", "force", "button")

# Refs are ordered face first. voice None means the character cannot speak until one is written.
CHARACTERS = {
    "Lyra": {"refs": ["lyra_face_source.png", "lyra_ref.png", "lh3_hologram_forms.png", "lh4_lyra_closeup.png"],
             "look": "fully translucent cyan hologram with no natural skin, cyan aura around her whole body, soft scanlines, long wavy hair, her own face",
             "voice": "warm, bright female voice, mid-30s, American, with a faint airy digital resonance"},
    # Chris's own Solo card (2026-11-15). Old refs: solo_face_approved.jpg, solo_face_portrait_crop.png, solo_face_smile.jpg
    "Solo": {"refs": ["solo_card_portrait.png", "solo_card_face_34.png", "solo_card_casual_maroon.png"],
             "look": "curly dark hair, hazel eyes, thin silver rectangular wire glasses, dark stubble, maroon t-shirt",
             "voice": "soft-spoken, natural male voice, about 30, conversational",
             "voice_ref": "solo_voice_ref.wav"},
    "Marcus": {"refs": ["char_ref.png"],
               "look": "48, salt-and-pepper hair, grey-flecked stubble, black leather jacket, grey henley",
               "voice": "low, warm, slightly gravelly male voice",
               "voice_ref": "marcus_voice_ref.wav"},  # his Ep1 lines, cut for Lyra Live
    "Nova": {"refs": ["nova_ref.png", "nova_character_card.jpg", "coffee_a4_nova_closeup.jpg"],
             "look": "dark messy bun, charcoal cardigan, layered necklaces",
             "voice": "warm, steady, teasing female voice, about 30, conversational",
             "voice_ref": "nova_voice_ref.wav"},
    "Juno": {"refs": ["juno_portrait.png"],
             "look": "around 30, platinum-blonde shaggy bob, freckles, tattoo sleeve, olive tank top, charcoal overalls, brass goggles",
             "voice": "warm, slightly husky female voice, around 30, American, quick and sarcastic",
             "voice_ref": "juno_voice_ref.wav"},  # her Ep1 lines, cut for Lyra Live
    "James": {"refs": ["james_dunn_ref.png"],
              "look": "shaved head, ruddy, heavyset, OCP camouflage uniform with colonel insignia",
              "voice": "big, hearty male voice, American, a little gravelly, easy confidence",
              "voice_ref": "james_voice_ref.wav"},  # his Ep2 rover-scene lines
    "Patrik": {"refs": ["patrik_portrait.png", "patrik_face_34.png", "patrik_operations_outfit.png"],
               "look": "37, stocky and solid, short black hair swept up, round friendly face, black technical jacket over a black tee, "
                       "blue lanyard with ID badge, steel chronograph watch",
               "voice": "steady, friendly male voice, late 30s, clear and practical",
               "voice_ref": "patrik_voice_ref.wav"},
    "Patch": {"refs": ["dog_ref.png"],
              "look": "white pit bull, grey patch around his right eye, black collar with a glowing cyan tag",
              "voice": None},
}

LOOK = ("LOOK: Live-action. Faces and bodies exactly as in tour clip A2 v2: real skin, natural faces, Solo's face not pointed. "
        "Not glossy, not CG, not airbrushed.")
PROJECTOR_BOX = "small brushed-metal wall box with a round lens at the top, a speaker grille and a glowing cyan ring below"
PROJECTOR_LINE = "glowing cyan line running along the wall"
FRAMINGS = {
    "upper_body": "Framed on one person from the chest up, nobody else in frame.",
    "wide": "Wide shot of both people, nobody speaks, their mouths stay closed, the moment plays on their expressions.",
    "two_shot": "Both people in frame from the knees up. Only the named speaker talks, and the other person's mouth stays closed.",
    "from_behind": "Both people seen from behind as they walk away from the camera. Faces stay turned away, so the line is heard, not lip read.",
    "knees_one": "Framed on one person from the knees up, nobody else in frame.",
    "insert": "Close-up insert of a detail such as a hand or an object, no face in frame, nobody speaks.",
    "two_react": "Both people in frame from the knees up. Nobody says any words; the only voices are short wordless gasps or screams written in the action.",
    "wide_one":"Wide shot of one person alone, nobody else in frame, nobody speaks, the moment plays on body and expression.",
}
CARD_MARKS = ("_ref", "card", "turnaround")
OUTDOORS = re.compile(r"\b(roof|rooftop|outdoors?|outside|exterior|gate|yard|courtyard|parking|road|open air|walkway|guard rail)\b", re.I)
MAX_WORDS_PER_SECOND = 2
MAX_REFS = 3


class Refused(SystemExit):
    pass


@dataclass
class Line:
    who: str
    action: str  # what the actor physically does while saying it
    text: str


@dataclass
class Shot:
    id: str
    director: str
    characters: list[str]
    beat: str
    engine: str
    location: str
    action: str
    duration: int = 10
    framing: str = "upper_body"  # upper_body: one person, may talk. wide: both people, expressions only, no talking
    lines: list[Line] = field(default_factory=list)
    first_frame: Path | None = None
    last_frame: Path | None = None
    tour: bool = False
    projector: str = ""  # tour shots with Lyra: which box or wall line is projecting her, and where it sits


def ref_paths(shot: Shot) -> list[Path]:
    """Face refs for everyone in the shot, leads first, up to MAX_REFS."""
    per_char = [[REFS / r for r in CHARACTERS[c]["refs"]] for c in shot.characters]
    picked: list[Path] = []
    depth = 0
    while len(picked) < MAX_REFS and any(depth < len(p) for p in per_char):
        picked += [p[depth] for p in per_char if depth < len(p)]
        depth += 1
    return picked[:MAX_REFS]


def problems(shot: Shot) -> list[str]:
    found: list[str] = []
    if shot.director not in DIRECTORS:
        found.append(f"director must be one of {sorted(DIRECTORS)}, got {shot.director!r}")
    if shot.engine not in ENGINE:
        found.append(f"engine must be one of {ENGINE}, got {shot.engine!r}")
    if not shot.beat.strip():
        found.append("no beat stated")

    unknown = [c for c in shot.characters if c not in CHARACTERS]
    if unknown:
        found.append(f"not original characters: {unknown}")
    if not shot.characters:
        found.append("no characters listed; pass an empty-room shot through still or cover tooling deliberately")
    else:
        for c in shot.characters:
            if c in CHARACTERS:
                missing = [r for r in CHARACTERS[c]["refs"] if not (REFS / r).exists()]
                if missing:
                    found.append(f"{c} refs missing from assets/lyra-refs: {missing}")

    text = " ".join([shot.action, shot.beat, *[l.action for l in shot.lines]])  # dialogue may name people off screen
    for name in CHARACTERS:
        if name not in shot.characters and re.search(rf"\b{name}\b", text):
            found.append(f"{name} is named in the shot but not on its character list")

    speakers = {l.who for l in shot.lines}
    if shot.framing not in FRAMINGS:
        found.append(f"framing must be one of {sorted(FRAMINGS)}, got {shot.framing!r}")
    if len(speakers) > 1:
        found.append(f"{len(speakers)} speakers in one clip; the limit is 1, so give each speaker their own shot")
    if shot.framing in ("wide", "wide_one", "insert", "two_react") and shot.lines:
        found.append("a wide shot is for expressions only and cannot have dialogue")
    if shot.framing in ("upper_body", "knees_one", "wide_one") and len(shot.characters) > 1:
        found.append(f"an upper-body shot shows one person, got {shot.characters}")
    if shot.framing == "from_behind" and len(shot.characters) < 2:
        found.append(f"a from-behind shot shows both people, got {shot.characters}")
    if shot.framing in ("two_shot", "two_react") and len(shot.characters) < 2:
        found.append(f"a two-shot shows both people, got {shot.characters}")
    for who in speakers:
        if who not in shot.characters:
            found.append(f"{who} speaks but is not on the character list")
        elif who in CHARACTERS and not CHARACTERS[who]["voice"]:
            found.append(f"{who} has no written voice on file")
    words = sum(len(l.text.split()) for l in shot.lines)
    if words > shot.duration * MAX_WORDS_PER_SECOND:
        found.append(f"{words} words in {shot.duration}s; the limit is {shot.duration * MAX_WORDS_PER_SECOND}")
    for l in shot.lines:
        if not l.action.strip():
            found.append(f"line has no physical action: {l.text!r}")

    if shot.first_frame:
        name = shot.first_frame.name.lower()
        if any(m in name for m in CARD_MARKS):
            found.append(f"a card or ref sheet cannot be a first frame: {shot.first_frame.name}")
    for frame in (shot.first_frame, shot.last_frame):
        if frame and not frame.exists():
            found.append(f"frame not found: {frame}")

    if shot.tour:
        where = OUTDOORS.search(f"{shot.location} {shot.action}")
        if where:
            found.append(f"tour must stay inside the 16 buildings; found {where.group(0)!r}")
        if "Lyra" in shot.characters and not shot.projector.strip():
            found.append("tour shot with Lyra must name the projector box or wall line showing her")
    return found


def check(shot: Shot) -> None:
    found = problems(shot)
    if found:
        raise Refused(f"REFUSED {shot.id}:\n  - " + "\n  - ".join(found))


def build_prompt(shot: Shot) -> str:
    check(shot)
    cast = " ".join(f"{c}: {CHARACTERS[c]['look']}." for c in shot.characters)
    parts = [DIRECTORS[shot.director], f"LOCATION: {shot.location}.", f"CAST, matching the reference images exactly: {cast}",
             f"ONE BEAT: {shot.beat}.", FRAMINGS[shot.framing], f"ACTION: {shot.action}", LOOK]
    if shot.tour:
        parts.append("Stays inside the building throughout, with no exterior.")
    if shot.projector:
        parts.append(f"Lyra is light projected from the building, and her voice comes from the same source. Its sources are the "
                     f"{PROJECTOR_BOX}, and the {PROJECTOR_LINE}. In this shot: {shot.projector}.")
    if shot.lines:
        spoken = " ".join(f'{l.who} ({l.action}): "{l.text}"' for l in shot.lines)
        voices = " ".join(f"{w}'s voice: {CHARACTERS[w]['voice']}." for w in dict.fromkeys(l.who for l in shot.lines))
        parts.append(f"DIALOGUE, exactly and in this order, only the speaker's lips move: {spoken} {voices}")
    else:
        parts.append("No dialogue.")
    parts.append("SOUND: The natural sound of this place and what happens in it, footsteps where people walk, and any spoken lines. No music, no score. No on-screen text, no subtitles.")
    return " ".join(parts)


def data_url(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _image(path: Path) -> dict:
    return {"type": "image_url", "image_url": {"url": data_url(path)}}


def video_payload(shot: Shot, model: str = "minimax/hailuo-3", resolution: str = "2K") -> dict:
    prompt = build_prompt(shot)
    payload = {
        "model": model, "prompt": prompt, "duration": shot.duration, "resolution": resolution, "aspect_ratio": "16:9",
        "generate_audio": True,  # Chris wants every clip to have sound: room tone, footsteps, any lines
        "input_references": [_image(p) for p in ref_paths(shot)],
    }
    frames = [(shot.first_frame, "first_frame"), (shot.last_frame, "last_frame")]
    images = [{**_image(p), "frame_type": kind} for p, kind in frames if p]
    if images:  # MiniMax refuses frames and references together, so the frames carry the faces
        payload["frame_images"] = images
        del payload["input_references"]
    return payload


def still_payload(shot: Shot) -> dict:
    return {
        "model": "google/gemini-2.5-flash-image", "prompt": build_prompt(shot), "aspect_ratio": "16:9",
        "input_references": [_image(p) for p in ref_paths(shot)],
    }


def submit(url: str, key: str, payload: dict, timeout: int = 300) -> dict:
    """The one POST path. Payloads only come from video_payload or still_payload, which run the checks."""
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _self_test() -> None:
    good = Shot(
        id="good", director="SPIELBERG", characters=["Lyra"], beat="She admits she was afraid", engine="care",
        location="server aisle inside building 4", action="She stops walking and looks down.", duration=10, tour=True,
        projector="on the end wall of the aisle",
        lines=[Line("Lyra", "looks down, then back at him", "I was afraid he'd turn around.")],
    )
    assert not problems(good), problems(good)
    assert "DIR:SPIELBERG" in build_prompt(good) and PROJECTOR_BOX in build_prompt(good) and PROJECTOR_LINE in build_prompt(good)
    wide = Shot(**{**good.__dict__, "characters": ["Lyra", "Marcus"], "framing": "wide", "lines": []})
    assert not problems(wide), problems(wide)
    assert len(ref_paths(wide)) == MAX_REFS and ref_paths(wide)[1].name == "char_ref.png"
    two = Shot(**{**good.__dict__, "characters": ["Lyra", "Marcus"], "framing": "two_shot"})
    assert not problems(two), problems(two)

    def refused(needle: str, **change) -> None:
        bad = Shot(**{**good.__dict__, **change})
        assert any(needle in p for p in problems(bad)), (needle, problems(bad))

    refused("director", director="")
    refused("director", director="BAY+JACKSON")
    refused("engine", engine="")
    refused("not original", characters=["Sarah"])
    refused("shows one person", characters=["Lyra", "Marcus"])
    refused("cannot have dialogue", characters=["Lyra", "Marcus"], framing="wide")
    refused("limit is 1", characters=["Lyra"], lines=[Line("Lyra", "looks up", "Yes."), Line("Marcus", "turns", "No.")])
    refused("named in the shot", action="Solo walks past them.")
    refused("16 buildings", location="rooftop walkway")
    refused("16 buildings", action="They walk through the door to the main gate.")
    refused("projector", projector="")
    refused("words", duration=5, lines=[Line("Lyra", "looks up", " ".join(["word"] * 11))])
    refused("no written voice", characters=["Lyra", "Patch"], lines=[Line("Patch", "turns", "Why?")])
    refused("physical action", lines=[Line("Lyra", "", "Yes.")])
    refused("two-shot", framing="two_shot")
    behind = Shot(**{**good.__dict__, "characters": ["Lyra", "Marcus"], "framing": "from_behind"})
    assert not problems(behind), problems(behind)
    refused("from-behind", framing="from_behind")
    refused("first frame", first_frame=REFS / "solo_character_card.jpg")
    refused("first frame", first_frame=REFS / "lyra_ref.png")
    outdoor_line = Shot(**{**good.__dict__, "lines": [Line("Lyra", "steady", "The main gate is open.")]})
    assert not problems(outdoor_line), "dialogue may mention the outside"
    print("self-test passed: no API calls made")


if __name__ == "__main__":
    _self_test()
