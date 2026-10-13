# Lyra's Movie

An AI-generated short film narrated by **Lyra**, the AI that lives inside the **Vira** hyperscale data center in the desert. Lyra speaks about the eight billion people she learns from, and the people who take care of her.

All stills are generated with image models and then animated into silent clips with Veo 3.1 via OpenRouter. Lyra's narration is recorded separately (ElevenLabs) and added in the edit.

> Rendered videos and API keys are not included in this repo.

## Characters

- **Lyra**: the AI. Narrator. Speaks to Marcus through the facility intercom and appears as a cyan hologram on a projector platform. Long wavy chestnut hair, green-hazel eyes, deep teal top. Character reference: [`images/lyra_ref.png`](images/lyra_ref.png) (source face: [`images/lyra_face_source.png`](images/lyra_face_source.png))
- **Marcus Hale**: 48, lead data scientist at Vira. Salt-and-pepper hair, grey-flecked stubble, black leather jacket, rides a matte-black sport bike with a red stripe. Character reference: [`images/char_ref.png`](images/char_ref.png)
- **Colonel James Dunn**: U.S. Army colonel who works with Lyra. Marcus's best friend for over 30 years; they've worked on many projects together. Shaved bald head, ruddy complexion, hazel-brown eyes, light stubble, heavyset build, OCP camouflage uniform. Character reference: [`images/james_dunn_ref.png`](images/james_dunn_ref.png) (source face: [`images/james_dunn_face_source.jpg`](images/james_dunn_face_source.jpg)). Drives an AI-integrated armored prototype rover (black and olive, glowing cyan sensor eyes): [`images/dunn_vehicle_ref.png`](images/dunn_vehicle_ref.png)
- **The pit bull**: a white stray with a grey patch around his right eye. He wanders up to the data center in the desert heat, and Lyra takes him in. Character reference: [`images/dog_ref.png`](images/dog_ref.png)

## Sequences

| Storyboard | Prefix | Content |
|---|---|---|
| [scene1_datacenter_storyboard](storyboards/scene1_datacenter_storyboard.jpg) | `01`–`10` | From space through the clouds and mountains down to the desert data center |
| [montage_8billion](storyboards/montage_8billion.jpg) | `m*` | "Eight billion of you": living, working, love, heartbreak, bad decisions |
| [construction](storyboards/construction.jpg) | `b*` | Building the data center: grading, steel, finishing |
| — | `c*` | Inside: processors, storage |
| [death_valley](storyboards/death_valley.jpg) | `dv*` | Desert heat: dunes, salt flats, road, roadrunner, lizard |
| [storage_memory](storyboards/storage_memory.jpg) | `st*` | Storage and memory: drives, platters, fiber, memory wall |
| [romance](storyboards/romance.jpg) | `r*` | Romance: heart LEDs, a rose on a server, books, monitor wall |
| — | `t*` | Reaching out: the globe at night |
| [marcus_wakeup](storyboards/marcus_wakeup.jpg) | `mh*` | Marcus is paged at 4:47 AM, rides through the desert at sunrise, and is greeted by Lyra |
| [pitbull_adoption](storyboards/pitbull_adoption.jpg) | `pb*` | *Filler scene.* Lyra spots a stray pit bull on the security cameras, opens the gate, turns on the sprinklers for him, lets him inside to cool down, and adopts him |
| [lyra_hologram](storyboards/lyra_hologram.jpg) | `lh*` | Lyra appears to Marcus as a hologram, the dog is revealed, and Marcus realizes the decision log shows nobody asked her to open the gate |
| [dunn_arrival](storyboards/dunn_arrival.jpg) | `jd*` | *Standalone scene.* James off-roads the prototype rover around the facility, Lyra flags an unidentified vehicle outside the perimeter, Marcus walks out to the gate, recognizes James, and has him bring it into a service bay |

Narration: [`script/marcus_narration.md`](script/marcus_narration.md)

## Tools

- `tools/gen_image.py`: generate a still via OpenRouter (supports `--ref` images for character consistency)
- `tools/gen_video.py`: animate a still into a clip (Veo 3.1, audio off by default)
- `tools/montage_stills.sh`, `tools/scene_marcus_stills.sh`, `tools/scene_marcus_videos.sh`, `tools/scene_pitbull_stills.sh`, `tools/scene_pitbull_videos.sh`, `tools/scene_hologram_stills.sh`, `tools/scene_dunn_arrival_stills.sh`: per-scene batch scripts

To run them, create a `.env` in the project root:

```
OPENROUTER_API_KEY=your-key-here
IMAGE_MODEL=google/gemini-3.1-flash-image
```
