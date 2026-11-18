"""Male-voice runs for the voices still unbeaten in the Arena (Daniel, 2026-11-18: "all the voices that were generated
for the best models were all female ... for the best ones generate one or two clips with a male voice, so I can also
grade them on that"). Same models, prompts and inputs as their main runs; only the prebuilt voice changes.

Writes results/<base>-male/ (plain) and results/<base>-male-nikud/ (checked nikud), each with meta voice_gender "male".
Items: s01 (Screening) and p01 (Arena paragraph, data/rounds/round2.jsonl) by default.

    with-secrets uv run --with google-genai python models/male-voices-api.py [--ids s01,p01] [--only gemini-3.8-live,...]
"""
import argparse, asyncio, base64, importlib.util, io, json, os, time, wave
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _api_common import ROOT, fal, gemini_synth, get, to_wav  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).parent / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


GEMINI_MALE = "Charon"   # Gemini prebuilt voice described by Google as "informative", male
ELEVEN_MALE = "Brian"    # ElevenLabs default-library male voice
OPENAI_MALE = "cedar"    # OpenAI realtime/audio male voice


def live_synth(model):
    live = load("gemini-live-api"); live.VOICE = GEMINI_MALE
    def synth(text, path):
        path.write_bytes(asyncio.run(live.say(model, text))); return 24000
    return synth


def eleven_synth(text, path):
    resp = fal("elevenlabs/tts/eleven-v4", {"text": text, "voice": ELEVEN_MALE, "language_code": "he"})
    return to_wav(get(resp["audio"]["url"]), path)


def gpt_audio_synth(text, path):
    ga = load("openai-gpt-audio-api"); ga.VOICE = OPENAI_MALE
    wav = ga.say(text); path.write_bytes(wav)
    with wave.open(io.BytesIO(wav)) as w:
        return w.getframerate()


# base slug -> (model id, voice, generated_via, synth)
RUNS = {
    "gemini-flash-tts": ("gemini-3.1-flash-tts-preview", f"{GEMINI_MALE} (prebuilt, male)", "Google Gemini API generateContent", gemini_synth("gemini-3.1-flash-tts-preview", GEMINI_MALE)),
    "gemini-3.8-flash-tts": ("gemini-3.8-flash-tts", f"{GEMINI_MALE} (prebuilt, male)", "Google Gemini API generateContent", gemini_synth("gemini-3.8-flash-tts", GEMINI_MALE)),
    "gemini-3.8-flash-lite-tts": ("gemini-3.8-flash-lite-tts", f"{GEMINI_MALE} (prebuilt, male)", "Google Gemini API generateContent", gemini_synth("gemini-3.8-flash-lite-tts", GEMINI_MALE)),
    "gemini-3.8-live": ("gemini-3.8-live", f"{GEMINI_MALE} (prebuilt, male)", "gemini Live API (native audio, instructed to read verbatim)", live_synth("gemini-3.8-live")),
    "elevenlabs-v4": ("fal elevenlabs/tts/eleven-v4", f"{ELEVEN_MALE} (male)", "fal", eleven_synth),
    "openai-gpt-audio": ("gpt-audio-1.5", f"{OPENAI_MALE} (male)", "openai chat completions, audio output", gpt_audio_synth),
}


def items(ids):
    rows = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    for f in sorted((ROOT / "data/rounds").glob("round*.jsonl")):
        rows += [json.loads(l) for l in open(f, encoding="utf8") if l.strip()]
    return [r for r in rows if r["id"] in ids]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ids", default="s01,p01"); ap.add_argument("--only", default="")
    a = ap.parse_args()
    rows = items(set(a.ids.split(",")))
    for base, (model, voice, via, synth) in RUNS.items():
        if a.only and base not in a.only.split(","):
            continue
        for slug, field in ((base + "-male", "text"), (base + "-male-nikud", "text_nikud")):
            out = ROOT / "results" / slug; out.mkdir(parents=True, exist_ok=True)
            mp = out / "meta.json"
            meta = json.loads(mp.read_text()) if mp.exists() else {}
            times, errs, rate = dict(meta.get("per_sentence_s") or {}), {}, meta.get("sample_rate")
            for r in rows:
                t = time.time()
                try:
                    rate = synth(r[field], out / f"{r['id']}.wav") or rate; times[r["id"]] = round(time.time() - t, 2)
                except Exception as e:
                    errs[r["id"]] = repr(e)[:300]
            meta.update(slug=slug, hf_id=None, revision=model, licence=meta.get("licence") or "provider API terms",
                        input="nikud" if field == "text_nikud" else "plain", voice=voice, voice_gender="male", reference_clip=None,
                        gpu="API", sample_rate=rate, load_s=None, per_sentence_s=times, generated="2026-11-18",
                        generated_via=f"api:{via} {model}",
                        notes=("Given the checked nikud as text. " if field == "text_nikud" else "Given plain Hebrew. ") +
                              f"Male-voice variant of {base}: same model and prompt, voice {voice}. per_sentence_s is the request round trip.")
            if errs: meta["errors"] = errs
            else: meta.pop("errors", None)
            mp.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            print(slug, sorted(times), "errors:", errs or "-", "rate", rate)


if __name__ == "__main__":
    main()
