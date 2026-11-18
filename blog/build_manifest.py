import json,re,sys
def inline(t):
    out=[];pos=0
    pat=re.compile(r'\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`')
    def txt(v,marks=()):
        return {"nodeType":"text","value":v,"marks":[{"type":m} for m in marks],"data":{}}
    for m in pat.finditer(t):
        if m.start()>pos: out.append(txt(t[pos:m.start()]))
        if m.group(1): out.append({"nodeType":"hyperlink","data":{"uri":m.group(2)},"content":[txt(m.group(1))]})
        elif m.group(3): out.append(txt(m.group(3),["bold"]))
        elif m.group(4): out.append(txt(m.group(4),["italic"]))
        else: out.append(txt(m.group(5),["code"]))
        pos=m.end()
    if pos<len(t): out.append(txt(t[pos:]))
    return out
blocks=[];items=[]
def flush():
    global items
    if items:
        blocks.append({"nodeType":"unordered-list","data":{},"content":[{"nodeType":"list-item","data":{},"content":[{"nodeType":"paragraph","data":{},"content":inline(i)}]} for i in items]});items=[]
for para in open('post.md').read().split('\n\n'):
    lines=para.strip().split('\n')
    if lines[0].startswith('- '):
        items=[l[2:] for l in lines]; flush()
    elif lines[0].startswith('## '):
        blocks.append({"nodeType":"heading-2","data":{},"content":inline(lines[0][3:])})
    else:
        blocks.append({"nodeType":"paragraph","data":{},"content":inline(' '.join(lines))})
m={
 "title":"Choosing a Hebrew text-to-speech voice: a first look at 26 models",
 "slug":"hebrew-tts-bakeoff-first-look",
 "description":"I compared about 26 Hebrew TTS voices on 20 sentences, with and without nikud, to pick a new reference voice. Gemini 3.1 Flash TTS leads so far, one listener, 16 votes. Leaderboard, clips and notes are public. Not a verdict.",
 "publishedAt":"2026-11-18T20:30:00.000Z",
 "tags":["evals","hebrew","text-to-speech","tts","nikud","hebrish","benchmarks"],
 "targetBlog":["personal"],"category":"ai","topicPath":"technology/ai/evaluations","author":"Daniel Rosehill",
 "heroAssetKey":"hero","ogAssetKey":"hero",
 "assets":[{"key":"hero","path":"/home/daniel/repos/github/audio-dictation/Hebrew-TTS-Bakeoff-1126/blog/hero.webp","title":"Abstract ribbons of sound being compared on a listening bench with headphones and a scorecard"}],
 "content":{"nodeType":"document","data":{},"content":blocks}}
assert len(m["description"])<=255,len(m["description"])
json.dump(m,open('manifest.json','w'),ensure_ascii=False,indent=1)
