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

The config sets these:

- **Display:** right to left, Noto Sans Hebrew, language pack `he`. The pack holds the IPA keypad, a tooltip per
  symbol, and an IPA help drawer with the Hebrew cliff notes.
- **Sentence fields:** `text_nikud` is the line with tappable words. `text` is shown small above it, and `english`
  below.
- **Rows to answer:**
  - Naturalness, Clarity and Hebrew accuracy, each 1 to 5.
  - **"Vowels match the nikud?"**, yes or no on the keys V and X. On a plain-text clip this measures the model's
    nikud inference.
  - **"Use it as the reference voice?"**, Yes / Maybe / No on the keys Y, M and N.
- **Evaluations:** listed from the public registry `Hebrish/Hebrew-TTS-Evaluations` (`evals.jsonl`).
- **Annotations:** saved to the private dataset `danielrosehill/Hebrew-TTS-Listening-Notes`, at
  `annotations/<eval_id>.jsonl`. The format is `tts-annotation/1`; see the starter's
  `schema/annotation.schema.json`.
- **Word references:** each sentence in the manifest has a `words` list with IPA, syllables and stress, from
  Phonikud. It is labelled "Machine reference (Phonikud): check it" because it is sometimes wrong. For example, s12
  הַסַּפָּר is marked as stressed on "sa", but the correct reading is sa-PAR.

Space secret `HF_TOKEN` needs write access to the annotations dataset.

## Deploy

```bash
uv run --with huggingface_hub python -c "from huggingface_hub import HfApi; HfApi().upload_folder(repo_id='danielrosehill/Hebrew-TTS-Listening-Notes', repo_type='space', folder_path='notes-space')"
```
