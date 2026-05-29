# Overnight Build Summary — 2026-05-30

> Steve gave 10 hours overnight to make the auto-video-cut demo "compelling, eye-catching, professional, covers multiple edit scenarios". Here's what landed.

---

## Headline URL

**https://reports.steveouyang.com/2026-05-30-v0.3-demo** — landing page with 6 fixture tabs, before/after side-by-side, methodology section.

GitHub repo: https://github.com/when2buy/auto-video-cut

---

## What's new vs v0.2

| Layer | v0.2 | v0.3 |
|---|---|---|
| ASR | sentence-level | + word-level timestamps (for caption sync) |
| LLM pick | sentence-pick | unchanged |
| Cut | ffmpeg | unchanged |
| **Reframe to 9:16** | ❌ | ✅ OpenCV Haar + EMA-smoothed face tracking + ffmpeg crop expression |
| **Burned captions** | ❌ | ✅ Opus-style word-by-word, PIL-rendered PNGs + ffmpeg overlay |
| **Multi-language** | zh + en | + auto Latin/CJK font picking per chunk |
| **CLI** | `avc cut --mode asr` | + `avc pipeline INPUT --out --reframe --captions` |
| **Demo report** | single fixture compare-grid | 6-fixture landing page with tabs |

---

## Per-fixture results (full pipeline: cut + reframe + captions)

| Fixture | Source | In → Out | Kept | Sentences | Reframe |
|---|---|---:|---:|---|---|
| `julian-treasure-speak` | TED tech-talk EN | 584s → 161s | 27% | 36/156 | face-tracked |
| `marketing-bili` | Bilibili 营销号 ZH | 237s → 66s | 28% | 32/79 | center-crop |
| `maz-jobrani-standup` | TED stand-up EN | 415s → 102s | 25% | 31/149 | face-tracked |
| `sam-harris-ai` | TED philosophical EN | 858s → 226s | 26% | 69/259 | face-tracked |
| `ted-cn` | TED science (Boroditsky) EN | 843s → 234s | 28% | 73/285 | face-tracked |
| `tim-urban-procrast` | TED storytelling EN | 834s → 225s | 27% | 64/226 | face-tracked |

All hit the target 30% ratio within ±5%. Face-tracking found a speaker on 5/6 fixtures (marketing-bili has no consistent face → center-crop fallback worked).

---

## Pipeline wall-clock (per fixture, observed)

For a typical 14-min input (e.g. ted-cn, sam-harris):
- ASR (faster-whisper large-v3 on H100): **~13s/min input → ~3 min**
- LLM pick (Gemini 2.5 Pro, 200-300 sentence prompt): **~70-90s**
- Cut (ffmpeg per-segment + concat): **~3-5s**
- Reframe (10 frame samples + crop expr): **~30-45s for 4-min cut**
- Captions (re-transcribe + PIL render + overlay): **~60-90s for 700+ word frames**
- **TOTAL: ~5-7 min wall-clock for a 14-min input** (~2× realtime)

---

## Bug log + fixes during build

| Bug | Fix |
|---|---|
| `re.sub` repl interprets `\n` → corrupted JSON in HTML reports | Lambda repl form, plus round-trip JSON validation |
| ffmpeg ass / subtitles / drawtext filters all missing in this build | Pivot to PIL+overlay (one PNG per word, ffmpeg overlay with `enable=between(t,a,b)`) |
| MediaPipe 0.10.35 deprecated `solutions` API | Pivot to OpenCV Haar (bundled, no model download) |
| `marketing-bili` source already has burned subs → ours overlap | Re-ran with `--captions` off; demo uses no-captions version |
| `ted-cn` audio is English (not Chinese) → opus-cn font (Droid Sans Fallback) had tofu blocks | Per-chunk auto font: Latin if ASCII, CJK if any CJK char |
| `report publish` single-file overwrites Cloudflare Pages prod → historical URLs 404 | Batch via `eval/publish_all.sh` (single wrangler deploy of `reports/*.html` + `assets/`) |
| 78 MB HTML with base64-embedded videos exceeds CF Pages 25 MB/file limit | Switch HTML to relative video URLs, deploy `assets/` dir alongside |
| `he-tongxue-5g.mp4` (Bilibili) has h264 NAL corruption surviving `err_detect ignore_err` re-mux → cut step silently strips video | **Dropped from demo.** Future: re-encode source with `-c:v libx264` instead of stream-copy |

---

## Open issues / v0.4 candidates

In rough priority order:

1. **Vision-LLM frame analysis** (per `tate-2-oss.md`/NarratoAI) — current LLM pick is text-only. Sending Gemini-Vision 8-12 keyframes per candidate clip would let it weight visual significance (gesture, scene change, on-screen graphics).
2. **OCR / region-skip for hardcoded subtitles** — auto-detect a horizontal text band in input, skip our caption rendering in that zone (or skip entirely if heavy text presence).
3. **剪映 draft export** (NarratoAI's killer feature for Chinese creators) — emit a JSON draft alongside the mp4 so the user can do final-mile edits in 剪映.
4. **Speaker-tracking reframe (multi-face)** — current single-face Haar fails on dialog clips; clipify's frame-differencing approach is portable.
5. **Per-genre prompt templates** — `--style` is one knob; offer presets (`viral-hook`, `documentary-narration`, `interview-cuts`, `tutorial-summary`).
6. **gemini-3.5-flash for keep-list** — Pro is ~70s, Flash should be <10s; quality trade-off needs A/B.
7. **Bilibili source robustness** — h264 stream-copy fails on some downloads; switch fetch to `-c:v libx264` re-encode at source time.

---

## Credit + references consulted overnight

- `docs/research/competitive-landscape.md` — 12 OSS projects evaluated; `clipify` (393★) was the closest neighbor, ports of its `build_ass.py` informed `captions.py`'s API surface (we ended up not using libass/ASS due to ffmpeg build).
- `docs/research/skill-design-patterns.md` — 12 skills surveyed for SKILL.md style.
- `docs/research/tate-2-oss.md` — NarratoAI (9.5k★) identified mid-build as the most relevant peer for AI-narrated long-form video; informed the v0.4 list above.

---

## Files added this build

```
src/avc/captions.py         220 lines — PIL+overlay caption rendering, 4 style presets, auto-font
src/avc/reframe.py          175 lines — Haar face track + EMA + ffmpeg crop expr
src/avc/pipeline.py         100 lines — orchestrator
src/avc/asr.py              + word-level timestamps support
src/avc/cli.py              + `pipeline` subcommand
tests/test_captions.py      3 tests
tests/test_reframe.py       2 tests
tests/test_pipeline.py      1 test (full smoke)
eval/fetch_*.sh             5 fixture fetch scripts (incl orchestrator)
eval/run_demos.sh           per-fixture pipeline runner
eval/publish_all.sh         bundle deploy to Cloudflare Pages
reports/build_demo.py       landing page generator
reports/2026-05-30-v0.3-demo.html      the deliverable
reports/assets/v0.3/        12 video previews (6 fixtures × in/out)
docs/research/{tate-2-oss, skill-design-patterns, competitive-landscape}.md
docs/plans/2026-05-29-v0.3-overnight-demo.md
```

---

*Generated 2026-05-30 morning, after ~3.5 hours of actual build time + research.*
