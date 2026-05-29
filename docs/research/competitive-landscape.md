# Competitive Landscape — Video Auto-Edit OSS / SaaS (2026-05)

> Scan window: ~15 min. All stars verified via `gh api repos/<owner>/<name>` (GitHub REST), 2026-05-29.

## 1. TL;DR (5 lines, actionable)

1. **v0.2 (whisper → Gemini → ffmpeg) is the simplest possible cut of this space** — the same recipe is shipped by 100+ tiny "OpusClip alt" repos. Differentiation has to come from *reframe + caption styling + virality ranking*, not from "transcribe + cut".
2. **The real OSS leader for transcript-based cutting is `mli/autocut` (7.7k stars, archived-ish, last push 2024-10)** — text-editor style, but no reframe/captions. **`WyattBlue/auto-editor` (4.4k, very active, Nim rewrite)** is the leader for *silence/motion* cutting.
3. **For long → short viral clips the canonical OSS lib is `ClipsAI/clipsai` (492 stars, stale since 2024-01)** — TextTiling + WhisperX + face-tracked 9:16 reframe. **It is the right thing to fork** if you want a serious OpusClip clone — its core algorithm (TextTiling + speaker-aware reframe) is what's missing from v0.2.
4. **The biggest commercial gap is not the cut algorithm, it's: (a) face-tracked vertical reframe, (b) "kinetic" word-by-word burned captions, (c) virality ranking with hook-detection.** All three exist in OSS form (clipsai, captacity, several Opus clones) — combinable in ~1–2 weeks.
5. **Don't reinvent — assemble.** Fork `clipsai` for reframe+segmentation, swap its old MiniLM for Gemini for ranking, add `captacity` (138★) or `clipify` (393★, Claude Code skill!) for caption burn-in, keep your faster-whisper + ffmpeg backbone.

## 2. OSS Ranking (verified stars)

| # | Repo | Stars | Last push | What it does | Reusable? |
|---|------|------:|-----------|--------------|-----------|
| 1 | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 67,668 | 2026-05-29 | 一句话生成短视频（脚本→TTS→素材→剪辑），中文社区龙头 | Different scope (gen, not edit). Steal: ffmpeg subtitle styling, Streamlit UI |
| 2 | [FujiwaraChoki/MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) | 30,620 | recent | YouTube Shorts auto-pipeline (script + render + upload) | Different scope |
| 3 | [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | 17,176 | 2026-03-24 | "Netflix-level" subtitle cut/translate/dub, end-to-end | **Yes** — borrow segmentation + sub style |
| 4 | [WEIFENG2333/VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) | 14,792 | 2026-05-24 | LLM-based subtitle 断句/校正/翻译 (中文 GUI) | **Yes** — LLM punctuation + line-break logic |
| 5 | [FujiwaraChoki/MoneyPrinter](https://github.com/FujiwaraChoki/MoneyPrinter) | 13,319 | 2026-03-26 | MoviePy-based YouTube Shorts maker | Style ref |
| 6 | [YaoFANGUK/video-subtitle-extractor](https://github.com/YaoFANGUK/video-subtitle-extractor) | 8,892 | recent | OCR-based hard-sub → SRT | Sidecar tool |
| 7 | [mli/autocut](https://github.com/mli/autocut) | 7,715 | 2024-10-05 | 用文本编辑器剪视频（whisper + 删句即删段） | **Direct competitor** — same algo as v0.2 |
| 8 | [RayVentura/ShortGPT](https://github.com/RayVentura/ShortGPT) | 7,367 | 2025-02-10 | AI framework for shorts/tiktok automation | Architecture ref |
| 9 | [MoneyPrinterPlus](https://github.com/ddean2009/MoneyPrinterPlus) | 6,395 | recent | 一键混剪 + 自动发抖音/快手/小红书 | Publishing layer |
| 10 | [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 4,871 | 2026-05-28 | OpenCV scene/cut detection (lib) | **Yes — drop in for shot boundary** |
| 11 | [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | 4,354 | 2026-05-29 | Silence/motion-based auto cut, Nim rewrite, very active | Different paradigm (raw signal, not LLM) |
| 12 | [m1guelpf/auto-subtitle](https://github.com/m1guelpf/auto-subtitle) | 2,232 | 2024-07-12 | Whisper → SRT → ffmpeg burn-in | Sub burn-in ref |
| 13 | [ClipsAI/clipsai](https://github.com/ClipsAI/clipsai) | 492 | 2024-01-17 | **Long → short clips: TextTiling segmentation + face-tracked 9:16 reframe** | **★ Best fork target ★** (stale but battle-tested) |
| 14 | [louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify) | 393 | 2026-05-05 | **Claude Code skill** for clip extraction + 9:16 reframe + Opus-style captions | **★ Plug-in candidate ★** |
| 15 | [unconv/captacity](https://github.com/unconv/captacity) | 138 | 2024-06-07 | Whisper → kinetic word-by-word burned captions for Shorts | **Yes — drop in for caption styling** |

(Smaller niche: `Anil-matcha/ai-clipping-comfyui` 17★ — ComfyUI nodes; `KazKozDev/auto-vertical-reframe` 5★ — reframe CLI; `suryaelidanto/Opus-Pro-Clone-AI-Video-Clipper-SaaS` 12★ — full Opus SaaS clone.)

## 3. Tech-Stack Matrix

| Tool | Silence | ASR | LLM ranking | Face / ASD | Scene cut | Vision (CLIP/multimodal) | 9:16 reframe | Burned captions |
|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **auto-video-cut v0.2 (us)** | implicit | ✅ faster-whisper | ✅ Gemini | ❌ | ❌ | ❌ | ❌ | ❌ |
| mli/autocut | ❌ | ✅ whisper | ❌ | ❌ | ❌ | ❌ | ❌ | optional SRT |
| auto-editor | ✅ (core) | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| ClipsAI | ❌ | ✅ WhisperX | TextTiling+MiniLM | ✅ pyannote | ❌ | ❌ | ✅ face-track | ❌ |
| clipify | ❌ | ✅ | ✅ Claude | ✅ | ❌ | ❌ | ✅ | ✅ Opus-style |
| captacity | ❌ | ✅ whisper | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ kinetic |
| VideoLingo | ❌ | ✅ WhisperX | ✅ GPT/Claude (split+translate) | ❌ | ❌ | ❌ | ❌ | ✅ + dub |
| VideoCaptioner | ❌ | ✅ | ✅ punctuation/break | ❌ | ❌ | ❌ | ❌ | ✅ |
| MoneyPrinterTurbo | ❌ | ✅ | ✅ script-gen | ❌ | ❌ | (stock B-roll search) | ✅ portrait | ✅ |
| ai-clipping-comfyui | ❌ | ✅ Whisper | virality rank + dedupe | ✅ face-track (muapi) | ❌ | ❌ | ✅ | ✅ |
| Opus-Pro-Clone (SaaS) | ❌ | ✅ | ✅ Gemini | ✅ | ❌ | ❌ | ✅ | ✅ |
| **Submagic / OpusClip (商用)** | ✅ | ✅ | ✅ "virality" model | ✅ | ✅ | ✅ (CLIP/Gemini-vid) | ✅ | ✅ animated |

## 4. v0.2 vs Commercial — Top 5 Gaps

| # | Gap | What we have | What they do | Effort to close |
|---|-----|--------------|--------------|-----------------|
| 1 | **No 9:16 vertical reframe with face/speaker tracking** | landscape only | every Shorts/TikTok tool ships face-tracked auto-crop | **1 wk** — fork `ClipsAI` resize module (uses pyannote ASD) or use MediaPipe Face Detection + per-frame ROI smoothing. `clipify` already does it in Python. |
| 2 | **No burned "kinetic" captions** (word-by-word highlight, animated) | nothing burned | Submagic's #1 selling point; OpusClip auto-styles | **1 wk** — drop in `unconv/captacity` (138★) or copy `clipify`'s ASS-style generator. faster-whisper already gives word timestamps. |
| 3 | **No virality / hook ranking** (1 long video → N ranked short clips) | one-shot keep-or-cut | OpusClip ranks 10–20 candidate clips with a "virality score" + hook strength + retention prediction | **2 wk** — Gemini-based scoring on `(hook_text, payoff, length, controversy)`; `ClipsAI`'s TextTiling is the segmentation layer. |
| 4 | **No multimodal signals** (no face / scene / saliency / video frame analysis) | text-only | commercial tools combine Gemini-Pro-Video / CLIP / face count / scene cuts | **3 mo** — proper engineering: PySceneDetect + Gemini Vision + speaker diarization + saliency. Gemini-Pro-Video already does most of this in one API call. |
| 5 | **No b-roll / kinetic typography / overlay generation** | bare cut+concat | Submagic auto-inserts emojis/B-roll/zooms at keywords | **1–3 mo** — keyword-triggered overlay templates (easy MVP) → AI-generated B-roll w/ stock-footage search (medium) → generative B-roll with Veo/Sora-style models (hard). |

## 5. Recommended Next Steps — 3 options

| Option | Description | Effort | Risk |
|--------|-------------|-------|------|
| **A. "Catch up to OSS"** (1 week sprint) | Fork `ClipsAI` (reframe + segmentation) + integrate `captacity` (kinetic captions). Result: v0.3 = transcript cut + 9:16 reframe + animated burned captions. | **5–7 days** | Low. ClipsAI is stale (2024-01) — may need pinned deps; pyannote needs HF token. |
| **B. "Pure assembly play"** | Don't fork — declare `clipify` (393★) as the upstream skill, contribute back, focus our work on the *Gemini-based ranking layer* and a CLI/SDK Steve actually wants. | **3–5 days** | Medium. Tied to clipify maintainer's pace, but lowest code we own. |
| **C. "Commercial-grade swing"** (3 month roadmap) | Build the full pipeline: PySceneDetect + Gemini-Pro-Video for hook detection + ASD reframe + virality scoring + auto B-roll insertion + auto kinetic captions + auto thumbnail. | **8–12 weeks** | High. Real engineering, but the only path to "actually competitive with Submagic/OpusClip" rather than "another 5-star OSS demo". |

**Recommendation**: do **A this week** (close the embarrassing gaps), then evaluate **C** with Steve based on whether this is a serious project or a side demo. **B** is the cheapest if the goal is "use, not build".

## 6. References (verified URLs)

- https://github.com/mli/autocut — 7,715★, last push 2024-10-05
- https://github.com/WyattBlue/auto-editor — 4,354★, last push 2026-05-29
- https://github.com/ClipsAI/clipsai — 492★, last push 2024-01-17
- https://github.com/Huanshere/VideoLingo — 17,176★
- https://github.com/WEIFENG2333/VideoCaptioner — 14,792★
- https://github.com/harry0703/MoneyPrinterTurbo — 67,668★
- https://github.com/FujiwaraChoki/MoneyPrinter — 13,319★
- https://github.com/FujiwaraChoki/MoneyPrinterV2 — 30,620★
- https://github.com/ddean2009/MoneyPrinterPlus — 6,395★
- https://github.com/RayVentura/ShortGPT — 7,367★
- https://github.com/Breakthrough/PySceneDetect — 4,871★
- https://github.com/m1guelpf/auto-subtitle — 2,232★
- https://github.com/YaoFANGUK/video-subtitle-extractor — 8,892★
- https://github.com/louisedesadeleer/clipify — 393★, Claude Code skill, 2026-05-05
- https://github.com/unconv/captacity — 138★, kinetic captions
- https://github.com/Anil-matcha/ai-clipping-comfyui — 17★, ComfyUI nodes for OpusClip alt
- https://github.com/suryaelidanto/Opus-Pro-Clone-AI-Video-Clipper-SaaS — 12★, full Opus SaaS clone (Gemini + reframe + subs + Docker)
- https://github.com/KazKozDev/auto-vertical-reframe — 5★, scene-aware 9:16 CLI

---
*Generated 2026-05-29. Stars verified via `gh api`. No fabricated repos.*
