"""Bake-off model: thewh1teagle/piper-he-noa (Piper VITS). Plain Hebrew -> renikud-onnx G2P (the frontend the card says it was trained on) -> Piper phoneme ids.
Note: piper-tts 1.8.0 `phoneme_type: hebrew` does NOT use renikud (it uses Nakdimon + its own rule G2P), so renikud is called explicitly.
The native piper-tts path is kept as results/piper-he-noa/nakdimon-default/ (first run)."""
import json
import time
from pathlib import Path

import modal

SLUG, HF_ID = "piper-he-noa", "thewh1teagle/piper-he-noa"
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libsndfile1")
    .pip_install("piper-tts", "renikud-onnx", "soundfile", "numpy", "huggingface_hub")
)
app = modal.App(f"bakeoff-{SLUG}", image=image)


@app.function(cpu=4, memory=4096, timeout=1800)
def synth(rows: list[dict]) -> dict:
    import importlib.metadata as md
    import io
    import logging
    import warnings
    import wave

    import numpy as np
    import soundfile as sf
    from huggingface_hub import HfApi, hf_hub_download

    logging.basicConfig(level=logging.INFO)
    t0 = time.time()
    rev = HfApi().model_info(HF_ID).sha
    onnx = hf_hub_download(HF_ID, "he_IL-noa-medium.onnx", revision=rev)
    hf_hub_download(HF_ID, "he_IL-noa-medium.onnx.json", revision=rev)
    from piper import PiperVoice
    from renikud_onnx import G2P
    voice = PiperVoice.load(onnx)
    g2p = G2P()
    load_s = round(time.time() - t0, 2)
    out, times, ipas = {}, {}, {}
    for r in rows:
        t = time.time()
        ipa = g2p.phonemize(r["text"])
        ids = voice.phonemes_to_ids(list(ipa))
        y = voice.phoneme_ids_to_audio(ids)
        y = np.asarray(y, dtype=np.float32)
        if y.dtype != np.float32 or np.abs(y).max() > 1.5:
            y = y / 32768.0
        sr = voice.config.sample_rate
        buf = io.BytesIO()
        sf.write(buf, y, sr, format="WAV", subtype="PCM_16")
        out[r["id"]] = buf.getvalue()
        times[r["id"]] = round(time.time() - t, 2)
        ipas[r["id"]] = ipa
    notes = []
    return {"wavs": out, "times": times, "load_s": load_s, "sr": sr, "rev": rev, "warnings": notes, "ipa": ipas,
            "versions": {p: md.version(p) for p in ("piper-tts", "renikud-onnx", "onnxruntime")}}


@app.local_entrypoint()
def main():
    import datetime
    rows = [json.loads(l) for l in Path("data/sentences.jsonl").read_text().splitlines() if l.strip()]
    res = synth.remote(rows)
    d = Path("results") / SLUG
    d.mkdir(parents=True, exist_ok=True)
    for k, b in res["wavs"].items():
        (d / f"{k}.wav").write_bytes(b)
    (d / "ipa.json").write_text(json.dumps(res["ipa"], ensure_ascii=False, indent=1))
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": res["rev"], "licence": "cc-by-4.0", "input": "plain",
            "voice": "noa (speaker 0, default; he_IL-noa-medium.onnx)", "reference_clip": None, "gpu": "none (cpu=4)",
            "sample_rate": res["sr"], "load_s": res["load_s"], "per_sentence_s": res["times"],
            "generated": datetime.date.today().isoformat(),
            "notes": f"Plain Hebrew -> renikud-onnx {res['versions']['renikud-onnx']} G2P (stressed IPA, as the card says the voice was trained on) -> piper-tts {res['versions']['piper-tts']} phonemes_to_ids / phoneme_ids_to_audio with the voice config's default inference settings. piper-tts 1.8.0 phoneme_type hebrew does not use renikud (Nakdimon + own G2P); that native path was the first run, kept in nakdimon-default/. ipa.json holds the IPA fed in. Warnings: none seen in logs."}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False)[:1500])
