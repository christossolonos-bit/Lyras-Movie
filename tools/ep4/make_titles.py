"""Episode 4 title card and end credits, drawn locally (PIL + ffmpeg, free).
  python make_titles.py title     -> Extras/Ep4_title.mp4    (cyan title flickers and dies to red)
  python make_titles.py credits   -> Extras/Ep4_credits.mp4  (cast cards with Ep4 stills, cast plate, producers)
No music: Chris lays his own track under the credits.
"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

E4 = Path(__file__).resolve().parent
FR, OUT = E4 / "Frames", E4 / "Extras"
TMP = OUT / "cards"; TMP.mkdir(parents=True, exist_ok=True)
W, H = 1920, 1080
BG = (5, 7, 10)
CYAN, RED, WHITE = (90, 225, 240), (220, 40, 40), (238, 238, 232)
SANS = "C:/Windows/Fonts/bahnschrift.ttf"
SERIF = "C:/Windows/Fonts/georgia.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def glow_text(img, xy, text, f, color, glow=18, anchor="mm", spacing=0):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=f, fill=color + (255,), anchor=anchor, spacing=spacing)
    blur = layer.filter(ImageFilter.GaussianBlur(glow))
    img.alpha_composite(blur)
    img.alpha_composite(blur)
    img.alpha_composite(layer)


def spaced(text, n=1):
    return (" " * n).join(text)


def vignette(img, color, strength=70):
    v = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    d.ellipse([W * 0.15, H * 0.2, W * 0.85, H * 0.95], fill=color + (strength,))
    img.alpha_composite(v.filter(ImageFilter.GaussianBlur(220)))


def title_frame(color, on=True):
    img = Image.new("RGBA", (W, H), BG + (255,))
    if on:
        vignette(img, color, 45)
        glow_text(img, (W / 2, H / 2 - 60), spaced("LYRA", 2), font(SANS, 230), color, glow=26)
        d = ImageDraw.Draw(img)
        d.rectangle([W / 2 - 260, H / 2 + 95, W / 2 + 260, H / 2 + 99], fill=color + (255,))
        glow_text(img, (W / 2, H / 2 + 170), spaced("EPISODE 4  ·  LIGHTS OUT"), font(SANS, 54), WHITE, glow=6)
    return img.convert("RGB")


def make_title():
    paths = {}
    for name, col, on in [("cyan", CYAN, True), ("red", RED, True), ("off", CYAN, False)]:
        p = TMP / f"title_{name}.png"; title_frame(col, on).save(p); paths[name] = p
    # timeline: cyan 0-3.4, flicker 3.4-4.3, red 4.3-7.4, fade out by 8.0
    seq = [("cyan", 3.4), ("off", 0.12), ("cyan", 0.08), ("off", 0.2), ("cyan", 0.06), ("off", 0.44), ("red", 3.7)]
    lst = TMP / "title_seq.txt"
    lst.write_text("".join(f"file '{paths[n].as_posix()}'\nduration {d}\n" for n, d in seq) + f"file '{paths['red'].as_posix()}'\n")
    out = OUT / "Ep4_title.mp4"
    total = sum(d for _, d in seq)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-vf", f"fps=30,format=yuv420p,fade=t=in:st=0:d=0.8,fade=t=out:st={total - 0.8:.2f}:d=0.8", "-t", f"{total:.2f}",
                    "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-shortest", str(out)], check=True)
    print("SAVED", out, f"{total:.1f}s")


CAST = [  # (character, still, crop box as fractions l,t,r,b of the still)
    ("SOLO", "I8_v1_sheet.png", None),
]
CARDS = [
    ("SOLO", FR / "I2_solo_core_frame_v1.png", (0.25, 0.0, 0.85, 1.0)),
    ("LYRA", FR / "I9_lyra_hologram_frame_v1.png", (0.0, 0.0, 0.6, 1.0)),
    ("MARCUS HALE", FR / "G3_marcus_core_frame_v1.png", (0.4, 0.0, 1.0, 1.0)),
    ("NOVA", FR / "F6_nova_rack_frame_v1.png", (0.08, 0.0, 0.68, 1.0)),
    ("JUNO", FR / "F11_juno_pipes_frame_v1.png", (0.05, 0.0, 0.65, 1.0)),
    ("PATRIK", FR / "D6_patrik_ops_frame_v1.png", (0.0, 0.0, 0.6, 1.0)),
    ("COLONEL JAMES DUNN", FR / "H2_james_corridor_frame_v1.png", (0.4, 0.0, 1.0, 1.0)),
    ("PATCH", FR / "G2_solo_kneel_frame_v1.png", (0.12, 0.48, 0.58, 1.0)),
]


def cast_card(name, still, box, i):
    img = Image.new("RGBA", (W, H), BG + (255,))
    s = Image.open(still).convert("RGB")
    l, t, r, b = box
    s = s.crop((int(s.width * l), int(s.height * t), int(s.width * r), int(s.height * b)))
    ph = H; pw = int(s.width * ph / s.height)
    s = s.resize((pw, ph), Image.LANCZOS)
    left = i % 2 == 0  # alternate sides
    x0 = 0 if left else W - pw
    mask = Image.new("L", (pw, ph), 255)
    md = ImageDraw.Draw(mask)
    fadew = int(pw * 0.45)
    for k in range(fadew):  # fade the inner edge into black
        a = int(255 * k / fadew)
        x = pw - 1 - k if left else k
        md.line([(x, 0), (x, ph)], fill=a)
    img.paste(s, (x0, 0), mask)
    tx = W * 0.72 if left else W * 0.28
    size = 120
    while font(SERIF, size).getlength(spaced(name)) > W * 0.48:
        size -= 4
    glow_text(img, (tx, H / 2 - 20), spaced(name), font(SERIF, size), WHITE, glow=10)
    d = ImageDraw.Draw(img)
    d.rectangle([tx - 140, H / 2 + 70, tx + 140, H / 2 + 73], fill=CYAN + (255,))
    return img.convert("RGB")


def text_card(lines, path):
    img = Image.new("RGBA", (W, H), BG + (255,))
    vignette(img, CYAN, 30)
    y = H / 2 - (len(lines) - 1) * 45
    for txt, size, col in lines:
        glow_text(img, (W / 2, y), txt, font(SERIF if col == WHITE else SANS, size), col, glow=8)
        y += 90 if size > 40 else 70
    img.convert("RGB").save(path)


def cast_plate(path):
    img = Image.new("RGBA", (W, H), BG + (255,))
    vignette(img, CYAN, 35)
    glow_text(img, (W / 2, H / 2), spaced("CAST", 2), font(SANS, 60), CYAN, glow=12)
    names = [n for n, _, _ in CARDS]
    left, right = names[:4], names[4:]
    for col, xs in [(left, W / 2 - 330), (right, W / 2 + 330)]:
        y = H / 2 - 165
        for n in col:
            glow_text(img, (xs, y), n, font(SERIF, 52), WHITE, glow=6)
            y += 110
    img.convert("RGB").save(path)


def make_credits():
    clips = []
    def clip_from(png, dur, name, push=True):
        out = TMP / f"{name}.mp4"
        z = "zoompan=z='min(zoom+0.0006,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps=30".format(n=int(dur * 30))
        vf = (z + "," if push else "") + f"format=yuv420p,fade=t=in:st=0:d=0.8,fade=t=out:st={dur - 0.8:.2f}:d=0.8"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                        "-vf", vf, "-t", str(dur), "-r", "30", "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-shortest", str(out)], check=True)
        clips.append(out)
    p = TMP / "c00_lyra.png"
    text_card([(spaced("LYRA", 2), 150, CYAN), (spaced("EPISODE 4  ·  LIGHTS OUT"), 44, WHITE)], p); clip_from(p, 6, "c00")
    for i, (name, still, box) in enumerate(CARDS):
        p = TMP / f"c{i + 1:02d}.png"; cast_card(name, still, box, i).save(p); clip_from(p, 8, f"c{i + 1:02d}")
    p = TMP / "c20_cast.png"; cast_plate(p); clip_from(p, 8, "c20", push=False)
    p = TMP / "c21_prod.png"
    text_card([(spaced("PRODUCED BY"), 40, CYAN), ("BOLLENBACH PRODUCTIONS", 58, WHITE), ("SOLONARAS PRODUCTIONS", 58, WHITE),
               ("BACK CHANNEL PRODUCTIONS", 58, WHITE)], p); clip_from(p, 8, "c21", push=False)
    lst = TMP / "credits.txt"
    lst.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips))
    out = OUT / "Ep4_credits.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], check=True)
    print("SAVED", out)


{"title": make_title, "credits": make_credits}[sys.argv[1]]()
