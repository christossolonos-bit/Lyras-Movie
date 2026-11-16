# Coffee with Nova — Clip plan (OpenRouter MiniMax H3)

**Strategy (LOCKED):** Same as pre-OpenRouter / Nova private session — **~15s scenes** packing a full beat of dialogue (both voices OK in one take when the prompt names who says what). Not one-line micro-clips.

**Model:** `minimax/hailuo-3` · 2K · 16:9 · **15s** · native audio  
**Cost:** ~**$1.99/clip** ($0.13×15 + $0.04 ref)  
**Chain:** last frame → next first_frame. Bridge still only when angle must change hard.

---

## Continuity bible (every clip)

| Lock | Spec |
|------|------|
| **Room** | Vira staff break room — grey panels, cyan waist strip, round white table, coffee machine + frosted door on the **interior** wall. |
| **Window lock (S10+)** | Window is on their **side** (lateral), not a backdrop behind faces. **Walls behind** both. Table + mugs in the **middle**. Desert/campus only in side window glints — **nobody outside the glass**. |
| **Seats** | Both seated at the table by the window wall. **Nova = camera-LEFT** · **Solo = camera-RIGHT** — never swap. Coverage = **OTS on each other** (FG shoulder of listener). |
| **Nova face/wardrobe** | Dark hair messy bun, grey zip hoodie, navy underlayer, layered cord necklaces, jeans — lock to `nova_ref` + `B03.1` / `coffee_a4` |
| **Nova freckles** | Light dusting only — match **S05/S07** density. Do **not** densify (S08 drifted heavy; avoid that) |
| **Solo face/wardrobe** | Curly dark hair, thin glasses, maroon tee — lock to `src_solo_closeup` + `coffee_a5` / B02 |
| **Props** | Two white ceramic mugs on table; do not invent third person |
| **Lyra** | S01–S10: ceiling PA only. **S11+:** freefwalk cyan hologram OK — face from repo `lyra_ref` / `ref_lyra_face_holo` / `lh4`. **NEVER look into camera** (eyeline Solo/Nova only). No floor pad. |
| **S12 exit** | Into **facility corridor** (cyan strip / server-hall language from movie plates) — **NOT** outdoors/desert. Chain from coffee door + aisle plates (`vira_staff_break_room`, `pb8_server_aisle`). |
| **Audio** | Exact script lines; prompt must say **who** speaks each line; CLEAR ENGLISH; no subtitles. S11: **no dead air** before Nova’s “Go on.” |
| **Generation rule** | Prefer **movie scene lasts / set plates** as first frames — not generic invented rooms. |
| **Refs (identity only)** | Cards `nova_character_card` / `solo_character_card` and turnarounds = wardrobe/face lock — **never** open H3 on the 4-view sheet alone |
| **Positions master** | `coffee_master_room_positions.jpg` for geography |

**Prompt opener (every video):**  
`CRITICAL: continue THIS exact first frame — same faces, clothes, seats (Nova LEFT / Solo RIGHT), mugs, window light, Vira break room. Do not reinvent.`

---

## Already shot (keep)

| # | Dur | Cam | What | File |
|---|-----|-----|------|------|
| **B01** ✅ | 8s | Wide two-shot | Cyprus open | `B01_cyprus_open.mp4` |
| **B02** ✅ | 12s | Wide → Solo | Flights / GPS | `B02_flights_gps.mp4` |
| **B03.1** ✅ | 10s | OTS Solo → Nova CU | “It wasn’t. Lyra was routing you.” | `B03.1_lyra_routing.mp4` · last=`B03.1_lyra_routing_last.jpg` |
| **S01** ✅ | 15s | Nova CU / OTS | Of course / mug / Black’s fine / Marcus | `S01_mug_marcus.mp4` · last=`S01_mug_marcus_last.jpg` (~$1.95) |
| **S02** ✅ | 15s | Nova CU / OTS | Pretty boy → before today | `S02_pretty_boy.mp4` · last=`S02_pretty_boy_last.jpg` (~$1.95) |
| **S03** ✅ | 15s | Solo CU (alone — keeper) | “No.” + NDAs speech | `S03_ndas.mp4` · last=`S03_ndas_last.jpg` (~$1.95) · face lock=`solo_face_lock_approved.jpg` |
| **S04** ✅ | 15s | Solo CU | Wasn’t lying OS + picture speech | `S04_picture.mp4` · last=`S04_picture_last.jpg` |
| **S05** ✅ | 15s | Nova CU → eye push | Sip + employer / blanks / technically | `S05_employer.mp4` · last=`S05_employer_last.jpg` (~$1.95) |
| **S06** ✅ | 15s | Nova CU | Hypothetical AI banter | `S06_hypothetical.mp4` · last=`S06_hypothetical_last.jpg` (~$1.95) |
| **S06b** ✅ | 5s | Solo CU | Head in hands (silent insert after S06) | `S06b_head_in_hands.mp4` (~$0.65) |
| **S07** ✅ | 15s | Nova CU | Coffee-machine story | `S07_coffee_machine.mp4` · last=`S07_coffee_machine_last.jpg` (~$1.95) |
| **S08** ✅ | 15s | Nova CU | Halfway / best friend | **keeper** `S08_halfway_v3.mp4` · last=`S08_halfway_v3_last.jpg` (~$1.95) |
| **S09** ✅? | 15s | Nova CU | Biggest thing / don’t break her heart | `S09_biggest_thing_v3.mp4` · last=`S09_biggest_thing_v3_last.jpg` (~$1.95) — **check freckles** · **PAUSED: OpenRouter credits empty** |

---

## Remaining — 15s scenes (correct placement)

Start chain: `B03.1_lyra_routing_last.jpg` (Nova CU / OTS Solo FG, seated, mugs).

| # | Dur | Camera / coverage | Voices & exact lines (in order) | First frame |
|---|-----|-------------------|----------------------------------|-------------|
| **S01** | 15s | Hold **Nova CU / OTS** (same as B03.1). Solo may answer from FG/OS — lips OK if face glimpsed; do not cut wide. | **SOLO:** “…Of course she was.” → Nova slides mug. **NOVA:** “How do you take it?” **SOLO:** “Black’s fine.” **NOVA:** “Good, because that’s all we’ve got. Marcus drinks it like motor oil.” | B03.1 last (no bridge) |
| **S02** | 15s | Stay **Nova CU**; micro push allowed, no teleport. | **NOVA:** “Can I ask you something, pretty boy?” **SOLO:** “Do I have a choice?” **NOVA:** “Not really.” Beat. **NOVA:** “Before today… you really didn’t know?” | S01 last |
| **S03** | 15s | **Bridge → Solo CU** (A5 lineage). Camera on Solo for the confession. | **SOLO:** “No.” (into mug) “She said her job meant there were things she couldn’t tell me. What she looked like. Where she lived, exactly. I figured government, or some tech company with a lot of NDAs.” | Bridge from S02 last → Solo CU (`coffee_a5` + Solo refs) |
| **S04** | 15s | **Solo CU** continue from S03 (camera stays on him). Nova’s line is **clear OS** — her voice only, do not cut to her. End on Solo’s ache. | **NOVA (OS):** “Well. She wasn’t lying.” **SOLO:** “I’ve never even seen a picture. Months, and all I ever had was her voice.” (short laugh) “I used to try to picture her face.” | S03 last |
| **S05** | 15s | **Bridge → Nova CU → slow push into eyes** (depth). Sip down → look up at Solo as push lands. | Sip then **NOVA:** “She works here…” **SOLO OS:** never lied / fill blanks. **NOVA:** “She’s very good at technically.” | Bridge=`S05_nova_cu_bridge.jpg` |
| **S06** | 15s | **Nova CU / OTS Solo** — banter punch. Optional tiny Bay energy, no room drift. | **SOLO:** “Yeah. Very good.” **NOVA:** “And you posted a video asking if you could fall for an AI.” **SOLO:** “That was a hypothetical!” **NOVA:** “Apparently not.” → Solo head in hands; Nova bites smile. | S05 last (or Solo bridge if last frame is wrong speaker — prefer stay Nova OTS so both readable) |
| **S07** | 15s | **Nova CU** warm. | **NOVA:** “If it helps, nobody gets it right away. My first week here, I said good morning to the coffee machine. Every day. Just in case.” **SOLO:** “Was it her?” **NOVA:** “No. But she thought it was hilarious.” | S06 last |
| **S08** | 15s | **Nova CU** soft → slight low angle by end (Jackson dignity). Heart of scene. | **NOVA:** “Here’s the thing. Lyra doesn’t do anything halfway. When she decided she wanted to meet you, she planned it for weeks. Ran it a thousand times.” **SOLO:** “She told you that?” **NOVA:** “She tells me everything. Best friend, remember?” **SOLO:** “Right. Best friend.” | S07 last |
| **S09** | 15s | **Nova CU** (weight). Solo “No pressure” OS or brief FG. | **NOVA:** “So I’m only going to say this once. She’s new at wanting things. And you’re the biggest thing she’s ever wanted.” **SOLO:** “No pressure.” **NOVA:** “Oh, tons of pressure.” (small smile) “Don’t break her heart, Cyprus. She’s got a lot of cooling fans, but none of them are built for that.” | S08 last |
| **S10** | 15s | **OTS ↔ faces** — keep seats. Ceiling insert only at Lyra line if needed mid-clip; else PA voice with camera on Nova reaction. | **SOLO:** “Can she even… does she actually feel things?” **NOVA:** “Ask her yourself. But I’d bet the building on it.” **SOLO:** “You mean you’d bet her.” **NOVA:** “…Yeah. Don’t tell her I said that.” **LYRA (PA):** “I heard that.” **NOVA:** “Of course you did.” Solo laugh. | S09 last |
| **S11a** | 8s | **DIR:SPIELBERG** Tight OTS Nova+Solo → door. Free-walk cyan hologram Lyra (game card look) **hand on door rim**; indoor corridor beyond. | **LYRA:** “Solo? Whenever you’re ready… I’d like to show you around.” (B5 locked) Eyeline to Solo — never camera. | `S11a_ots_lyra_door_bridge_v12a` · refs `game/assets/characters/lyra_face.png` + `lyra_body.png` |
| **S11b** | 5s | **Nova CU** (chain S10 Nova-face last). | **NOVA:** “Don’t keep the building waiting.” | `S10_solo_ots_nova_face_last.jpg` |
| **S11c** | 8–10s | **Solo** (chain S10 Solo-face / seating). | **SOLO:** “Sure, let’s go. See you, Nova. Was nice talking to you.” Then walks **toward camera** (toward the door/Lyra). | `S10_nova_ots_solo_face_v2_last.jpg` or Solo seat last. |

---

## Angle / face checklist (QA reject if any fail)

1. Nova still **left**, Solo **right** when both visible  
2. Same hoodie / maroon tee / glasses / bun as B03.1  
3. Same room + desert window — no cafe, no hangar  
4. Spoken lines match the table **in order** — no improvisation  
5. Lyra = speakers only on S10–S11  
6. Reject morph faces, standing Nova during dialogue seats, or character-card collage opens  

---

## Cost quote (remaining)

| Clips | Sec | Video $ | Refs/bridges ~ | **Total ~** |
|-------|-----|---------|----------------|-------------|
| S01–S12 | ~12 × 15s = 180s | **$23.40** | ~$1–2 | **~$24–25** |

Balance ~$31 → **fits**. Matches the ~$20–25 band (not the $37 micro-split).

---

## Edit order

Hangar → **B01 → B02 → B03.1 → S01 → S02 → … → S12**

## Next

Reply **yes** to generate **S01** (chain from `B03.1_lyra_routing_last.jpg`, 15s, mug exchange through Marcus) under this bible.

---

## Act C — Tour (Lyra x Solo) · `assets/coffee_clips/tour/` · `gen_tour.py`

Realism lock: one physical set per shot, shared lens/light, feet planted + contact shadows, Lyra's glow lights the set, real gait/inertia.

| # | Dir | Place | Beat | Status |
|---|-----|-------|------|--------|
| T1 | JACKSON | Cyan corridor | LYRA: "Most people only ever see the lobby. You get the long way." | done |
| T2 | SPIELBERG | Server aisle | LYRA: "This is where I think. It's louder than people expect." | done |
| T3 | JACKSON | Processor hall | LYRA: "Every light in here... is a little piece of me." | done |
| T4 | SPIELBERG | Memory wall | SOLO: "Is that... Cyprus?" / LYRA: "...Next room." | done |
| T5 | SPIELBERG | Patch corner | LYRA: "This is Patch. He chose me first." | done |
| T6 | BAY | Rooftop (new) | LYRA: "And this is where I come to watch the world." | done |
| T7 | SPIELBERG | Rooftop rail | SOLO: "Why me, Lyra?" / LYRA: "Ask me again... at the end of the tour." | done |
| T8 | JACKSON | Past Marcus's glass office | No dialogue; Lyra dims meeting Marcus's eyes | done |


Coffee close done: `S11b_final` (Nova mug tip), `S11c_final` (Solo leaves), `S12b_final` (Nova sip, B7).
Stitched: `assets/coffee_clips/Ep3_ActB_door_to_ActC_tour.mp4` (S11a → S11b → S11c → S12b → T1–T8, 1:32).

