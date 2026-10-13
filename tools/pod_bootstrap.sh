#!/bin/bash
# Runs ON the RunPod pod: installs ComfyUI (CUDA 13 torch) + MiniMax H3 FL2VA weights on the pod's LOCAL disk (/root/lyra)
# and starts ComfyUI on :8188. No network volume. Safe to re-run. Log: /root/bootstrap.log
set -e
B=/root/lyra; mkdir -p $B; cd $B
[ -x $B/venv/bin/python ] || python -m venv $B/venv
V=$B/venv/bin
( # weights download in parallel with the Python install
  $V/pip install -q huggingface_hub
  $V/python - <<'PY'
import os, time
from huggingface_hub import hf_hub_download
t = time.time()
for f in ["diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
          "text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
          "vae/minimax_h3_audio_vae_fp32.safetensors",
          "vae/minimax_h3_video_vae_int8_convrot.safetensors",
          "loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"]:
    p = hf_hub_download("Comfy-Org/MiniMax-H3", f, local_dir="/root/lyra/hf")
    print("OK", f, os.path.getsize(p) >> 20, "MiB", f"{time.time()-t:.0f}s", flush=True)
PY
  echo WEIGHTS_DONE ) > $B/weights.log 2>&1 &
WPID=$!
$V/python -c "import torch; assert torch.version.cuda.startswith('13')" 2>/dev/null || \
  $V/pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
[ -d ComfyUI ] || git clone -q --depth 1 https://github.com/comfyanonymous/ComfyUI.git
$V/pip install -q -r ComfyUI/requirements.txt
wait $WPID; grep -q WEIGHTS_DONE $B/weights.log
cd $B/ComfyUI/models
for d in diffusion_models text_encoders vae loras; do mkdir -p $d; ln -sfn $B/hf/$d/* $d/; done
cd $B/ComfyUI
pgrep -f '[m]ain.py --listen' >/dev/null || nohup $V/python main.py --listen 0.0.0.0 --port 8188 > $B/comfy.log 2>&1 &
echo BOOTSTRAP_DONE
