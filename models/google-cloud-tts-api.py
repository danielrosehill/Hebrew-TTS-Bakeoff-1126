"""Google Cloud Text-to-Speech he-IL, best tier available (see VOICE), service-account auth from env GOOGLE_SA_CLAUDE_ADMIN_PERSONAL.
Run: with-secrets uv run --with google-auth --with requests python models/google-cloud-tts-api.py   (writes results/google-cloud-tts/ and results/google-cloud-tts-nikud/). Keys come from the env only.
"""
import base64, io, json, os, subprocess, time, urllib.request, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SLUG = "google-cloud-tts"
VIA = "Google Cloud TTS v1 text:synthesize he-IL-Chirp3-HD-Kore"
VOICE = "he-IL-Chirp3-HD-Kore (female)"
LICENCE = "Google Cloud Terms of Service"


def post(url, body, headers, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def write_wav(path, pcm, rate):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)


def to_wav(raw, path):
    """Any container ffmpeg reads -> mono 16-bit WAV at the native rate; returns the rate."""
    tmp = path.with_suffix(".raw")
    tmp.write_bytes(raw)
    rate = int(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(tmp)]).split()[0])
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ac", "1", "-c:a", "pcm_s16le", str(path)])
    tmp.unlink()
    return rate


def run(synth, notes_extra=""):
    rows = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    for slug, field in ((SLUG, "text"), (SLUG + "-nikud", "text_nikud")):
        out = ROOT / "results" / slug
        out.mkdir(parents=True, exist_ok=True)
        times, rate, errs = {}, None, {}
        for r in rows:
            t = time.time()
            try:
                rate = synth(r[field], out / (r["id"] + ".wav")) or rate
                times[r["id"]] = round(time.time() - t, 2)
            except Exception as e:
                errs[r["id"]] = repr(e)[:200]
        meta = {"slug": slug, "hf_id": None, "revision": VIA, "licence": LICENCE,
                "input": "nikud" if field == "text_nikud" else "plain", "voice": VOICE, "reference_clip": None,
                "gpu": "hosted API", "sample_rate": rate, "load_s": None, "per_sentence_s": times,
                "generated": "2026-11-18", "generated_via": "api:" + VIA,
                "notes": ("Given the checked nikud as text. " if field == "text_nikud" else "Given plain Hebrew. ") + "per_sentence_s is the request round trip. " + notes_extra}
        if errs:
            meta["errors"] = errs
        (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        print(slug, len(times), "ok,", len(errs), "errors, mean", round(sum(times.values()) / max(1, len(times)), 2), "s, rate", rate)

def token():
    from google.oauth2 import service_account
    import google.auth.transport.requests as tr
    c = service_account.Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_SA_CLAUDE_ADMIN_PERSONAL"]), scopes=["https://www.googleapis.com/auth/cloud-platform"])
    c.refresh(tr.Request())
    return c.token, c.project_id


def synth(text, path):
    tok, proj = token()
    resp = json.loads(post("https://texttospeech.googleapis.com/v1/text:synthesize",
                           {"input": {"text": text}, "voice": {"languageCode": "he-IL", "name": "he-IL-Chirp3-HD-Kore"}, "audioConfig": {"audioEncoding": "LINEAR16"}},
                           {"Authorization": "Bearer " + tok, "x-goog-user-project": proj}))
    raw = base64.b64decode(resp["audioContent"])
    path.write_bytes(raw)
    with wave.open(str(path)) as w:
        return w.getframerate()


if __name__ == "__main__":
    run(synth)
