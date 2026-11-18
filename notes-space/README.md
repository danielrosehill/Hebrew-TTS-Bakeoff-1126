---
title: Hebrew TTS Listening Notes
emoji: 🎧
colorFrom: yellow
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Hebrew TTS listening notes

This is Daniel's private deployment of the public
[TTS Pronunciation Annotation Starter](https://github.com/danielrosehill/TTS-Pronunciation-Annotation-Starter), with
a Hebrew config. The app code is not copied in. The `Dockerfile` clones the starter at a pinned commit
(`STARTER_COMMIT`) and adds this folder's `config.json`.

- **To upgrade:** change `STARTER_COMMIT` and redeploy.
- **To change the axes, the keypad language or the datasets:** edit `config.json`.

## Hebrew config

The method is **screen, then rank** (the `ai-eval` plugin's `screen-then-rank` skill):

- **Pass 1, Screen:** judge the whole clip, Pass (P) or Fail (X).
  - A fail needs one tap on a category (keys 1-6): Mispronunciation, Wrong emphasis (stress), Glitch / artefact,
    Truncated / skipped words, Wrong voice or language, Other (with a comment).
  - Voice gender is recorded with F, M or U.
  - A vowel that doesn't match the nikud is a Fail: Mispronunciation. There is no separate nikud axis.
  - **Add detail** is optional and collapsed. It holds word issues: the stressed syllable heard vs. the one it should
    be, and the IPA heard vs. expected, with the Hebrew IPA keypad and IPA help. Quality ratings are off in this
    config.
- **Pass 2, Rank:** blind A/B comparisons among the clips that passed, as an adaptive play-off per sentence.
  - Keys: 1 = A better, 2 = B better, 3 = tie, 4 = both bad (both go back as late fails), U = undo.
  - Results give a Bradley–Terry ranking.

The rest of the config:

- **Display:** right to left, Noto Sans Hebrew, language pack `he`.
- **Sentence fields:** `text_nikud` is the line with tappable words, `text` sits above it and `english` below.
- **Evaluations:** listed from the public registry `Hebrish/Hebrew-TTS-Evaluations`.
- **Annotations:** in the private dataset `danielrosehill/Hebrew-TTS-Listening-Notes`:
  - `annotations/<eval_id>/screen.jsonl`, schema `tts-annotation/2`;
  - `annotations/<eval_id>/pairs.jsonl`, schema `tts-pairwise/1`.
- **Word reference:** from Phonikud, labelled "Machine reference (Phonikud): check it", because it is sometimes
  wrong. For example, s12 הַסַּפָּר is marked as stressed on "sa", but the correct reading is sa-PAR.

Space secret `HF_TOKEN` needs write access to the annotations dataset.

## Deploy

```bash
uv run --with huggingface_hub python -c "from huggingface_hub import HfApi; HfApi().upload_folder(repo_id='danielrosehill/Hebrew-TTS-Listening-Notes', repo_type='space', folder_path='notes-space')"
```
