"""Bakeoff candidate f5-hebrew-v2: Yzamari/f5tts-hebrew-v2 (F5-TTS, Hebrew fine-tune). Run: modal-dsr run models/f5-hebrew-v2-nikud.py"""
import json, pathlib, modal

SLUG, HF_ID = "f5-hebrew-v2-nikud", "Yzamari/f5tts-hebrew-v2"
image = (modal.Image.debian_slim(python_version="3.11")
         .apt_install("ffmpeg", "libsndfile1")
         .pip_install("f5-tts==1.1.22", "safetensors", "soundfile", "huggingface_hub",
                      "transformers<4.50"))
app = modal.App(f"bakeoff-{SLUG}", image=image)

CFG = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, text_mask_padding=True, qk_norm=None,
           conv_layers=4, pe_attn_head=None, attn_backend="torch", attn_mask_enabled=False,
           checkpoint_activations=False)

@app.function(gpu="L4", timeout=1500)
def run(rows: list):
    import io, tarfile, time, csv, unicodedata, numpy as np, soundfile as sf, torch
    from huggingface_hub import hf_hub_download, HfApi
    from safetensors.torch import load_file
    from f5_tts.infer.utils_infer import infer_process, load_vocoder
    from f5_tts.model import CFM, DiT
    from f5_tts.model.utils import get_tokenizer

    t0 = time.time()
    rev = HfApi().model_info(HF_ID).sha
    vocab_path = hf_hub_download(HF_ID, "vocab.txt")
    ckpt = hf_hub_download(HF_ID, "model.safetensors")
    cmap, vsize = get_tokenizer(vocab_path, "custom")
    model = CFM(transformer=DiT(**CFG, text_num_embeds=vsize, mel_dim=100),
                mel_spec_kwargs=dict(n_fft=1024, hop_length=256, win_length=1024, n_mel_channels=100,
                                     target_sample_rate=24000, mel_spec_type="vocos"),
                odeint_kwargs=dict(method="euler"), vocab_char_map=cmap)
    model.load_state_dict(load_file(ckpt, device="cpu"), strict=True)
    model = model.eval().to("cuda")
    vocoder = load_vocoder("vocos", device="cpu").eval().to("cuda")

    # Reference clip: the model repo and demo ship none, so use a Fleurs he_il dev clip (female, 6-10 s)
    tsv = hf_hub_download("google/fleurs", "data/he_il/dev.tsv", repo_type="dataset")
    rowsv = [r for r in csv.reader(open(tsv, encoding="utf-8"), delimiter="\t") if len(r) >= 7 and r[5].isdigit()]
    fem = [r for r in rowsv if r[6].strip().upper().startswith("F")] or rowsv
    fem = [r for r in fem if len(r[2]) < 200] or fem
    ref = min(fem, key=lambda r: abs(int(r[5]) - 9 * 16000))
    tar = hf_hub_download("google/fleurs", "data/he_il/audio/dev.tar.gz", repo_type="dataset")
    with tarfile.open(tar) as tf:
        m = [x for x in tf.getmembers() if x.name.endswith(ref[1])][0]
        pathlib.Path("/tmp/ref.wav").write_bytes(tf.extractfile(m).read())
    ref_text = " ".join(ref[2].split())  # raw transcription (cased/punctuated, no nikud)
    ref_note = f"fleurs he_il dev {ref[1]} ({ref[5]} samples@16k), transcript: {ref_text}"
    # Vocalize the reference transcript the same way as the target sentences (DictaBERT)
    try:
        from transformers import AutoModel, AutoTokenizer
        tk = AutoTokenizer.from_pretrained("dicta-il/dictabert-large-char-menaked")
        dm = AutoModel.from_pretrained("dicta-il/dictabert-large-char-menaked", trust_remote_code=True).eval()
        out = dm.predict([ref_text], tk)[0]
        ref_text = unicodedata.normalize("NFC", out) if isinstance(out, str) else ref_text
        ref_note += f" -> vocalized: {ref_text}"
    except Exception as e:
        ref_note += f" (vocalization failed, plain used: {e!r})"
    if ref_text[-1] not in ".!?": ref_text += "."
    ref_text += " "
    load_s = time.time() - t0

    outs, times, warn = {}, {}, []
    for r in rows:
        text = " ".join(r["text_nikud"].split())
        bad = sorted({c for c in text if c not in cmap})
        if bad: warn.append(f'{r["id"]}: chars not in vocab {bad}')
        torch.cuda.synchronize(); t = time.time()
        wav, sr, _ = infer_process("/tmp/ref.wav", ref_text, text, model, vocoder, mel_spec_type="vocos",
                                   nfe_step=32, cfg_strength=2.0, speed=1.0, device="cuda")
        torch.cuda.synchronize(); times[r["id"]] = round(time.time() - t, 2)
        buf = io.BytesIO(); sf.write(buf, np.asarray(wav, dtype=np.float32), sr, format="WAV", subtype="PCM_16")
        outs[r["id"]] = buf.getvalue()
    return dict(rev=rev, sr=sr, load_s=round(load_s, 1), times=times, outs=outs, ref_note=ref_note, warn=warn)

@app.local_entrypoint()
def main():
    import datetime
    rows = [json.loads(l) for l in open("data/sentences.jsonl", encoding="utf-8") if l.strip()]
    res = run.remote(rows)
    d = pathlib.Path("results") / SLUG; d.mkdir(parents=True, exist_ok=True)
    for k, b in res["outs"].items(): (d / f"{k}.wav").write_bytes(b)
    meta = dict(slug=SLUG, hf_id=HF_ID, revision=res["rev"], licence="apache-2.0", input="nikud",
                voice="cloned from reference clip (no built-in voice shipped in the HF repo)",
                reference_clip=res["ref_note"], gpu="L4", sample_rate=res["sr"], load_s=res["load_s"],
                per_sentence_s=res["times"], generated=datetime.date.today().isoformat(),
                notes="DictaBERT nikud (text_nikud) used; card trained on Phonikud G2P vocalization with stress marks, not reproduced. "
                      "nfe_step=32, cfg_strength=2.0, speed=1.0, euler. Warnings: " + "; ".join(res["warn"]))
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False)[:1500])
