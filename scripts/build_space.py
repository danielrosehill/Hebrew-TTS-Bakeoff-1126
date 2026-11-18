#!/usr/bin/env python3
"""Build the public listening Space (static) from data/ and results/.

    python3 scripts/build_space.py            # writes space/ (index.html, data.json, audio/<slug>/<id>.mp3)
    python3 scripts/build_space.py --push     # and uploads it to the HF Space Hebrish/Hebrew-TTS-Bakeoff-1126

Audio: every results/<slug>/sNN.wav becomes space/audio/<slug>/sNN.mp3 (64 kbps mono, ffmpeg; a few MB in all).
results/phonikud-piper/plain/ is listed as its own row, `phonikud-piper-plain` (the same voice without the stress marks).
Models without a meta.json are skipped, so the page can be rebuilt as runs finish.
"""
import json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "space"
SPACE = "Hebrish/Hebrew-TTS-Bakeoff-1126"
# Display order: nikud-aware first, then the Hebrew-specific plain-text models, then multilingual ones.
ORDER = ["phonikud-piper", "piper-he-noa", "kokoro-hebrew", "bluev3", "f5-hebrew-v2",
         "zonos3-mini", "chatterbox-multilingual", "voxcpm2", "omnivoice", "fish-s2-pro",
         "gemini-flash-tts", "elevenlabs-v3", "openai-tts", "google-cloud-tts"]
# Variants of one model sit right after it (Daniel, 2026-11-18: "the same sentence with and without the nikud").
# Longest suffix first: "-male-nikud" must match before "-nikud". Male-voice runs (models/male-voices-api.py) are
# variants of the same model, so they share its provenance row in data/models.json.
VARIANTS = {"-male-nikud": " · male voice, with our nikud", "-male": " · male voice", "-nikud": " · with our nikud",
            "-auto": " · its own nikud", "-plain": " · no stress marks"}
# Voice gender of each model's main (default) voice, for the leaderboard's "Best by voice" panel. A run's own meta
# `voice_gender` wins (the -male runs set it). Only voices whose gender is documented or was checked by ear/pitch are
# listed; the rest stay unset (chatterbox, f5, fish, voxcpm2, phonikud: default or cloned voices, not checked).
VOICE_GENDER = {"gemini-flash-tts": "female", "gemini-3.8-flash-tts": "female", "gemini-3.8-flash-lite-tts": "female",
                "gemini-2.5-pro-tts": "female", "gemini-2.5-flash-tts": "female", "gemini-3.8-live": "female",
                "gemini-3.1-flash-live": "female", "gemini-2.5-native-audio": "female",  # Kore
                "google-cloud-tts": "female", "elevenlabs-v3": "female", "elevenlabs-v4": "female",  # Kore, Rachel
                "openai-tts": "female", "openai-gpt-audio": "female", "xai-tts": "female",  # coral, coral, eve
                "inworld-tts-2": "female", "minimax-speech-2.8-hd": "female", "piper-he-noa": "female",
                "bluev3": "female", "omnivoice": "female", "zonos3-mini": "female",  # noa, voice design "female", Savannah
                "kokoro-hebrew": "male"}  # he_shaul (SASPEECH, one male speaker)


def base_of(slug):
    for suf in VARIANTS:
        if slug.endswith(suf):
            return slug[: -len(suf)], VARIANTS[suf]
    return slug, ""


def rank(slug):
    b, v = base_of(slug)
    order = ["", " · with our nikud", " · its own nikud", " · no stress marks", " · male voice", " · male voice, with our nikud"]
    return (ORDER.index(b) if b in ORDER else 99, order.index(v) if v in order else 9)


def generated_via(meta):
    """How a run's clips were made, in words, for the annotation app (Daniel, 2026-11-18: "record when the clips were
    generated, how they were generated"). An explicit meta `generated_via` (API runs set it) wins."""
    if meta.get("generated_via"):
        return meta["generated_via"]
    hw = str(meta.get("gpu") or "")
    if "api" in hw.lower():
        return hw
    hw = "CPU" if "cpu" in hw.lower() or hw.lower().startswith("none") else (hw.replace("|", " or ") + " GPU").replace("NVIDIA ", "")
    return f"self-hosted on Modal ({hw})"


def runs():
    found = {}
    for meta in sorted(ROOT.glob("results/*/meta.json")):
        slug = meta.parent.name
        m = json.loads(meta.read_text())
        m["generated_via"] = generated_via(m)
        m.setdefault("generated", "2026-11-18")
        if not m.get("voice_gender") and VOICE_GENDER.get(base_of(slug)[0]):
            m["voice_gender"] = VOICE_GENDER[base_of(slug)[0]]
        found[slug] = (m, meta.parent)
        if (meta.parent / "plain").is_dir():
            m = dict(found[slug][0], slug=f"{slug}-plain",
                     notes="Same voice and nikud, without the Phonikud stress and vocal-shva marks (plain phonemize()): "
                           "how the recorder's Listen clips sounded before this bake-off.")
            found[f"{slug}-plain"] = (m, meta.parent / "plain")
    return sorted(found.items(), key=lambda kv: rank(kv[0]))


VOWELS = set("aeiouə")
METRICS = json.loads((ROOT / "data/clip_metrics.json").read_text()) if (ROOT / "data/clip_metrics.json").exists() else {}
REF = ROOT / "results/phonikud-piper/ipa.json"


def syllables(ipa_word):
    """Split one IPA word into syllables at each vowel (onset consonants go with the vowel, trailing ones with the last
    syllable) and return (syllables, index of the stressed one or None). Display aid for stress tags, not phonology."""
    w = re.sub(r"[.,!?:;\"'()]", "", ipa_word)
    out, pend, stress = [], "", None
    for ch in w:
        pend += ch
        if ch in VOWELS:
            if "ˈ" in pend:
                stress = len(out)
            out.append(pend.replace("ˈ", ""))
            pend = ""
    if pend:
        out = out[:-1] + [out[-1] + pend.replace("ˈ", "")] if out else [pend.replace("ˈ", "")]
    return out, stress


def add_words(sentences):
    """Per-word reference for word-level annotation (Daniel, 2026-11-18: stress heard vs correct, IPA heard vs expected).
    Source: the Phonikud IPA with stress marks (results/phonikud-piper/ipa.json, `stress`): a machine reference, so the
    annotation UI labels it "check it"."""
    if not REF.exists():
        return
    ref = json.loads(REF.read_text())
    for s in sentences:
        nik, ipa = s["text_nikud"].split(), ref.get(s["id"], {}).get("stress", "").split()
        if len(nik) != len(ipa):
            continue
        s["words"] = []
        for i, (n, w) in enumerate(zip(nik, ipa), 1):
            syl, st = syllables(w)
            s["words"].append({"position": i, "nikud": n.strip(".,!?:;\"'()"), "ipa_ref": re.sub(r"[.,!?:;\"'()]", "", w),
                               "syllables": syl, "stress_ref": st})
        s["words_source"] = "Phonikud phonemize() on the checked nikud with Phonikud diacritizer stress marks (machine reference)"


ROUND1 = ["s01"]  # what round 1 actually played; s02-s20 were generated up front (2026-11-18) and are not served


def load_items():
    """The 20 eval-set sentences plus the items of later rounds (data/rounds/round<N>.jsonl), each with its `round`."""
    items = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    for s in items:
        s["round"] = 1 if s["id"] in ROUND1 else None
    for f in sorted((ROOT / "data/rounds").glob("round*.jsonl")):
        items += [json.loads(l) for l in open(f, encoding="utf8") if l.strip()]
    return items


def main():
    sentences = load_items()
    add_words(sentences)
    prov = {m["slug"]: m for m in json.loads((ROOT / "data/models.json").read_text())} if (ROOT / "data/models.json").exists() else {}
    if OUT.exists():
        shutil.rmtree(OUT / "audio", ignore_errors=True)
    (OUT / "audio").mkdir(parents=True, exist_ok=True)
    models = []
    for slug, (meta, folder) in runs():
        base, label = base_of(slug)
        dest = OUT / "audio" / slug
        dest.mkdir(parents=True, exist_ok=True)
        clips = {}
        for s in sentences:
            wav = folder / f"{s['id']}.wav"
            if wav.exists():
                # Listening copies are loudness-normalised (Daniel, 2026-11-18: levels varied from near-silent F5 to clipping),
                # so every voice plays at the same level; raw levels are kept in data/clip_metrics.json and the WAVs.
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af", "loudnorm=I=-18:TP=-1.5:LRA=11", "-ar", "44100",
                                "-ac", "1", "-b:a", "64k", str(dest / f"{s['id']}.mp3")], check=True)
                clips[s["id"]] = f"audio/{slug}/{s['id']}.mp3"
        p = prov.get(base, {})
        models.append({"slug": slug, "run": meta, "provenance": p, "clips": clips, "metrics": METRICS.get(slug, {}),
                       "base": base, "name": (p.get("name") or meta.get("hf_id") or slug) + label})
    data = {"title": "Hebrew TTS Bake-off 11/26", "built": __import__("datetime").date.today().isoformat(),
            "sentences": sentences, "models": models}
    (OUT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    shutil.copy(ROOT / "scripts/space_index.html", OUT / "index.html")
    (OUT / "README.md").write_text(
        "---\ntitle: Hebrew TTS Bake-off 11/26\nemoji: 🔊\ncolorFrom: blue\ncolorTo: indigo\nsdk: static\npinned: false\n"
        "license: cc-by-4.0\nshort_description: Open Hebrew TTS models side by side on 20 sentences\n---\n\n"
        "Listening page for [Hebrew-TTS-Bakeoff-1126](https://github.com/danielrosehill/Hebrew-TTS-Bakeoff-1126), "
        "sentences from [Hebrish/Hebrew-TTS-Eval-Set](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Eval-Set). "
        "Part of [Hebrish](https://hebrish.app). Generated by `scripts/build_space.py`; do not edit here.\n")
    print(f"{len(models)} models, {sum(len(m['clips']) for m in models)} clips -> {OUT}")
    if "--push" in sys.argv:
        from huggingface_hub import HfApi
        a = HfApi()
        a.create_repo(SPACE, repo_type="space", space_sdk="static", exist_ok=True)
        c = a.upload_folder(repo_id=SPACE, repo_type="space", folder_path=str(OUT), delete_patterns=["audio/**"],
                            commit_message=f"Rebuild: {len(models)} models")
        print(c.commit_url)


if __name__ == "__main__":
    main()
