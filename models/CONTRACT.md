# Model script contract

One Modal app per candidate: `models/<slug>.py`, app name `bakeoff-<slug>`, run from the repo root on any machine
with Modal set up (the local entrypoint writes the results locally):

    modal run models/<slug>.py

Exception: `models/fish-s2-pro-api.py` calls Fish Audio's hosted API (`FISH_API_KEY`), no Modal.

- Input: `data/sentences.jsonl` (20 rows), read by the local entrypoint and passed to the remote function.
  A model that phonemizes vocalized Hebrew by rule gets `text_nikud`; every other model gets `text` (no nikud).
- Output: `results/<slug>/<id>.wav` (the model's native sample rate, mono) and `results/<slug>/meta.json`:
  `{slug, hf_id, revision, licence, input: "nikud"|"plain", voice, reference_clip, gpu, sample_rate,
  load_s, per_sentence_s: {id: seconds}, generated: "YYYY-MM-DD", notes}`.
- Settings: the model card's or official demo's defaults, one built-in voice (female if there is a choice),
  no tuning per sentence. If the model needs a reference clip, use the sample clip its own repo or demo ships
  and name it in `reference_clip`.
- Budget: about US$0.20 per model. Smallest GPU that runs it (L4 / A10G), or CPU for small ONNX models.
- Models never run on a laptop; Modal (or the publisher's API) does the work.
- Variants of one model: `<slug>-nikud` (given `text_nikud`), `<slug>-auto` (the model's own diacritizer), `<slug>/plain/` (Phonikud without stress marks).
