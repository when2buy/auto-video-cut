# Learnings

> Agents append to this file. Humans periodically distill into `docs/decisions.md` or how-tos.

Format: `- YYYY-MM-DD <feature>: <one-line learning>`

---

- 2026-05-26 v0.1: auto-editor's prebuilt linux binary requires GLIBC_2.38 — not on Pluto pod. Pure ffmpeg silencedetect + concat works in <200 lines. Decision reversibility paid off.
- 2026-05-26 v0.1: ffmpeg's `-f null -` muxer needs `-vn` to drop video stream — some builds lack `wrapped_avframe` encoder. Otherwise silencedetect never runs.
- 2026-05-26 v0.1: AAC audio adds tiny noise floor; -30 dBFS threshold still catches `anullsrc` digital silence reliably with d=0.4.
- 2026-05-26 v0.1: ffmpeg "-c copy" with concat demuxer works only if all segments have identical codec params; we re-encode each segment with consistent settings to be safe (~10% size overhead, frame-accurate).
- 2026-05-26 process: report-skill compare-grid template handles `kind: "video"` cells with data: URIs — self-contained reports embed input vs output mp4s directly.
- 2026-05-26 v0.1-real-eval: synthetic fixture was misleading. Real already-edited content (TED talk Chinese-subbed) only trims 11%. v0.1 alone is INSUFFICIENT for marketing/creator use case. Need v0.2 ASR.
- 2026-05-26 data: Bilibili anti-bot (HTTP 412), YouTube channel API 404 from this pod. yt-dlp works on TED.com. For real 营销号 fixture, need Steve to provide mp4 directly OR fetch from non-blocked machine.
- 2026-05-26 perf: full 14min run = 49s wall-clock (~3.5s compute / 1min input). Most of it is ffmpeg re-encoding segments, not silence detection itself.
