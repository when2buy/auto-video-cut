# auto-video-cut — Research Phase

> First-pass survey. Goal: pick an architecture in <2min. Date: 2026-05.

## Problem

Long raw video (1h talk / lecture / vlog / stream) → tight 5-10min cut. Remove silence + filler + boring stretches; keep the good parts.

---

## Candidate Approaches

### A. Silence-based cut (the dumb-fast baseline)

**How**: Detect non-silent audio segments (RMS / dBFS threshold), drop the rest, concatenate. ffmpeg `silenceremove` filter or auto-editor's audio-loudness pass. No transcription, no semantics.

**Real**: [auto-editor](https://github.com/WyattBlue/auto-editor) (4.3k stars, actively maintained May 2026), `ffmpeg -af silenceremove`, Premiere's "auto-detect silence". This is what most YouTubers actually ship with.

**Pros**:
- Trivial to implement (1 day, ffmpeg-only, no GPU)
- Deterministic, no hallucination, no API cost
- Already battle-tested at scale

**Cons**:
- Can only compress ~30-50%, not 90% (1h → 5min)
- No notion of "interesting" — keeps every "uhh I think maybe…"
- Useless for vlogs / B-roll / interview cross-cuts where speaker is silent

**MVP**: 1 day. Deps: `ffmpeg`, `auto-editor`.
**Best for**: solo talking-head, screencasts, podcasts where 30% trim is the target.

---

### B. ASR + LLM scene-selection (the "let Gemini read the transcript" play)

**How**: Whisper transcribes with word-level timestamps → chunk into sentences/paragraphs → LLM ranks/selects "best 10%" with timestamps → ffmpeg cuts and concatenates.

**Real**: [autocut](https://github.com/mli/autocut) (7.7k stars, Mu Li's tool — transcribe + manual sentence-select via Markdown). Descript's "Underlord", Opus Clip, Submagic, Captions.ai all use this pattern under the hood (transcript + LLM = highlight reel). [WhisperX](https://github.com/m-bain/whisperX) (22k stars) gives the word-level timing.

**Pros**:
- Genuinely smart selection — LLM picks substantive content, drops filler
- Achieves 10:1+ compression (this is the only approach that does)
- Multilingual basically free (Whisper + Gemini both multilingual)
- Steve has Foundry Gemini → cost is ~$0.10 per hour-long transcript

**Cons**:
- Audio-only signal — misses "great visual moment, no speech" (sports, demos)
- 2-stage pipeline → more failure modes (timestamp drift, LLM hallucinated cuts)
- ~1-2min latency per hour of input (Whisper transcribe dominant)

**MVP**: 2-3 days. Deps: `faster-whisper` or WhisperX (H100 = 30-40x realtime), Foundry Gemini, ffmpeg.
**Best for**: lectures, talks, interviews, podcasts, technical content — anything speech-driven.

---

### C. ML highlight detection (the visual-energy / multimodal play)

**How**: Run frame-level features (scene change via [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) 4.8k stars, motion energy, face/laughter detect, CLIP embeddings, or full multimodal LLM like Gemini-Pro-Video) → score each segment → pick top-K → cut.

**Real**: Vizard.ai, Munch (visual-aware highlight reels), academic work (TVSum, SumMe benchmarks). Gemini-Pro can natively ingest 1h of video and return timestamped highlights.

**Pros**:
- Catches non-verbal moments (reactions, demos, action)
- Gemini-video collapses pipeline to 1 API call
- Foundation for "viral clip" features later (face-zoom, b-roll)

**Cons**:
- Pure visual scoring is noisy without training data — TVSum-style models are mediocre off-the-shelf
- Gemini-Pro-Video is $$$ per hour and rate-limited (1h video ≈ 1M tokens)
- Hardest to debug ("why did it pick that frame")

**MVP**: 3-5 days for v0 visual; 2 days for Gemini-Pro-Video wrapper. Deps: PySceneDetect, Gemini, ffmpeg.
**Best for**: vlogs, sports, gaming, anything where speech ≠ signal.

---

### D. Hybrid: silence + ASR + LLM (recommended)

**How**: (1) auto-editor strips obvious silence — easy 30% wins. (2) Whisper transcribes the survivor. (3) Gemini ranks paragraphs and emits a keep-list of `[start_ts, end_ts]`. (4) ffmpeg final concat. Each stage is independently testable.

**Real**: This is essentially Descript's pipeline. auto-editor itself supports `--edit` chaining; pairing with ASR is a common community recipe.

**Pros**:
- Each layer fixes the previous layer's weakness; degrades gracefully if LLM fails
- Cheapest at scale (silence-prune halves Whisper cost; Whisper halves Gemini context)
- All components are off-the-shelf — no training, no novel ML

**Cons**:
- 4 moving parts → more orchestration code (but each part is small)
- Still audio-centric — vlogs/B-roll edge case unsolved (punt to later)

**MVP**: 3-4 days. Deps: auto-editor, faster-whisper, Foundry Gemini, ffmpeg.

---

## Recommendation: **D (Hybrid)**

**Why**: Steve's target inputs (talks, lectures, podcasts) are speech-driven, where D dominates. Each stage is replaceable — start with A's silence pass for v0.1 in 1 day; bolt on Whisper for v0.2; add Gemini for v0.3. No wasted work, no training compute, fits Foundry+H100 stack exactly.

---

## Decision Matrix

| Approach | Quality | Speed-to-MVP | Cost | Flexibility | Multilingual |
|---|---|---|---|---|---|
| A. Silence | ⚠️ shallow | ✅ 1d | ✅ free | ❌ rigid | ✅ N/A |
| B. ASR+LLM | ✅ smart | ⚠️ 2-3d | ✅ ~$0.10/h | ✅ promptable | ✅ Whisper+Gemini |
| C. Visual/Multimodal | ⚠️ noisy | ❌ 3-5d | ❌ $$$/h | ⚠️ opaque | ✅ visual |
| **D. Hybrid** | ✅ best | ⚠️ 3-4d | ✅ cheapest@scale | ✅ stage-swap | ✅ inherits B |

---

## References

- auto-editor — https://github.com/WyattBlue/auto-editor (4,338 stars)
- autocut (Mu Li) — https://github.com/mli/autocut (7,716 stars)
- openai/whisper — https://github.com/openai/whisper (100,611 stars)
- WhisperX — https://github.com/m-bain/whisperX (22,106 stars)
- faster-whisper — https://github.com/SYSTRAN/faster-whisper (23,168 stars)
- PySceneDetect — https://github.com/Breakthrough/PySceneDetect (4,858 stars)
- Descript Underlord — https://www.descript.com/underlord
- Opus Clip — https://www.opus.pro
- Submagic — https://www.submagic.co
- Vizard — https://vizard.ai
- ffmpeg silenceremove — https://ffmpeg.org/ffmpeg-filters.html#silenceremove
