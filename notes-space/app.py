"""Private listening notes for the Hebrew TTS bake-off: three 1-5 ratings and a note per model and sentence.

Axes (Daniel, 2026-11-18): voice quality, accuracy of the Hebrew, accuracy of the nikud (do the vowels heard match the
pointed text on the card). Each save appends one JSON line to notes.jsonl in the private dataset NOTES_REPO; the latest
line per (model, sentence) wins. Sentence "overall" holds a note on the model as a whole.
"""
import json, os, time, urllib.request

import gradio as gr
from huggingface_hub import HfApi, hf_hub_download

SPACE = "Hebrish/Hebrew-TTS-Bakeoff-1126"
BASE = f"https://huggingface.co/spaces/{SPACE}/resolve/main/"
NOTES_REPO = os.environ.get("NOTES_REPO", "danielrosehill/Hebrew-TTS-Bakeoff-1126-Notes")
AXES = [("voice", "Voice quality"), ("hebrew", "Hebrew accuracy"), ("nikud", "Nikud accuracy (vowels heard match the card)")]
SCALE = ["1", "2", "3", "4", "5"]
api = HfApi(token=os.environ.get("HF_TOKEN"))
LOCAL = "/tmp/notes.jsonl"


def load_data():
    with urllib.request.urlopen(BASE + "data.json?t=" + str(int(time.time()))) as r:
        return json.load(r)


def load_notes():
    try:
        p = hf_hub_download(NOTES_REPO, "notes.jsonl", repo_type="dataset", token=os.environ.get("HF_TOKEN"), force_download=True)
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
MODELS = {m["name"]: m for m in D["models"]}
SENTS = [s["id"] for s in D["sentences"]] + ["overall"]
SBY = {s["id"]: s for s in D["sentences"]}


def show(model_name, sid):
    m = MODELS[model_name]
    n = NOTES.get((m["slug"], sid), {})
    if sid == "overall":
        card = f"### {model_name}: overall\nA note on the model as a whole."
        audio = None
    else:
        s = SBY[sid]
        card = (f"**{sid}** · {s['focus']}\n\n<div dir='rtl' style='font-size:22px'>{s['text']}</div>\n\n"
                f"<div dir='rtl' style='font-size:28px'>{s['text_nikud']}</div>\n\n{s['english']}")
        audio = BASE + m["clips"][sid] if sid in m["clips"] else None
    done = sum(1 for x in SENTS if (m["slug"], x) in NOTES)
    status = f"{done}/{len(SENTS)} rated for {model_name}" + (f" · last saved {n['saved']}" if n else "")
    return [card, audio] + [n.get(k) for k, _ in AXES] + [n.get("note", ""), status]


def save(model_name, sid, voice, hebrew, nikud, note):
    m = MODELS[model_name]
    row = {"model": m["slug"], "model_name": model_name, "sentence": sid, "voice": voice, "hebrew": hebrew, "nikud": nikud,
           "note": note or "", "saved": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}
    with open(LOCAL, "a", encoding="utf8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    api.create_repo(NOTES_REPO, repo_type="dataset", private=True, exist_ok=True)
    api.upload_file(path_or_fileobj=LOCAL, path_in_repo="notes.jsonl", repo_id=NOTES_REPO, repo_type="dataset",
                    commit_message=f"{m['slug']} {sid}")
    NOTES[(m["slug"], sid)] = row
    nxt = SENTS[min(SENTS.index(sid) + 1, len(SENTS) - 1)]
    return [gr.update(value=nxt)] + show(model_name, nxt)


def step(sid, d):
    return gr.update(value=SENTS[max(0, min(len(SENTS) - 1, SENTS.index(sid) + d))])


def table():
    return [[n["model_name"], n["sentence"], n["voice"], n["hebrew"], n["nikud"], n["note"], n["saved"]]
            for n in sorted(NOTES.values(), key=lambda n: (n["model"], n["sentence"]))]


with gr.Blocks(title="TTS bake-off notes") as demo:
    gr.Markdown("## Hebrew TTS bake-off: listening notes\n1 = bad, 5 = native-perfect. Nikud accuracy: do the vowels you "
                "hear match the pointed text? On a clip made from plain text (no nikud given) that score is the model's "
                "**nikud inference**; on a clip given the nikud it is how faithfully it follows it.")
    with gr.Tab("Rate"):
        with gr.Row():
            model = gr.Dropdown(list(MODELS), value=list(MODELS)[0], label="Model")
            sent = gr.Dropdown(SENTS, value=SENTS[0], label="Sentence")
        card = gr.Markdown()
        audio = gr.Audio(type="filepath", label="Clip", interactive=False, autoplay=True)
        radios = [gr.Radio(SCALE, label=lbl) for _, lbl in AXES]
        note = gr.Textbox(label="Note", lines=2)
        with gr.Row():
            prev = gr.Button("◀ Previous")
            sv = gr.Button("Save and next ▶", variant="primary")
            nxt = gr.Button("Skip ▶")
        status = gr.Markdown()
    with gr.Tab("All notes"):
        grid = gr.Dataframe(headers=["model", "sentence", "voice", "hebrew", "nikud", "note", "saved"], wrap=True)
        gr.Button("Refresh").click(table, outputs=grid)
    outs = [card, audio, *radios, note, status]
    for c in (model.change, sent.change):
        c(show, [model, sent], outs)
    sv.click(save, [model, sent, *radios, note], [sent, *outs])
    prev.click(lambda s: step(s, -1), sent, sent)
    nxt.click(lambda s: step(s, 1), sent, sent)
    demo.load(show, [model, sent], outs)

demo.launch()
