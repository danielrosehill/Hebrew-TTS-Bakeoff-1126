#!/usr/bin/env python3
"""Measure every generated clip: level, clipping, pace and pauses (Daniel's listening notes, 2026-11-18: some clips too
quiet, BlueV3 "a bit hot/clipping"; Chatterbox "20-30% above baseline" pace, "something that can be computed
programmatically very easily"; OmniVoice "a pause after אני that wasn't in the source").

Per results/<run>/sNN.wav (ffmpeg only, a few seconds in all):
  duration_s        length
  lufs, true_peak   integrated loudness (EBU R128) and true peak, dBTP
  clipped           true peak at or above -0.1 dBTP
  speech_s          duration minus leading and trailing silence
  syll_per_s        syllables (from the sentence's reference syllables) per second of speech
  pace_vs_median    syll_per_s relative to the median of all runs on that sentence (+0.25 = 25% faster)
  pauses            internal silences of 250 ms or more (30 dB below the clip's peak, between -60 and -35 dBFS), and the longest
Writes data/clip_metrics.json: {run: {sentence: {...}}}. scripts/build_space.py reads it.

    python3 scripts/clip_metrics.py
"""
import json, re, statistics, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def ff(args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *args], capture_output=True, text=True).stderr


def measure(wav):
    e = ff(["-i", str(wav), "-af", "ebur128=peak=true", "-f", "null", "-"])
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", e)[-1].replace("-inf", "-99"))
    dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)", e).group(3)) + 60 * int(re.search(r"Duration: (\d+):(\d+)", e).group(2))
    floor = max(-60, min(-35, tp - 30))  # silence is relative to the clip's own peak, so very quiet clips (F5) still measure
    s = ff(["-i", str(wav), "-af", f"silencedetect=noise={floor}dB:d=0.25", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", s)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", s)]
    sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
    lead = sil[0][1] if sil and sil[0][0] <= 0.05 else 0.0
    trail = dur - sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else 0.0
    inner = [(a, b) for a, b in sil if a > 0.05 and b < dur - 0.05]
    return {"duration_s": round(dur, 2), "lufs": round(lufs, 1), "true_peak": round(tp, 1), "clipped": tp >= -0.1,
            "speech_s": round(max(0.1, dur - lead - trail), 2), "pauses": len(inner),
            "longest_pause_s": round(max((b - a for a, b in inner), default=0), 2)}


def main():
    from build_space import add_words, runs
    sentences = [json.loads(l) for l in open(ROOT / "data/sentences.jsonl", encoding="utf8")]
    add_words(sentences)
    syl = {s["id"]: sum(len(w["syllables"]) for w in s.get("words", [])) or None for s in sentences}
    out = {}
    for slug, (meta, folder) in runs():
        for s in sentences:
            wav = folder / f"{s['id']}.wav"
            if wav.exists():
                m = measure(wav)
                if syl[s["id"]]:
                    m["syll_per_s"] = round(syl[s["id"]] / m["speech_s"], 2)
                out.setdefault(slug, {})[s["id"]] = m
    for s in sentences:
        rates = [r[s["id"]]["syll_per_s"] for r in out.values() if s["id"] in r and "syll_per_s" in r[s["id"]]]
        if rates:
            med = statistics.median(rates)
            for r in out.values():
                if s["id"] in r and "syll_per_s" in r[s["id"]]:
                    r[s["id"]]["pace_vs_median"] = round(r[s["id"]]["syll_per_s"] / med - 1, 2)
    (ROOT / "data/clip_metrics.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for slug, r in out.items():
        v = list(r.values())
        print(f"{slug:32} lufs {statistics.median(x['lufs'] for x in v):6.1f}  peak {max(x['true_peak'] for x in v):5.1f}"
              f"  clipped {sum(x['clipped'] for x in v):2}  pace {statistics.median(x.get('pace_vs_median', 0) for x in v):+.2f}"
              f"  pauses/clip {statistics.mean(x['pauses'] for x in v):.1f}")


if __name__ == "__main__":
    main()
