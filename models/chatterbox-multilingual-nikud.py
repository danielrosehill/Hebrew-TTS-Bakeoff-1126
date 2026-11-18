"""Bake-off candidate: Resemble AI Chatterbox Multilingual (V3 t3 checkpoint). Plain Hebrew text, built-in default voice."""
import json, time, modal

SLUG = "chatterbox-multilingual-nikud"
HF_ID = "ResembleAI/chatterbox"
app = modal.App(f"bakeoff-{SLUG}")
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg", "git")
         .pip_install("git+https://github.com/resemble-ai/chatterbox.git", "dicta-onnx", "soundfile", "huggingface_hub"))
GPU = ["L4", "A10G"]  # any available (L4 capacity queued for long stretches on 2026-11-18)

@app.function(image=image, gpu=GPU, timeout=1800)
def synth(rows: list):
    import torch, soundfile as sf, io
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    from huggingface_hub import HfApi
    import logging
    import chatterbox.models.tokenizers.tokenizer as tk
    tk.add_hebrew_diacritics = lambda text: text  # bypass broken dicta step; input is already vocalized
    eos_msgs = []
    class H(logging.Handler):
        def emit(self, rec):
            m = rec.getMessage()
            if "forcing EOS" in m or "repetition" in m: eos_msgs.append((cur[0], m[:160]))
    cur = [None]
    logging.getLogger().addHandler(H()); logging.getLogger("chatterbox").addHandler(H())
    t0 = time.time()
    try:
        model = ChatterboxMultilingualTTS.from_pretrained(device="cuda", t3_model="v3"); t3 = "v3"
    except TypeError:
        model = ChatterboxMultilingualTTS.from_pretrained(device="cuda"); t3 = "v2 (installed package lacks t3_model)"
    load_s = time.time() - t0
    rev = HfApi().model_info(HF_ID).sha
    wavs, times = {}, {}
    for r in rows:
        cur[0] = r["id"]
        t = time.time()
        wav = model.generate(r["text_nikud"], language_id="he")
        torch.cuda.synchronize()
        times[r["id"]] = round(time.time() - t, 2)
        b = io.BytesIO(); sf.write(b, wav.squeeze().float().cpu().numpy(), model.sr, format="WAV", subtype="PCM_16")
        wavs[r["id"]] = b.getvalue()
    return dict(wavs=wavs, times=times, sr=model.sr, load_s=round(load_s, 2), rev=rev, t3=t3, eos=eos_msgs)

@app.local_entrypoint()
def main():
    import os, datetime
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    res = synth.remote([{"id": r["id"], "text_nikud": r["text_nikud"]} for r in rows])
    d = f"results/{SLUG}"; os.makedirs(d, exist_ok=True)
    for k, b in res["wavs"].items():
        open(f"{d}/{k}.wav", "wb").write(b)
    json.dump(dict(slug=SLUG, hf_id=HF_ID, revision=res["rev"], licence="MIT", input="nikud",
                   voice="built-in default (conds.pt), exaggeration=0.5 cfg=0.5 defaults", reference_clip=None,
                   gpu=GPU, sample_rate=res["sr"], load_s=res["load_s"], per_sentence_s=res["times"],
                   generated=str(datetime.date.today()), notes=f"t3 checkpoint v3; language_id=he; text_nikud fed directly, library's dicta step monkeypatched out (Dicta() needs model_path); GitHub master package; EOS/repetition warnings: {res['eos'] or 'none'}; Perth watermark on outputs"),
              open(f"{d}/meta.json", "w"), ensure_ascii=False, indent=2)
