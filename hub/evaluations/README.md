---
license: cc-by-4.0
language:
- he
pretty_name: Hebrew TTS Evaluations
tags:
- hebrew
- tts-evaluation
- registry
configs:
- config_name: evals
  data_files:
  - split: all
    path: evals.jsonl
- config_name: runs
  data_files:
  - split: all
    path: runs.jsonl
---

# Hebrew TTS Evaluations

The register of Hebrew text-to-speech evaluations run for [Hebrish](https://hebrish.app): when each ran, which
models it included, the sentence set and the raw run parameters. One source of truth, added to as evaluations are run.

- **`evals`**: one row per evaluation. Date, purpose, scope, sentence set and its revision, models, counts, and links
  to the results dataset, the listening Space, the clip index (`data_json`) and the code at the commit that made it.
- **`runs`**: one row per model run inside an evaluation. The model and the revision it ran, the input (`plain` Hebrew
  or `nikud`), voice or reference clip, hardware, sample rate, load and per-sentence time, licence, publisher, release
  date, training origin, the script, and notes from the run.

Rows are written by `scripts/register_eval.py` in each evaluation's repo; re-registering an evaluation replaces its
rows. Listening notes are kept privately and are not part of this dataset.

| Evaluation | Date | Models | Runs |
| --- | --- | --- | --- |
| [Hebrew TTS Bake-off 11/26](https://github.com/danielrosehill/Hebrew-TTS-Bakeoff-1126) | 2026-11-18 | 10 | 17 |

Index of all Hebrew evaluations: [Hebrew-AI-Evaluations](https://github.com/danielrosehill/Hebrew-AI-Evaluations).
