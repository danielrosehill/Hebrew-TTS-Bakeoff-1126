#!/usr/bin/env python3
"""Objective voice profile per run: speaking rate and an acoustic profile, with no listener judgement (Daniel,
2026-11-18: "WPM computed for each of the voices, average across generations" and "an acoustic profile that is
objective ... purely looking at the frequency distribution in their voices", to help people pick a voice by type).

Per run, pooled over every clip it has (s01-s20, p01):
  wpm               words of the source text / seconds of speech (leading and trailing silence trimmed; internal
                    pauses count, as a listener hears them), pooled: total words / total speech seconds, x 60
  wpm_clips         clips it is based on; wpm_by_clip: per clip
  f0_median_hz      median pitch of voiced frames (Praat autocorrelation, 60-400 Hz)
  f0_p10_hz, f0_p90_hz
  f0_range_st       p90 / p10 in semitones: how far the voice moves
  f0_sd_st          standard deviation of pitch in semitones around its median: intonation liveliness
  centroid_hz       spectral centre of gravity of the speech (500-8000 Hz band-limited sound resampled to 16 kHz,
                    so sample rate and low-frequency rumble do not decide it): brightness
  hnr_db            harmonics-to-noise ratio of voiced frames: high = clean and clear, low = breathy or rough
Labels (written down so they can be argued with; the numbers are the data):
  register    absolute, by voice gender: male low < 110 Hz <= mid < 140 Hz <= high; female low < 185 <= mid < 225 <= high
  intonation  f0_sd_st, brightness centroid_hz, clarity hnr_db: thirds among all runs of the same voice gender
              (flatter / moderate / livelier, darker / neutral / brighter, breathier / moderate / cleaner): relative to
              this field of voices, not absolute (male voices have lower HNR, so absolute cut-offs called them all breathy)
  pace        wpm vs the median of all runs: slow < -10% <= average <= +10% < fast
Pitch is tracked in 60-250 Hz for male voices and 100-450 Hz for female ones (60-400 if unknown), to avoid octave errors.
Caveats: a run that repeats text (gpt-audio-1.5 male + nikud repeats the end of p01) has inflated duration, so its wpm
reads low; `flags` says so, and flags any run whose wpm is below 0.65x or above 1.4x the median (skipped, repeated
or truncated text, e.g. a model that dropped half the sentence). Clips are the model's raw output, not the loudness-normalised listening copies.

    uv run --with praat-parselmouth --with numpy python3 scripts/voice_profile.py   # writes data/voice_profiles.json
"""
import json, math, re, statistics, subprocess, sys
from pathlib import Path

import numpy as np
import parselmouth

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
FLAGS = {"openai-gpt-audio-male-nikud": ["repeats the end of p01 three times: wpm reads low"]}


def words(text):
    return len([w for w in re.split(r"\s+", re.sub(r"[^\w\s֐-׿'\"-]", " ", text)) if re.search(r"\w", w)])


PITCH_RANGE = {"male": (60, 250), "female": (100, 450)}  # Praat's usual per-gender floors/ceilings; others 60-400


def acoustics(wav, gender=None):
    # Decoded through ffmpeg, not Praat's reader: the Fish S2 Pro WAVs carry a streamed header (data size 0xFFFFFFFF)
    # that makes Praat allocate ~2^31 samples (16 GB) and get OOM-killed (found 2026-11-18).
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "f32le", "-ac", "1", "-ar", "24000", "-"],
                         capture_output=True, check=True).stdout
    snd = parselmouth.Sound(np.frombuffer(raw, dtype=np.float32).astype(np.float64), sampling_frequency=24000)
    lo, hi = PITCH_RANGE.get(gender, (60, 400))
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=lo, pitch_ceiling=hi)
    f0 = pitch.selected_array["frequency"]
    f0 = f0[f0 > 0]
    band = parselmouth.praat.call(snd.resample(16000), "Filter (pass Hann band)", 500, 8000, 100)
    centroid = band.to_spectrum().get_center_of_gravity(power=2.0)
    harm = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=60)
    h = harm.values[0]
    h = h[h > -100]
    return f0, centroid, float(np.median(h)) if len(h) else None, snd.duration


def main():
    from build_space import load_items, runs
    items = {s["id"]: s for s in load_items()}
    metrics = json.loads((ROOT / "data/clip_metrics.json").read_text())
    out = {}
    for slug, (meta, folder) in runs():
        f0s, cents, hnrs, w_tot, s_tot, by_clip = [], [], [], 0, 0.0, {}
        for sid, s in items.items():
            wav = folder / f"{sid}.wav"
            if not wav.exists():
                continue
            f0, c, h, dur = acoustics(wav, meta.get("voice_gender"))
            f0s.append(f0); cents.append(c); hnrs.append(h) if h is not None else None
            sp = metrics.get(slug, {}).get(sid, {}).get("speech_s") or dur
            n = words(s["text"])
            w_tot += n; s_tot += sp; by_clip[sid] = round(60 * n / sp, 1)
        if not by_clip:
            continue
        f0 = np.concatenate(f0s) if f0s else np.array([])
        med = float(np.median(f0)) if len(f0) else None
        p = {"wpm": round(60 * w_tot / s_tot, 1), "wpm_clips": len(by_clip), "wpm_by_clip": by_clip,
             "voice_gender": meta.get("voice_gender")}
        if med:
            st = 12 * np.log2(f0 / med)
            p.update(f0_median_hz=round(med, 1), f0_p10_hz=round(float(np.percentile(f0, 10)), 1),
                     f0_p90_hz=round(float(np.percentile(f0, 90)), 1),
                     f0_range_st=round(12 * math.log2(np.percentile(f0, 90) / np.percentile(f0, 10)), 1),
                     f0_sd_st=round(float(np.std(st)), 2))
        p["centroid_hz"] = round(statistics.mean(cents))
        p["hnr_db"] = round(statistics.mean(hnrs), 1) if hnrs else None
        p["flags"] = list(FLAGS.get(slug, []))
        out[slug] = p
    label(out)
    (ROOT / "data/voice_profiles.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for slug, p in out.items():
        print(f"{slug:36} {p['wpm']:6.1f} wpm  f0 {p.get('f0_median_hz', 0):6.1f}  sd {p.get('f0_sd_st', 0):4.2f}st"
              f"  cog {p['centroid_hz']:5}  hnr {p['hnr_db']}  {p['labels']}")


def label(out):
    med_wpm = statistics.median(p["wpm"] for p in out.values())

    def thirds(key, names):  # tertiles among runs of the same voice gender (relative labels)
        for g in {p["voice_gender"] for p in out.values()}:
            vs = sorted(p[key] for p in out.values() if p["voice_gender"] == g and p.get(key) is not None)
            if len(vs) < 3:
                continue
            a, b = vs[len(vs) // 3], vs[2 * len(vs) // 3]
            for p in out.values():
                if p["voice_gender"] == g and p.get(key) is not None:
                    p["labels"][names[0]] = names[1] if p[key] < a else names[3] if p[key] >= b else names[2]

    for p in out.values():
        p["labels"] = {}
        g, f = p["voice_gender"], p.get("f0_median_hz")
        if f and g in ("male", "female"):
            lo, hi = (110, 140) if g == "male" else (185, 225)
            p["labels"]["register"] = "low" if f < lo else "high" if f >= hi else "mid"
    thirds("f0_sd_st", ("intonation", "flatter", "moderate", "livelier"))
    thirds("centroid_hz", ("brightness", "darker", "neutral", "brighter"))
    thirds("hnr_db", ("clarity", "breathier", "moderate", "cleaner"))
    for p in out.values():
        r = p["wpm"] / med_wpm - 1
        p["labels"]["pace"] = "slow" if r < -0.1 else "fast" if r > 0.1 else "average"
        p["pace_vs_median"] = round(r, 2)
        if not 0.65 <= p["wpm"] / med_wpm <= 1.4:
            p["flags"].append("pace far outside the other voices: check for skipped, repeated or truncated text")
        if not p["flags"]:
            del p["flags"]

if __name__ == "__main__":
    main()
