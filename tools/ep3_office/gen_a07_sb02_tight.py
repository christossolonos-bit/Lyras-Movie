#!/usr/bin/env python3
from __future__ import annotations
import base64, io, json, urllib.request, urllib.error
from pathlib import Path
from PIL import Image

OFFICE = Path(r"D:\Music for distrokid\Solo Stories\Lyra AI movie\assets\office_clips")
SB = OFFICE / "a05_storyboard"
ENV = Path(r"d:\movie maker\.env")
OUT = SB / "A07_sb02_lyra_appears_eyeline.jpg"
CROP = SB / "A07_a06_crop_screenwall.jpg"
LYRA_LOOK = OFFICE / "ref_lyra_ots_scarf.png"
LYRA_FACE = OFFICE / "ref_lyra_face_solid.jpg"

def load_env():
    env={}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); env[k.strip()]=v.strip()
    return env

def data_url(path, max_side=1400, q=90):
    im=Image.open(path).convert("RGB"); im.thumbnail((max_side,max_side))
    buf=io.BytesIO(); im.save(buf, format="JPEG", quality=q)
    return "data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode("ascii")

key=load_env()["OPENROUTER_API_KEY"]
refs=[p for p in (CROP, LYRA_LOOK if LYRA_LOOK.exists() else LYRA_FACE, LYRA_FACE) if p.exists()][:3]
prompt=(
 "OUTPUT 16:9 landscape full-bleed. NO letterbox. NO text. "
 "TIGHT MEDIUM two-shot on the couch — BACKGROUND is ONLY the glowing blue DATA SCREEN WALL behind them. "
 "FORBIDDEN: city window, skyline, desk, chairs, open room wing, floor expanse. "
 "Marcus seated left/center in leather jacket (same man as crop ref). "
 "Lyra cyan translucent hologram SITS ON THE COUCH beside him (hips on cushion, not floating bust) — "
 "cream top + patterned scarf, living hologram with soft scanlines, FACE locked to Lyra refs. "
 "CRITICAL: they LOOK AT EACH OTHER — mutual eyeline, faces both readable, intimate. "
 "Marcus calmer pity. Camera eye-level close to faces. No collage."
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
im=Image.open(OUT); print(f"OK {OUT.name} {im.size} cost={float((body.get('usage') or {}).get('cost') or 0)}", flush=True)
# also copy crop as sb01 lock
(SB/"A07_sb01_marcus_screenwall.jpg").write_bytes(CROP.read_bytes())
print("sb01 <- crop", flush=True)
