"""Bake-off candidate: Zyphra/ZONOS3-Mini (transformers packaging, -hf). Plain Hebrew text, release voice Savannah."""
import json, time, modal

SLUG = "zonos3-mini"
HF_ID = "Zyphra/ZONOS3-Mini-hf"
app = modal.App(f"bakeoff-{SLUG}")
image = (modal.Image.debian_slim(python_version="3.11")
         .pip_install("transformers>=4.57", "torch", "soundfile", "numpy", "zyphra-textnorm", "huggingface_hub"))
GPU = ["L4", "A10G"]

@app.function(image=image, gpu=GPU, timeout=1800)
def synth(rows: list):
    import torch, soundfile as sf, io, warnings
    from transformers import AutoModel
    from huggingface_hub import HfApi
    t0 = time.time()
    model = AutoModel.from_pretrained(HF_ID, trust_remote_code=True, dtype=torch.float32).to("cuda")
    load_s = time.time() - t0
    rev = HfApi().model_info(HF_ID).sha
    wavs, times, sr = {}, {}, None
    for r in rows:
        t = time.time()
        out = model.generate(r["text"], voice="Savannah", speaker_mode="embedding", language="he", seed=0)
        torch.cuda.synchronize()
        times[r["id"]] = round(time.time() - t, 2)
        sr = out.sampling_rate
        b = io.BytesIO(); sf.write(b, out.waveform.float().cpu().numpy(), sr, format="WAV", subtype="PCM_16")
        wavs[r["id"]] = b.getvalue()
    return dict(wavs=wavs, times=times, sr=sr, load_s=round(load_s, 2), rev=rev)

@app.local_entrypoint()
def main():
    import os, datetime
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    res = synth.remote([{"id": r["id"], "text": r["text"]} for r in rows])
    d = f"results/{SLUG}"; os.makedirs(d, exist_ok=True)
    for k, b in res["wavs"].items():
        open(f"{d}/{k}.wav", "wb").write(b)
    json.dump(dict(slug=SLUG, hf_id=HF_ID, revision=res["rev"], licence="apache-2.0", input="plain",
                   voice="Savannah (release voice, English American female) via speaker embedding; language=he, seed=0",
                   reference_clip=None, gpu="L4|A10G", sample_rate=res["sr"], load_s=res["load_s"],
                   per_sentence_s=res["times"], generated=str(datetime.date.today()),
                   notes="transformers remote code, fp32; attempt 1 (bf16, default reference-mode voice) gave ~0.5 s near-empty clips for almost every sentence, so speaker_mode=embedding used; no Hebrew-native voice in the release set"),
              open(f"{d}/meta.json", "w"), ensure_ascii=False, indent=2)
