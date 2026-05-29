# Demo Fixtures — Overnight Auto-Edit Reel

Curated set of 5 **public, license-clean** real-world videos covering different
edit scenarios. Combined with the existing two fixtures (`marketing-bili`,
`ted-cn`), this stresses the tool across vlog, podcast-like, lecture, comedy,
and creator-explainer content.

All URLs verified live on **2026-05-29** from `pluto-prod-zouyang-xpu-1gpu-2-0`.
Probe commands shown are metadata-only (no download).

---

## Diversity matrix

| Slug                  | Lang | Genre                       | Stress angle                                                                 |
|-----------------------|------|-----------------------------|------------------------------------------------------------------------------|
| `marketing-bili` (✅ exists) | zh-CN | 营销号 / commentary         | baseline; punchline density, fast cuts already in source                     |
| `ted-cn` (✅ exists)         | zh-CN | edited TED talk             | proves v0.1 alone is insufficient on already-edited content                  |
| `he-tongxue-5g`       | zh-CN | tech vlog (creator b-roll)  | visual signal-heavy, low speech density → tests visual reframe + b-roll skip |
| `bi-dao-science`      | zh-CN | knowledge science explainer | single-speaker, dense info, mid-length → tests "summarize the lecture" path  |
| `tim-urban-procrast`  | en   | TED storytelling / comedy   | punchline-heavy, narrative arcs → tests LLM "find punchlines" prompt         |
| `sam-harris-ai`       | en   | TED philosophical talk      | wandering speech, fillers, abstract argumentation → podcast proxy            |
| `maz-jobrani-standup` | en   | TED stand-up comedy         | audience laughter beats, fast punchlines → stress timing-based clip picker   |
| `julian-treasure-speak` | en | TED tech-talk (slides)      | single-speaker minimal silence → tests "don't over-cut a tight talk"         |

**5 new picks below, ranked by importance.**

---

## 1. `he-tongxue-5g` — Bilibili tech vlog (Chinese)

- **URL**: https://www.bilibili.com/video/BV1f4411M7QC
- **Title**: 【何同学】有多快？5G在日常使用中的真实体验
- **Why it stresses the tool differently**: visual b-roll heavy (city shots, speed tests, on-screen graphics), single creator narration with editorial cuts already baked in — opposite of 营销号 chaos; tests whether the cutter respects existing visual rhythm and uses visual reframe rather than over-cutting speech.
- **Duration**: 7:34 (454s) | **Language**: Chinese | **License**: Bilibili UGC — eval-only fair use, not redistributed
- **Author**: 老师好我叫何同学 | **Views**: 33.7M (top creator, stable URL)
- **Fetch command**:
  ```bash
  bash eval/fetch_bilibili.sh BV1f4411M7QC he-tongxue-5g
  ```
- **Prediction**: 7:34 vlog → 1-2 vertical 60-90s clips centered on (a) the iPhone speed-test reveal, (b) the rooftop drone shot punchline. Speech-only LLM should NOT be the dominant signal here; visual saliency must lead.

---

## 2. `tim-urban-procrast` — TED storytelling / punchline-heavy (English)

- **URL**: https://www.ted.com/talks/tim_urban_inside_the_mind_of_a_master_procrastinator
- **Title**: Inside the mind of a master procrastinator
- **Why it stresses the tool differently**: monologue with comedic timing, drawn diagrams, recurring "Instant Gratification Monkey" callbacks. Audience laughs are clip-anchor signals. Stress-tests the LLM's "find punchlines" prompt against narrative buildup, not just one-liners.
- **Duration**: 13:54 (834s) | **Language**: English | **License**: CC BY-NC-ND 4.0 (TED)
- **Fetch command**:
  ```bash
  yt-dlp --no-warnings -f "best[height<=720]/best" \
    -o "eval/data/tim-urban-procrast.%(ext)s" \
    "https://www.ted.com/talks/tim_urban_inside_the_mind_of_a_master_procrastinator"
  ```
- **Prediction**: 14 min talk → 3 clips of 45-75s each, centered on (a) "Instant Gratification Monkey" reveal, (b) the panic monster, (c) the calendar-of-life closer. Each clip should land on an audience-laugh boundary.

---

## 3. `sam-harris-ai` — TED philosophical talk, podcast-proxy (English)

- **URL**: https://www.ted.com/talks/sam_harris_can_we_build_ai_without_losing_control_over_it
- **Title**: Can we build AI without losing control over it?
- **Why it stresses the tool differently**: wandering, abstract, low audience-reaction signal, lots of "you know", "I think", "imagine that" — closest TED gets to a Lex-Fridman-style podcast. No YouTube podcast available on this pod (YouTube is bot-blocked), so this is the substitute. Tests fillers/disfluency removal and topical-clustering to find a quotable thesis.
- **Duration**: 14:18 (858s) | **Language**: English | **License**: CC BY-NC-ND 4.0 (TED)
- **Fetch command**:
  ```bash
  yt-dlp --no-warnings -f "best[height<=720]/best" \
    -o "eval/data/sam-harris-ai.%(ext)s" \
    "https://www.ted.com/talks/sam_harris_can_we_build_ai_without_losing_control_over_it"
  ```
- **Prediction**: 14 min ramble → 1-2 viral 60s clips, each a thesis statement ("we will build superintelligent AI ... we have not yet decided we care") with disfluencies trimmed. Should be a stark before/after vs the 营销号 case.

---

## 4. `maz-jobrani-standup` — TED stand-up comedy (English)

- **URL**: https://www.ted.com/talks/maz_jobrani_a_saudi_an_indian_and_an_iranian_walk_into_a_qatari_bar
- **Title**: A Saudi, an Indian and an Iranian walk into a Qatari bar...
- **Why it stresses the tool differently**: pure stand-up. Audience laughter is the loudest signal. Punchlines are dense (every 15-30s). Stress-tests whether the cut-picker correctly aligns to laugh-boundaries instead of cutting into the next setup.
- **Duration**: 6:54 (414s) | **Language**: English | **License**: CC BY-NC-ND 4.0 (TED)
- **Fetch command**:
  ```bash
  yt-dlp --no-warnings -f "best[height<=720]/best" \
    -o "eval/data/maz-jobrani-standup.%(ext)s" \
    "https://www.ted.com/talks/maz_jobrani_a_saudi_an_indian_and_an_iranian_walk_into_a_qatari_bar"
  ```
- **Prediction**: 6:54 set → 2-3 self-contained 30-45s bits, each a setup→punchline→laugh-tail. Cuts should NEVER end mid-laugh. Good test for laughter-VAD.

---

## 5. `julian-treasure-speak` — TED tech-talk, tight pacing (English)

- **URL**: https://www.ted.com/talks/julian_treasure_how_to_speak_so_that_people_want_to_listen
- **Title**: How to speak so that people want to listen
- **Why it stresses the tool differently**: tightly-paced single-speaker talk with structured lists ("the seven deadly sins of speaking", "HAIL"). Minimal silence, no filler. Inverse-stress: the tool should know NOT to over-cut; if it produces 5 clips of equal length, that's a fail mode.
- **Duration**: 9:44 (584s) | **Language**: English | **License**: CC BY-NC-ND 4.0 (TED)
- **Fetch command**:
  ```bash
  yt-dlp --no-warnings -f "best[height<=720]/best" \
    -o "eval/data/julian-treasure-speak.%(ext)s" \
    "https://www.ted.com/talks/julian_treasure_how_to_speak_so_that_people_want_to_listen"
  ```
- **Prediction**: 9:44 talk → 1 highlight clip (~60s) on the HAIL framework reveal + the vocal demonstration. Should NOT chop the seven-sins enumeration. If the tool produces a flat 3x60s split, that's a regression vs human edit.

---

## Notes on what we DIDN'T pick (and why)

- **YouTube (Lex Fridman, JRE, NeurIPS, dev-conf talks)**: this pod is in
  YouTube's bot-detection blocklist for unauthenticated yt-dlp (`Sign in to
  confirm you're not a bot`). Tried `player_client` overrides for `ios`,
  `android`, `web_safari`, `mweb`, `tv`, `tv_simply` — all blocked. Would need
  cookies-from-browser export. Punted.
- **archive.org standup mirrors**: most were <2 min clips, not representative
  of a real comedy set.
- **Vimeo**: returned 404 on the few public IDs tried; not worth chasing.
- **Reaction / split-screen video**: skipped intentionally for this round.
  Speaker-tracking reframe is a v0.2+ feature; better to demo what v0.1 ships
  with first. If we want it, `BV1U35g61Eho` (老外看《瑞克和莫蒂》) is a 31min
  reaction with a webcam-overlay that would work.

## Total budget for overnight run

| Fixture | Duration |
|---------|---------:|
| marketing-bili (existing) | ~3 min |
| ted-cn (existing) | 14 min |
| he-tongxue-5g | 7:34 |
| tim-urban-procrast | 13:54 |
| sam-harris-ai | 14:18 |
| maz-jobrani-standup | 6:54 |
| julian-treasure-speak | 9:44 |
| **Total** | **~70 min source** |

At faster-whisper large-v3 on H100 ≈ 30-40x realtime, transcription ≈ 2-3 min.
LLM cut-picking + ffmpeg encode dominates wall time. Whole reel should fit in
an overnight run comfortably.
