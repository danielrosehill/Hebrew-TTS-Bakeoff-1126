"""Gemini native-audio models (Live API) used as TTS: the multimodal models that speak natively, not the dedicated TTS
models (Daniel, 2026-11-18: "multimodal models that have audio output and claim Hebrew support ... a whole other
category"). Each is told to read the user's Hebrew text aloud verbatim with neutral Israeli pronunciation.

    with-secrets uv run --with google-genai python models/gemini-live-api.py --ids s01
"""
import argparse, asyncio, io, json, os, time, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS = {"gemini-3.8-live": "gemini-3.8-live", "gemini-3.1-flash-live": "gemini-3.1-flash-live-preview",
          "gemini-2.5-native-audio": "gemini-2.5-flash-native-audio-latest"}
VOICE = "Kore"
SYSTEM = ("You are a text-to-speech engine. When the user sends Hebrew text, read it aloud exactly as written, word for word, "
          "as a native Israeli speaker with standard, neutral modern Israeli pronunciation. Do not add, translate or answer anything.")


async def say(model, text):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options={"api_version": "v1alpha"})
    cfg = types.LiveConnectConfig(response_modalities=["AUDIO"], system_instruction=SYSTEM,
                                  speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE))))
    pcm = bytearray()
    async with client.aio.live.connect(model=model, config=cfg) as s:
        await s.send_client_content(turns=types.Content(role="user", parts=[types.Part(text=text)]), turn_complete=True)
        async for msg in s.receive():
            if msg.data:
                pcm += msg.data
            if msg.server_content and msg.server_content.turn_complete:
                break
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(bytes(pcm))
    return buf.getvalue()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ids", default=""); a = ap.parse_args()
    rows = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    rows = [r for r in rows if not a.ids or r["id"] in a.ids.split(",")]
    for base, model in MODELS.items():
        for slug, field in ((base, "text"), (base + "-nikud", "text_nikud")):
            out = ROOT / "results" / slug; out.mkdir(parents=True, exist_ok=True)
            times, errs = {}, {}
            for r in rows:
                t = time.time()
                try:
                    (out / f"{r['id']}.wav").write_bytes(asyncio.run(say(model, r[field]))); times[r["id"]] = round(time.time() - t, 2)
                except Exception as e:
                    errs[r["id"]] = repr(e)[:300]
            meta = {"slug": slug, "hf_id": None, "revision": model, "licence": "Google Gemini API terms", "input": "nikud" if field == "text_nikud" else "plain",
                    "voice": VOICE, "reference_clip": None, "gpu": "API", "sample_rate": 24000, "load_s": None, "per_sentence_s": times,
                    "generated": "2026-11-18", "generated_via": f"api:gemini Live API {model} (native audio, instructed to read verbatim)",
                    "notes": "A conversational native-audio model used as TTS; it may paraphrase or answer instead of reading: listen for that.",
                    **({"errors": errs} if errs else {})}
            (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
            print(slug, "ok" if times else "FAILED", errs or "")
            if not times:
                import shutil; shutil.rmtree(out)


if __name__ == "__main__":
    main()
