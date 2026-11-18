#!/usr/bin/env python3
"""Register this evaluation in Hebrish/Hebrew-TTS-Evaluations: the source of truth for every Hebrew TTS evaluation
Daniel runs (Daniel, 2026-11-18): when it ran, which models, the sentence set, and the raw run parameters.

Two configs in the dataset: `evals` (evals.jsonl, one row per evaluation) and `runs` (runs.jsonl, one row per model run
in an evaluation). Rows of the same eval_id are replaced; other evaluations' rows are kept. The listening-notes Space
reads `evals` to list the evaluations it can annotate (`data_json` is the clip index it plays from).

    uv run --with huggingface_hub python scripts/register_eval.py            # dry run: prints the rows
    uv run --with huggingface_hub python scripts/register_eval.py --push
"""
import json, subprocess, sys
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

ROOT = Path(__file__).resolve().parent.parent
REPO = "Hebrish/Hebrew-TTS-Evaluations"
EVAL = {
    "eval_id": "hebrew-tts-bakeoff-1126",
    "title": "Hebrew TTS Bake-off 11/26",
    "task": "text-to-speech",
    "date": "2026-11-18",
    "purpose": "Pick the reference voice the Hebrish recorder plays before a learner reads a Hebrew sentence aloud from "
               "nikud; measure each model's nikud inference (plain text vs checked nikud).",
    "scope": "Open models (weights on Hugging Face); Fish S2 Pro run through its publisher's API",
    "sentence_set": "Hebrish/Hebrew-TTS-Eval-Set",
    "sentence_set_revision": "667f8dac2eaab969cb0c275ffe976d1aab9896fc",
    "results_dataset": "Hebrish/Hebrew-TTS-Bakeoff-1126",
    "listening_space": "Hebrish/Hebrew-TTS-Bakeoff-1126",
    "data_json": "https://huggingface.co/spaces/Hebrish/Hebrew-TTS-Bakeoff-1126/resolve/main/data.json",
    "repo": "https://github.com/danielrosehill/Hebrew-TTS-Bakeoff-1126",
    "annotation_axes": ["naturalness (1-5)", "clarity (1-5)", "hebrew (1-5)", "nikud (yes/no)", "use (yes/maybe/no)", "word_issues (stress, mispronunciation, minor)", "note"],
}


def runs():
    prov = {m["slug"]: m for m in json.loads((ROOT / "data/models.json").read_text())}
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_space import base_of, runs as all_runs
    out = []
    for slug, (meta, folder) in all_runs():
        base, label = base_of(slug)
        p, t = prov.get(base, {}), meta.get("per_sentence_s") or {}
        out.append({
            "eval_id": EVAL["eval_id"], "run": slug, "model": base, "variant": label.strip(" ·") or "main",
            "input": meta.get("input"), "hf_id": meta.get("hf_id"), "revision": str(meta.get("revision")),
            "voice": str(meta.get("voice")), "reference_clip": str(meta.get("reference_clip")),
            "hardware": str(meta.get("gpu")), "sample_rate": meta.get("sample_rate"), "load_s": meta.get("load_s"),
            "mean_s_per_sentence": round(sum(t.values()) / len(t), 2) if t else None, "clips": len(list(folder.glob("s*.wav"))),
            "generated": meta.get("generated") or EVAL["date"], "licence": p.get("licence") or meta.get("licence"),
            "publisher": p.get("publisher"), "publisher_type": p.get("publisher_type"), "release_date": p.get("release_date"),
            "training_origin": p.get("training_origin"), "script": f"models/{slug.removesuffix('-plain')}.py",
            "run_notes": meta.get("notes"),
        })
    return out


def merge(existing, new, eval_id):
    return [r for r in existing if r.get("eval_id") != eval_id] + new


def main():
    rs = runs()
    ev = dict(EVAL, models=sorted({r["model"] for r in rs}), n_models=len({r["model"] for r in rs}), n_runs=len(rs),
              n_clips=sum(r["clips"] for r in rs),
              repo_commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())
    if "--push" not in sys.argv:
        print(json.dumps(ev, ensure_ascii=False, indent=1)); print(len(rs), "runs"); return
    a = HfApi()
    a.create_repo(REPO, repo_type="dataset", exist_ok=True)

    def get(name):
        try:
            return [json.loads(l) for l in open(hf_hub_download(REPO, name, repo_type="dataset", force_download=True), encoding="utf8") if l.strip()]
        except Exception:
            return []
    tmp = ROOT / "hub/evaluations"
    tmp.mkdir(parents=True, exist_ok=True)
    for name, rows in (("evals.jsonl", merge(get("evals.jsonl"), [ev], ev["eval_id"])), ("runs.jsonl", merge(get("runs.jsonl"), rs, ev["eval_id"]))):
        (tmp / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    c = a.upload_folder(repo_id=REPO, repo_type="dataset", folder_path=str(tmp), commit_message=f"Register {ev['eval_id']}")
    print(c.commit_url)


if __name__ == "__main__":
    main()
