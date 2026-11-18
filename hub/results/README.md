---
license: other
license_name: per-model
language:
- he
task_categories:
- text-to-speech
pretty_name: Hebrew TTS Bake-off 11/26 (clips)
tags:
- hebrew
- nikud
- tts-evaluation
- synthetic
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*
---

# Hebrew TTS Bake-off 11/26: generated clips

340 clips: 10 open Hebrew TTS models (17 runs) reading the 20 sentences of
[Hebrish/Hebrew-TTS-Eval-Set](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Eval-Set), generated 2026-11-18.
Part of [Hebrish](https://hebrish.app). Listen side by side in the Space
[Hebrish/Hebrew-TTS-Bakeoff-1126](https://huggingface.co/spaces/Hebrish/Hebrew-TTS-Bakeoff-1126); method, code and
provenance: [GitHub](https://github.com/danielrosehill/Hebrew-TTS-Bakeoff-1126).

Where a model can take both, it was run on plain Hebrew (it infers the vowels) and on the checked nikud (`input`
`nikud`, `variant` "with our nikud"): the pair isolates its **nikud inference**.

All audio is synthetic. Each clip is under its model's licence (column `licence`); several are non-commercial.

| Column | Meaning |
| --- | --- |
| `run` | Run slug (`<model>`, `<model>-nikud`, `<model>-auto`, `<model>-plain`) |
| `model`, `variant`, `input` | Base model, variant label, `plain` or `nikud` |
| `sentence_id`, `text`, `text_nikud`, `english`, `focus` | The sentence |
| `audio` | The clip at the model's native sample rate |
| `hf_id`, `voice`, `sample_rate`, `hardware`, `seconds_to_generate` | Run settings |
| `publisher`, `publisher_type`, `release_date`, `training_origin`, `licence` | Model provenance |
| `run_notes` | Notes from the run |
