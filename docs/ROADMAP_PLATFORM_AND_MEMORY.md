# Lyra World: Platform, Accounts and Character Memory

Design for turning the Lyra world into a platform you log into: each player gets their own
experience of the world, and every character remembers them across days and weeks, while also
keeping up with the series as new episodes are released.

Status: **roadmap, not started.** Saved for later. Decisions marked **Open** need an answer before building.

---

## 1. The idea in one paragraph

A player logs in and drops into their own copy of the Lyra world (Vira, Saltbrush, Halcyon,
Ironwood, the desert between). They can walk up to any of the cast and talk. Each character
knows two things: **the series** (everything that has happened in the released episodes, from
that character's point of view, and where things stand right now) and **this player** (every
conversation they have had, what the player told them, promises made, how they feel about
them). When a new episode is released, the characters' world moves forward for everyone: a
player who comes back after Episode 3 drops finds Juno talking about her new job at Vira, and
she still remembers what that player told her last week.

---

## 2. Three layers of memory

Every character's prompt is built from three layers, from most shared to most personal:

| Layer | Who it belongs to | Changes when | Example |
|---|---|---|---|
| **Character canon** | The character, shared by all players | Rarely (you edit the bible) | Juno: mechanic, platinum bob, tattoo sleeve, fixes what others give up on |
| **Series memory** | The character, shared by all players | A new episode is released | "Six years with him, and he lied. Then a work order from a data center in the desert..." |
| **Player memory** | One player and one character | Every conversation | "You told me you're a welder too. You promised to look at my trike's carburetor." |

The first two are written by you (with help from the scripts and Claude). The third is written
automatically after each conversation, and the player can see and manage it.

---

## 3. Series memory: the episode ledger

### 3.1 What gets recorded for each episode

When an episode is released, it gets one **ledger entry**, built from the script, the edit's
transcript and the story bible:

- **Episode summary**: what happened, in order (one or two paragraphs).
- **Events**: a list of discrete facts with who was present.
  Example: `Patch arrives at the gate; Lyra opens it and runs the sprinklers` (present: Lyra, Patch).
- **Per-character point of view**: for each character, what they *experienced*, what they
  *learned*, and how they *feel* about it. Characters only know what they saw, were told, or
  (for Lyra) observed through Vira's cameras and systems.
- **Knowledge boundaries**: what each character does **not** know yet. These carry forward
  until an episode changes them.
  Example: after Episode 2, Solo had not known Lyra was an AI until the Bay Three reveal.
- **Relationship changes** between cast members.
  Example: Juno is hired at Vira; Nova and Solo meet over coffee.
- **World changes** the game can reflect (and the map can show).
  Example: James's rover is now parked at Vira; Patch lives in the ops room.
- **Where we left off**: each character's situation at the end of the episode: where they
  are, what they are doing, their mood, and the open threads on their mind.
- **Talking points**: things the character is likely to bring up or react to if asked.

### 3.2 How it is stored and used

- Ledger entries are versioned: `canon_version` goes up by one with each release.
- For each character, the ledger is compiled into a **series memory block**: a running
  first-person account of the series so far, plus "where things stand now", plus the current
  knowledge boundaries. It is generated once per release per character, then reviewed by you.
- That block sits right after the character canon in the prompt and is identical for every
  player, so it is cached (see section 8): adding episodes does not make conversations slower.
- Characters are told the episode boundary explicitly: they speak about what has happened up to
  the latest released episode and must not invent future plot.

### 3.3 Returning players after a new episode

When a player comes back and the world's `canon_version` has moved past the one they last
talked under, the character is told:

> "Since you last spoke with this player, these things happened in your life: [episode deltas].
> You may bring them up naturally."

So Nova might open with: *"You missed a lot. Remember the guy from the island I mentioned?
He's here. Lyra's guest."* The per-player record stores the `canon_version` of each
conversation, which is how the game knows what is "news" to that player.

### 3.4 Spoilers (**Open**)

Two options:

- **A. World follows the series (recommended):** characters always live at the latest released
  episode. Simple, and makes each release feel like the world moved on.
- **B. World follows the player:** a setting lets a player hold the world at the episode they
  have watched. Characters then use the ledger only up to that episode.

Option A with an optional "I haven't seen Episode N yet" spoiler shield (characters avoid
details of that episode until the player turns it off) gives most of B's benefit.

### 3.5 Sources already in this repo

`STORY_BIBLE.md`, `script/ep2_breakdown.md`, `script/ep2_transcript.txt`,
`script/final_transcript.txt`, every `script/*_dialogue.md` and `*_narration.md`, the cast
and vehicle cards in `images/`. The first ledger (Episodes 1 and 2) can be drafted from these
by Claude and then corrected by you.

---

## 4. Who has memory

| Tier | Who | Memory |
|---|---|---|
| **A: the cast** | Lyra, Marcus, Nova, Juno, Solo, James Dunn | Full: canon, series memory, player memory, live AI conversation |
| **A-: Patch** | The pit bull | No speech. Remembers the player through a simple affection score and a few facts (fed him, played fetch). Lyra can talk about Patch. |
| **B: regulars** | Named townsfolk: the diner owner, the gate guard, the motel clerk, the mechanic next to Juno, etc. | Light: short canon card, player facts, last few conversation summaries. Same pipeline, smaller budget. |
| **C: crowd** | Everyone else (the thousands of NPCs) | No AI conversation. Pre-written lines. At most a "seen you before" flag. |

**Lyra is special.** She *is* the data center. In-world she can perceive anything that happens
on Vira's grounds and on the highway cameras (as in her narration), so her memory can include
things she *observed* the player do there, not only what they said to her. She cannot see inside
Halcyon, Ironwood or Saltbrush unless the story gives her a camera there.

---

## 5. Player memory: what each character keeps about each player

Stored per (player, character):

1. **Relationship state**: numbers for familiarity, trust and warmth (0 to 100), plus a short
   paragraph in the character's own voice: "how I feel about you and why". Updated after each
   conversation.
2. **Facts about the player**: the name they use, what they do, what they like, things they
   shared. Each fact has a source (which conversation), a confidence, and a date. Contradictions
   replace the older fact and are noted ("you used to say...").
3. **Episodes (conversation memories)**: after each conversation, one to five memory entries:
   a summary in the character's voice, real date and time, in-game place and time of day,
   emotional tone, an importance score from 1 to 10, and an embedding for search.
4. **Open threads and promises**: things left unresolved: "promised to bring Patch a toy",
   "Juno asked you to come back at sunset to test the trike". Each has a status: open, done or
   expired. Open threads are always in the prompt until closed.
5. **Core memories**: pinned moments that never fade (the first meeting, a big confession).
   The extraction step can propose them; the player can also pin or unpin.
6. **Recent transcript**: the raw text of the last conversation, kept for a limited time (for
   example 30 days) so the character can quote it accurately, then removed in favor of the
   summaries.

### Gossip between characters (**Open**)

By default, what you tell Nova stays with Nova. Optional rule set, run nightly:

- Characters who are close in the series (from the ledger's relationship map) can pass along a
  fact or event, with a delay and attribution: *"Nova told me you're a welder."*
- Facts the player marked private never travel.
- Lyra learns anything said on Vira's grounds directly.

Recommendation: start with private-only, and add gossip later as an opt-in setting.

---

## 6. How a conversation works

### 6.1 Building the prompt

In this order (stable parts first, so caching works):

1. **World rules** (same for everyone, cached): how characters behave, stay in canon, never
   invent future episodes, keep a persona, content limits.
2. **Character canon** (per character, cached).
3. **Series memory block** at the current `canon_version` (per character, cached).
4. **Player memory block** (per player and character, changes between visits):
   relationship paragraph and numbers, top player facts, core memories, open threads, last
   conversation summary, "what's new since you last spoke" (episode deltas), and the 5 to 10
   most relevant older memories (see 6.3).
5. **Right now** (changes every turn): where you are, real Death Valley time and weather (the
   game already runs on real time), what's around (Patch is asleep by the desk), any active
   event (dust storm), what the player is doing.
6. The conversation so far.

### 6.2 After the conversation

When the player walks away (or after a few minutes of silence), a background job reads the
transcript and produces structured output: new facts, updated facts, episode summaries,
importance, emotional tone, opened and closed threads, a relationship update, and proposed core
memories. These are written to the database and embedded.

### 6.3 Choosing which older memories to bring back

Score each memory by **relevance** (embedding similarity to the current conversation and
place), **recency** (fades over about two weeks, never to zero) and **importance**, then take the
top few that fit the token budget. Pinned memories and open threads are always included.

### 6.4 Keeping memory healthy over weeks

A nightly job per active player:

- merges near-duplicate memories,
- rolls older episodes up into "chapters" ("the week you helped Juno rebuild the trike"),
- re-scores importance,
- expires stale threads (the character may ask about them once before letting go).

Nothing is deleted silently; summarized memories stay visible to the player.

---

## 7. Accounts and the player's memory controls

### 7.1 Account

- Sign up and log in (email plus a social login). A managed auth provider is recommended over
  writing auth by hand.
- Profile: display name, the name characters should call you, pronouns (optional).
- Settings: graphics quality, crowd density, audio and character voices, subtitles, real-time
  clock vs. fixed time of day, spoiler shield, gossip on or off.
- Save state: where you are in the world, what you are driving, story-side progress.

### 7.2 Memory page (per character)

- See everything a character remembers about you: relationship, facts, conversations,
  threads, core memories. Searchable.
- Edit or delete any single memory ("forget that I said this").
- Pin or unpin core memories.
- Reset one character ("start over with Juno").
- Pause memory (talk without being remembered).
- Export all your data (JSON) and delete your account (removes all personal data within a set
  period).

---

## 8. Technology

- **Game client**: the existing three.js world in the browser.
- **Platform API on Railway**: a Node/TypeScript service (accounts, saves, settings, the
  conversation endpoint, background jobs).
- **Database**: Postgres on Railway with the `pgvector` extension for memory search.
- **Character AI**: Claude through the official Anthropic SDK, streamed so characters start
  speaking right away.
  - Default dialogue model: **Claude Opus 5.5** (`claude-opus-5-5`).
  - The extraction and nightly jobs can use the same model at low effort. A cheaper model
    (Claude Haiku 5.5) is an option if cost matters more than nuance there; that's your call
    after testing.
- **Embeddings**: Anthropic doesn't provide an embeddings model, so memory search uses a separate
  embeddings provider (Voyage AI is the usual pairing). Stored as vectors in Postgres.
- **Prompt caching**: world rules, character canon and series memory form a long, stable prefix
  shared by every player, so it is cached. A new episode changes it once per character.
- **Voices** (optional): ElevenLabs, which already voices Lyra in the film.

### Data model (first pass)

```
users(id, email, display_name, call_me, pronouns, created_at, settings jsonb)
characters(id, slug, tier, canon_md, voice_id)
episodes(id, number, title, released_at, canon_version, ledger jsonb)
character_series_memory(character_id, canon_version, block_md, reviewed_by, reviewed_at)
player_character_state(user_id, character_id, familiarity, trust, warmth,
                       feeling_md, last_canon_version, last_seen_at, paused)
player_facts(id, user_id, character_id, fact, source_conversation_id, confidence,
             created_at, superseded_by, private)
memories(id, user_id, character_id, kind /* episode | chapter | core */, summary_md,
         happened_at, game_place, game_time_of_day, tone, importance, embedding vector,
         pinned, last_recalled_at, source_conversation_id)
threads(id, user_id, character_id, text, status /* open | done | expired */,
        opened_at, closed_at)
conversations(id, user_id, character_id, started_at, ended_at, canon_version, place)
messages(id, conversation_id, role, text, created_at)   -- kept ~30 days
world_saves(user_id, position, vehicle, flags jsonb, updated_at)
```

---

## 9. Cost and scale (rough, for planning)

Using current Claude API list prices (Opus 5.5: $4 per million input tokens, $20 per million
output, $0.20 per million cached input). Assume a 6,000-token prompt per turn, about 5,000
of it cached (rules, canon, series memory), and a 300-token reply:

- One turn costs about **1 cent** on Opus 5.5.
- A 20-turn conversation costs about **20 cents**.
- The after-conversation extraction adds a few cents.

That is the number to plan around: an active player who has two or three conversations a day
costs on the order of a dollar a day in AI. Ways to manage it: per-player daily conversation
limits, a subscription tier, a cheaper model for regulars (tier B), and short replies by
default. These are product decisions to make once there is real usage data.

---

## 10. Build order

1. **Accounts and saves**: sign-up, login, settings, save and restore position. The game loads
   your world.
2. **One character end to end**: Lyra at Vira. Canon, the Episode 1 and 2 ledger, live
   conversation, post-conversation memory, the memory page. Prove it remembers you a week later.
3. **The whole cast**: Marcus, Nova, Juno, Solo and James, each in their place in the world.
4. **Episode release flow**: an admin page to add an episode's ledger, review each character's
   series memory, and publish (canon_version goes up).
5. **Regulars and Patch**: tier B memory and Patch's affection.
6. **Gossip, events and weather hooks**: characters react to the dust storm you're both in.

---

## 11. Open questions

1. **Spoilers:** does the world always follow the latest episode (with an optional spoiler
   shield), or follow each player's watched episode? (Section 3.4.)
2. **Gossip:** should characters share what you tell them, and should it be on by default?
3. **Voice:** typed chat only, or spoken replies with the film's voices (and voice input)?
4. **Who is the player?** Their own character in the world (recommended for a platform), or
   playing as cast members in story missions? This changes how characters address you.
5. **Business model:** free with limits, subscription, or both? This decides the per-player
   AI budget.
