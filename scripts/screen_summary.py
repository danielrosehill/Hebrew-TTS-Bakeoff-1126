#!/usr/bin/env python3
"""Record the screen (pass 1) as part of the evaluation: who survived, who failed, on which item, why, in the
annotator's own words (Daniel, 2026-11-18: "make sure all these failures are recorded in the dataset and the
evaluation, because that's actually very valuable data").

Reads the public annotations dataset (danielrosehill/Hebrew-TTS-Listening-Notes: screen.jsonl + screen-voice.jsonl,
voice.jsonl + voice-applied.jsonl), takes the latest verdict per (run, item), and writes:
  data/screen_results.json   per run: status (survivor | out | not screened), verdicts per item, fail reasons,
                             observations, first fail, and the annotator's words (tidied voice-note transcript or note)
  README.md                  the table between <!-- screen:begin --> and <!-- screen:end -->
register_eval.py adds status and reasons to each run's row in Hebrish/Hebrew-TTS-Evaluations.

    uv run --with huggingface_hub python scripts/screen_summary.py
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
NOTES, EVAL = "danielrosehill/Hebrew-TTS-Listening-Notes", "hebrew-tts-bakeoff-1126"


def load(f):
    from huggingface_hub import hf_hub_download
    try:
        return [json.loads(l) for l in open(hf_hub_download(NOTES, f"annotations/{EVAL}/{f}", repo_type="dataset", force_download=True), encoding="utf8") if l.strip()]
    except Exception:
        return []


def main():
    from build_space import runs
    rows = sorted(load("screen.jsonl") + load("screen-voice.jsonl"), key=lambda r: r.get("saved", ""))
    latest = {}
    for r in rows:
        latest[(r["run"], r["sentence"])] = r
    said = {}
    clean = {v["target"]: v.get("transcript_clean") or v.get("transcript") for v in load("voice-applied.jsonl") if v.get("transcript")}
    for n in load("voice.jsonl"):
        if not n.get("type") and n["id"] in clean:
            said.setdefault((n.get("run"), n.get("sentence")), []).append(clean[n["id"]])
    out = {}
    for slug, (meta, _) in runs():
        items = {sid: r for (run, sid), r in latest.items() if run == slug and sid != "overall"}
        fails = {sid: r for sid, r in items.items() if r["verdict"] == "fail"}
        status = "out" if fails else "survivor" if items else "not screened"
        first = min(fails) if fails else None
        if first:
            words = said.get((slug, first)) or [fails[first].get("note") or ""]
        else:
            words = [w for sid in sorted(items) for w in said.get((slug, sid), [])] or [r.get("note") for r in items.values() if r.get("note")]
        out[slug] = {"status": status, "verdicts": {sid: r["verdict"] for sid, r in sorted(items.items())},
                     "fail_reasons": sorted({x for r in fails.values() for x in r.get("fail_reasons") or []}),
                     "observations": sorted({x for r in items.values() for x in r.get("observations") or []}),
                     "first_fail": first, "gender": next((r.get("gender") for r in items.values() if r.get("gender")), None),
                     "annotator_words": (words[0] or "")[:600] if words else "", "annotator": next((r.get("annotator") for r in items.values() if r.get("annotator")), None)}
    (ROOT / "data/screen_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    order = {"survivor": 0, "out": 1, "not screened": 2}
    lines = ["| Run | Status | Items heard | Why it failed | Observations | In the annotator's words |", "| --- | --- | --- | --- | --- | --- |"]
    for slug, r in sorted(out.items(), key=lambda kv: (order[kv[1]["status"]], kv[0])):
        q = r["annotator_words"].replace("|", "/").replace("\n", " ")
        lines.append(f"| `{slug}` | {r['status']} | {', '.join(f'{k} {v}' for k, v in r['verdicts'].items()) or '-'} | {', '.join(r['fail_reasons']) or '-'} | "
                     f"{', '.join(r['observations']) or '-'} | {(q[:220] + '…') if len(q) > 220 else q} |")
    block = "<!-- screen:begin -->\n" + "\n".join(lines) + "\n<!-- screen:end -->"
    readme = (ROOT / "README.md").read_text()
    if "<!-- screen:begin -->" in readme:
        readme = readme[:readme.index("<!-- screen:begin -->")] + block + readme[readme.index("<!-- screen:end -->") + len("<!-- screen:end -->"):]
    else:
        readme = readme.replace("## Layout", "## Screen results (pass 1)\n\nEvery run's pass/fail record from Daniel's listening, "
                                "written by `scripts/screen_summary.py` from the public annotations dataset "
                                "[`danielrosehill/Hebrew-TTS-Listening-Notes`](https://huggingface.co/datasets/danielrosehill/Hebrew-TTS-Listening-Notes). "
                                "A run is out at its first fail; survivors go on to head-to-head ranking on the round-2 paragraph.\n\n"
                                + block + "\n\n## Layout", 1)
    (ROOT / "README.md").write_text(readme)
    print({k: sum(1 for r in out.values() if r["status"] == k) for k in order})


if __name__ == "__main__":
    main()
