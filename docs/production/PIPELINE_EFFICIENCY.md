# Making episodes cheaper, same tactics (approved by Chris, 2026-11-15)

**Goal (Chris):** improve the process, not cut the episode. Every rule stays:
- one director per clip
- the original character refs
- one clip at a time, with approval
- each character's voice reference

Prices are from OpenRouter's video model list on 2026-11-15.

## Where the money goes now

- **Hailuo 3 (H3) 2K:** $0.13 per second, billed for any length from 5 to 15 s.
- **Retakes.** The Episode 3 tour has 123 clip files for 48 shots, about 2.5 per shot. Some are free local voice and level fixes, but most of the extra spend was paid retakes caused by drift: faces turning glossy as each clip copied the last, framing creeping in, and rooms being invented.
- **Ep4 as written:** 63 clips, about 313 s, so about $41 before retakes. At Episode 3's retake rate it could pass $80.

## 1. Approve a still before every video (biggest saving)

- A GPT Image 2 still costs about $0.07. A 5 s H3 clip costs $0.65.
- Build one approved start frame per setup. A setup is one set, one camera angle and one character's position. Every clip in that setup starts from that frame, not from the previous clip's last frame.
- The BTS remake proved it: chaining drifted the face and colours, while one base frame kept 15 clips consistent with no drift retakes.
- Cuts between clips from the same frame look like a locked-off camera, which is normal coverage.
- Show the stills for a whole scene as one contact sheet, then generate the videos one at a time as now.

## 2. Pay only for seconds we use

- H3 bills per second from 5 to 15 s. Lines that need 3–4 s still cost 5 s, so give those beats a reaction to fill the time rather than paying for silence on the cutting-room floor.
- When the same character speaks several beats in a row in the same setup (Solo A2–A4, Marcus B2–B4), make one clip of the combined length instead of three. That's fewer generations and fewer chances of a retake, and the cutter can still split it.

## 3. Silent shots on a cheaper model

About 22 Ep4 shots have no dialogue (wides, inserts, the rover, the lights coming back), roughly 120 s.

| Model | Price | Notes |
|---|---|---|
| Hailuo 3 (now) | $0.13/s | 2K, with audio |
| Hailuo 3 Max | $0.08/s at 768p | Already allowed for silent cover shots by PRODUCTION_RULES |
| Kling 3.0 Pro | $0.112/s | Approved Ep3 A9 v3 |

Moving the silent shots to H3 Max saves about $6. Needs one test clip to check that 768p cuts in cleanly next to the 2K shots.

## 4. Dialogue stays on Hailuo 3 (Chris, 2026-11-15)

- No cheaper model for dialogue. Chris rates MiniMax H3 and Seedance as the best right now and won't trade H3's quality.
- Savings come only from points 1–3 and 5–7.

## 5. Fix sound locally, never with a retake

- If the picture is good but the voice is off, convert the line to the character's voice reference (Chatterbox VC, free) or redo it with their Fish voice.
- Only retake for picture problems.

## 6. Free checks before every paid call

- `production_lock.py` checks: director, refs, at most 2 words per second, and prompts under about 2800 characters.
- No "…" in lines, because it causes mumbled filler.
- Check the OpenRouter balance first, which avoids 402 errors and waiting.
- After each clip: a Whisper word check and a contact sheet before it's shown.

## 7. Reuse approved sets

- Episode 3's plates are already approved: the core door corridor, processor hall, cooling cathedral and office.
- For Ep4, re-light them to red emergency light with an image edit (about $0.07 each) instead of building new sets.

## Rough Ep4 estimate

| Plan | Cost |
|---|---|
| As written, Ep3 retake rate | about $80 |
| As written, no retakes | about $41 |
| Stills first + right-sized clips + H3 Max for silent shots | about $33–36, with few retakes |
