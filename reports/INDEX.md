# Reports — auto-video-cut

> Every human-checkpoint produces a report URL. Newest at top.

| Date | Phase | URL | Summary |
|------|-------|-----|---------|
| 2026-05-29 | **v0.2 ASR SHIPPED** | https://reports.steveouyang.com/2026-05-29-v0.2-asr-shipped | 🎉 First real product output. Bilibili 营销号 237s → 79s (67% trim) via Whisper + Gemini-2.5-pro + ffmpeg. 86s wall-clock. Coherent narrative preserved. |
| 2026-05-26 | v0.1 on real 营销号 → 0% trim | https://reports.steveouyang.com/2026-05-26-bili-real | Definitive negative result. v0.1 alone is useless for this genre. Motivated v0.2. |
| 2026-05-26 | v0.1 on TED Chinese-subbed | https://reports.steveouyang.com/2026-05-26-real-eval | 11% trim on already-edited content. |
| 2026-05-26 | MVP shipped (synthetic) | https://reports.steveouyang.com/2026-05-26-mvp-shipped | ⚠️ MISLEADING — synthetic fixture. Superseded. |
| 2026-05-26 | Research | https://reports.steveouyang.com/2026-05-26-research | 4 candidate approaches. v0.2 = Hybrid (chosen). |

## Channel notes

- All URLs use `public-cf-pages` (Cloudflare Pages, custom domain `reports.steveouyang.com`)
- IMPORTANT: each `report publish <single-file>` overwrites the production deployment with ONLY that file. To keep multiple reports live, deploy all together via `wrangler pages deploy <dir>`. See `eval/publish_all.sh`.
