"""Round 1 API script: Inworld TTS 2 via Replicate (inworld/realtime-tts-2), language he. Tries voice Yael, falls back to Ashley (schema default).
Run: with-secrets python3 models/inworld-tts-2-api.py --ids s01"""
import sys, time, urllib.error; from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import *
USED = {}

def predict(text, voice):
    for i in range(4):
        try:
            return _predict(text, voice)
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(12)
    return _predict(text, voice)

def _predict(text, voice):
    h = {"Authorization": "Bearer " + os.environ["REPLICATE_API_TOKEN"], "Prefer": "wait=60"}
    p = json.loads(post("https://api.replicate.com/v1/models/inworld/realtime-tts-2/predictions",
                        {"input": {"text": text, "language": "he", "voice_id": voice, "audio_format": "wav", "sample_rate": 48000}}, h))
    while p["status"] in ("starting", "processing"):
        time.sleep(2); p = json.loads(get(p["urls"]["get"], h))
    if p["status"] != "succeeded":
        raise RuntimeError(str(p.get("error"))[:200])
    return p["output"] if isinstance(p["output"], str) else p["output"][0]

def synth(text, path):
    try:
        url = predict(text, "Yael"); USED["voice"] = "Yael"
    except Exception as e:
        print("Yael failed:", repr(e)[:150]); url = predict(text, "Ashley"); USED["voice"] = "Ashley"
    return to_wav(get(url), path)

run("inworld-tts-2", ("replicate", "inworld/realtime-tts-2"), "Yael if accepted, else Ashley (see notes/stdout; female)", "Inworld AI Terms of Service via Replicate", synth, "language he; wav 48 kHz requested.")

for sl in ("inworld-tts-2", "inworld-tts-2-nikud"):
    m = ROOT / "results" / sl / "meta.json"
    if m.exists() and USED:
        d = json.loads(m.read_text()); d["voice"] = USED["voice"] + " (female)"; m.write_text(json.dumps(d, ensure_ascii=False, indent=1))
