"""Bake-off model: thewh1teagle/piper-he-noa fed from OUR nikud (text_nikud).
Soundness: the noa voice's phoneme map is the standard Piper IPA table and its training frontend (renikud) emits the same
convention as Phonikud (ʔ ʁ χ, ˈ before the stressed vowel; checked on sample sentences). piper-tts's native hebrew step
(Nakdimon + own G2P) would accept pointed text (skips Nakdimon) but uses its own rules, not the trained convention, and
ignores our stress marks. So: Dicta nikud + hataama/vocal shva transplanted from the Phonikud diacritizer (as in
phonikud-piper) -> phonikud.phonemize -> piper phoneme ids -> noa voice. renikud-onnx cannot take pointed text."""
import json
import time
from pathlib import Path

import modal

SLUG, HF_ID = "piper-he-noa-nikud", "thewh1teagle/piper-he-noa"
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libsndfile1")
    .pip_install("piper-tts", "phonikud", "phonikud-onnx", "soundfile", "numpy", "huggingface_hub")
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
    from phonikud import phonemize
    from phonikud_onnx import Phonikud
    from piper import PiperVoice
    drev = HfApi().model_info("Phonikud/phonikud-onnx").sha
    dia = Phonikud(hf_hub_download("Phonikud/phonikud-onnx", "phonikud-1.0.int8.onnx", revision=drev))
    voice = PiperVoice.load(onnx)
    load_s = round(time.time() - t0, 2)
    out, times, ipas = {}, {}, {}
    for r in rows:
        t = time.time()
        diac = dia.add_diacritics(r["text"])
        tn = transplant(r["text_nikud"], diac)
        ok = tn is not None
        tn = tn or r["text_nikud"]
        ipa = phonemize(tn)
        ids = voice.phonemes_to_ids(list(ipa))
        y = np.asarray(voice.phoneme_ids_to_audio(ids), dtype=np.float32)
        if np.abs(y).max() > 1.5:
            y = y / 32768.0
        sr = voice.config.sample_rate
        buf = io.BytesIO()
        sf.write(buf, y, sr, format="WAV", subtype="PCM_16")
        out[r["id"]] = buf.getvalue()
        times[r["id"]] = round(time.time() - t, 2)
        missing = [c for c in ipa if c not in voice.config.phoneme_id_map]
        ipas[r["id"]] = {"transplanted": ok, "ipa": ipa, "nikud": tn, "symbols_not_in_voice_map": missing}
    notes = []
    return {"wavs": out, "times": times, "load_s": load_s, "sr": sr, "rev": rev, "warnings": notes, "ipa": ipas,
            "versions": {p: md.version(p) for p in ("piper-tts", "phonikud", "phonikud-onnx", "onnxruntime")}}


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
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": res["rev"], "licence": "cc-by-4.0", "input": "nikud",
            "voice": "noa (speaker 0, default; he_IL-noa-medium.onnx)", "reference_clip": None, "gpu": "none (cpu=4)",
            "sample_rate": res["sr"], "load_s": res["load_s"], "per_sentence_s": res["times"],
            "generated": datetime.date.today().isoformat(),
            "notes": f"Input nikud: Dicta text_nikud (vowels kept) + hataama U+05AB and vocal shva U+05BD transplanted from Phonikud/phonikud-onnx diacritizer run on plain text (same as phonikud-piper) -> phonikud {res['versions']['phonikud']} phonemize -> piper-tts {res['versions']['piper-tts']} phonemes_to_ids / phoneme_ids_to_audio on the noa voice (speaker 0, config defaults). Bypasses piper's native hebrew phonemizer. Symbols outside the voice's id map: {sorted({c for v in res['ipa'].values() for c in v['symbols_not_in_voice_map']})}. ipa.json has the IPA per sentence."}
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False)[:1500])
