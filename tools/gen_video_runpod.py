"""Generate a video with self-hosted MiniMax H3 (FL2VA) on the RunPod ComfyUI pod.
Same CLI as gen_video.py, so scene scripts can swap it in:
Usage: python tools/gen_video_runpod.py <out_name> "<prompt>" [--first img] [--last img]
       [--duration 8] [--aspect 16:9] [--audio] [--turbo] [--steps N] [--seed N]
Native output is 768p (1344x768 for 16:9). Without --audio the audio track is dropped.
--turbo uses the lightx2v 8-step LoRA (much faster, some quality loss); default is the full 20 steps.
"""
import argparse, json, pathlib, random, sys, time, urllib.request, urllib.error, urllib.parse, uuid

ROOT = pathlib.Path(__file__).resolve().parent.parent
POD = (ROOT / ".runpod_pod").read_text().strip()
BASE = f"https://{POD}-8188.proxy.runpod.net"
SIZES = {"16:9": (1344, 768), "9:16": (768, 1344), "1:1": (1024, 1024), "4:3": (1184, 896), "21:9": (1536, 640)}

p = argparse.ArgumentParser()
p.add_argument("name"); p.add_argument("prompt")
p.add_argument("--first"); p.add_argument("--last")
p.add_argument("--duration", type=float, default=8)
p.add_argument("--aspect", default="16:9")
p.add_argument("--audio", action="store_true")
p.add_argument("--turbo", action="store_true")
p.add_argument("--steps", type=int)
p.add_argument("--seed", type=int, default=random.randint(1, 2**48))
p.add_argument("--model"); p.add_argument("--res")  # accepted for gen_video.py compatibility, ignored
a = p.parse_args()

def http(path, data=None, headers=None):
    req = urllib.request.Request(BASE + path, data=data, headers={"User-Agent": "Mozilla/5.0 lyra-movie", **(headers or {})})
    try:
        return urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {path}: {e.read().decode()[:1500]}")

def upload(path):
    b = uuid.uuid4().hex
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{a.name}_{pathlib.Path(path).name}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + open(path, "rb").read() + \
           f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    return json.load(http("/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={b}"}))["name"]

w, h = SIZES[a.aspect]
f = max(5, round(a.duration * 24)); length = f + (5 - f % 17) % 17   # 17k+5 frame grid at 24fps (from the official template)
steps = a.steps or (8 if a.turbo else 20)
model = ["6", 0]
g = {
  "6":  {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
  "13": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
  "11": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
  "104": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["13", 0], "vae": ["11", 0], "prompt": a.prompt,
          "width": w, "height": h, "length": length}},
  "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": a.seed}},
  "17": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
  "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["15", 0], "guider": ["16", 0], "sampler": ["17", 0],
         "sigmas": ["9", 0], "latent_image": ["104", 1]}},
  "10": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["11", 0]}},
  "91": {"class_type": "CreateVideo", "inputs": {"images": ["10", 0], "fps": 24}},
  "92": {"class_type": "SaveVideo", "inputs": {"video": ["91", 0], "filename_prefix": f"lyra/{a.name}", "format": "auto", "codec": "auto"}},
}
if a.turbo:
    g["121"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["6", 0],
                "lora_name": "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors", "strength_model": 1.0}}
    model = ["121", 0]
g["9"] = {"class_type": "BasicScheduler", "inputs": {"model": model, "scheduler": "simple", "steps": steps, "denoise": 1.0}}
g["16"] = {"class_type": "BasicGuider", "inputs": {"model": model, "conditioning": ["104", 0]}}
if a.audio:
    g["24"] = {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}}
    g["23"] = {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["14", 0], "vae": ["24", 0]}}
    g["91"]["inputs"]["audio"] = ["23", 0]
for key, node in (("first_frame", "30"), ("last_frame", "31")):
    src = getattr(a, key.split("_")[0])
    if src:
        g[node] = {"class_type": "LoadImage", "inputs": {"image": upload(src)}}
        g["104"]["inputs"][key] = [node, 0]

t0 = time.time()
pid = json.load(http("/prompt", json.dumps({"prompt": g, "client_id": "lyra"}).encode(), {"Content-Type": "application/json"}))["prompt_id"]
print(a.name, "queued", pid, f"{w}x{h} {length}f steps={steps} seed={a.seed}", flush=True)
while True:
    time.sleep(10)
    hist = json.load(http(f"/history/{pid}")).get(pid)
    if not hist: continue
    st = hist.get("status", {})
    if st.get("status_str") == "error":
        sys.exit(f"{a.name} FAILED: " + json.dumps(st.get("messages"))[:2000])
    if st.get("completed"): break
vids = [v for o in hist["outputs"].values() for k in ("images", "videos", "gifs") for v in o.get(k, [])]
v = vids[0]
q = urllib.parse.urlencode({"filename": v["filename"], "subfolder": v.get("subfolder", ""), "type": v.get("type", "output")})
out = ROOT / "videos" / f"{a.name}.mp4"; out.parent.mkdir(exist_ok=True)
out.write_bytes(http(f"/view?{q}").read())
print(a.name, "saved", out, f"| {time.time() - t0:.0f}s on pod", flush=True)
