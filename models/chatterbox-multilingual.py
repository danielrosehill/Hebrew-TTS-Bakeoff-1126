"""Bake-off candidate: Resemble AI Chatterbox Multilingual (V3 t3 checkpoint). Plain Hebrew text, built-in default voice."""
import json, time, modal

SLUG = "chatterbox-multilingual"
HF_ID = "ResembleAI/chatterbox"
app = modal.App(f"bakeoff-{SLUG}")
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg", "git")
         .pip_install("git+https://github.com/resemble-ai/chatterbox.git", "dicta-onnx", "soundfile", "huggingface_hub"))
GPU = "L4"

@app.function(image=image, gpu=GPU, timeout=1800)
def synth(rows: list):
    import torch, soundfile as sf, io
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from huggingface_hub import HfApi
    t0 = time.time()
    try:
        model = ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3"); t3 = "v3"
    except TypeError:
        model = ChatterboxMultilingualTTS.from_pretrained(device="cuda"); t3 = "v2 (installed package lacks t3_model)"
    load_s = time.time() - t0
    rev = HfApi().model_info(HF_ID).sha
    wavs, times = {}, {}
    for r in rows:
        t = time.time()
        wav = model.generate(r["text"], language_id="he")
        torch.cuda.synchronize()
        times[r["id"]] = round(time.time() - t, 2)
        b = io.BytesIO(); sf.write(b, wav.squeeze().float().cpu().numpy(), model.sr, format="WAV", subtype="PCM_16")
        wavs[r["id"]] = b.getvalue()
    return dict(wavs=wavs, times=times, sr=model.sr, load_s=round(load_s, 2), rev=rev, t3=t3)

@app.local_entrypoint()
def main():
    import os, datetime
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    res = synth.remote([{"id": r["id"], "text": r["text"]} for r in rows])
    d = f"results/{SLUG}"; os.makedirs(d, exist_ok=True)
    for k, b in res["wavs"].items():
        open(f"{d}/{k}.wav", "wb").write(b)
    json.dump(dict(slug=SLUG, hf_id=HF_ID, revision=res["rev"], licence="MIT", input="plain",
                   voice="built-in default (conds.pt), exaggeration=0.5 cfg=0.5 defaults", reference_clip=None,
                   gpu=GPU, sample_rate=res["sr"], load_s=res["load_s"], per_sentence_s=res["times"],
                   generated=str(datetime.date.today()), notes=f"t3 checkpoint: {res['t3']}; language_id=he; package from GitHub master (pip 0.1.7 lacks t3_model=v3); dicta-onnx installed but its Hebrew diacritization fails (Dicta needs model_path), so plain text is used; Perth watermark on outputs"),
              open(f"{d}/meta.json", "w"), ensure_ascii=False, indent=2)
