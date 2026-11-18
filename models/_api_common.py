"""Shared helpers for the round-1 API scripts (--ids subset). Keys come from the env only (with-secrets)."""
import argparse, base64, json, os, subprocess, time, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "tts-bakeoff/1.0"}


def post(url, body, headers, timeout=240):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **UA, **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get(url, headers=None, timeout=120):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def write_wav(path, pcm, rate):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)


def to_wav(raw, path):
    tmp = path.with_suffix(".raw")
    tmp.write_bytes(raw)
    rate = int(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(tmp)]).split()[0])
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ac", "1", "-c:a", "pcm_s16le", str(path)])
    tmp.unlink()
    return rate


def fal(endpoint, body):
    resp = json.loads(post("https://fal.run/" + endpoint, body, {"Authorization": "Key " + os.environ["FAL_KEY"]}))
    return resp


def run(slug, via, voice, licence, synth, notes_extra=""):
    ap = argparse.ArgumentParser(); ap.add_argument("--ids", default="s01")
    ids = set(ap.parse_args().ids.split(","))
    rows = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    rows = [r for r in rows if r["id"] in ids]
    for sl, field in ((slug, "text"), (slug + "-nikud", "text_nikud")):
        out = ROOT / "results" / sl
        out.mkdir(parents=True, exist_ok=True)
        times, rate, errs = {}, None, {}
        for r in rows:
            t = time.time()
            try:
                rate = synth(r[field], out / (r["id"] + ".wav")) or rate
                times[r["id"]] = round(time.time() - t, 2)
            except Exception as e:
                errs[r["id"]] = repr(e)[:300]
        meta = {"slug": sl, "hf_id": None, "revision": via[1], "licence": licence,
                "input": "nikud" if field == "text_nikud" else "plain", "voice": voice, "reference_clip": None,
                "gpu": "API", "sample_rate": rate, "load_s": None, "per_sentence_s": times,
                "generated": "2026-11-18", "generated_via": "api:" + via[0] + " " + via[1],
                "notes": ("Given the checked nikud as text. " if field == "text_nikud" else "Given plain Hebrew. ") + "per_sentence_s is the request round trip. Round 1: ids " + ",".join(sorted(ids)) + " only. " + notes_extra}
        if errs:
            meta["errors"] = errs
        (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(sl, len(times), "ok,", len(errs), "errors", errs, "rate", rate)


def gemini_synth(model, voice="Kore"):
    def synth(text, path):
        body = {"contents": [{"parts": [{"text": text}]}],
                "generationConfig": {"responseModalities": ["AUDIO"],
                                     "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
        resp = json.loads(post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", body, {"x-goog-api-key": os.environ["GEMINI_API_KEY"]}))
        part = resp["candidates"][0]["content"]["parts"][0]["inlineData"]
        raw = base64.b64decode(part["data"])
        if raw[:4] == b"RIFF":
            path.write_bytes(raw)
            with wave.open(str(path)) as w:
                return w.getframerate()
        rate = int(part["mimeType"].split("rate=")[1].split(";")[0]) if "rate=" in part["mimeType"] else 24000
        write_wav(path, raw, rate)
        return rate
    return synth


def gemini_script(slug, model):
    run(slug, ("Google Gemini API generateContent", model), "Kore (prebuilt, female)", "Google Gemini API Additional Terms of Service", gemini_synth(model))
