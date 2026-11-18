"""Round 1 API script: xAI TTS via fal (xai/tts/v1), voice eve (female default), language auto (Hebrew not in the enum).
Run: with-secrets python3 models/xai-tts-api.py --ids s01"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *

def synth(text, path):
    resp = fal("xai/tts/v1", {"text": text, "voice": "eve", "language": "auto", "output_format": {"codec": "wav", "sample_rate": 24000}})
    return to_wav(get(resp["audio"]["url"]), path)

run("xai-tts", ("fal", "xai/tts/v1"), "eve (default, female)", "xAI Terms of Service via fal.ai", synth, "language auto; Hebrew is not in the endpoint's supported list.")
