"""Bake-off candidate: k2-fsa/OmniVoice, plain text, voice design (no reference)."""
import json, time, datetime, pathlib
import modal

SLUG, HF_ID, GPU = "omnivoice", "k2-fsa/OmniVoice", "L4"
INSTRUCT = "female, young adult, moderate pitch"
app = modal.App(f"bakeoff-{SLUG}")
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg", "libsndfile1")
         .pip_install("torch==2.8.0", "torchaudio==2.8.0", extra_index_url="https://download.pytorch.org/whl/cu128")
         .pip_install("omnivoice", "soundfile", "huggingface_hub"))


@app.function(image=image, gpu=["L4", "A10G"], timeout=1500)
def run(rows: list):
    import soundfile as sf, io, torch
    from huggingface_hub import HfApi
    t0 = time.time()
    import sys; sys.modules.pop('omnivoice', None)
    sys.path = [q for q in sys.path if q != '/root']
    from omnivoice import OmniVoice
    model = OmniVoice.from_pretrained(HF_ID, device_map="cuda:0", dtype=torch.float16)
    load_s = time.time() - t0
    import subprocess
    gpu = subprocess.run(['nvidia-smi','--query-gpu=name','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()
    rev = HfApi().model_info(HF_ID).sha
    out, times = {}, {}
    for r in rows:
        t = time.time()
        audio = model.generate(text=r["text"], instruct=INSTRUCT)
        times[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, audio[0], 24000, format="WAV"); out[r["id"]] = buf.getvalue()
    meta = dict(slug=SLUG, hf_id=HF_ID, revision=rev, licence="code Apache-2.0, weights CC-BY-NC",
                input="plain", voice=f"voice design instruct='{INSTRUCT}' (Israeli accent is not a supported attribute; design is trained on zh/en only)",
                reference_clip=None, gpu=gpu, sample_rate=24000, load_s=round(load_s, 2),
                per_sentence_s=times, generated=datetime.date.today().isoformat(),
                notes="omnivoice pip, fp16, default generation params")
    return out, meta


@app.local_entrypoint()
def main():
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    out, meta = run.remote(rows)
    d = pathlib.Path("results") / SLUG; d.mkdir(parents=True, exist_ok=True)
    for k, b in out.items(): (d / f"{k}.wav").write_bytes(b)
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps(meta, ensure_ascii=False))
