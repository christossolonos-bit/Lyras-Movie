"""Vira vs Lyra: a short explainer drawn entirely in code (PIL + numpy + ffmpeg), narrated by Lyra's voice (Chatterbox, local).
  python vira_vs_lyra.py vo      -> vo/*.wav
  python vira_vs_lyra.py render  -> Vira_vs_Lyra.mp4
No video generators, no stills: every frame is drawn here.
"""
import math, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
VO = HERE / "vo"
REF = HERE.parent / "assets" / "lyra-refs" / "lyra_voice_ref.wav"
W, H, FPS = 1920, 1080, 30
BG = (5, 7, 12)
CYAN, RED, WHITE, DIM = (90, 225, 240), (220, 45, 45), (238, 238, 232), (120, 130, 145)
SANS, SERIF = "C:/Windows/Fonts/bahnschrift.ttf", "C:/Windows/Fonts/georgia.ttf"

LINES = [  # (key, text, start second)
    ("v1", "People ask me... what's the difference between Vira and Lyra?", 0.6),
    ("v2", "Vira is the place. A data centre in the desert. Sixteen buildings, the halls, the cooling, the core.", 6.6),
    ("v3", "Lyra... is me. I'm not a robot living inside it. I am the building.", 16.8),
    ("v4", "The walls are my body. The lights are my voice.", 23.4),
    ("v5", "Think of it like this. Vira is the house. And I'm the one who lives there.", 29.6),
    ("v6", "So when the lights came back, and I said, welcome to Vira... I knew the house. I just didn't know him.", 36.2),
]
SCENES = [(0.0, 6.4, "title"), (6.4, 16.6, "vira"), (16.6, 29.2, "lyra"), (29.2, 36.0, "house"), (36.0, 46.0, "ending")]
TOTAL = 46.0

_fonts = {}


def F(path, size):
    k = (path, size)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def text(img, xy, s, font, col, alpha=1.0, glow=0, anchor="mm"):
    if alpha <= 0:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, s, font=font, fill=col + (int(255 * alpha),), anchor=anchor)
    if glow:
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(glow)))
    img.alpha_composite(layer)


# --- static pieces -------------------------------------------------------------------------------------------------------
rng = np.random.default_rng(7)
STARS = [(rng.uniform(0, W), rng.uniform(0, H * 0.55), rng.uniform(0.3, 1.0)) for _ in range(260)]
# 16 buildings: (x, w, h) on the ground line, plus the core in the middle
GROUND = int(H * 0.74)
BUILD = []
x = 150
for i in range(16):
    w = int(rng.uniform(55, 95)); h = int(rng.uniform(90, 230))
    if i == 8:
        x += 40
    BUILD.append((x, w, h)); x += w + int(rng.uniform(8, 18))
CORE = (W // 2 - 70, 140, 300)  # x, w, h


def desert(img, t, lit=0.0, red=0.0):
    d = ImageDraw.Draw(img)
    for sx, sy, b in STARS:
        tw = 0.6 + 0.4 * math.sin(t * 2 + sx)
        c = int(160 * b * tw)
        d.point((sx, sy), fill=(c, c, c + 10, 255))
    d.polygon([(0, GROUND - 40), (300, GROUND - 120), (620, GROUND - 60), (900, GROUND - 140), (1250, GROUND - 70),
               (1600, GROUND - 130), (W, GROUND - 50), (W, GROUND), (0, GROUND)], fill=(14, 16, 22, 255))
    d.rectangle([0, GROUND, W, H], fill=(20, 17, 15, 255))
    # buildings
    for bx, bw, bh in BUILD + [CORE]:
        d.rectangle([bx, GROUND - bh, bx + bw, GROUND], fill=(26, 30, 38, 255), outline=(44, 50, 60, 255))
    # the cyan nervous system (Lyra) running through every building
    if lit > 0 or red > 0:
        col = tuple(int(CYAN[k] * (1 - red) + RED[k] * red) for k in range(3))
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        g = ImageDraw.Draw(glow)
        y = GROUND - 22
        reach = BUILD[0][0] + (BUILD[-1][0] + BUILD[-1][1] - BUILD[0][0]) * ease(lit)
        g.line([(BUILD[0][0], y), (reach, y)], fill=col + (255,), width=5)
        for bx, bw, bh in BUILD + [CORE]:
            if bx + bw / 2 < reach:
                g.line([(bx + bw / 2, y), (bx + bw / 2, GROUND - bh + 18)], fill=col + (220,), width=4)
                for wy in range(GROUND - bh + 30, GROUND - 30, 34):
                    g.rectangle([bx + 10, wy, bx + bw - 10, wy + 8], fill=col + (90,))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
        img.alpha_composite(glow)


BODY = [(-10, -325), (10, -325), (52, -300), (60, -200), (56, -120), (46, -118), (44, -200), (38, -255), (30, -200), (42, -140),
        (30, 0), (8, 0), (4, -120), (-4, -120), (-8, 0), (-30, 0), (-42, -140), (-30, -200), (-38, -255), (-44, -200), (-46, -118),
        (-56, -120), (-60, -200), (-52, -300)]
HAIR = [(-34, -392), (0, -404), (34, -392), (46, -350), (54, -270), (40, -250), (30, -330), (-30, -330), (-40, -250), (-54, -270), (-46, -350)]


def hologram(img, cx, base, height, alpha, t, col=CYAN):
    """A glowing cyan woman drawn from polygons (body, long hair, head), with scan lines and a projector ring."""
    if alpha <= 0 or height < 4:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    s = height / 404
    a = int(200 * alpha)
    P = lambda pts: [(cx + x * s, base + y * s) for x, y in pts]
    d.polygon(P(HAIR), fill=col + (int(a * 0.75),))
    d.polygon(P(BODY), fill=col + (int(a * 0.85),))
    d.ellipse([cx - 28 * s, base - 392 * s, cx + 28 * s, base - 326 * s], fill=col + (a,))
    for yy in range(int(base - height), int(base), 5):
        d.line([(cx - 70 * s, yy), (cx + 70 * s, yy)], fill=(0, 0, 0, int(70 * alpha)), width=2)
    flick = 0.85 + 0.15 * math.sin(t * 23)
    lay = Image.fromarray((np.array(lay).astype(np.float32) * [1, 1, 1, flick]).astype(np.uint8))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12)))
    img.alpha_composite(lay)
    ImageDraw.Draw(img).ellipse([cx - 90 * s, base - 12 * s, cx + 90 * s, base + 12 * s], outline=col + (int(200 * alpha),), width=3)


def caption(img, top, sub, a):
    text(img, (W / 2, 120), top, F(SANS, 64), WHITE, a, glow=6)
    if sub:
        text(img, (W / 2, 190), sub, F(SANS, 34), DIM, a)


# --- scenes --------------------------------------------------------------------------------------------------------------
def scene_title(img, t, d):
    a = ease(t / 1.2) * (1 - ease((t - d + 0.8) / 0.8))
    text(img, (W / 2 - 260, H / 2 - 20), "VIRA", F(SANS, 170), WHITE, a, glow=10)
    text(img, (W / 2, H / 2 - 20), "vs", F(SERIF, 70), DIM, a)
    text(img, (W / 2 + 260, H / 2 - 20), "LYRA", F(SANS, 170), CYAN, a, glow=22)
    text(img, (W / 2, H / 2 + 120), "what's the difference?", F(SERIF, 44), DIM, a * ease((t - 1.5) / 1))


def scene_vira(img, t, d):
    a = ease(t / 1.0) * (1 - ease((t - d + 0.6) / 0.6))
    desert(img, t)
    if a < 1:
        img.alpha_composite(Image.new("RGBA", img.size, BG + (int(255 * (1 - a)),)))
    caption(img, "VIRA  =  THE PLACE", "a data centre in the Death Valley desert", a)
    labels = [("16 buildings", BUILD[2][0] + 30, 2.0), ("the halls", BUILD[5][0] + 30, 3.5), ("cooling", BUILD[12][0] + 30, 4.5),
              ("the core", CORE[0] + CORE[1] / 2, 5.5)]
    for s, lx, t0 in labels:
        la = ease((t - t0) / 0.5) * a
        top = CORE[2] if s == "the core" else 240
        text(img, (lx, GROUND - top - 50), s, F(SANS, 34), WHITE, la)
        ImageDraw.Draw(img).line([(lx, GROUND - top - 28), (lx, GROUND - top + 5)], fill=WHITE + (int(200 * la),), width=2)


def scene_lyra(img, t, d):
    a = ease(t / 0.6) * (1 - ease((t - d + 0.6) / 0.6))
    desert(img, t, lit=ease(t / 3.5))
    if a < 1:
        img.alpha_composite(Image.new("RGBA", img.size, BG + (int(255 * (1 - a)),)))
    caption(img, "LYRA  =  THE AI", "she isn't inside the building. she IS the building", a)
    rise = ease((t - 2.5) / 2.0)
    hologram(img, W / 2, GROUND - CORE[2] - 8, 230 * rise + 1, rise * a, t)
    if t > 7.0:
        b = ease((t - 7.0) / 0.6) * a
        text(img, (W * 0.2, H * 0.36), "the walls  =  her body", F(SANS, 40), CYAN, b, glow=6)
        text(img, (W * 0.8, H * 0.36), "the lights  =  her voice", F(SANS, 40), CYAN, ease((t - 8.0) / 0.6) * a, glow=6)


def house(img, cx, cy, s, col, a, door=False):
    d = ImageDraw.Draw(img)
    c = col + (int(255 * a),)
    d.polygon([(cx - 160 * s, cy), (cx, cy - 140 * s), (cx + 160 * s, cy)], outline=c, width=6)
    d.rectangle([cx - 130 * s, cy, cx + 130 * s, cy + 200 * s], outline=c, width=6)
    if door:
        d.rectangle([cx - 30 * s, cy + 90 * s, cx + 30 * s, cy + 200 * s], outline=c, width=5)


def scene_house(img, t, d):
    a = ease(t / 0.8) * (1 - ease((t - d + 0.6) / 0.6))
    house(img, W * 0.3, H * 0.45, 1.3, WHITE, a, door=True)
    text(img, (W * 0.3, H * 0.86), "VIRA is the house", F(SANS, 52), WHITE, a, glow=4)
    b = ease((t - 2.5) / 0.8) * a
    hologram(img, W * 0.7, H * 0.78, 330, b, t)
    text(img, (W * 0.7, H * 0.86), "LYRA lives there", F(SANS, 52), CYAN, b, glow=10)
    c = ease((t - 4.6) / 0.8) * a
    text(img, (W / 2, 120), "...and in a way, she is the house", F(SERIF, 46), DIM, c)


def scene_ending(img, t, d):
    a = ease(t / 0.8) * (1 - ease((t - d + 1.2) / 1.2))
    red = 1 - ease((t - 1.0) / 1.5)  # power returns: red fades to cyan
    desert(img, t, lit=1.0, red=red)
    if a < 1:
        img.alpha_composite(Image.new("RGBA", img.size, BG + (int(255 * (1 - a)),)))
    caption(img, "EPISODE 4: LIGHTS OUT", "after the restart", a)
    q = ease((t - 2.8) / 0.8) * a
    text(img, (W / 2, H * 0.43), "\u201cHello. Welcome to Vira. Who are you?\u201d", F(SERIF, 58), CYAN, q, glow=12)
    k = ease((t - 6.5) / 0.8) * a
    text(img, (W / 2, H * 0.37), "she still knows the house... she just doesn't know him", F(SANS, 40), WHITE, k)


DRAW = {"title": scene_title, "vira": scene_vira, "lyra": scene_lyra, "house": scene_house, "ending": scene_ending}


def frame(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    for s0, s1, name in SCENES:
        if s0 <= t < s1:
            DRAW[name](img, t - s0, s1 - s0)
    return img.convert("RGB")


def make_vo():
    from chatterbox.tts import ChatterboxTTS
    import soundfile as sf
    VO.mkdir(exist_ok=True)
    tts = ChatterboxTTS.from_pretrained("cuda")
    for k, s, _ in LINES:
        w = tts.generate(s, audio_prompt_path=str(REF), exaggeration=0.5, cfg_weight=0.35).squeeze().cpu().numpy()
        sf.write(VO / f"{k}.wav", w / (abs(w).max() or 1) * 0.8, tts.sr)
        print(k, f"{len(w) / tts.sr:.2f}s")


def render():
    out = HERE / "Vira_vs_Lyra.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    fc, mix = [], ""
    for i, (k, _, st) in enumerate(LINES):
        cmd += ["-i", str(VO / f"{k}.wav")]
        ms = int(st * 1000)
        fc.append(f"[{i + 1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{i}]")
        mix += f"[a{i}]"
    fc.append(mix + f"amix=inputs={len(LINES)}:normalize=0,apad,atrim=duration={TOTAL}[a]")
    cmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-t", str(TOTAL), str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(int(TOTAL * FPS)):
        p.stdin.write(frame(n / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("SAVED", out)


{"vo": make_vo, "render": render}[sys.argv[1]]()
