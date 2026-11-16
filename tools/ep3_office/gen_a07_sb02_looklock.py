#!/usr/bin/env python3
"""A07 SB02 with full repo look locks: char_ref Marcus age + lyra cyan body."""
from __future__ import annotations
import base64, io, json, shutil, urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie")
OFFICE = ROOT / "assets" / "office_clips"
REFS = ROOT / "assets" / "lyra-refs"
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")
OUT = SB / "A07_sb02_lyra_appears_eyeline.jpg"
BAK = SB / "A07_sb02_before_looklock.jpg"
COMP = SB / "A07_sb02_lyra_appears_eyeline_young.jpg"  # layout fallback
if not COMP.exists():
    COMP = OUT
CHAR = REFS / "char_ref.png"  # Marcus age/wardrobe bible
LYRA_HOLO = REFS / "lh4_lyra_closeup.png"
LYRA_CARD = REFS / "lyra_ref.png"

def load_env():
    env={}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); env[k.strip()]=v.strip()
    return env

def data_url(path, max_side=1300, q=90):
    im=Image.open(path).convert("RGB"); im.thumbnail((max_side,max_side))
    buf=io.BytesIO(); im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode("ascii")

# Crop Marcus head from char_ref left panel for stronger face
im = Image.open(CHAR).convert("RGB")
w,h = im.size
# three panels roughly — left third is closeup
left = im.crop((0, 0, w//3, h))
marcus_crop = SB / "A07_ref_marcus_char_ref_face.jpg"
left.save(marcus_crop, quality=95)

shutil.copy2(OUT, BAK)
key = load_env()["OPENROUTER_API_KEY"]
refs = [p for p in (marcus_crop, LYRA_HOLO, COMP if COMP.exists() else OUT) if p.exists()][:3]
prompt = (
 "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO text. "
 "TIGHT couch two-shot, mutual eyeline, BACKGROUND = ONLY glowing blue DATA SCREEN WALL (no window). "
 "MARCUS (left) FACE+AGE LOCKED to reference 1 / char_ref: late 40s, crow's feet, weathered skin, "
 "salt-and-pepper hair, FULL grey-flecked beard — NOT younger, NOT smooth. "
 "Black leather cafe-racer jacket over grey henley (char_ref wardrobe). "
 "LYRA (right) FACE LOCKED to hologram closeup ref — long wavy chestnut hair, green-hazel eyes. "
 "She is a translucent CYAN hologram with a strong glowing CYAN AURA around her ENTIRE body "
 "(hair, shoulders, arms, torso) + soft scanlines — like lh4/lyra_ref hologram panels. "
 "Seated on couch beside him. Cream/white top ok with cyan fringe. "
 "They look at each other; Marcus calmer pity. No collage."
)
print("refs", [p.name for p in refs], flush=True)
payload={"model":"google/gemini-2.5-flash-image","prompt":prompt,"aspect_ratio":"16:9",
 "input_references":[{"type":"image_url","image_url":{"url":data_url(p)}} for p in refs]}
req=urllib.request.Request("https://openrouter.ai/api/v1/images", data=json.dumps(payload).encode(),
 headers={"Authorization":f"Bearer {key}","Content-Type":"application/json",
 "HTTP-Referer":"https://moviemaker-cloud.local","X-Title":"movieMaker Cloud"}, method="POST")
with urllib.request.urlopen(req, timeout=300) as resp:
    body=json.loads(resp.read().decode())
data=(body.get("data") or [None])[0]
if data.get("b64_json"): OUT.write_bytes(base64.b64decode(data["b64_json"]))
elif data.get("url"):
    with urllib.request.urlopen(data["url"], timeout=120) as img: OUT.write_bytes(img.read())
print(f"OK {OUT.name} cost={float((body.get('usage') or {}).get('cost') or 0)}", flush=True)
