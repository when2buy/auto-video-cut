# Reports — auto-video-cut

> Every human-checkpoint produces a report URL. Newest at top.

| Date | Phase | URL | Summary |
|------|-------|-----|---------|
| 2026-05-30 | **v0.5 MULTI-SOURCE MASHUP** ⭐ | https://reports.steveouyang.com/2026-05-30-v0.5-multi-demo | Throw N videos in, get one coherent supercut out. Gemini reads all transcripts together, finds (or honors) a theme, weaves pieces from each speaker into one argument. 3 demos: auto-discovered + 2 user-given themes. |
| 2026-05-30 | v0.4 SEMANTIC REMIX | https://reports.steveouyang.com/2026-05-30-v0.4-remix-demo | Template-driven non-chronological reordering. 2 fixtures × 3 templates (viral_hook / top3 / thesis) = 6 remixes. |
| 2026-05-30 | v0.3 LANDING DEMO | https://reports.steveouyang.com/2026-05-30-v0.3-demo | Multi-fixture demo (6 videos): full pipeline (cut + 9:16 reframe + Opus-style burned captions). |
| 2026-05-29 | v0.2 ASR shipped | https://reports.steveouyang.com/2026-05-29-v0.2-asr-shipped | First real product output. 营销号 237s → 79s. |
| 2026-05-26 | v0.1 on real 营销号 → 0% trim | https://reports.steveouyang.com/2026-05-26-bili-real | Definitive negative result motivating v0.2. |
| 2026-05-26 | v0.1 on TED Chinese-subbed | https://reports.steveouyang.com/2026-05-26-real-eval | 11% trim on already-edited content. |
| 2026-05-26 | MVP shipped (synthetic) | https://reports.steveouyang.com/2026-05-26-mvp-shipped | ⚠️ MISLEADING — synthetic fixture. Superseded. |
| 2026-05-26 | Research | https://reports.steveouyang.com/2026-05-26-research | 4 candidate approaches compared. |

## Channel notes

- All URLs use `public-cf-pages` (Cloudflare Pages, custom domain `reports.steveouyang.com`)
- Use `eval/publish_all.sh` to deploy: bundles all reports + assets/{v0.3,v0.4,v0.5}/ in one wrangler call
