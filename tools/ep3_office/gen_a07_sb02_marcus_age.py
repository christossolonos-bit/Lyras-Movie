#!/usr/bin/env python3
from __future__ import annotations
import base64, io, json, shutil, urllib.request
from pathlib import Path
from PIL import Image

OFFICE = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\office_clips")
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")
PREV = SB / "A07_sb02_lyra_appears_eyeline.jpg"
BAK = SB / "A07_sb02_lyra_appears_eyeline_young.jpg"
OUT = PREV
# Older Marcus locks — A06 seated face + repo face
A06 = SB / "A07_first_from_a06.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"

def load_env():
    env={}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); env[k.strip()]=v.strip()
    return env

def data_url(path, max_side=1400, q=92):
    im=Image.open(path).convert("RGB"); im.thumbnail((max_side,max_side))
    buf=io.BytesIO(); im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode("ascii")

# Crop Marcus face region from A06 wide for stronger age lock
a06 = Image.open(A06).convert("RGB")
w,h = a06.size
# marcus roughly center of couch
face = a06.crop((int(w*0.35), int(h*0.12), int(w*0.62), int(h*0.55)))
face_path = SB / "A07_ref_marcus_a06_face.jpg"
face.save(face_path, quality=95)
print("face crop", face.size, flush=True)

shutil.copy2(PREV, BAK)
key=load_env()["OPENROUTER_API_KEY"]
# Lead with older Marcus: A06 face crop + marcus ref; keep composition from prev
refs=[p for p in (face_path, MARCUS, PREV) if p.exists()][:3]
prompt=(
 "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO text. "
 "KEEP composition of reference frame 3: tight couch two-shot, mutual eyeline, screen-wall ONLY (no window). "
 "MARCUS FACE LOCK — CRITICAL: he must look the SAME AGE as Marcus in references 1 and 2 — "
 "late 40s / ~48, weathered skin, crow's feet, forehead lines, salt-and-pepper hair going grey, "
 "full grey-flecked beard. NOT younger, NOT smooth-faced, NOT late 30s. "
 "Match the exact older face from the A06 face crop and Marcus face card. Leather jacket. "
 "Lyra: cyan translucent hologram with glowing CYAN AURA around her whole body, scarf + cream top, "
 "face from the two-shot. They look at each other. Pity calm. No collage."
)
print("refs",[p.name for p in refs], flush=True)
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
im=Image.open(OUT)
print(f"OK {OUT.name} {im.size} cost={float((body.get('usage') or {}).get('cost') or 0)}", flush=True)
