# Character reference lock (mandatory)

Source of truth: https://github.com/seed0001/Lyras-Movie

**Always** pass these refs on any still/video that includes the character. Prefer repo files over prompt-only description.

| Character | Repo path | Local cache | Topview fileId (session) |
|-----------|-----------|-------------|---------------------------|
| **Lyra** | `images/lyra_ref.png` (+ face `images/lyra_face_source.png`) | `assets/lyra-refs/lyra_ref.png` | face `be457b34e981477ea6d5f3b9cb443fd4` |
| **Lyra hologram** | `images/lh3_hologram_forms.png`, `lh4_lyra_closeup.png` | `assets/lyra-refs/lh3_*.png` | platform `8e080d10642343b4a491f68cdfe7a592` · closeup `55cdf8cfd1d84e179ec0e1aacf5a6eb6` |
| **Nova** | `images/nova_ref.png` | `assets/lyra-refs/nova_ref.png` · **card** `nova_character_card.jpg` (turnaround) · coffee CU `Episode 2/Coffee clips/B03.1_*` | `00eb971106c94f07a031c9dc5f20c67c` |
| **Marcus** | `images/char_ref.png` | `assets/lyra-refs/char_ref.png` | *(upload when needed)* |
| **Patch** | `images/dog_ref.png` | `assets/lyra-refs/dog_ref.png` | *(upload when needed)* |
| **Solo** | `images/src/solo_closeup_source.png` (+ shop; **never the seafront image, it isn't him**) | `assets/lyra-refs/src_solo_*.png` · **card** `solo_character_card_real.jpg` (real frames only, never generated) · face refs `solo_face_approved.jpg`, `solo_face_portrait.png`, `solo_face_smile.jpg` | closeup `5d3d4fc8a47845c9aacb52cb15e30299` · shop `bab7940209c34ee9b18f360003c8d4f6` · seafront `cc13a2269c9444f39c021d8f9c0dc375` |
| **Juno** | `images/juno_ref.png` (**use cropped single portrait only** — never the 4-panel turnaround as Image1) | `assets/lyra-refs/juno_portrait.png` | `ae0aa346ff8d47fe9d1caeba738e76da` |
| **Projector ops room** | Episode 1 Juno-fixing-projector set (circular floor platform, monitor wall, server racks) | `assets/lyra-juno-room/room_ep1_0940.jpg` (+ `1000` / `1020`) | `18551eccbea642d3a343172a5527e45d` (use as **first frame** for Juno projector scenes) |
| **Staff break room** | Ep2 coffee scene — small room by window, coffee machine, two-seat table, cyan wall strip, desert mountains outside, PA grille in ceiling | `vira_staff_break_room.jpg` · **positions master** `coffee_clips/coffee_master_room_positions.jpg` (Nova L / Solo R) | *(room + blocking bible for coffee scene)* |

**Coffee scene rule:** Character **cards** are identity/wardrobe refs only — never use the 4-view turnaround alone as H3 Image1/first_frame (opens on the sheet). Prefer B03.1 / seated masters for first frames.

## Juno / projector scene lock
- **Always** match the Episode 1 ops room where Juno fixes Lyra’s floor projector: circular brushed-metal platform, open side panel / tools / boards, curved blue monitor wall, glass server racks, cool industrial lighting.
- Pass room still as `<<<Image2>>>` (or Image3 if Lyra face is Image2) on every Juno dialogue clip in that set.
- Never use the 4-panel `juno_ref.png` turnaround as the sole Image1 — H3 will open the video on that sheet.
| **James Dunn** | `images/james_dunn_ref.png` | *(download when needed)* | *(upload when needed)* |

## Generation rules
1. **Never** invent a new face for Lyra / Nova / Solo / Marcus / Juno / Dunn / Patch.
2. For Topview MiniMax H3 `omni_reference`: pass `inputImages` with `name` exactly `Image1`, `Image2`, … matching prompt tags `<<<Image1>>>`, `<<<Image2>>>` (arbitrary names fail). Lyra=`Image1`, Nova=`Image2` by convention in two-hander scenes.
3. Lyra look lock (from repo README): long wavy chestnut hair, green-hazel eyes, deep teal top; cyan hologram / projector platform.
4. Re-download from GitHub if local cache is missing; do not substitute Midjourney-style “close enough” faces.
