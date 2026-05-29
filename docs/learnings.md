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
- 2026-05-26 bili-fetch: yt-dlp fails on Bilibili w/ HTTP 412 even with iPhone UA + Referer. Workaround: `bilibili-api-python` (PyPI) handles wbi signing properly. Direct HTTP to /x/web-interface/view also works for metadata. Saved as eval/fetch_bilibili.sh.
- 2026-05-26 bili-real-eval: real Bilibili 营销号 (BV1XJDKBhEyE) has mean_volume -11.7 dB and almost zero silence — v0.1 trims 0% even at -20 dB / 0.15s. This is the worst case and the target case simultaneously.
- 2026-05-26 mux: bilibili-api-python's get_download_url can return baseUrl that occasionally serves truncated streams when downloaded via raw requests w/o retry adapter. Use Session + Retry(total=5, backoff_factor=1.0) on requests, then ffmpeg copy mux.
- 2026-05-26 report-channel: published 24 MB report via private-svc-tunnel; tunnel was dead (84s timeouts). HTML JSON also had unescaped \n in a string causing Alpine.js to fail. Two fixes: (1) downsize embedded videos (640x… + crf 28 → ~1.5 MB each, total report 3.8 MB); (2) round-trip JSON through json.loads to validate before saving; (3) prefer public-cf-pages (https://reports.steveouyang.com/<slug>) channel over private-svc-tunnel for reports >5 MB.
- 2026-05-29 v0.2-shipped: Whisper + Gemini-2.5-pro + ffmpeg pipeline works end-to-end. 237s -> 79s (67% trim) on real 营销号. Each stage independently testable. Reusing silence.extract_and_concat for the final cut step kept the diff small (~250 LOC for v0.2 over v0.1).
- 2026-05-29 cf-pages: each `report publish single-file` overwrites the prod deployment with only that file — historical URLs become 404 unless you batch-deploy. Solution: eval/publish_all.sh deploys reports/*.html in one wrangler call.
- 2026-05-29 json-injection: `re.sub(pattern, repl_string, ...)` interprets backslash escapes in repl_string. Using `re.sub(pattern, lambda m: ..., ...)` avoids this. Was silently corrupting JSON with literal newlines from \n in repl strings, breaking Alpine.js rendering.
- 2026-05-29 gemini-2.5-pro latency: ~70s for a 88-sentence prompt with structured output. faster-whisper is 5-6x faster than the LLM stage now. v0.3 candidate: switch to gemini-3.5-flash for the keep-list step, expect <10s.
