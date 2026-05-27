# eval/

Real-world fixtures and runs. Heavy data is `.gitignore`d.

## Layout

```
eval/
├── data/    fixtures (mp4, srt). gitignored.
├── runs/    avc cut outputs. gitignored.
└── README.md
```

## Adding a fixture

1. Drop the source mp4 into `data/<slug>.mp4`
2. Add a `data/<slug>.json` with: `{source, license, why_representative, transcript_path?}`
3. Run `python3 -m avc.cli cut data/<slug>.mp4 --out runs/<slug>-v0.1.mp4`
4. Compare durations; if anomalous, file a learning in `../docs/learnings.md`

## Why these aren't in git

Real videos are too heavy for a small skill repo, and licenses (e.g. TED CC-BY-NC-ND)
forbid redistribution. The fetch script makes them reproducible without redistributing.

## Current fixtures

| Slug | Duration | Source | License | Status |
|------|---------:|--------|---------|--------|
| ted-cn | 14:03 | https://www.ted.com/talks/lera_boroditsky_how_language_shapes_the_way_we_think?language=zh-cn | CC BY-NC-ND 4.0 (TED) | proxy for "edited content" — used to prove v0.1 alone is insufficient |

## Wanted fixtures

- 真实中文 营销号 / Bilibili creator (1-3 min) — pod can't fetch Bilibili, please drop mp4 manually
- Raw vlog (un-edited 5-10 min) — to confirm v0.1 helps on un-edited content
- Lex-style podcast (10-30 min) — predicted v0.1 effective
