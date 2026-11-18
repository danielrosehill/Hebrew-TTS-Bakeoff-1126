"""Bake-off: thewh1teagle/kokoro-hebrew-nc (Kokoro ONNX, voice he_shaul). CPU. Plain text -> renikud-onnx phonemes (per the repo's official hebrew.py example)."""
import json, time, datetime, pathlib
import modal

SLUG = "kokoro-hebrew"
HF_ID = "thewh1teagle/kokoro-hebrew-nc"
VOICE = "he_shaul"
G2P_REPO, G2P_REV = "thewh1teagle/renikud", "neobert-130m"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libsndfile1", "espeak-ng")
    .pip_install("kokoro-onnx", "renikud-onnx", "soundfile", "huggingface_hub")
)
app = modal.App(f"bakeoff-{SLUG}", image=image)


@app.function(cpu=4, memory=4096, timeout=1200)
def run(rows: list[dict]) -> dict:
    import io, soundfile as sf
    from huggingface_hub import hf_hub_download, HfApi
    t0 = time.time()
    model = hf_hub_download(HF_ID, "kokoro.onnx")
    voices = hf_hub_download(HF_ID, "voices-hebrew.bin")
    g2p_path = hf_hub_download(G2P_REPO, "model.onnx", revision=G2P_REV)
    rev = HfApi().model_info(HF_ID).sha
    from renikud_onnx import G2P
    from kokoro_onnx import Kokoro
    g2p = G2P(g2p_path)
    kokoro = Kokoro(model, voices)
    load_s = time.time() - t0
    out, per, ph = {}, {}, {}
    for r in rows:
        t = time.time()
        p = g2p.phonemize(r["text"])
        ph[r["id"]] = p
        samples, sr = kokoro.create(p, VOICE, is_phonemes=True, continuous=True)
        per[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
        out[r["id"]] = buf.getvalue()
    stress = any(("ˈ" in p or "ˌ" in p) for p in ph.values())
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": f"{rev}; G2P {G2P_REPO}@{G2P_REV}",
            "licence": "other: non-commercial (terms of avris/kokoro-hebrew-saspeech)", "input": "plain", "voice": VOICE,
            "reference_clip": "none (built-in voice, only voice in voices-hebrew.bin)", "gpu": "none (CPU, 4 vCPU, ONNX Runtime)",
            "sample_rate": sr, "load_s": round(load_s, 1), "per_sentence_s": per,
            "generated": datetime.date.today().isoformat(),
            "notes": f"Model card and official examples/hebrew.py (kokoro-onnx) use renikud-onnx on PLAIN text, not Phonikud on nikud; followed that, so text_nikud unused. Stress marks (ˈ/ˌ) in phonemes: {stress}. continuous=True as in the official example. Voice is male (only one in the bundle). Phonemes sample: {ph['s01']}"}
    return {"wavs": out, "meta": meta, "phonemes": ph}


@app.local_entrypoint()
def main():
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    res = run.remote(rows)
    out = pathlib.Path("results") / SLUG; out.mkdir(parents=True, exist_ok=True)
    for k, b in res["wavs"].items():
        (out / f"{k}.wav").write_bytes(b)
    (out / "phonemes.json").write_text(json.dumps(res["phonemes"], ensure_ascii=False, indent=1))
    (out / "meta.json").write_text(json.dumps(res["meta"], ensure_ascii=False, indent=2))
    print(json.dumps(res["meta"], ensure_ascii=False))
