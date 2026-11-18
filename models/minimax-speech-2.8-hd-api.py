"""Round 1 API script: MiniMax Speech 2.8 HD via fal (fal-ai/minimax/speech-2.8-hd), voice Wise_Woman, language_boost Hebrew.
Run: with-secrets python3 models/minimax-speech-2.8-hd-api.py --ids s01"""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *

def synth(text, path):
    resp = fal("fal-ai/minimax/speech-2.8-hd", {"prompt": text, "language_boost": "Hebrew", "voice_setting": {"voice_id": "Wise_Woman", "speed": 1, "vol": 1, "pitch": 0},
                                                "audio_setting": {"sample_rate": 32000, "format": "mp3"}})
    return to_wav(get(resp["audio"]["url"]), path)

run("minimax-speech-2.8-hd", ("fal", "fal-ai/minimax/speech-2.8-hd"), "Wise_Woman (fal default, female)", "MiniMax Terms of Service via fal.ai", synth, "language_boost Hebrew.")
