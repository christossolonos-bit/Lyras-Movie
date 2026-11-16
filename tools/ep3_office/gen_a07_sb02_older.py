#!/usr/bin/env python3
from __future__ import annotations
import base64, io, json, shutil, urllib.request
from pathlib import Path
from PIL import Image

OFFICE = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\office_clips")
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")
PREV = SB / "A07_sb02_lyra_appears_eyeline.jpg"
OUT = PREV
BAK = SB / "A07_sb02_v_softage.jpg"
# Strongest older Marcus stills we have
A05C = OFFICE / "A05c_marcus_what_you_are_last.jpg"
A04D = OFFICE / "A04d_marcus_rest_of_us_last.jpg"
MARCUS = OFFICE / "ref_marcus_face.jpg"
A06FACE = SB / "A07_ref_marcus_a06_face.jpg"

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

shutil.copy2(PREV, BAK)
key=load_env()["OPENROUTER_API_KEY"]
# Prefer A05c / A04d older closeups as face lead; keep PREV only for layout via prompt describe
refs=[]
for p in (A05C if A05C.exists() else None, A06FACE, MARCUS):
    if p and p.exists():
        refs.append(p)
refs=refs[:3]
# If we have A04d use instead of marcus card
if A04D.exists() and len(refs)>=2:
    refs = [A05C if A05C.exists() else A04D, A06FACE if A06FACE.exists() else A04D, PREV][:3]
print("refs",[p.name for p in refs], flush=True)
prompt=(
 "OUTPUT 16:9. NO text. "
 "COMPOSITION like a tight couch two-shot against ONLY blue data SCREEN WALL (no window): "
 "Marcus left, Lyra cyan hologram right with full-body CYAN aura, scarf, mutual eyeline. "
 "IDENTITY LOCK MARCUS: copy the OLDER face from reference images 1–2 exactly — "
 "same weathered late-40s man, deep eye wrinkles, grey beard density, mature cheeks — "
 "DO NOT rejuvenate him, DO NOT de-age, DO NOT smooth skin. He must look identical to A05c/A06 Marcus. "
 "Lyra keeps cyan hologram body glow. Pity calm. No collage."
)
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
