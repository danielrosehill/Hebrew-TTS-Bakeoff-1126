#!/usr/bin/env python3
"""Generate one round of items for the surviving runs only (Daniel, 2026-11-18: "generate in rounds"; Canopy preference
`evals-generate-in-rounds`; ai-eval skill `screen-then-rank`).

The model scripts read data/sentences.jsonl and write results/<run>/<id>.wav + meta.json. To run them on a new item
without touching round 1, this copies the repo (no results, no .git) to a scratch folder whose data/sentences.jsonl
holds only the round's items, runs each script there (Modal scripts on residencehome through modal-dsr, API scripts
here through with-secrets), then copies back only the new item's WAVs and merges their timings into the real meta.json.

    python3 scripts/run_round.py --items data/rounds/round2.jsonl --runs bluev3,kokoro-hebrew,...   # dry run: the plan
    python3 scripts/run_round.py --items data/rounds/round2.jsonl --runs ... --go

Survivors: runs with a Pass and no Fail in the screen (latest verdict per clip), plus, optionally, runs not yet
screened. `--survivors` prints them from the annotations dataset.
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST, REMOTE = "residencehome", "~/tmp/hebrew-tts-round"
NOTES = "danielrosehill/Hebrew-TTS-Listening-Notes"
EVAL = "hebrew-tts-bakeoff-1126"


def survivors():
    from huggingface_hub import hf_hub_download
    rows = []
    for f in ("screen.jsonl", "screen-voice.jsonl"):
        try:
            rows += [json.loads(l) for l in open(hf_hub_download(NOTES, f"annotations/{EVAL}/{f}", repo_type="dataset", force_download=True)) if l.strip()]
        except Exception:
            pass
    latest = {}
    for r in sorted(rows, key=lambda r: r.get("saved", "")):
        latest[(r["run"], r["sentence"])] = r["verdict"]
    runs = {d.name for d in (ROOT / "results").iterdir() if (d / "meta.json").exists()}
    failed = {run for (run, _), v in latest.items() if v == "fail"}
    passed = {run for (run, _), v in latest.items() if v == "pass"} - failed
    return sorted(passed), sorted(runs - passed - failed)


def script_for(run):
    """(script, is_api, runs it writes). API scripts write the plain and -nikud run together."""
    base = run.removesuffix("-nikud")
    api = ROOT / f"models/{base}-api.py"
    if api.exists():
        return api, True, [base, base + "-nikud"]
    return ROOT / f"models/{run}.py", False, [run]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items")
    ap.add_argument("--runs", help="comma-separated run slugs")
    ap.add_argument("--survivors", action="store_true")
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    if a.survivors:
        p, u = survivors()
        print("passed:", ",".join(p)); print("not screened:", ",".join(u)); return
    items = [json.loads(l) for l in open(a.items, encoding="utf8") if l.strip()]
    want = a.runs.split(",")
    jobs = {}
    for r in want:
        sc, api, writes = script_for(r)
        jobs.setdefault(sc, (api, set()))[1].update(w for w in writes if w in want or api)
    for sc, (api, writes) in jobs.items():
        print(("API  " if api else "Modal"), sc.name, "->", ", ".join(sorted(writes)))
    if not a.go:
        print(f"{len(items)} item(s) x {len(want)} run(s); add --go"); return
    scratch = Path("/tmp/hebrew-tts-round")
    shutil.rmtree(scratch, ignore_errors=True)
    shutil.copytree(ROOT, scratch, ignore=shutil.ignore_patterns(".git", "results", "space", "hub", "__pycache__"))
    (scratch / "results").mkdir()
    (scratch / "data/sentences.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf8")
    modal = [sc for sc, (api, _) in jobs.items() if not api]
    if modal:
        subprocess.run(["ssh", HOST, f"rm -rf {REMOTE} && mkdir -p {REMOTE}"], check=True)
        subprocess.run(["rsync", "-a", f"{scratch}/", f"{HOST}:{REMOTE}/"], check=True)
        # one at a time on the server: CPU jobs are seconds; GPU ones a minute or two each
        cmds = " ; ".join(f"echo '== {sc.name}' && ~/.local/bin/modal-dsr run models/{sc.name} 2>&1 | tail -3" for sc in modal)
        subprocess.run(["ssh", HOST, f"cd {REMOTE} && {cmds}"])
        subprocess.run(["rsync", "-a", f"{HOST}:{REMOTE}/results/", f"{scratch}/results/"], check=True)
    for sc, (api, _) in jobs.items():
        if api:
            subprocess.run(["with-secrets", "uv", "run", "-q", "--with", "google-auth", "--with", "requests", "python", str(scratch / "models" / sc.name)], cwd=scratch)
    for run in sorted({w for _, (_, ws) in jobs.items() for w in ws}):
        src, dst = scratch / "results" / run, ROOT / "results" / run
        if not (src / "meta.json").exists():
            print("MISSING", run); continue
        new = json.loads((src / "meta.json").read_text())
        old = json.loads((dst / "meta.json").read_text())
        for i in items:
            w = src / f"{i['id']}.wav"
            if w.exists():
                shutil.copy(w, dst / w.name)
                old.setdefault("per_sentence_s", {})[i["id"]] = (new.get("per_sentence_s") or {}).get(i["id"])
        old.setdefault("rounds", {})[items[0].get("round", 2)] = {"items": [i["id"] for i in items], "generated": new.get("generated")}
        (dst / "meta.json").write_text(json.dumps(old, ensure_ascii=False, indent=1))
        print("ok", run, [i["id"] for i in items if (src / f"{i['id']}.wav").exists()])


if __name__ == "__main__":
    main()
