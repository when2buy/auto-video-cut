# Reports — auto-video-cut

> Every human-checkpoint produces a report URL. Newest at top.

| Date | Phase | URL | Summary |
|------|-------|-----|---------|
| 2026-05-26 | **v0.1 on real 营销号 → 0% trim** | https://reports.steveouyang.com/2026-05-26-bili-real | Definitive negative result on real Bilibili 营销号 (BV1XJDKBhEyE). Wall-to-wall narration + BGM = zero detectable silence. v0.1 alone is useless for this genre. |
| 2026-05-26 | v0.1 on TED Chinese-subbed | https://reports.steveouyang.com/2026-05-26-real-eval | 11% trim on already-edited content. Predicted v0.1 weak; bili-real confirms it's worse than predicted. |
| 2026-05-26 | MVP shipped (synthetic) | https://reports.steveouyang.com/2026-05-26-mvp-shipped | ⚠️ MISLEADING — synthetic tone→silence→tone fixture. Code-path test, not a feature test. Superseded by real-eval. |
| 2026-05-26 | Research | https://reports.steveouyang.com/2026-05-26-research | 4 candidate approaches compared. v0.1 = silence (bottom layer), v0.2 = ASR (the missing critical piece). |

## Channel notes

- All URLs above use `public-cf-pages` (Cloudflare Pages)
- The earlier `thdscoring.adobefoundry.com` / `pluto-prod-zouyang-xpu-1gpu-2-0-41004.or2.colligo.dev` URLs published via `private-svc-tunnel` were dead (~84s timeouts on this pod's tunnel; SimpleHTTPServer was up locally but tunnel was down). Use `public-cf-pages` channel by default.
