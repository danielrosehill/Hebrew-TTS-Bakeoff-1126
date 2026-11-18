"""Bake-off model: Phonikud phonemize(nikud) + Piper voice Phonikud/phonikud-tts-checkpoints.

Stress: plain phonemize() on Dicta nikud has no stress marks (ends up final-syllable stress). The Phonikud diacritizer
(Phonikud/phonikud-onnx via pip phonikud-onnx) adds hataama (U+05AB) and vocal shva (U+05BD). We run it on the plain
`text`, then copy only those two marks onto the given Dicta `text_nikud` letter by letter, keeping Dicta's vowels.
Results: main dir = with transplanted marks; plain/ = unmodified text_nikud for comparison.
"""
import json
import time
from pathlib import Path

import modal

SLUG, HF_ID = "phonikud-piper", "Phonikud/phonikud-tts-checkpoints"
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libsndfile1")
    .pip_install("phonikud", "phonikud-onnx", "piper-onnx", "onnxruntime", "soundfile", "numpy", "huggingface_hub")
)
app = modal.App(f"bakeoff-{SLUG}", image=image)

HAT, VSHVA = "֫", "ֽ"


def clusters(s):
    """[(base, marks)] for each Hebrew letter; other chars (space, punctuation, '|') are skipped."""
    out = []
    for ch in s:
        if "א" <= ch <= "ת":
            out.append([ch, ""])
        elif "֑" <= ch <= "ׇ" and out:
            out[-1][1] += ch
    return out


def transplant(given, diac):
    """Copy HAT/VSHVA from `diac` (diacritizer output) onto `given` nikud; None if the letters don't line up."""
    a, b = clusters(given), clusters(diac)
    if [x[0] for x in a] != [x[0] for x in b]:
        return None
    marks = [(i, "".join(c for c in m if c in (HAT, VSHVA))) for i, (_, m) in enumerate(b)]
    res, ci, out = [], -1, []
    mk = dict(marks)
    for ch in given:
        out.append(ch)
        if "א" <= ch <= "ת":
            ci += 1
            # place marks right after the letter; phonikud accepts any order within the cluster
            out.append(mk[ci])
    return "".join(out)


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

    def wav(y, sr):
        b = io.BytesIO()
        sf.write(b, np.asarray(y, dtype=np.float32), sr, format="WAV", subtype="PCM_16")
        return b.getvalue()

    res = {"stress": {}, "plain": {}, "times": {}, "ipa": {}, "nikud_used": {}}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for r in rows:
            t = time.time()
            diac = dia.add_diacritics(r["text"])
            tn = transplant(r["text_nikud"], diac)
            ok = tn is not None
            tn = tn or r["text_nikud"]
            ipa = phonemize(tn)
            ipa_plain = phonemize(r["text_nikud"])
            y, sr = piper.create(ipa, is_phonemes=True)
            res["stress"][r["id"]] = wav(y, sr)
            res["times"][r["id"]] = round(time.time() - t, 2)  # includes diacritizer + phonemize + synthesis
            y2, _ = piper.create(ipa_plain, is_phonemes=True)
            res["plain"][r["id"]] = wav(y2, sr)
            res["ipa"][r["id"]] = {"transplanted": ok, "stress": ipa, "plain": ipa_plain, "nikud": tn, "diacritizer_out": diac}
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
    (d / "plain").mkdir(parents=True, exist_ok=True)
    for k, b in res["stress"].items():
        (d / f"{k}.wav").write_bytes(b)
    for k, b in res["plain"].items():
        (d / "plain" / f"{k}.wav").write_bytes(b)
    (d / "ipa.json").write_text(json.dumps(res["ipa"], ensure_ascii=False, indent=1))
    n_ok = sum(v["transplanted"] for v in res["ipa"].values())
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": res["rev"], "licence": "non-commercial (per the voice's model card; Phonikud code MIT)",
            "input": "nikud", "voice": "Phonikud Piper voice model.onnx (single voice, default settings of piper-onnx)",
            "reference_clip": None, "gpu": "none (cpu=4)", "sample_rate": res["sr"], "load_s": res["load_s"],
            "per_sentence_s": res["times"], "generated": datetime.date.today().isoformat(),
            "notes": f"versions {res['versions']}; diacritizer Phonikud/phonikud-onnx@{res['drev']} phonikud-1.0.int8.onnx. Main wavs: text_nikud (Dicta vowels kept) plus hataama U+05AB and vocal shva U+05BD copied from the Phonikud diacritizer run on plain text, letter-aligned; transplanted for {n_ok}/{len(res['ipa'])} sentences (rest fall back to unmodified). plain/ = unmodified text_nikud phonemize() without stress. ipa.json holds both IPA strings. per_sentence_s includes diacritizer+phonemize+both syntheses. Python warnings: {res['warnings']}"}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False)[:1800])
    for k, v in list(res["ipa"].items())[:4]:
        print(k, v["plain"], "|", v["stress"])
