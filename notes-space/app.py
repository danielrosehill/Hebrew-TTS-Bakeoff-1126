"""Private listening notes for the Hebrew TTS bake-off.

Per clip (model run x sentence), Daniel 2026-11-18: naturalness, clarity, Hebrew accuracy, nikud accuracy (1-5), whether
he would use the voice as the recorder's reference ("Use it?": yes / maybe / no) and a free note. Two ways through:
one sentence across every run (compare like with like; Blind hides the run name and shuffles the order) or one run
across all 20 sentences. Each save appends one JSON line to notes.jsonl in the private dataset NOTES_REPO; the latest
line per (run, sentence) wins. Sentence "overall" holds a note on a run as a whole.
"""
import json, os, random, time, urllib.request

import gradio as gr
from huggingface_hub import HfApi, hf_hub_download

SPACE = "Hebrish/Hebrew-TTS-Bakeoff-1126"
BASE = f"https://huggingface.co/spaces/{SPACE}/resolve/main/"
NOTES_REPO = os.environ.get("NOTES_REPO", "danielrosehill/Hebrew-TTS-Bakeoff-1126-Notes")
TOKEN = os.environ.get("HF_TOKEN")
AXES = [("naturalness", "Naturalness", "Does it sound like a person?"),
        ("clarity", "Clarity", "Every syllable easy to make out and copy?"),
        ("hebrew", "Hebrew accuracy", "Right words, stress and accent for Israeli Hebrew?"),
        ("nikud", "Nikud accuracy", "Do the vowels you hear match the pointed text?")]
SCALE = ["1", "2", "3", "4", "5"]
USE = ["Yes", "Maybe", "No"]
api = HfApi(token=TOKEN)
LOCAL = "/tmp/notes.jsonl"


def load_data():
    with urllib.request.urlopen(BASE + "data.json?t=" + str(int(time.time()))) as r:
        return json.load(r)


def load_notes():
    try:
        p = hf_hub_download(NOTES_REPO, "notes.jsonl", repo_type="dataset", token=TOKEN, force_download=True)
        lines = open(p, encoding="utf8").read().splitlines()
    except Exception:
        lines = []
    open(LOCAL, "w", encoding="utf8").write("".join(l + "\n" for l in lines if l.strip()))
    latest = {}
    for l in lines:
        if l.strip():
            n = json.loads(l)
            latest[(n["model"], n["sentence"])] = n
    return latest


D = load_data()
NOTES = load_notes()
RUNS = {m["slug"]: m for m in D["models"]}
NAMES = {m["name"]: m["slug"] for m in D["models"]}
SIDS = [s["id"] for s in D["sentences"]]
SBY = {s["id"]: s for s in D["sentences"]}
SENT_LABELS = {f"{s['id']} · {s['english']}": s["id"] for s in D["sentences"]}


def queue(mode, model_name, sent_label, blind):
    """The clips to walk through, as (run slug, sentence id)."""
    if mode == "One sentence, every voice":
        sid = SENT_LABELS[sent_label]
        slugs = [m["slug"] for m in D["models"] if sid in m["clips"]]
        if blind:
            random.Random(sid).shuffle(slugs)  # stable per sentence, so Previous/Next keep their place
        return [(s, sid) for s in slugs]
    slug = NAMES[model_name]
    return [(slug, sid) for sid in SIDS if sid in RUNS[slug]["clips"]] + [(slug, "overall")]


def run_label(m, blind, i):
    if blind:
        return f"Voice {chr(65 + i)}"
    how = "given the nikud" if m["run"].get("input") == "nikud" else "plain text, infers the vowels"
    return f"{m['name']} ({how})"


def view(mode, model_name, sent_label, blind, pos):
    q = queue(mode, model_name, sent_label, blind)
    pos = max(0, min(pos, len(q) - 1))
    slug, sid = q[pos]
    m, n = RUNS[slug], NOTES.get((slug, sid), {})
    if sid == "overall":
        card, audio = f"### {m['name']}: overall\nA note on this voice as a whole.", None
    else:
        s = SBY[sid]
        card = (f"<div style='color:#888'>{sid} · {s['focus']}</div>"
                f"<div dir='rtl' style='font-size:22px;margin-top:6px'>{s['text']}</div>"
                f"<div dir='rtl' style='font-size:30px;color:#c98a00'>{s['text_nikud']}</div>"
                f"<div style='margin-top:4px'>{s['english']}</div>")
        audio = BASE + m["clips"][sid]
    done = sum(1 for k in q if k in NOTES)
    head = f"**{run_label(m, blind, pos)}** · clip {pos + 1} of {len(q)} · {done} rated here"
    if n:
        head += f" · saved {n['saved']}"
    return [pos, card, head, audio] + [n.get(k) for k, _, _ in AXES] + [n.get("use"), n.get("note", "")]


def save(mode, model_name, sent_label, blind, pos, *vals):
    q = queue(mode, model_name, sent_label, blind)
    slug, sid = q[pos]
    m = RUNS[slug]
    *scores, use, note = vals
    row = {"model": slug, "model_name": m["name"], "input": m["run"].get("input"), "sentence": sid,
           **{k: v for (k, _, _), v in zip(AXES, scores)}, "use": use, "note": note or "", "blind": bool(blind),
           "saved": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}
    with open(LOCAL, "a", encoding="utf8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    api.create_repo(NOTES_REPO, repo_type="dataset", private=True, exist_ok=True)
    api.upload_file(path_or_fileobj=LOCAL, path_in_repo="notes.jsonl", repo_id=NOTES_REPO, repo_type="dataset",
                    commit_message=f"{slug} {sid}")
    NOTES[(slug, sid)] = row
    reveal = f"Saved: that was **{m['name']}**." if blind else "Saved."
    nxt = view(mode, model_name, sent_label, blind, min(pos + 1, len(q) - 1))
    return nxt + [reveal]


def summary():
    rows = []
    for m in D["models"]:
        ns = [n for (slug, sid), n in NOTES.items() if slug == m["slug"] and sid != "overall"]
        if not ns:
            continue
        mean = lambda k: round(sum(int(n[k]) for n in ns if n.get(k)) / max(1, sum(1 for n in ns if n.get(k))), 2)
        means = [mean(k) for k, _, _ in AXES]
        rows.append([m["name"], len(ns), *means, round(sum(means) / len(means), 2),
                     sum(1 for n in ns if n.get("use") == "Yes"), sum(1 for n in ns if n.get("use") == "No")])
    return sorted(rows, key=lambda r: -r[-3])


def all_notes():
    return [[n["model_name"], n["sentence"], *[n.get(k) for k, _, _ in AXES], n.get("use"), n["note"], n["saved"]]
            for n in sorted(NOTES.values(), key=lambda n: (n["model"], n["sentence"]))]


CSS = ".gradio-container {max-width: 900px !important} #save {min-height: 52px; font-size: 18px}"
with gr.Blocks(title="Hebrew TTS bake-off: listening notes", css=CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown("## Hebrew TTS bake-off: listening notes\n1 = poor, 5 = native-perfect. Leave a score empty if you "
                "can't judge it. On a plain-text clip, **Nikud accuracy** measures the model's nikud inference. "
                "[Listening page](https://huggingface.co/spaces/Hebrish/Hebrew-TTS-Bakeoff-1126)")
    with gr.Tab("Rate"):
        with gr.Row():
            mode = gr.Radio(["One sentence, every voice", "One voice, every sentence"], value="One sentence, every voice",
                            label="Go through")
            blind = gr.Checkbox(value=True, label="Blind (hide the voice's name until saved)")
        with gr.Row():
            sent = gr.Dropdown(list(SENT_LABELS), value=list(SENT_LABELS)[0], label="Sentence")
            model = gr.Dropdown(list(NAMES), value=list(NAMES)[0], label="Voice", visible=False)
        pos = gr.State(0)
        head = gr.Markdown()
        card = gr.HTML()
        audio = gr.Audio(type="filepath", label="Clip", interactive=False, autoplay=True)
        radios = [gr.Radio(SCALE, label=lbl, info=info) for _, lbl, info in AXES]
        use = gr.Radio(USE, label="Use it as the reference voice?")
        note = gr.Textbox(label="Note", lines=2, placeholder="What stood out: a wrong vowel, odd stress, accent, artefacts...")
        with gr.Row():
            prev = gr.Button("◀ Previous")
            sv = gr.Button("Save and next ▶", variant="primary", elem_id="save")
            skip = gr.Button("Skip ▶")
        saved = gr.Markdown()
    with gr.Tab("Summary"):
        gr.Markdown("Mean score per voice over the clips you rated (overall notes excluded), best first.")
        summ = gr.Dataframe(headers=["voice", "clips", *[l for _, l, _ in AXES], "mean", "use: yes", "use: no"], wrap=True)
        gr.Button("Refresh").click(summary, outputs=summ)
    with gr.Tab("All notes"):
        grid = gr.Dataframe(headers=["voice", "sentence", *[l for _, l, _ in AXES], "use", "note", "saved"], wrap=True)
        gr.Button("Refresh").click(all_notes, outputs=grid)

    sel = [mode, model, sent, blind]
    outs = [pos, card, head, audio, *radios, use, note]
    mode.change(lambda m: (gr.update(visible=m != "One sentence, every voice"), gr.update(visible=m == "One sentence, every voice")),
                mode, [model, sent])
    for c in (mode.change, model.change, sent.change, blind.change):
        c(lambda *a: view(*a, 0), sel, outs)
    sv.click(save, [*sel, pos, *radios, use, note], [*outs, saved])
    prev.click(lambda *a: view(*a[:-1], a[-1] - 1), [*sel, pos], outs)
    skip.click(lambda *a: view(*a[:-1], a[-1] + 1), [*sel, pos], outs)
    demo.load(lambda *a: view(*a, 0), sel, outs)
    demo.load(summary, outputs=summ)

demo.launch()
