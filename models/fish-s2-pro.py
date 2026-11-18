"""Bakeoff candidate fish-s2-pro: fishaudio/s2-pro via fish-speech tag v2.0.0-beta. Run: modal-dsr run models/fish-s2-pro.py"""
import json, os, pathlib, modal

SLUG, HF_ID = "fish-s2-pro", "fishaudio/s2-pro"
GPU = os.environ.get("BAKEOFF_GPU", "L4")
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("git", "ffmpeg", "libsndfile1", "portaudio19-dev", "build-essential")
         .pip_install("torch==2.8.0", "torchaudio==2.8.0", "numpy<2", "transformers<=4.57.3", "lightning>=2.1.0",
                      "hydra-core>=1.3.2", "natsort", "einops", "librosa", "rich", "loguru", "loralib",
                      "pyrootutils", "resampy", "einx[torch]==0.2.2", "zstandard", "pydub", "ormsgpack",
                      "tiktoken", "pydantic==2.9.2", "cachetools", "descript-audio-codec", "descript-audiotools",
                      "safetensors", "kui", "silero-vad", "soundfile", "huggingface_hub", "opencc-python-reimplemented==0.1.7",
                      "datasets", "wandb", "tensorboard", "modelscope", "uvicorn", "gradio")
         .pip_install("protobuf>=5.29")
         .run_commands("git clone --depth 1 --branch v2.0.0-beta https://github.com/fishaudio/fish-speech /opt/fs"))
app = modal.App(f"bakeoff-{SLUG}", image=image)

@app.function(gpu=GPU, timeout=1500, secrets=[modal.Secret.from_dict({"PYTHONPATH": "/opt/fs"})])
def run(rows: list):
    import io, sys, time, numpy as np, soundfile as sf, torch
    sys.path.insert(0, "/opt/fs"); os.chdir("/opt/fs")
    from huggingface_hub import snapshot_download, HfApi
    t0 = time.time()
    rev = HfApi().model_info(HF_ID).sha
    ck = snapshot_download(HF_ID, local_dir="/opt/fs/checkpoints/s2-pro")
    from fish_speech.inference_engine import TTSInferenceEngine
    from fish_speech.models.dac.inference import load_model as load_dec
    from fish_speech.models.text2semantic.inference import launch_thread_safe_queue
    from fish_speech.utils.schema import ServeTTSRequest
    q = launch_thread_safe_queue(checkpoint_path=ck, device="cuda", precision=torch.bfloat16, compile=False)
    dec = load_dec(config_name="modded_dac_vq", checkpoint_path=f"{ck}/codec.pth", device="cuda")
    eng = TTSInferenceEngine(llama_queue=q, decoder_model=dec, precision=torch.bfloat16, compile=False)
    def gen(text, seed=None):
        req = ServeTTSRequest(text=text, references=[], format="wav", seed=seed)
        for r in eng.inference(req):
            if r.code == "error": raise RuntimeError(str(r.error))
            if r.code == "final" and isinstance(r.audio, tuple): return r.audio
        raise RuntimeError("no audio")
    gen("Hello world.")  # warm-up
    load_s = time.time() - t0
    outs, times, warn = {}, {}, []
    for r in rows:
        torch.cuda.synchronize(); t = time.time()
        try:
            sr, wav = gen(r["text"])
        except Exception as e:
            warn.append(f'{r["id"]}: {e!r}'); continue
        torch.cuda.synchronize(); times[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, np.asarray(wav, dtype=np.float32).squeeze(), sr, format="WAV", subtype="PCM_16")
        outs[r["id"]] = buf.getvalue()
    return dict(rev=rev, sr=sr, load_s=round(load_s, 1), times=times, outs=outs, warn=warn,
                peak_gb=round(torch.cuda.max_memory_allocated() / 1e9, 1))

@app.local_entrypoint()
def main():
    import datetime
    rows = [json.loads(l) for l in open("data/sentences.jsonl", encoding="utf-8") if l.strip()]
    res = run.remote(rows)
    d = pathlib.Path("results") / SLUG; d.mkdir(parents=True, exist_ok=True)
    for k, b in res["outs"].items(): (d / f"{k}.wav").write_bytes(b)
    meta = dict(slug=SLUG, hf_id=HF_ID, revision=res["rev"], licence="Fish Audio Research License (non-commercial)",
                input="plain", voice="default (no reference; random timbre, no seed)", reference_clip=None, gpu=GPU,
                sample_rate=res["sr"], load_s=res["load_s"], per_sentence_s=res["times"],
                generated=datetime.date.today().isoformat(),
                notes=f"fish-speech tag v2.0.0-beta, bf16, no compile, defaults (temp 0.8, top_p 0.8); peak VRAM {res['peak_gb']} GB. Warnings: " + "; ".join(res["warn"]))
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False)[:1500])
