# Lyra AI: production rules (LOCKED)

Locked 2026-10-31. Every still and video goes through `production_lock.py`, which refuses a shot that breaks these rules.

Sources: `DIRECTORS.md`, `REF_LOCK.md`, `STORY_CRAFT.md`, `script_ep3_a05_storyboard.md`, both GitHub repos.

## Every generation

1. **One director.** Bay, Spielberg or Jackson, chosen by what the shot is for. Never blended.
2. **Original characters only.** Each character in the shot gets their repo refs passed to the model. Anyone named in the shot must be on the shot's character list.
2a. **Solo's card is locked:** `assets/lyra-refs/solo_character_card_real.jpg`, real frames only. Never generate a new Solo card or use the seafront image. Solo is Chris's own likeness, so Chris signs off his face.
3. **Cards are identity refs only.** A turnaround card or `*_ref` sheet is never a first frame. Juno uses `juno_portrait.png` only.
4. **One beat per clip.** Each clip states its single beat and its place in the engine: care, deny, force or button.
5. **Room to act.** One speaker per clip, at most 2 spoken words per second. The speaker is framed alone from the chest up, or in a knees-up two-shot where the other person's mouth stays closed, or seen from behind with both walking away from camera so the line is heard rather than lip read. Each line states what the actor physically does. Wide shots of both people have no dialogue and play on their expressions.
6. **Written voices.** A speaking character must have a voice on file. The prompt carries it. Solo and Nova's voices come from the Ep2 coffee clips: `assets/lyra-refs/solo_voice_ref.wav` and `nova_voice_ref.wav`. Convert their generated lines to these samples afterward.
7. **No on-screen text, subtitles or music.**
8. **Model.** `minimax/hailuo-3` by default. H3 Max has no audio or reference-image pricing listed on OpenRouter, so it is for silent cover shots only.

## The tour

1. **Inside the 16 buildings only.** No roof, gate, yard, road or other exterior. Lyra is a hologram and can only exist where a projector can show her.
2. **Projectors and communicators.** Two things in the buildings show Lyra and carry her voice: small brushed-metal wall boxes with a round lens, a speaker grille and a glowing cyan ring, as in `assets/lyra-refs/projector_box_ref.jpg` (cropped from the repo's `marcus_office_ref.png`), and the glowing cyan lines on the walls. Every tour shot with Lyra names the box or wall line that is projecting her and shows it or its light.
3. **Dialogue may mention the outside**, but the shot stays indoors.
2a. **Lyra's look.** Translucent cyan for the whole tour, with a cyan aura around her body and soft scanlines; never natural skin.
3a. **The core door.** They walk past a circular locked door leading underground to the core of the facility. It is off limits: it stays shut and nobody enters yet. It is off limits to Lyra too: she cannot enter it or see inside it. What's down there is revealed in the season's final episode, so no earlier scene explains it.
4. **Facts.** The facility is 16 buildings and a substation (`final_transcript.txt`, which overrides the older "three buildings" in the repo script).

Where this differs from Act A of `script_ep3_marcus_lyra_office.md` ("no wall emitter, no floor pad"), this applies to the tour. The finished office clips are not changed.

## Retired tours

The rooftop shots are out: T6, T7a and T7b in `script_ep3_tour_dialogue.md`, and C8 and C9 in `gen_tour_cont.py`.

## Old scripts

The older `gen_*.py` scripts call the API directly, so the lock cannot stop them all. Do not re-run them. New generation starts from `production_lock.py`.
