# Lyra series — full 3D atlas

Open `index.html` (needs network once for Three.js CDN). Data: `series-zones.js`. Plates: `refs/`.

Source: [seed0001/Lyras-Movie](https://github.com/seed0001/Lyras-Movie) README sequences + local Ep3 / Nova / Juno / Solo plates.

## Modes

| Mode | Shows |
|------|--------|
| **World** | Campus + interiors + off-site (Marcus / Nova / Juno / Death Valley / Solo Cyprus) |
| **Campus shell** | Exterior massing only |
| **Interiors** | Cutaway story rooms inside Vira |

## Campus exterior (plates `01–10`, `b*`, `pb4–5`, `jd13`)

| Element | Lock |
|---------|------|
| Halls | **~16** white flat-roof blocks in a grid (aerial `05_hero_aerial`) |
| Roofs | Dense HVAC / chillers / pipes (`07_rooftop`) |
| Bridges | Overhead pipe runs between parallel halls (`09_ground_hero`) |
| Solar | Large PV field **north** of halls |
| Substation | HV yard **west** |
| Cooling towers | Steam towers **southeast** |
| Perimeter | Chain-link fence + sliding **gate** + tan booth + yellow bollards |
| Signage | **DATA CENTER** fence sign (`pb5`) |
| Sprinklers | Gravel landscape strip where Lyra waters Patch |
| Bay Three | East hangar + roll-up service door; Dunn rover (cyan sensor eyes) outside |

## Facility interiors (story graph)

```
GATE → LOBBY (pb6) → APPLICANT HALL (ni8)
                  → CYAN CORRIDOR (pb7)
                       ├─ SERVER AISLE (pb8) ↔ MARCUS OFFICE (glass)
                       ├─ PROCESSOR HALL (c1 yellow beams)
                       ├─ MEMORY WALL (st4) / ROMANCE MONITORS (r*)
                       ├─ PROJECTOR OPS (lh1) + PATCH CORNER (pb9)
                       ├─ FAMILY / CLINICAL LAB (ni1)
                       ├─ EP3 COMMAND OFFICE (screen wall / freefwalk)
                       ├─ STAFF BREAK ROOM → corridor (coffee Act B)
                       └─ BAY THREE hangar (bay01 / jd13)
```

**Style tokens:** grey concrete + white panels · **cyan waist LED / access rings** · polished or raised floors · cool interior vs warm desert spill.

## Off-site world

| Place | Plates | Role |
|-------|--------|------|
| Marcus home / garage | `mh*` | 4:47 page · black bike red stripe · sunrise ride to gate |
| Nova hillside villa | `nv*` / `nova_home_ref` | Pool glass house · couch call · desert drive to Vira |
| Juno loft / workshop | `jn*` / `juno_loft_ref` | Trike · welding · projector repair visits |
| Death Valley | `dv*` | Dunes, salt, road, heat wildlife |
| Solo · Cyprus | `src/solo_*`, globe | Origin of coffee guest — distant from Vira |

## Sequences (README)

Orbit approach · 8 billion montage · construction · processors/storage · Death Valley · memory · romance · globe · Marcus wakeup · Patch adoption · hologram · Dunn arrival · (+ Bay Three, office logs, Juno, Nova, Ep3 locally).

## Characters / vehicles in world

- **Lyra** — building AI; hologram on circular projector pad (ops / Bay 3)
- **Marcus** — office + bike commute
- **Dunn** — olive/black rover with cyan eyes into Bay Three
- **Patch** — gate → sprinklers → lobby → servers → bed in ops
- **Nova / Juno / Solo** — off-site homes then Vira interiors
