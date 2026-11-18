"""Round 1 API script: ElevenLabs Eleven v4 via fal (elevenlabs/tts/eleven-v4), voice Rachel, language_code he.
Run: with-secrets python3 models/elevenlabs-v4-api.py --ids s01"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *

def synth(text, path):
    resp = fal("elevenlabs/tts/eleven-v4", {"text": text, "voice": "Rachel", "language_code": "he"})
    raw = get(resp["audio"]["url"])
    return to_wav(raw, path)

run("elevenlabs-v4", ("fal", "elevenlabs/tts/eleven-v4"), "Rachel (fal default, female)", "ElevenLabs Terms of Service via fal.ai", synth, "language_code he.")
