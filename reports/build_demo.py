#!/usr/bin/env python3
"""Generate the v0.3 landing-page demo report from eval/runs/ outputs.

Reads:
  reports/assets/v0.3/<slug>-input.mp4   (compressed input preview)
  reports/assets/v0.3/<slug>-output.mp4  (compressed pipeline output)
  eval/data/<slug>.json                  (source metadata, optional)
  eval/runs/<slug>-D.log                 (pipeline log, optional)

Writes:
  reports/2026-05-30-v0.3-demo.html      (single self-contained HTML)
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "reports" / "assets" / "v0.3"
RUNS = ROOT / "eval" / "runs"
DATA = ROOT / "eval" / "data"
OUT = ROOT / "reports" / "2026-05-30-v0.3-demo.html"


def collect_fixtures() -> list[dict]:
    """Reference videos via relative URLs so the HTML stays small.

    Videos are co-deployed alongside the HTML by ``eval/publish_all.sh``;
    URLs are relative to the deployed site root, e.g.
    ``assets/v0.3/<slug>-output.mp4``.
    """
    fixtures: list[dict] = []
    rel_assets = "assets/v0.3"
    for inp_video in sorted(ASSETS.glob("*-input.mp4")):
        slug = inp_video.stem.replace("-input", "")
        out_video = ASSETS / f"{slug}-output.mp4"
        if not out_video.exists():
            continue

        meta_path = DATA / f"{slug}.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

        log_path = RUNS / f"{slug}-D.log"
        summary = ""
        if log_path.exists():
            log = log_path.read_text(errors="ignore")
            m = re.search(
                r"✓ .*? → .*?: ([\d.]+)s → ([\d.]+)s \((\d+)% kept\)", log
            )
            if not m:
                m = re.search(
                    r"([\d.]+)s\s*->\s*([\d.]+)s\s*\((\d+)% kept\)", log
                )
            if m:
                summary = f"{m.group(1)}s → {m.group(2)}s ({m.group(3)}% kept)"

        title = meta.get("title") or slug.replace("-", " ").title()
        fixtures.append({
            "slug": slug,
            "title": title,
            "source": meta.get("source", ""),
            "duration": meta.get("duration_s"),
            "summary": summary,
            "input_url": f"{rel_assets}/{inp_video.name}",
            "output_url": f"{rel_assets}/{out_video.name}",
        })
    return fixtures


# Use a separate JSON-data-script-tag pattern (same approach as report-skill templates)
# rather than embedding into x-data — safer for embedded base64.
HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>auto-video-cut · v0.3 demo</title>
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<style>
  body { font-feature-settings: "ss01","cv11"; }
  .vid-vert { aspect-ratio: 9/16; max-height: 70vh; background: #0a0a0a; border-radius: 12px; }
  .vid-horiz { aspect-ratio: 16/9; max-height: 40vh; background: #0a0a0a; border-radius: 12px; width: 100%; }
  .glow { box-shadow: 0 0 60px rgba(255,255,255,0.08); }
  .ring-amber { box-shadow: 0 0 0 2px rgba(245, 158, 11, .4); }
  details > summary { cursor: pointer; user-select: none; }
</style>
</head>
<body class="bg-zinc-950 text-zinc-100">

<script id="fixtures" type="application/json">__FIXTURES_JSON__</script>

<div x-data="{ active: 0, fixtures: JSON.parse(document.getElementById('fixtures').textContent) }" class="max-w-6xl mx-auto p-6">

  <header class="text-center pt-12 pb-10">
    <div class="text-xs uppercase tracking-widest text-amber-400 mb-3">auto-video-cut · v0.3</div>
    <h1 class="text-5xl md:text-6xl font-bold tracking-tight leading-tight">
      Long video → social-ready clip<br/>
      <span class="text-amber-400">in 30 seconds.</span>
    </h1>
    <p class="mt-6 text-lg md:text-xl text-zinc-300 max-w-2xl mx-auto leading-relaxed">
      Whisper transcribes the speech. Gemini picks the punchlines.
      Face-tracked 9:16 reframe. Word-by-word burned captions. One command.
    </p>
    <code class="mt-7 inline-block px-5 py-3 bg-zinc-800/80 rounded-lg text-sm text-amber-300 font-mono">
      avc pipeline input.mp4 --out short.mp4 --reframe --captions
    </code>
  </header>

  <nav class="flex flex-wrap gap-2 justify-center mb-10 border-y border-zinc-800 py-4">
    <template x-for="(f, i) in fixtures" :key="f.slug">
      <button
        @click="active = i"
        :class="active === i ? 'bg-amber-500 text-zinc-950 font-semibold' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'"
        class="px-4 py-2 rounded-full text-sm transition"
        x-text="f.title.length > 32 ? f.title.slice(0,30) + '…' : f.title">
      </button>
    </template>
  </nav>

  <template x-for="(f, i) in fixtures" :key="f.slug">
    <section x-show="active === i" class="grid md:grid-cols-2 gap-8 items-start mb-16">
      <div>
        <div class="text-xs uppercase tracking-widest text-zinc-500 mb-3">BEFORE — first 30 s sample</div>
        <video :src="f.input_url" controls preload="metadata" class="vid-horiz glow"></video>
        <div class="mt-4 space-y-1 text-sm text-zinc-400">
          <div x-show="f.title" x-text="f.title"></div>
          <div x-show="f.duration" x-text="'full source: ' + Math.round(f.duration) + ' s'"></div>
          <div x-show="f.source">
            <a :href="f.source" class="text-amber-500/80 hover:text-amber-400 underline" target="_blank" rel="noopener">source</a>
          </div>
        </div>
      </div>
      <div>
        <div class="text-xs uppercase tracking-widest text-amber-400 mb-3">AFTER — 9:16 + captions, full output</div>
        <div class="flex justify-center">
          <video :src="f.output_url" controls preload="metadata" class="vid-vert glow ring-amber"></video>
        </div>
        <div class="mt-4 text-sm text-amber-400 font-mono" x-text="f.summary"></div>
      </div>
    </section>
  </template>

  <section class="mt-12 max-w-3xl mx-auto pb-12">
    <h2 class="text-2xl font-bold mb-6 text-zinc-100">How it works</h2>
    <ol class="space-y-4 text-zinc-300">
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">1</span>
        <div><b class="text-zinc-100">Transcribe</b> — faster-whisper large-v3 on H100, multi-language, word-level timestamps. ~13&nbsp;s per minute of input.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">2</span>
        <div><b class="text-zinc-100">AI pick</b> — Gemini 2.5 Pro reads the transcript, ranks each sentence against a style prompt, returns keep-indices. Default style: <span class="text-zinc-200 font-mono text-sm">"保留干货、punchline、关键信息；剪掉铺垫、重复、套话"</span>.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">3</span>
        <div><b class="text-zinc-100">Cut</b> — ffmpeg extracts each kept segment frame-accurately and concats.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">4</span>
        <div><b class="text-zinc-100">Reframe</b> — OpenCV Haar samples 10 frames, EMA-smooths the dominant face center, ffmpeg's <span class="font-mono text-sm">crop</span> filter follows the face. Falls back to center crop on failure.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">5</span>
        <div><b class="text-zinc-100">Captions</b> — re-transcribe the cut for synced timing, render PIL PNGs (Opus-style word-by-word highlight), ffmpeg overlay onto every frame.</div>
      </li>
    </ol>
  </section>

  <footer class="text-center text-xs text-zinc-500 pb-12 border-t border-zinc-800 pt-8">
    <a href="https://github.com/when2buy/auto-video-cut" class="underline hover:text-amber-400">github.com/when2buy/auto-video-cut</a>
    · MIT licensed · Built end-to-end overnight using
    <a href="https://github.com/when2buy/agent-native-repo" class="underline hover:text-amber-400">agent-native-repo</a>
  </footer>
</div>
</body>
</html>
"""


def build_html(fixtures: list[dict]) -> str:
    fixtures_json = json.dumps(fixtures, ensure_ascii=False, separators=(",", ":"))
    # Escape any </script> sequence inside the JSON (very unlikely with base64
    # data URIs but be safe). Browsers parse <script> tags by raw text, so
    # the only forbidden sequence is the literal "</script".
    fixtures_json = fixtures_json.replace("</script", "<\\/script")
    return HTML_TEMPLATE.replace("__FIXTURES_JSON__", fixtures_json)


def main() -> None:
    fixtures = collect_fixtures()
    if not fixtures:
        print("⚠️  no fixtures found in reports/assets/v0.3/. Build assets first.")
        return
    html = build_html(fixtures)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"✅ {OUT}")
    print(f"   {len(fixtures)} fixtures, {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
