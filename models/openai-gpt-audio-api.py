"""OpenAI gpt-audio-1.5 (chat completions with audio output) reading s01: the newest OpenAI speech model on
2026-11-18, added so the latest generation of each provider is screened. Instruction: read the Hebrew text exactly,
as a native Israeli speaker. Plain text -> openai-gpt-audio, checked nikud -> openai-gpt-audio-nikud.

    with-secrets python3 models/openai-gpt-audio-api.py --ids s01
"""
import argparse, base64, io, json, os, time, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL, VOICE = "gpt-audio-1.5", "coral"


def say(text):
    body = {"model": MODEL, "modalities": ["text", "audio"], "audio": {"voice": VOICE, "format": "wav"},
            "messages": [{"role": "system", "content": "You are a text-to-speech engine. Read the user's Hebrew text aloud exactly as written, "
                                                      "as a native Israeli speaker with standard, neutral modern Israeli pronunciation. Say nothing else."},
                         {"role": "user", "content": text}]}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=120))
    return base64.b64decode(r["choices"][0]["message"]["audio"]["data"])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ids", default=""); a = ap.parse_args()
    rows = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    rows = [r for r in rows if not a.ids or r["id"] in a.ids.split(",")]
    for slug, field in (("openai-gpt-audio", "text"), ("openai-gpt-audio-nikud", "text_nikud")):
        out = ROOT / "results" / slug; out.mkdir(parents=True, exist_ok=True)
        meta_p = out / "meta.json"
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
        times, rate = dict(meta.get("per_sentence_s") or {}), None
        for r in rows:
            t = time.time(); wav = say(r[field]); times[r["id"]] = round(time.time() - t, 2)
            (out / f"{r['id']}.wav").write_bytes(wav)
            with wave.open(io.BytesIO(wav)) as w: rate = w.getframerate()
        meta.update(slug=slug, hf_id=None, revision=MODEL, licence="OpenAI terms of service", input="nikud" if field == "text_nikud" else "plain",
                    voice=VOICE, reference_clip=None, gpu="API", sample_rate=rate, load_s=None, per_sentence_s=times, generated="2026-11-18",
                    generated_via=f"api:openai {MODEL} (chat completions, audio output)",
                    notes="Instructed to read the text exactly as a native Israeli speaker. A chat model, so it may paraphrase: listen for that.")
        meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(slug, list(times), rate)


if __name__ == "__main__":
    main()
