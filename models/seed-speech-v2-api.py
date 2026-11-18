"""Round 1 API script: ByteDance Seed Speech TTS v2 via fal (fal-ai/bytedance/seed-speech/tts/v2).
Run: with-secrets python3 models/seed-speech-v2-api.py --ids s01"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *
VOICE = "vivi_mixed_en_zh_ja_es_id"

def synth(text, path):
    resp = fal("fal-ai/bytedance/seed-speech/tts/v2", {"text": text, "voice": VOICE})
    return to_wav(get(resp["audio"]["url"]), path)

run("seed-speech-v2", ("fal", "fal-ai/bytedance/seed-speech/tts/v2"), VOICE + " (multilingual preset; Hebrew not listed; gender unverified)", "ByteDance Terms of Service via fal.ai", synth, "No Hebrew in any voice preset name; tests whether it reads Hebrew at all.")
