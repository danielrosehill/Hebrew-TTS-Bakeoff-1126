#!/usr/bin/env python3
"""Publish every generated clip as one audio dataset: Hebrish/Hebrew-TTS-Bakeoff-1126 (split `test`).

One row per (model run, sentence): the same runs the listening Space shows (scripts/build_space.py `runs()`), with the
sentence text, how the model was fed (plain or nikud), the run settings and the model's provenance from data/models.json.

    uv run --with datasets --with soundfile --with huggingface_hub python scripts/publish_results.py
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_space import ROOT, base_of, runs  # noqa: E402

REPO = "Hebrish/Hebrew-TTS-Bakeoff-1126"


def main():
    from datasets import Audio, Dataset
    sentences = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    prov = {m["slug"]: m for m in json.loads((ROOT / "data/models.json").read_text())}
    rows = []
    for slug, (meta, folder) in runs():
        base, label = base_of(slug)
        p = prov.get(base, {})
        for s in sentences:
            wav = folder / f"{s['id']}.wav"
            if not wav.exists():
                continue
            rows.append({"run": slug, "model": base, "variant": label.strip(" ·") or "main", "input": meta.get("input"),
                         "sentence_id": s["id"], "text": s["text"], "text_nikud": s["text_nikud"], "english": s["english"],
                         "focus": s["focus"], "audio": str(wav), "hf_id": meta.get("hf_id"), "voice": str(meta.get("voice")),
                         "sample_rate": meta.get("sample_rate"), "hardware": str(meta.get("gpu")),
                         "seconds_to_generate": (meta.get("per_sentence_s") or {}).get(s["id"]),
                         "publisher": p.get("publisher"), "publisher_type": p.get("publisher_type"),
                         "release_date": p.get("release_date"), "training_origin": p.get("training_origin"),
                         "licence": p.get("licence") or meta.get("licence"), "run_notes": meta.get("notes")})
    ds = Dataset.from_list(rows).cast_column("audio", Audio())
    ds.push_to_hub(REPO, split="test", commit_message=f"{len(rows)} clips from {len({r['run'] for r in rows})} runs")
    print(len(rows), "rows ->", REPO)


if __name__ == "__main__":
    main()
