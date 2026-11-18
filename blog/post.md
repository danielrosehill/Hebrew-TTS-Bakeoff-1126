There's a button in my recording app that I came to dislike. You press Listen, a voice reads a Hebrew sentence, and then you read it back yourself. Fair idea, no? The voice, though, kept putting the stress on the last syllable of everything: sef**ER** for סֵפֶר (book), yel**ED** for יֶלֶד (boy), as if every Hebrew word were a French one. (Nobody had told it that Israeli Hebrew stresses the penultimate syllable of most nouns.) It also sounded flat, and some of the nikud (the vowel points) it was reading was simply wrong.

So on 2026-11-18 I ran a bake-off to pick a replacement, and I'm sharing all of it for anyone who wants to follow along: the leaderboard, the clips, the data and my own listening notes.

The context: the button lives in the Hebrew project of the recording app for [Hebrish](https://hebrish.app), my English-Hebrew speech-recognition project. In that project I read Hebrew sentences aloud from nikud, to train a model on my own (accented) Hebrew. The reference voice plays first, so it had better be a good one.

## Results so far (a first look, not a verdict)

This is a small, one-listener evaluation: 20 sentences, about 26 models, one annotator (me), and 16 head-to-head votes so far. Read everything below as "in this run".

- **Gemini 3.1 Flash TTS**, given checked nikud, is unbeaten: 4 wins and 4 ties. I wrote "superb" in my notes, and it may be the best Hebrew synthesis I've heard.
- **Gemini 3.8 Flash TTS, 3.8 Flash Lite TTS, Gemini 3.8 Live and ElevenLabs v4** each held it to a tie by ear.
- **Gemini 3.8 Flash Lite** ties the leader at about a third of the price: $0.010 against $0.033 per 1,000 characters. That makes it the best value so far.
- **Out of the Arena:** Gemini 2.5 Pro TTS, xAI, Piper (which sounds like "a preceding generation of TTS"), Chatterbox (robotic, staccato), Kokoro (rushed) and Gemini 2.5 native audio.

The recording app now uses Gemini 3.1 Flash TTS with nikud. Tie-break rematches between the leader and the four voices that tied it are still to come, so this isn't final. If a 3.8 model wins, switching is a one-line change.

## How I tested

The method is "screen, then rank". Every voice is first screened on a whole clip: pass or fail, with a one-tap reason if it fails (mispronunciation, wrong stress, glitch, skipped words, wrong language). The yardstick is neutral modern Israeli pronunciation, so an accent fails even where it would be perfectly good Hebrew somewhere. The survivors then meet blind, A against B, on a four-sentence paragraph, and the votes feed a Bradley-Terry ranking.

I generated clips in rounds, only for the survivors. (My first attempt generated more than 500 clips for every model. That was far too many to listen to, and I said so at the time.)

Most of my annotations were spoken: I press a key, say what I heard, and a model transcribes it and files it into the schema. I tidy lightly and keep the offhand remarks, and the recordings are public. Failures are kept as results too, since a voice that fails is information.

The sentences are 20 in total: ten from Tatoeba across five difficulty grades, and ten I wrote to hit specific traps (segolate stress, the ספר homographs, times in words, a foreign surname, technical talk, English loanwords). The nikud came from DictaBERT and I checked it word by word, which corrected 12 words in 8 sentences.

## Nikud inference

Anyone reading unpointed Hebrew has to infer the vowels, and that is true of models too. So wherever a model could take both, I ran it twice on the same text: once plain, once with checked nikud. The gap between the two clips shows how well it infers vowels and stress.

The finding is blunt: every voice still in the Arena passed only when given checked nikud. The one exception, Kokoro, is already out. Kokoro's case is a nice illustration: on plain text it read הספר as *ha-sefer* (the book); given the nikud, it read *ha-sapar* (the barber).

## What it costs

Per 1,000 characters of Hebrew, at list prices on 2026-11-18: Gemini 3.8 Flash Lite $0.010, 3.8 Flash $0.015, 3.1 Flash $0.033, ElevenLabs v4 $0.08. Open models on a CPU, such as Piper, come to about $0.0001. For reference audio that is generated once per sentence and cached, none of this is a lot of money. So which voice sounds right matters more than the fraction of a cent.

## Scope

About 26 models in all. The open ones from Hugging Face: Piper, Phonikud, Kokoro, BlueV3, F5, Zonos, Chatterbox, VoxCPM2, OmniVoice and Fish S2 Pro. The commercial APIs: the Gemini TTS family, OpenAI, ElevenLabs, Google Cloud Chirp 3, MiniMax, Inworld and xAI. And a newer category I hadn't expected to include: multimodal models with native audio output (Gemini 3.8 Live, Gemini 2.5 native audio, OpenAI gpt-audio-1.5), told to read the text verbatim and used as TTS.

## Caveats

One listener, 20 sentences, 16 votes, one day. Voices change between releases and APIs get repriced (the Gemini 3.8 prices roughly double from 2027). I'm not a linguist, just someone with strong opinions about stress. Treat the ranking as "what worked for this job".

## Follow along

Start with the collection, which links everything else:

- [Hebrew TTS Bake-off 11/26 (Hugging Face collection)](https://huggingface.co/collections/danielrosehill/hebrew-tts-bake-off-11-26-6afdec3193ad9622ff5a3d69)
- [Leaderboard](https://huggingface.co/spaces/danielrosehill/Hebrew-TTS-Leaderboard)
- [Listen to every clip](https://huggingface.co/spaces/Hebrish/Hebrew-TTS-Bakeoff-1126)
- [My spoken notes, in a reader](https://huggingface.co/spaces/danielrosehill/Hebrew-TTS-Listening-Notes-Reader) and [the annotations dataset](https://huggingface.co/datasets/danielrosehill/Hebrew-TTS-Listening-Notes)
- [The 20-sentence eval set](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Eval-Set), [all the clips](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Bakeoff-1126) and the [evaluations registry](https://huggingface.co/datasets/Hebrish/Hebrew-TTS-Evaluations)
- [The bake-off repo on GitHub](https://github.com/danielrosehill/Hebrew-TTS-Bakeoff-1126), the reusable [annotation starter](https://github.com/danielrosehill/TTS-Pronunciation-Annotation-Starter) and an [index of my Hebrew AI evaluations](https://github.com/danielrosehill/Hebrew-AI-Evaluations)

If you build Hebrew voice tools, the eval set and the annotation starter are there to be reused. I'd like to see someone prove my ear wrong.
