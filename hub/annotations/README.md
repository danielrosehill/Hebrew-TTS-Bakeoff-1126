---
license: cc-by-4.0
language:
- he
- en
pretty_name: Hebrew TTS Listening Annotations
tags:
- hebrew
- tts-evaluation
- human-annotation
- voice-notes
---

# Hebrew TTS Listening Annotations

Daniel Rosehill's own listening annotations of Hebrew text-to-speech evaluations (part of [Hebrish](https://hebrish.app)),
made with the [TTS Pronunciation Annotation Starter](https://github.com/danielrosehill/TTS-Pronunciation-Annotation-Starter).
Evaluations are listed in [Hebrish/Hebrew-TTS-Evaluations](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Evaluations).

Method: **screen, then rank**. Each clip is first passed or failed as a whole (a fail carries a reason category; word-level
detail such as the syllable stressed vs the one that should be, or IPA heard vs expected, is optional). Clips that pass
then meet head to head, blind, ranked with Bradley-Terry.

| Path | What |
| --- | --- |
| `annotations/<eval_id>/screen.jsonl` | Pass/fail per clip (`tts-annotation/2`); the latest line per (run, sentence) wins |
| `annotations/<eval_id>/pairs.jsonl` | Pairwise comparisons among passing clips (`tts-pairwise/1`) |
| `annotations/<eval_id>/voice.jsonl` + `voice/<id>.webm` | Spoken annotations: the recording, then a `processed` line with the verbatim transcript and the structured reading a model applied (screen rows derived from a note carry `source: "voice:<id>"`) |
| `annotations/<eval_id>.jsonl` | One early annotation in the first (1-5 scale) format |
