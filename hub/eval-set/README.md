---
license: cc-by-4.0
language:
- he
task_categories:
- text-to-speech
pretty_name: Hebrew TTS Eval Set
size_categories:
- n<1K
tags:
- hebrew
- nikud
- tts-evaluation
configs:
- config_name: default
  data_files:
  - split: test
    path: sentences.jsonl
---

# Hebrew TTS Eval Set

20 Hebrew sentences for listening tests of text-to-speech models, each given **with and without nikud**, so the same
set serves models that read vocalized Hebrew by rule and models that infer the vowels from context.

Part of [Hebrish](https://hebrish.app). Made for the reference voice in the Hebrish recorder's Hebrew project, where a
learner hears a sentence before reading it aloud from nikud. First used by the bake-off
[Hebrew-TTS-Bakeoff-1126](https://github.com/danielrosehill/Hebrew-TTS-Bakeoff-1126) (2026-11-18).

## Sentences

- `s01`-`s10`: Tatoeba sentences, two from each of five difficulty grades.
- `s11`-`s20`: hand-written, each aimed at one known difficulty: stress on segolate nouns (sefer, yeled, boker, lechem),
  homographs (ספר as sapar, safar, siper), times in words, a foreign surname, technical talk, material-handling
  vocabulary, English loanwords, and one long sentence with commas. The `focus` column says which.

## Nikud

`text_nikud` was produced by `dicta-il/dictabert-large-char-menaked` (revision `4dfc20b`), then checked word by word.
12 words in 8 sentences were corrected, among them both homographs in `s12` (the model read the barber as "the book")
and the habit in `s10` (read as "the leg"). The raw model output is kept in `nikud_model_output` and each fix is
explained in `nikud_corrections`, so the set doubles as a small check of the diacritizer. `text_nikud` is NFC-normalized.

## Columns

| Column | Meaning |
| --- | --- |
| `id` | `s01`-`s20` |
| `text` | Hebrew without nikud |
| `text_nikud` | Hebrew with checked nikud |
| `english` | English translation |
| `source` | `tatoeba` or `hand-written` |
| `focus` | What the sentence tests |
| `nikud_model`, `nikud_model_output` | The diacritizer and its raw output |
| `nikud_corrections` | Each corrected word, `raw -> fixed: reason` |
| `nikud_reviewed_by` | Who checked the nikud, and when |
| `licence` | Per row |
| `tatoeba_id`, `tatoeba_author`, `english_tatoeba_id`, `english_author` | Attribution for Tatoeba rows |

## Licence

Hand-written rows CC BY 4.0. Tatoeba rows CC BY 2.0 FR, by the authors named in each row.
