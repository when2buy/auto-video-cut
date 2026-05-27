# Decisions

> Curated, durable record. Agents propose via PR; humans curate.

---

## 2026-05-26: v0.1 implementation = pure ffmpeg, not auto-editor wrapper

**Context**: spec called out 3 candidates (A: auto-editor wrapper, B: pure ffmpeg silenceremove filter, C: librosa+ffmpeg from scratch). Chose A. auto-editor turned out to need GLIBC_2.38, which isn't on the Pluto pod.

**Decision**: implemented C-lite: pure ffmpeg `silencedetect` filter (not the fragile `silenceremove`) + per-segment cut + concat demuxer. ~200 lines.

**Why**: zero external binary deps, works on any pod with ffmpeg, frame-accurate, easy to extend (silencedetect output is exactly what v0.2 ASR will need to merge with).

**Reversibility**: easy. If auto-editor becomes available later we can A/B test.

---

## 2026-05-26: v0.1 staging = ship silence-only first, add ASR in v0.2

**Context**: research recommended approach D (Hybrid silence + ASR + LLM). Doing all of D at once = 3-4 days of code before any user feedback.

**Decision**: ship v0.1 as silence-only (1 day). v0.2 adds Whisper. v0.3 adds Gemini ranking.

**Why**: each version is independently demoable + has its own report URL. Steve sees real progress per cycle, not a 4-day vacuum.

**Reversibility**: trivial — additive.
