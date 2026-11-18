"""Fish Audio S2 Pro through Fish Audio's own API (https://api.fish.audio/v1/tts, header `model: s2-pro`), instead of
self-hosting fishaudio/s2-pro on Modal: the Modal run was still generating after about 40 minutes and was stopped
(Daniel, 2026-11-18). Same open model, served by its publisher; default voice (no reference_id), API defaults.

    FISH_API_KEY=... python3 models/fish-s2-pro-api.py            # writes results/fish-s2-pro/ and results/fish-s2-pro-nikud/

The API needs no local model, so this runs anywhere. The key is Fish Audio's (1Password item "Fish Audio").
"""
import io, json, os, time, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = "s2-pro"


def tts(text, key):
    req = urllib.request.Request("https://api.fish.audio/v1/tts", method="POST",
                                 data=json.dumps({"text": text, "format": "wav"}).encode(),
                                 headers={"Authorization": f"Bearer {key}", "model": MODEL, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main():
    key = os.environ["FISH_API_KEY"]
    rows = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    for slug, field in (("fish-s2-pro", "text"), ("fish-s2-pro-nikud", "text_nikud")):
        out = ROOT / "results" / slug
        out.mkdir(parents=True, exist_ok=True)
        times, rate = {}, None
        for r in rows:
            t = time.time()
            audio = tts(r[field], key)
            times[r["id"]] = round(time.time() - t, 2)
            (out / f"{r['id']}.wav").write_bytes(audio)
            with wave.open(io.BytesIO(audio)) as w:
                rate = w.getframerate()
        meta = {"slug": slug, "hf_id": "fishaudio/s2-pro", "revision": f"Fish Audio API, model header `{MODEL}`",
                "licence": "Fish Audio Research License (weights); API under Fish Audio terms",
                "input": "nikud" if field == "text_nikud" else "plain", "voice": "API default (no reference_id)",
                "reference_clip": None, "gpu": "Fish Audio API (hosted)", "sample_rate": rate, "load_s": None,
                "per_sentence_s": times, "generated": time.strftime("%Y-%m-%d"),
                "notes": "Served by the publisher's API instead of self-hosted; per_sentence_s is the API round trip. "
                         "Self-hosting on Modal was stopped after about 40 minutes. "
                         + ("Given the checked nikud as text." if field == "text_nikud" else "Given plain Hebrew.")}
        (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(slug, len(times), "clips, mean", round(sum(times.values()) / len(times), 2), "s, rate", rate)


if __name__ == "__main__":
    main()
