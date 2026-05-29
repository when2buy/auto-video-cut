# Reports — auto-video-cut

> Every human-checkpoint produces a report URL. Newest at top.

| Date | Phase | URL | Summary |
|------|-------|-----|---------|
| 2026-05-30 | **v0.3 LANDING DEMO** ⭐ | https://reports.steveouyang.com/2026-05-30-v0.3-demo | Multi-fixture demo (6 videos): full pipeline (cut + 9:16 reframe + Opus-style burned captions). The product Steve would actually share. |
| 2026-05-29 | v0.2 ASR shipped | https://reports.steveouyang.com/2026-05-29-v0.2-asr-shipped | First real product output. 营销号 237s → 79s. ASR + Gemini sentence-pick + ffmpeg cut, no reframe/captions. |
| 2026-05-26 | v0.1 on real 营销号 → 0% trim | https://reports.steveouyang.com/2026-05-26-bili-real | Definitive negative result on real Bilibili 营销号. Wall-to-wall narration → zero detectable silence. Motivated v0.2. |
| 2026-05-26 | v0.1 on TED Chinese-subbed | https://reports.steveouyang.com/2026-05-26-real-eval | 11% trim on already-edited content. |
| 2026-05-26 | MVP shipped (synthetic) | https://reports.steveouyang.com/2026-05-26-mvp-shipped | ⚠️ MISLEADING — synthetic fixture. Superseded by bili-real. |
| 2026-05-26 | Research | https://reports.steveouyang.com/2026-05-26-research | 4 candidate approaches compared. v0.2 = Hybrid (chosen). |

## Channel notes

- All URLs use `public-cf-pages` (Cloudflare Pages, custom domain `reports.steveouyang.com`)
- The v0.3 demo references videos via relative paths under `assets/v0.3/` (not base64 inlined) so the bundle stays under the 25 MB per-file CF Pages limit (~7 KB HTML + ~80 MB videos co-deployed).
- Use `eval/publish_all.sh` to deploy: it bundles all reports + assets in one wrangler call, avoiding the single-file-overwrites-prod failure mode.
