# Vira staff character cards

Every one of Vira's 280 staff has a character card: who they are, where they came from, how they talk,
who they love and can't stand, and what they know. The cards are the "canon" layer of each
character's memory (see [ROADMAP_PLATFORM_AND_MEMORY.md](ROADMAP_PLATFORM_AND_MEMORY.md)). They're
written so that, later, these people can talk to the player and to each other and stay themselves.

## Two layers

1. **Facts**: [`game/data/staff/roster.json`](../game/data/staff/roster.json), built by
   [`tools/staff_roster.py`](../tools/staff_roster.py) from the game's own data. These include the name,
   pronouns, age, birthday, look, job, title, supervisor, shift, post, years at Vira, home address,
   commute, neighbors, car and household, plus the relationship web (friends, friction, mentors,
   siblings, cousins, exes, crushes, couples). The game draws these people, so the facts are fixed.
   A card never contradicts them.
2. **The card**: `game/data/staff/cards/<id>.json`, the written life. It's built on the facts.

`python tools/staff_brief.py <id>` prints everything a writer needs for one person: their facts,
their household, everyone they're connected to (with each link's type and any history already
written on the other person's card), their crewmates and their neighbors.

## Canon rules (hard)

- **Lyra.** Most staff think Vira runs on ordinary automation. Only people with `knows_lyra: true`
  (eight senior engineers) know Lyra by name and talk to her. Nobody outside Marcus's circle knows
  about her choices, the dog or the hologram. Everyone else might notice odd things (a gate that
  opened by itself, sprinklers at a strange hour), but they explain them as glitches.
- **The cast.** Marcus works at Vira and rides a motorcycle in from Saltbrush. Staff may know him
  by sight or as a coworker, but nothing personal or plot-related. Staff don't know Solo, Nova,
  Juno or James Dunn unless the user adds that later. Don't invent anything about the cast.
- **Places.** Use only the places in `roster.json → places`, and refer to them generically ("the
  diner in Saltbrush", "the truck stop in Ironwood"). Don't invent business names, towns,
  companies or landmarks. Earlier lives (hometowns, colleges, the military, past employers)
  happened elsewhere, so real-world places are fine there.
- **Vira itself.** It came online in 2019 (an assumption until canon says otherwise). It's a
  hyperscale data center. Don't invent who owns it or what it's for beyond that.
- **Relationships.** Each edge in the roster is canon. If the other person's card already gives
  the history, use it word for word in spirit. If not, write the history and it becomes binding.

## Card format

```json
{
  "id": 72,
  "name": "Nadia Coyle",
  "summary": "Two or three sentences: who this person is at a glance.",
  "backstory": {
    "childhood": "", "family_of_origin": "", "education": "", "before_vira": "",
    "how_they_came_to_vira": "", "turning_points": ["", ""]
  },
  "household_notes": [{ "who": "name or staff id", "note": "what living with them is like" }],
  "personality": {
    "traits": [], "values": [], "fears": [], "humor": "", "temper": "", "quirks": []
  },
  "voice": {
    "how_they_talk": "", "vocabulary": "", "phrases": [], "with_strangers": "", "with_friends": ""
  },
  "daily_life": {
    "workday": "", "after_work": "", "days_off": "", "hobbies": [], "food": "", "music": "",
    "hangouts": []
  },
  "work": {
    "what_they_actually_do": "", "how_good_they_are": "", "how_they_feel_about_the_job": "",
    "opinion_of_vira": "", "ambition": ""
  },
  "relationships": [{ "id": 0, "name": "", "type": "friends", "history": "", "how_they_feel": "" }],
  "inner_life": { "wants": [], "worries": [], "secrets": [], "regrets": "" },
  "health_and_money": { "health": "", "money": "" },
  "beliefs": { "faith": "", "politics": "" },
  "knowledge": {
    "about_vira": "", "about_lyra": "", "about_marcus": "", "rumors_they_believe": []
  },
  "memories": [{ "when": "", "what": "", "with": [0] }],
  "conversation_starters": []
}
```

### Depth

- Write a full life, specific and lived-in. Use concrete details (the truck's cracked dash, the
  daughter's soccer schedule, the debt), not adjectives.
- **Relationships:** cover every roster edge for the person, plus their supervisor and two or three
  notable crewmates or neighbors.
- **Memories:** six to ten, shared with other staff where possible (listing their ids), so people
  have history with each other from day one. Shared memories must also fit the other person's facts.
- **Ordinary people.** Most of them are good at their jobs, a bit tired, funny in their own way and
  carrying something. Avoid making everyone quirky or tragic. Vary politics, faith, temperament and
  education realistically for rural Nevada and California desert towns and a city an hour away.
- **Voice** should be distinct enough that dialogue written from it is recognizable without a name tag.

Validate with `python tools/staff_cards_check.py`.
