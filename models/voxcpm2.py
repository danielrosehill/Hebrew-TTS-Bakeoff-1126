"""Bake-off candidate: openbmb/VoxCPM2, plain text, default voice (no reference)."""
import json, time, datetime, pathlib
import modal

SLUG, HF_ID, GPU = "voxcpm2", "openbmb/VoxCPM2", "L4"
app = modal.App(f"bakeoff-{SLUG}")
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg", "libsndfile1")
         .pip_install("voxcpm", "soundfile", "huggingface_hub"))


@app.function(image=image, gpu=GPU, timeout=1500)
def run(rows: list):
    import soundfile as sf, io, torch
    from huggingface_hub import HfApi
    t0 = time.time()
    from voxcpm import VoxCPM
    model = VoxCPM.from_pretrained(HF_ID, load_denoiser=False)
    load_s = time.time() - t0
    sr = model.tts_model.sample_rate
    rev = HfApi().model_info(HF_ID).sha
    out, times = {}, {}
    for r in rows:
        t = time.time()
        wav = model.generate(text=r["text"], cfg_value=2.0, inference_timesteps=10)
        times[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, wav, sr, format="WAV"); out[r["id"]] = buf.getvalue()
    meta = dict(slug=SLUG, hf_id=HF_ID, revision=rev, licence="apache-2.0", input="plain",
                voice="model default (no reference, no voice-design prompt)", reference_clip=None,
                gpu=GPU, sample_rate=sr, load_s=round(load_s, 2), per_sentence_s=times,
                generated=datetime.date.today().isoformat(),
                notes="voxcpm pip, cfg_value=2.0, inference_timesteps=10 (model card defaults)")
    return out, meta


@app.local_entrypoint()
def main():
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    out, meta = run.remote(rows)
    d = pathlib.Path("results") / SLUG; d.mkdir(parents=True, exist_ok=True)
    for k, b in out.items(): (d / f"{k}.wav").write_bytes(b)
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps(meta, ensure_ascii=False))
