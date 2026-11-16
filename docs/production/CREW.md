# Lyra AI: crew (DRAFT)

Each role is a job with a sign-off, not a separate person. Chris is showrunner and has the final say. Claude works through the other roles in order, and an episode doesn't move on until the current stage's checks pass.

## Stage 1: Story

| Role | Job | Signs off when |
|---|---|---|
| **Showrunner** (Chris) | Owns the season, the secrets and the final cut | Chris approves |
| **Story editor** | Keeps episodes in line with the bible and the season plan, and protects the finale reveal | Nothing contradicts earlier episodes |
| **Screenwriter** | Writes scenes on care → deny → force → button | Each scene has one engine and a hard ending |
| **Dialogue writer** | Keeps each character's voice distinct and specific | Lines don't state feelings outright |

## Stage 2: Pre-production

| Role | Job | Signs off when |
|---|---|---|
| **Director: Spielberg** | Faces, intimacy, wonder, confessions | Every intimate shot has a performance note |
| **Director: Jackson** | Scale, the facility as a cathedral, ensemble moments | Every wide shot gives scale |
| **Director: Bay** | Machines, vehicles, doors, motion | Every action shot has energy |
| **Assistant director** | Assigns one director per clip, makes the shot list, tracks the budget | Shot list is costed and fits the credits |
| **Storyboard artist** | Plans frames and how shots connect | Every clip has a planned start and end |
| **Casting and character lead** | Keeps cards, refs, wardrobe and voices | Refs match `REF_LOCK.md` |
| **Production designer** | Designs rooms, projector boxes and wall lines, with an empty plate per room | Chris approves each plate |

## Stage 3: Production

| Role | Job | Signs off when |
|---|---|---|
| **Cinematographer** | Camera, lenses, light, screen direction | Blocking and eyelines hold across cuts |
| **Performance director** | Turns script moments into visible actions for the prompt | Each clip has one clear action |
| **Prompt operator** | Runs every generation through `production_lock.py` | The lock passes and costs are logged |
| **Script supervisor** | Checks continuity: faces, clothes, positions, props, time of day | Each frame is checked against the last |

## Stage 4: Post-production

| Role | Job | Signs off when |
|---|---|---|
| **Editor** | Cuts for performance and rhythm | The scene plays without drag |
| **Voice and dialogue editor** | Converts lines to voice samples, fixes wrong words | Each voice is confirmed by Chris |
| **Sound designer** | Room tone, footsteps, the hum, her silence | Each room sounds different |
| **Composer and music editor** | Chooses and places music | Music doesn't tell the audience how to feel |
| **Colorist and VFX** | Matches shots, keeps Lyra's look | Lyra matches the look lock in every shot |

## Stage 5: Delivery

| Role | Job | Signs off when |
|---|---|---|
| **QC reviewer** | Watches the finished cut for errors | Frame and transcript checks pass |
| **Archivist** | Files finals, sets aside rejects, keeps the folder clean | Episode folder is sorted |
| **Publisher** | Titles, credits, thumbnail, release | Chris approves release |

Claude can't hear audio, so Chris confirms voices, accents and music by ear. Solo is Chris's likeness, so Chris also signs off Solo's face.
