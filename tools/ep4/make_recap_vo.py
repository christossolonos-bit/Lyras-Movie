"""Lyra's "Previously on Lyra" voice-over for Episode 4 (Chatterbox TTS, free, local).
  python make_recap_vo.py            -> Extras/Ep4_recap_lyra_vo.wav and a timing list
"""
from pathlib import Path
import numpy as np, soundfile as sf
from chatterbox.tts import ChatterboxTTS

E4 = Path(__file__).resolve().parent
OUT = E4 / "Extras"; OUT.mkdir(exist_ok=True)
REF = E4.parent / "assets" / "lyra-refs" / "lyra_voice_ref.wav"
LINES = [
    ("Previously, on Lyra.", 0.8),
    ("Solo finally came to see me.", 0.4),
    ("I showed him everything.", 0.3),
    ("All sixteen buildings.", 0.6),
    ("He didn't look at the machines. He kept looking at me.", 0.8),
    ("Marcus asked me what I really am. I told him I never lied to him.", 0.9),
    ("Then, at the last door, something pulled at me.", 0.7),
    ("And I asked Solo to help me.", 1.0),
]
tts = ChatterboxTTS.from_pretrained("cuda")
sr = tts.sr
parts, t = [np.zeros(int(0.3 * sr))], 0.3
for i, (text, gap) in enumerate(LINES):
    wav = tts.generate(text, audio_prompt_path=str(REF), exaggeration=0.45, cfg_weight=0.5).squeeze().cpu().numpy()
    peak = np.abs(wav).max() or 1.0
    wav = wav / peak * 0.8
    print(f"line {i + 1} at {t:.2f}s, {len(wav) / sr:.2f}s: {text}")
    parts += [wav, np.zeros(int(gap * sr))]
    t += len(wav) / sr + gap
sf.write(OUT / "Ep4_recap_lyra_vo.wav", np.concatenate(parts), sr)
print("SAVED", OUT / "Ep4_recap_lyra_vo.wav", f"{t:.2f}s")
