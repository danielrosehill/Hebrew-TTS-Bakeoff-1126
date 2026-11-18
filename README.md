# Hebrew TTS Bake-off 11/26

A small listening comparison of **open Hebrew text-to-speech models**, run 2026-11-18, on 20 sentences given both
with and without nikud.

- **Listen:** [Space `Hebrish/Hebrew-TTS-Bakeoff-1126`](https://huggingface.co/spaces/Hebrish/Hebrew-TTS-Bakeoff-1126).
  Its views are by sentence, by model, nikud inference, and a table of the models.
- **Sentences:** [`Hebrish/Hebrew-TTS-Eval-Set`](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Eval-Set),
  20 rows, each with and without nikud. It is meant to be reused.
- **All clips:** [`Hebrish/Hebrew-TTS-Bakeoff-1126`](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Bakeoff-1126).
  This dataset has 340 rows, one per run and sentence, with an audio player, run settings and model provenance.

## Background

This bake-off is part of [Hebrish](https://hebrish.app), a speech-recognition project for English–Hebrew
code-switching. Its recording app has a Hebrew project where a learner reads Hebrew sentences aloud from nikud, and a
▶ Listen button plays a native reference voice first.

That reference voice was Phonikud with its Piper voice, pre-rendered per sentence. It sounded flat. It also stressed
many words on the last syllable (sef**ER** for סֵפֶר, yel**ED** for יֶלֶד), because the nikud carried no stress marks.
In addition, the newer sentence sets had no clips at all. This bake-off looks for a better voice. It also measures how
much the nikud matters to each model.

Scope is open models (weights on Hugging Face). The ivrit.ai
[Hebrew TTS Arena](https://huggingface.co/spaces/ivrit-ai/TTS-Arena-Hebrew) was checked first, on 2026-11-18. Its top
places are held by proprietary APIs: Gemini 3.1 Flash TTS, Deepdub, ElevenLabs v3 and Soniox. Its one open entry,
Blue V2, ranked #8 of 12. Candidates were chosen from Hugging Face models that say they support Hebrew.

## Nikud inference

Anyone reading unpointed Hebrew infers the vowels, whether that reader is a model or a person. The bake-off isolates
this skill. Where a model can take both forms, it is run twice:

- once on the plain text, where it has to infer the vowels
- once on the checked nikud, where the vowels are given

The difference between the two clips is that model's **nikud inference**.

Example (Kokoro-Hebrew, s12). On plain text it read הספר as *ha-sefer* ("the book"). Given the nikud, it read
*ha-sapar* ("the barber"). Its phonemes differ between the two inputs in 16 of 20 sentences
(`results/kokoro-hebrew-nikud/phonemes.json`).

## The sentences

There are 20 sentences:

- 10 from Tatoeba, two at each of five difficulty grades.
- 10 written by hand. Each targets one difficulty: segolate stress, the ספר homographs, times in words, a foreign
  surname, technical talk, material handling, English loanwords, and one long sentence with commas.

The nikud comes from DictaBERT (`dicta-il/dictabert-large-char-menaked`), checked word by word. The checking corrected
**12 words in 8 sentences**. The errors included both ספר homographs and הרגל read as *ha-regel* ("the leg") where
the sentence means *hergel* ("habit"). The raw diacritizer output is kept next to each fix.

## Models

| Run(s) | Model | Publisher | Released | Training | Input |
| --- | --- | --- | --- | --- | --- |
| `phonikud-piper`, `-auto`, `/plain` | Phonikud + Piper voice | Phonikud (community; Kolani, Melichov, Calev, Alper) | 2025-06-02 | Unresolved. The paper says the voices were fine-tuned from English on synthetic Hebrew. | Our nikud with stress marks added; its own diacritizer; nikud without stress |
| `piper-he-noa`, `-nikud` | Piper `noa` | thewh1teagle (individual) | 2026-10-26 | Fine-tuned from `en_US-ljspeech-medium` on synthetic Hebrew | Plain (renikud); our nikud |
| `kokoro-hebrew`, `-nikud` | Kokoro Hebrew | thewh1teagle (ONNX), avris (model) | 2026-07-05 | Fine-tuned from Kokoro-82M on SASPEECH | Plain (renikud); our nikud |
| `bluev3` | BlueV3 v3.0.1 | Maxim Melichov / notmax123 (individual) | 2026-11-14 | From scratch on 7 languages (inferred) | Plain. It strips nikud, so it has no nikud run. |
| `f5-hebrew-v2`, `-nikud` | F5-TTS Hebrew v2 | Yzamari (individual) | 2026-03-28 | Fine-tuned from F5-TTS v1 Base on 158 h | Plain; our nikud |
| `zonos3-mini` | ZONOS3-Mini | Zyphra (company) | 2026-11-09 | Multilingual, 43 languages | Plain |
| `chatterbox-multilingual`, `-nikud` | Chatterbox Multilingual v3 | Resemble AI (company) | 2025-09-04 (v3 weights 2026-04-22) | Multilingual, 23 languages | Plain; our nikud. Its own Dicta step is broken. |
| `voxcpm2` | VoxCPM2 | OpenBMB (community) | 2026-04-03 | Multilingual, 30 languages | Plain |
| `omnivoice` | OmniVoice | k2-fsa (community) | 2026-03-30 | 600+ languages, initialised from Qwen3-0.6B | Plain |
| `fish-s2-pro`, `-nikud` | Fish Audio S2 Pro | Fish Audio (company) | 2026-03-09 | 80+ languages, initialised from Qwen3-4B | Plain; our nikud. Run via Fish's API. |

**No model was trained from scratch on Hebrew-only audio.** Every Hebrew-specific model is either a fine-tune of an
English or multilingual model, or trained on several languages. The Phonikud voices are the one case left unresolved.

The full provenance is in `data/models.json`, with sources, and with the fields that were confirmed kept apart from
those that were inferred. Run settings, voices, hardware and timings are in `results/<run>/meta.json`.

### Run notes

- **ZONOS3-Mini** has no Hebrew voice. It speaks in its American English release voice (Savannah).
- **OmniVoice** was run with voice design, which is trained on Chinese and English only. Its weights are
  CC-BY-NC.
- **Chatterbox** has a built-in Hebrew step that adds nikud with Dicta, and that step fails in the current release. So
  the plain run is Chatterbox's raw guess at the vowels.
- **Fish S2 Pro** was too slow to self-host here. The bf16 eager run on an L4 went at about 13 minutes per sentence.
  It was stopped and run through Fish Audio's API instead, with model header `s2-pro`, the same open model.
- **F5-Hebrew v2** ships no reference voice. It used a FLEURS he_il clip, `635125425165791315.wav`.
- **piper-he-noa** was first run through piper-tts's built-in Hebrew front end (Nakdimon), which is not the one the
  voice was trained on. It was redone with renikud. The first run is kept in `results/piper-he-noa/nakdimon-default/`.

## Layout

| Path | What |
| --- | --- |
| `data/sentences.jsonl` | The 20 sentences, the same rows as the eval set on the Hub |
| `data/dictabert-raw.jsonl` | The diacritizer's raw output |
| `data/models.json` | Provenance per model |
| `models/<run>.py` | One Modal app per run. See `models/CONTRACT.md`. `fish-s2-pro-api.py` calls Fish's API instead. |
| `results/<run>/` | `meta.json`, plus `ipa.json` / `phonemes.json` / `nikud.json` where they exist. The WAVs are gitignored; they are in the results dataset. |
| `scripts/build_space.py` | Builds and pushes the listening Space (`--push`) |
| `scripts/publish_results.py` | Pushes the results dataset |
| `notes-space/` | A private Gradio app for listening notes |
| `hub/eval-set/` | The eval set's Hub card |

The listening notes rate each clip from 1 to 5 on naturalness, clarity, Hebrew accuracy and nikud accuracy (whether
the vowels heard match the card), plus "use it as the reference voice?" (yes / maybe / no) and a note. You can go one
sentence across every voice, blind (names hidden and order shuffled until saved), or one voice across all sentences.
A summary tab ranks the voices. The app is a private Space; the notes go to a private dataset.

## Cost

The runs used Modal: CPU for the Piper, Kokoro and BlueV3 runs, and L4 or A10G GPUs for the rest, plus a few cents
on Fish Audio's API. The total was a few US dollars, most of it on retries and queue waits. The exact Modal bill was
not checked.

## Licence

Code: MIT. Sentences: CC BY 4.0 for the hand-written ones, and CC BY 2.0 FR for the Tatoeba ones, whose authors are
named in each row. Each generated clip carries its model's licence. Several are non-commercial: Phonikud,
Kokoro-Hebrew, OmniVoice and Fish S2 Pro.
