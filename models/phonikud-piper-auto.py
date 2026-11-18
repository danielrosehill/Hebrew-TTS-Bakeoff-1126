"""Bake-off model: plain text -> Phonikud's own diacritizer (add_diacritics: its vowels, hataama, vocal shva)
-> phonikud.phonemize -> Piper voice Phonikud/phonikud-tts-checkpoints. Our Dicta nikud is NOT used."""
import json
import time
from pathlib import Path

import modal

SLUG, HF_ID = "phonikud-piper-auto", "Phonikud/phonikud-tts-checkpoints"
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libsndfile1")
    .pip_install("phonikud", "phonikud-onnx", "piper-onnx", "onnxruntime", "soundfile", "numpy", "huggingface_hub")
)
app = modal.App(f"bakeoff-{SLUG}", image=image)


@app.function(cpu=4, memory=4096, timeout=1800)
def synth(rows: list[dict]) -> dict:
    import importlib.metadata as md
    import io
    import warnings

    import numpy as np
    import soundfile as sf
    from huggingface_hub import HfApi, hf_hub_download
    from phonikud import phonemize
    from phonikud_onnx import Phonikud
    from piper_onnx import Piper

    t0 = time.time()
    rev = HfApi().model_info(HF_ID).sha
    m = hf_hub_download(HF_ID, "model.onnx", revision=rev)
    c = hf_hub_download(HF_ID, "model.config.json", revision=rev)
    drev = HfApi().model_info("Phonikud/phonikud-onnx").sha
    dia = Phonikud(hf_hub_download("Phonikud/phonikud-onnx", "phonikud-1.0.int8.onnx", revision=drev))
    piper = Piper(m, c)
    load_s = round(time.time() - t0, 2)
    res = {"wavs": {}, "times": {}, "nikud": {}, "ipa": {}}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for r in rows:
            t = time.time()
            tn = dia.add_diacritics(r["text"])
            ipa = phonemize(tn)
            y, sr = piper.create(ipa, is_phonemes=True)
            b = io.BytesIO()
            sf.write(b, np.asarray(y, dtype=np.float32), sr, format="WAV", subtype="PCM_16")
            res["wavs"][r["id"]] = b.getvalue()
            res["times"][r["id"]] = round(time.time() - t, 2)
            res["nikud"][r["id"]] = {"text": r["text"], "phonikud_nikud": tn, "dicta_nikud": r["text_nikud"], "ipa": ipa}
        res["warnings"] = sorted({str(x.message)[:200] for x in w})
    res.update(load_s=load_s, sr=sr, rev=rev, drev=drev,
               versions={p: md.version(p) for p in ("phonikud", "phonikud-onnx", "piper-onnx", "onnxruntime")})
    return res


@app.local_entrypoint()
def main():
    import datetime
    rows = [json.loads(l) for l in Path("data/sentences.jsonl").read_text().splitlines() if l.strip()]
    res = synth.remote(rows)
    d = Path("results") / SLUG
    d.mkdir(parents=True, exist_ok=True)
    for k, b in res["wavs"].items():
        (d / f"{k}.wav").write_bytes(b)
    (d / "nikud.json").write_text(json.dumps(res["nikud"], ensure_ascii=False, indent=1))
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": res["rev"], "licence": "non-commercial (per the voice's model card; Phonikud code MIT)",
            "input": "plain", "voice": "Phonikud Piper voice model.onnx (single voice, piper-onnx defaults)", "reference_clip": None,
            "gpu": "none (cpu=4)", "sample_rate": res["sr"], "load_s": res["load_s"], "per_sentence_s": res["times"],
            "generated": datetime.date.today().isoformat(),
            "notes": f"Input is plain text; the nikud is Phonikud's own (Phonikud/phonikud-onnx@{res['drev']} phonikud-1.0.int8.onnx add_diacritics, incl. its vowels, hataama and vocal shva), then phonikud.phonemize, then Piper. Our Dicta nikud is not used. nikud.json has Phonikud's diacritized text next to ours per sentence. versions {res['versions']}. Python warnings: {res['warnings']}"}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False)[:1200])
    print("differs from dicta vowels (marks-stripped compare):", sum(v["phonikud_nikud"].replace("|", "") != v["dicta_nikud"] for v in res["nikud"].values()), "of", len(res["nikud"]))
