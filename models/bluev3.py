"""Bake-off: notmax123/BlueV3 (ONNX bundle BlueV3-onnx, BlueTTS blue_onnx). CPU. Plain text, voice noa."""
import json, time, datetime, pathlib
import modal

SLUG = "bluev3"
HF_ID = "notmax123/BlueV3"
BUNDLE = "notmax123/BlueV3-onnx"
VOICE = "noa"
BLUETTS_COMMIT = "cbe51508f3f05207662bc714ad646da8191861d0"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "libsndfile1", "espeak-ng")
    .pip_install(
        f"blue-onnx[hebrew] @ git+https://github.com/maxmelichov/BlueTTS@{BLUETTS_COMMIT}",
        "heb-tts-normalizer==0.2.0", "hebrew-num2words==0.1.0", "huggingface_hub", "soundfile",
    )
)
app = modal.App(f"bakeoff-{SLUG}", image=image)


@app.function(cpu=4, memory=8192, timeout=1800)
def run(rows: list[dict]) -> dict:
    import io, soundfile as sf
    from huggingface_hub import snapshot_download, HfApi
    t0 = time.time()
    d = snapshot_download(BUNDLE, allow_patterns=["onnx/*", "voices/*", "frontend/renikud/*", "frontend/polyg2p_data/*", "tts.json"])
    rev = HfApi().model_info(BUNDLE).sha
    from blue_onnx import BlueTTS
    tts = BlueTTS(onnx_dir=f"{d}/onnx", style_json=f"{d}/voices/{VOICE}.json")
    load_s = time.time() - t0
    out, per = {}, {}
    for r in rows:
        t = time.time()
        samples, sr = tts.synthesize(r["text"], lang="he")
        per[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
        out[r["id"]] = buf.getvalue()
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": f"{BUNDLE}@{rev}; BlueTTS@{BLUETTS_COMMIT[:7]}",
            "licence": "MIT (decoder OpenRAIL-M derivative)", "input": "plain", "voice": VOICE,
            "reference_clip": f"built-in voice JSON voices/{VOICE}.json (LibriTTS-R speaker 1088)", "gpu": "none (CPU, 4 vCPU, ONNX Runtime)",
            "sample_rate": sr, "load_s": round(load_s, 1), "per_sentence_s": per,
            "generated": datetime.date.today().isoformat(),
            "notes": "ONNX bundle v3.0.1 (ckpt 702000); 8 Euler steps, CFG 4.0, speed 1.0 (bundle defaults, speed_scale applied); Hebrew G2P RenikudPlus on plain text (nikud stripped/not supplied); lang='he'."}
    return {"wavs": out, "meta": meta}


@app.local_entrypoint()
def main():
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    res = run.remote(rows)
    out = pathlib.Path("results") / SLUG; out.mkdir(parents=True, exist_ok=True)
    for k, b in res["wavs"].items():
        (out / f"{k}.wav").write_bytes(b)
    (out / "meta.json").write_text(json.dumps(res["meta"], ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in res["meta"].items() if k != "notes"}, ensure_ascii=False))
