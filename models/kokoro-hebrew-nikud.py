"""Bake-off: kokoro-hebrew-nc fed Phonikud phonemes from our checked text_nikud (+ hataama/vocal-shva transplanted from the
Phonikud diacritizer, as in phonikud-piper.py). Also re-runs the renikud-on-plain variant and saves both phoneme sets."""
import json, time, datetime, pathlib
import modal

SLUG = "kokoro-hebrew-nikud"
HF_ID = "thewh1teagle/kokoro-hebrew-nc"
VOICE = "he_shaul"
HAT, VSHVA = "֫", "ֽ"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("libsndfile1", "espeak-ng")
    .pip_install("kokoro-onnx", "renikud-onnx", "phonikud", "phonikud-onnx", "soundfile", "huggingface_hub", "numpy")
)
app = modal.App(f"bakeoff-{SLUG}", image=image)


def clusters(s):
    out = []
    for ch in s:
        if "א" <= ch <= "ת":
            out.append([ch, ""])
        elif "֑" <= ch <= "ׇ" and out:
            out[-1][1] += ch
    return out


def transplant(given, diac):
    a, b = clusters(given), clusters(diac)
    if [x[0] for x in a] != [x[0] for x in b]:
        return None
    mk = {i: "".join(c for c in m if c in (HAT, VSHVA)) for i, (_, m) in enumerate(b)}
    ci, out = -1, []
    for ch in given:
        out.append(ch)
        if "א" <= ch <= "ת":
            ci += 1
            out.append(mk[ci])
    return "".join(out)


@app.function(cpu=4, memory=4096, timeout=1800)
def run(rows: list[dict]) -> dict:
    import io, soundfile as sf
    from huggingface_hub import hf_hub_download, HfApi
    from renikud_onnx import G2P
    from kokoro_onnx import Kokoro
    from phonikud import phonemize
    from phonikud_onnx import Phonikud
    t0 = time.time()
    model = hf_hub_download(HF_ID, "kokoro.onnx")
    voices = hf_hub_download(HF_ID, "voices-hebrew.bin")
    cfg = json.load(open(hf_hub_download(HF_ID, "config.json")))
    vocab = set(cfg["vocab"])
    g2p = G2P(hf_hub_download("thewh1teagle/renikud", "model.onnx", revision="neobert-130m"))
    dia = Phonikud(hf_hub_download("Phonikud/phonikud-onnx", "phonikud-1.0.int8.onnx"))
    rev = HfApi().model_info(HF_ID).sha
    kokoro = Kokoro(model, voices)
    load_s = time.time() - t0
    wavs, per, ph = {}, {}, {}
    for r in rows:
        t = time.time()
        diac = dia.add_diacritics(r["text"])
        tn = transplant(r["text_nikud"], diac)
        ok = tn is not None
        tn = tn or r["text_nikud"]
        p_nikud = phonemize(tn)
        p_plain_nikud = phonemize(r["text_nikud"])
        p_renikud = g2p.phonemize(r["text"])
        # synth from the phonikud phonemes exactly as produced (kokoro-onnx drops chars outside its vocab)
        samples, sr = kokoro.create(p_nikud, VOICE, is_phonemes=True, continuous=True)
        per[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
        wavs[r["id"]] = buf.getvalue()
        ph[r["id"]] = {"renikud_plain": p_renikud, "phonikud_nikud_marks": p_nikud, "phonikud_nikud_unmarked": p_plain_nikud,
                       "transplanted": ok, "nikud_used": tn, "outside_kokoro_vocab": sorted(set(p_nikud) - vocab)}
    sets = {k: sorted({c for v in ph.values() for c in v[k]}) for k in ("renikud_plain", "phonikud_nikud_marks")}
    missing = sorted({c for v in ph.values() for c in v["outside_kokoro_vocab"]})
    ren_ok = sorted(set(sets["renikud_plain"]) - vocab)
    return {"wavs": wavs, "ph": ph, "per": per, "sr": sr, "load_s": load_s, "rev": rev, "sets": sets, "missing": missing,
            "renikud_outside_vocab": ren_ok, "n_transplanted": sum(v["transplanted"] for v in ph.values())}


@app.local_entrypoint()
def main():
    rows = [json.loads(l) for l in open("data/sentences.jsonl") if l.strip()]
    res = run.remote(rows)
    out = pathlib.Path("results") / SLUG; out.mkdir(parents=True, exist_ok=True)
    for k, b in res["wavs"].items():
        (out / f"{k}.wav").write_bytes(b)
    (out / "phonemes.json").write_text(json.dumps({"charsets": res["sets"], "phonikud_chars_outside_kokoro_vocab": res["missing"],
                                                   "renikud_chars_outside_kokoro_vocab": res["renikud_outside_vocab"], "sentences": res["ph"]}, ensure_ascii=False, indent=1))
    meta = {"slug": SLUG, "hf_id": HF_ID, "revision": res["rev"], "licence": "other: non-commercial (terms of avris/kokoro-hebrew-saspeech)",
            "input": "nikud", "voice": VOICE, "reference_clip": "none (built-in voice)", "gpu": "none (CPU, 4 vCPU, ONNX Runtime)",
            "sample_rate": res["sr"], "load_s": round(res["load_s"], 1), "per_sentence_s": res["per"],
            "generated": datetime.date.today().isoformat(),
            "notes": f"Phonikud phonemize() on text_nikud with hataama U+05AB and vocal shva U+05BD transplanted from the Phonikud diacritizer (phonikud-onnx, run on plain text), letter-aligned: {res['n_transplanted']}/20 transplanted. Stress marks present: True. continuous=True. phonikud chars outside kokoro vocab (not mapped; kokoro-onnx drops them): {res['missing']}. phonemes.json has renikud_plain, phonikud_nikud_marks and phonikud_nikud_unmarked side by side; per_sentence_s includes diacritizer and both G2Ps."}
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps({k: meta[k] for k in ("sample_rate", "load_s", "per_sentence_s")}))
    print("charsets", json.dumps(res["sets"], ensure_ascii=False))
    print("phonikud outside vocab", res["missing"], "| renikud outside vocab", res["renikud_outside_vocab"], "| transplanted", res["n_transplanted"])
    for k in ("s01", "s05", "s12"):
        print(k, json.dumps(res["ph"][k], ensure_ascii=False))
