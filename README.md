# Hebrew TTS Bake-off 11/26

A small listening comparison of **open Hebrew text-to-speech models**, run 2026-11-18, on 20 sentences given both
with and without nikud.

- **Leaderboard:** [Space `danielrosehill/Hebrew-TTS-Leaderboard`](https://huggingface.co/spaces/danielrosehill/Hebrew-TTS-Leaderboard): the Arena ranking, who is waiting, and who
  failed Screening and why, live from the annotations.
- **Listen:** [Space `Hebrish/Hebrew-TTS-Bakeoff-1126`](https://huggingface.co/spaces/Hebrish/Hebrew-TTS-Bakeoff-1126).
  Its views are by sentence, by model, nikud inference, and a table of the models.
- **Sentences:** [`Hebrish/Hebrew-TTS-Eval-Set`](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Eval-Set),
  20 rows, each with and without nikud. It is meant to be reused.
- **Registry:** [`Hebrish/Hebrew-TTS-Evaluations`](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Evaluations) records
  every Hebrew TTS evaluation, with its date, models and raw run parameters (`scripts/register_eval.py`). All my Hebrew
  evaluations are indexed by task in [Hebrew-AI-Evaluations](https://github.com/danielrosehill/Hebrew-AI-Evaluations).
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

### Commercial APIs (added 2026-11-18)

| Run(s) | Model | Voice | Input |
| --- | --- | --- | --- |
| `gemini-flash-tts`, `-nikud` | Gemini 3.1 Flash TTS (`gemini-3.1-flash-tts-preview`), #1 on the ivrit.ai Hebrew TTS Arena | Kore | Plain; our nikud |
| `openai-tts`, `-nikud` | OpenAI `gpt-4o-mini-tts`, instructed to speak as a native Israeli | coral | Plain; our nikud |
| `elevenlabs-v3`, `-nikud` | ElevenLabs v3 via fal (`fal-ai/elevenlabs/tts/eleven-v3`, `he`) | Rachel | Plain; our nikud |
| `google-cloud-tts`, `-nikud` | Google Cloud TTS `he-IL-Chirp3-HD-Kore` | Kore | Plain; our nikud |

None rejected pointed input. The four together cost under US$1. The Gemini API now also lists `gemini-3.8-flash-tts`,
which its docs say replaces the 3.1 preview, so it is a candidate for a follow-up.

### Measured per clip

`scripts/clip_metrics.py` measures every clip with ffmpeg and writes `data/clip_metrics.json`. It measures loudness
(LUFS), true peak and clipping, pace (syllables per second, and that pace relative to the sentence's median), and
internal pauses. The listening copies in the Space are loudness-normalised to -18 LUFS, so voices are compared at
equal level; the raw levels are kept here.

What it found on 2026-11-18:
- **F5-Hebrew v2 is nearly silent:** about -50 LUFS, with a true peak around -32 dBTP.
- **Clipping:** Chatterbox, VoxCPM2 and Google Cloud clip on some clips.
- **BlueV3 is hot:** -14.7 LUFS.
- **Quiet voices:** OpenAI (-27.5 LUFS) and Kokoro (-26.5 LUFS).
- **Pace:** Chatterbox with nikud runs about 33% faster than the median. OpenAI runs about 30% slower and has the most
  pauses.

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

## Results so far (2026-11-18)

Live version: the [leaderboard Space](https://huggingface.co/spaces/danielrosehill/Hebrew-TTS-Leaderboard). Annotator:
Daniel Rosehill. The standard is neutral modern Israeli pronunciation. "$ / 1k chars" is the price of 1,000 characters
of Hebrew on 2026-11-18. For APIs it is the list price; per-token audio prices are converted at about 25 tokens per
second (Gemini) or about 600 per minute (OpenAI) and 15 characters per second of speech. For self-hosted models it is
warm Modal compute measured on our clips, excluding cold start. The basis and source of each figure are in
`data/models.json` (`cost`).

**Arena, first head-to-head round** (blind A vs B on the paragraph p01, 3 votes):

| Voice | Result | $ / 1k chars | Why, in the annotator's words (tidied) |
| --- | --- | --- | --- |
| Gemini 3.1 Flash TTS, given nikud | 2-0, preferred over Chatterbox and Piper | 0.033 (API) | "Superb", possibly the best Hebrew synthesis heard; expressive, good prosody and nikud |
| Piper Hebrew noa, given nikud | 1-1, preferred over Kokoro | ~0.0001 (CPU) | More human and expressive than Kokoro; next to Gemini, "a preceding generation of TTS" |
| Chatterbox Multilingual, given nikud | 0-1 | ~0.13 (GPU est.) | Robotic, staccato, clipped |
| Kokoro Hebrew | 0-1 | ~0.0007 (CPU) | Very rushed and distracting |

**Passed Screening and now in the Arena** (they had no paragraph clip for round 1; p01 was generated on 2026-11-18):
Gemini 3.8 Flash TTS ($0.015 to 2026-12-31, then $0.030), Gemini 3.8 Flash Lite TTS ($0.010, then $0.020), Gemini
2.5 Pro TTS ($0.033), ElevenLabs v4 via fal ($0.08) and OpenAI gpt-audio-1.5 ($0.043), all given nikud.

**Out at Screening:** 23 runs, each with its reason, in the table below. **Waiting for Screening:** 17 runs. These
include a new category, multimodal models with native audio output: Gemini 3.8 Live, Gemini 3.1 Flash Live and
Gemini 2.5 Flash native audio ($0.020 each). They are instructed to read verbatim through the Live API (v1alpha).

Every voice that has passed so far, except Kokoro, did so when it was given checked nikud.

## Screen results (pass 1)

Every run's pass/fail record from Daniel's listening, written by `scripts/screen_summary.py` from the public annotations dataset [`danielrosehill/Hebrew-TTS-Listening-Notes`](https://huggingface.co/datasets/danielrosehill/Hebrew-TTS-Listening-Notes). A run is out at its first fail; survivors go on to head-to-head ranking on the round-2 paragraph.

<!-- screen:begin -->
| Run | Status | Items heard | Arena (won / played) | $ per 1k chars | Why it failed | Observations | In the annotator's words |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `chatterbox-multilingual-nikud` | survivor | s01 pass, s03 pass, s05 pass, s06 pass | 0 / 1 | 0.1311 (compute) | - | - | This one is fine, and what's interesting to me is the different pacing in these clips. So this one sounded a little bit like a little bit rushed. I'm sure if we measure the WPM, in fact, this might be a very useful thing… |
| `elevenlabs-v4-nikud` | survivor | s01 pass | - | 0.08 (API) | - | - |  |
| `gemini-2.5-native-audio-nikud` | survivor | s01 pass | - | 0.02 (API) | - | - | Pacing is very unnaturally slow, but passing is because it's worth hearing how well it does on a longer multi-sentence narration And especially given that conditioning for speed is possible. |
| `gemini-2.5-pro-tts-nikud` | survivor | s01 pass | - | 0.0333 (API) | - | - |  |
| `gemini-3.8-flash-lite-tts-nikud` | survivor | s01 pass | - | 0.01 (API) | - | - |  |
| `gemini-3.8-flash-tts-nikud` | survivor | s01 pass | - | 0.015 (API) | - | - |  |
| `gemini-3.8-live` | survivor | s01 pass | - | 0.02 (API) | - | - |  |
| `gemini-3.8-live-nikud` | survivor | s01 pass | - | 0.02 (API) | - | - |  |
| `gemini-flash-tts-nikud` | survivor | s01 pass, s02 pass, s03 pass, s04 pass, s05 pass, s06 pass | 2 / 2 | 0.0333 (API) | - | - |  |
| `kokoro-hebrew` | survivor | s01 pass, s02 pass, s03 pass, s04 pass, s05 pass, s06 pass | 0 / 1 | 0.00069 (compute) | - | - | This one is is okay. It's not like mind-blowingly clear or whatever, fairly straightforward delivery of the sentence. |
| `openai-gpt-audio-nikud` | survivor | s01 pass | - | 0.0427 (API) | - | - |  |
| `piper-he-noa-nikud` | survivor | s01 pass, s02 pass, s03 pass, s04 pass, s05 pass, s06 pass | 1 / 2 | 0.00012 (compute) | - | - | Okay, so um female voice, אני הייתי עושה את זה שוב. Um sounds good. Tiny note, really not important but I guess just to be thorough in my annotations here. Um אני הייתי עושה את זה שוב, עושה. Um the vowelization is for fo… |
| `xai-tts` | survivor | s01 pass | - | 0.015 (API) | - | - |  |
| `xai-tts-nikud` | survivor | s01 pass | - | 0.015 (API) | - | - |  |
| `bluev3` | out | s01 pass, s02 fail | - | 0.00218 (compute) | Wrong stress | - | So this one, ze lo ze lo kashe im ata lomed. Ze lo kashe im ata lomed, it kind of went really, really up at the end. And I feel like I'm being a bit strict in terms of like the failing ones because I feel like maybe a fe… |
| `chatterbox-multilingual` | out | s01 fail | - | 0.1311 (compute) | Glitch / artefact, Mispronunciation, Not Hebrew / wrong voice, Wrong stress | - | Same failure mode as the previous model that just sounded like it was not able to do Hebrew at all. This just is not intelligible as anything, any language I'm familiar with anyway. Certainly not Hebrew. Well, it did it … |
| `elevenlabs-v3` | out | s01 pass, s02 pass, s03 pass, s04 fail | - | 0.1 (API) | Other | - | Accented |
| `elevenlabs-v3-nikud` | out | s01 pass, s02 pass, s04 fail | - | 0.1 (API) | Foreign accent, Mispronunciation | - | Uh, this is a very interesting one. I don't think we've heard it before. And I would say it was very accented. And sounded to me like one that didn't really have that average, like a multilingual TTS model that advertise… |
| `f5-hebrew-v2` | out | s02 fail | - | 0.05932 (compute) | Truncated / skipped words | - | Another case of what went wrong here, I'm not sure, but it sounded like someone like started with the Hebrew word, then words were just missing and truncated. So, you couldn't listen to this. |
| `f5-hebrew-v2-nikud` | out | s01 pass, s02 fail | - | 0.05932 (compute) | Glitch / artefact | - | Edge case again because pronunciation correct, but very, very noisy in the background. I suspect, I'm going to go out on a hunch with this, that this is one of the ones that Claude had to manually regain because the base… |
| `fish-s2-pro` | out | s01 fail | - | 0.03 (API) | Pacing / rhythm | Borderline pass | Borderline but I'm marking it fail because I wouldn't personally use it. And 'ani', it just sounded, the voice wasn't very, didn't sound natural. And the timing, the pacing wasn't good. |
| `fish-s2-pro-nikud` | out | s01 fail | - | 0.03 (API) | Not Hebrew / wrong voice | - | Okay, so, right, this is this is this is fascinating and I'm actually enjoying the fact that it's it's blinded because otherwise I'd be like, what the hell was that? Okay, first impression, this sounds like Farsi. The th… |
| `gemini-flash-tts` | out | s02 pass, s03 fail | - | 0.0333 (API) | Mispronunciation | - | Technically she said, hamatanah hazot i lechaver sheli, not hi. Tiny one, but there you go. |
| `google-cloud-tts` | out | s01 pass, s02 pass, s03 pass, s05 fail | - | 0.03 (API) | Mispronunciation | - |  |
| `google-cloud-tts-nikud` | out | s02 fail | - | 0.03 (API) | Mispronunciation | - |  |
| `inworld-tts-2-nikud` | out | s01 fail | - | 0.025 (API) | Mispronunciation | - |  |
| `kokoro-hebrew-nikud` | out | s01 pass, s03 pass, s04 fail | - | 0.00069 (compute) | Wrong stress | - |  |
| `minimax-speech-2.8-hd-nikud` | out | s01 fail | - | 0.1 (API) | Intonation, Not Hebrew / wrong voice | - |  |
| `omnivoice` | out | s01 fail | - | 0.03293 (compute) | Wrong stress | - | This one is an intriguing one. אני הייתי עושה את זה שוב. So, I'm this is my I guess there's a there's an element in annotation maybe kind of why I why I like doing this and why I like evaluations that is subjective. And … |
| `openai-tts` | out | s01 pass, s03 fail | - | 0.008 (API) | Pacing / rhythm | - | Pacing here was very awkward. |
| `openai-tts-nikud` | out | s01 pass, s02 fail | - | 0.008 (API) | Truncated / skipped words | - | This one is is is kind of comical actually. So actually managed to get the nikud correct, notwithstanding the female nikud mismatch, but just the pacing was like all over the place. It also sounded slightly like an Asian… |
| `phonikud-piper` | out | s01 fail | - | 8e-05 (compute) | Wrong stress | - | Okay, so um this one I've marked as fail because it just came out weird. Ani hayiti ose et ze shuv. Ani hayiti ose et ze shuv. Shuv, flat towards the end, and this voice just kind of is like it's kind of a it's a crazy o… |
| `phonikud-piper-auto` | out | s02 fail | - | 8e-05 (compute) | Mispronunciation | - | The pacing was very wrong here. That had kind of a French feeling to it, like it sounded like a bit like a French Hebrew speaker was the kind of pronunciation pattern. But regardless, pacing was so awkward that I don't t… |
| `phonikud-piper-plain` | out | s01 fail | - | 8e-05 (compute) | Wrong stress | - |  |
| `piper-he-noa` | out | s01 pass, s02 pass, s03 pass, s04 fail | - | 0.00012 (compute) | Mispronunciation | Slightly noisy or muddy |  |
| `voxcpm2` | out | s02 fail | - | 0.01225 (compute) | Audio quality (noise, narrowband, muddy, level) | - | Super weird one actually here. Sounded like pronunciation correct, audio quality very poor. Sounded like some guy, sounded like a slightly angry man shouting down a bad telephone connection. Like sounded very narrowband,… |
| `zonos3-mini` | out | s01 fail | - | 0.03721 (compute) | Not Hebrew / wrong voice | - | Okay, not sure what went wrong here, but this isn't even Hebrew. It came out as non- a non-intelligible language, whatever it was supposed to be. So yeah, this one is a this one is a hard fail. I'll be interested to know… |
| `elevenlabs-v4` | not screened | - | - | 0.08 (API) | - | - |  |
| `gemini-2.5-flash-tts` | not screened | - | - | 0.0167 (API) | - | - |  |
| `gemini-2.5-flash-tts-nikud` | not screened | - | - | 0.0167 (API) | - | - |  |
| `gemini-2.5-native-audio` | not screened | - | - | 0.02 (API) | - | - |  |
| `gemini-2.5-pro-tts` | not screened | - | - | 0.0333 (API) | - | - |  |
| `gemini-3.1-flash-live` | not screened | - | - | 0.02 (API) | - | - |  |
| `gemini-3.1-flash-live-nikud` | not screened | - | - | 0.02 (API) | - | - |  |
| `gemini-3.8-flash-lite-tts` | not screened | - | - | 0.01 (API) | - | - |  |
| `gemini-3.8-flash-tts` | not screened | - | - | 0.015 (API) | - | - |  |
| `inworld-tts-2` | not screened | - | - | 0.025 (API) | - | - |  |
| `minimax-speech-2.8-hd` | not screened | - | - | 0.1 (API) | - | - |  |
| `openai-gpt-audio` | not screened | - | - | 0.0427 (API) | - | - |  |
<!-- screen:end -->

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
| `scripts/register_eval.py` | Registers this evaluation (`--push`) in `Hebrish/Hebrew-TTS-Evaluations` |
| `hub/evaluations/` | That registry's Hub card and its last pushed rows |
| (moved) | The annotation Space's config and the listening work now live in the private repo `danielrosehill/Hebrew-TTS-Listening-Notes` |
| `hub/eval-set/` | The eval set's Hub card |

The listening notes rate each clip from 1 to 5 on naturalness, clarity and Hebrew accuracy. Nikud accuracy is a yes or
no: does every vowel heard match the pointed text? On a plain-text clip, that answer is the model's nikud inference.
There is also "use it as the reference voice?" (yes / maybe / no) and an overall comment. Problems are tagged per word:
**stress** (the syllable the voice stressed, and the one it should have stressed) and **mispronunciation** (the IPA
heard, and the IPA expected), with a few minor tags besides. The expected values are prefilled from a machine reference
and can be corrected. [`docs/hebrew-ipa-cliff-notes.md`](docs/hebrew-ipa-cliff-notes.md) is the IPA quick reference
for annotators. You can go one sentence across every voice, blind (names hidden and order shuffled until saved), or one
voice across all sentences, and a results tab ranks the voices. The app is a private Space; the notes go to a private dataset.

## Cost

The runs used Modal: CPU for the Piper, Kokoro and BlueV3 runs, and L4 or A10G GPUs for the rest, plus a few cents
on Fish Audio's API. The total was a few US dollars, most of it on retries and queue waits. The exact Modal bill was
not checked. Per-model unit costs as of 2026-11-18 are in "Results so far" and `data/models.json`; generating each
round for the survivors only costs cents.

## Licence

Code: MIT. Sentences: CC BY 4.0 for the hand-written ones, and CC BY 2.0 FR for the Tatoeba ones, whose authors are
named in each row. Each generated clip carries its model's licence. Several are non-commercial: Phonikud,
Kokoro-Hebrew, OmniVoice and Fish S2 Pro.
