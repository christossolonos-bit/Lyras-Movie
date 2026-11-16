#!/usr/bin/env python3
from __future__ import annotations
import base64, io, json, shutil, urllib.request, urllib.error
from pathlib import Path
from PIL import Image

OFFICE = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\office_clips")
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")
PREV = SB / "A07_sb02_lyra_appears_eyeline.jpg"
BAK = SB / "A07_sb02_lyra_appears_eyeline_v1.jpg"
OUT = PREV
LYRA_HOLO = OFFICE / "ref_lyra_face_holo.jpg"
LYRA_FACE = OFFICE / "ref_lyra_face_solid.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"

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

if PREV.exists():
    shutil.copy2(PREV, BAK)
key=load_env()["OPENROUTER_API_KEY"]
refs=[p for p in (PREV, LYRA_HOLO, MARCUS) if p.exists()][:3]
prompt=(
 "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO text. "
 "KEEP this exact composition: tight couch two-shot, mutual eyeline, screen-wall ONLY behind (no window). "
 "Marcus on left — FACE LOCKED exactly to Marcus face reference (salt-and-pepper, grey beard, same nose/eyes/jaw). "
 "Do NOT change Marcus identity. Leather jacket stays. "
 "Lyra on right seated on couch — FACE LOCKED to hologram/face refs, cream top + patterned scarf. "
 "CRITICAL: Lyra must be a translucent CYAN HOLOGRAM with a clear glowing CYAN AURA / fringe / rim-light "
 "all around her body silhouette (shoulders, arms, hair edges) — soft scanlines, not a solid flesh person with a thin outline. "
 "They look at each other. Marcus calmer pity. Same camera. No collage."
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
