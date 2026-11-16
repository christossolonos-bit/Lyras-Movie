#!/usr/bin/env python3
"""Print OpenRouter credit balance."""
from __future__ import annotations

from gen_s11a_ots_v10_facelock import http_json, load_key

data = http_json("https://openrouter.ai/api/v1/credits", load_key()).get("data", {})
total, used = float(data.get("total_credits", 0)), float(data.get("total_usage", 0))
print(f"total={total:.2f} used={used:.2f} remaining={total - used:.2f}")
