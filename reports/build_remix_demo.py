#!/usr/bin/env python3
"""Generate the v0.4 remix-demo report.

Reads:
  reports/assets/v0.4/<fixture>-<template>.mp4   (compressed remix outputs)
  eval/remix/<fixture>-<template>.log            (LLM rationale)

Writes:
  reports/2026-05-30-v0.4-remix-demo.html        (single self-contained HTML)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "reports" / "assets" / "v0.4"
REMIX = ROOT / "eval" / "remix"
DATA = ROOT / "eval" / "data"
OUT = ROOT / "reports" / "2026-05-30-v0.4-remix-demo.html"

# Templates (subset shipped) — keep in sync with src/avc/remix.py TEMPLATES
TEMPLATE_META = {
    "viral_hook": {
        "label": "Viral Hook",
        "description": "Cold-open with the strongest line, then setup, then payoff. Optimized for TikTok/Reels.",
        "target_s": 35,
    },
    "top3": {
        "label": "Top-3 Highlights",
        "description": "Top-3 punchlines, ranked by impact (not original timeline).",
        "target_s": 75,
    },
    "thesis": {
        "label": "Thesis",
        "description": "Speaker's main argument distilled. One thesis statement + one supporting example.",
        "target_s": 50,
    },
}

FIXTURE_META = {
    "tim-urban-procrast": {
        "label": "Tim Urban — Procrastinator",
        "source_s": 834,
    },
    "maz-jobrani-standup": {
        "label": "Maz Jobrani — Stand-up",
        "source_s": 415,
    },
}


def collect() -> list[dict]:
    """One record per (fixture, template) cell. Skip if either video missing."""
    rows: list[dict] = []
    for fixture, fix_meta in FIXTURE_META.items():
        for template, tpl_meta in TEMPLATE_META.items():
            video = ASSETS / f"{fixture}-{template}.mp4"
            if not video.exists():
                continue
            log_path = REMIX / f"{fixture}-{template}.log"
            rationale = ""
            in_dur = out_dur = None
            n_kept = n_total = None
            if log_path.exists():
                log = log_path.read_text(errors="ignore")
                m = re.search(r"\[remix\] rationale: (.+)", log)
                if m:
                    rationale = m.group(1).strip()
                m2 = re.search(
                    r"\(([\w_]+)\): ([\d.]+)s → ([\d.]+)s \((\d+)/(\d+) sentences",
                    log,
                )
                if m2:
                    in_dur = float(m2.group(2))
                    out_dur = float(m2.group(3))
                    n_kept = int(m2.group(4))
                    n_total = int(m2.group(5))
            rows.append({
                "fixture": fixture,
                "template": template,
                "fixture_label": fix_meta["label"],
                "template_label": tpl_meta["label"],
                "template_desc": tpl_meta["description"],
                "video_url": f"assets/v0.4/{video.name}",
                "rationale": rationale,
                "in_dur": in_dur,
                "out_dur": out_dur,
                "n_kept": n_kept,
                "n_total": n_total,
            })
    return rows


HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>auto-video-cut · v0.4 remix demo</title>
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<style>
  body { font-feature-settings: "ss01","cv11"; }
  .vid-vert { aspect-ratio: 9/16; max-height: 60vh; background: #0a0a0a; border-radius: 12px; }
  .glow { box-shadow: 0 0 40px rgba(255,255,255,0.06); }
  .ring-amber { box-shadow: 0 0 0 2px rgba(245, 158, 11, .35); }
</style>
</head>
<body class="bg-zinc-950 text-zinc-100">

<script id="rows" type="application/json">__ROWS_JSON__</script>
<script id="fixtures" type="application/json">__FIXTURES_JSON__</script>
<script id="templates" type="application/json">__TEMPLATES_JSON__</script>

<div x-data="{
    rows: JSON.parse(document.getElementById('rows').textContent),
    fixtures: JSON.parse(document.getElementById('fixtures').textContent),
    templates: JSON.parse(document.getElementById('templates').textContent),
    activeFixture: null,
    activeTemplate: null,
    init() { this.activeFixture = this.fixtures[0]?.key; this.activeTemplate = this.templates[0]?.key; },
    cell(fix, tpl) { return this.rows.find(r => r.fixture === fix && r.template === tpl); }
  }" x-init="init()" class="max-w-6xl mx-auto p-6">

  <header class="text-center pt-10 pb-8">
    <div class="text-xs uppercase tracking-widest text-amber-400 mb-3">auto-video-cut · v0.4 — semantic remix</div>
    <h1 class="text-4xl md:text-5xl font-bold tracking-tight leading-tight">
      Same source. <span class="text-amber-400">Three formats.</span><br/>
      Pick the one that hits.
    </h1>
    <p class="mt-5 text-base md:text-lg text-zinc-300 max-w-2xl mx-auto leading-relaxed">
      Gemini classifies each sentence by narrative role (hook · setup · punchline · thesis · payoff)
      then <b>reorders</b> them per a creative template. Output is non-chronological by design.
    </p>
    <code class="mt-5 inline-block px-4 py-2 bg-zinc-800/80 rounded-lg text-xs text-amber-300 font-mono">
      avc remix input.mp4 --out short.mp4 --template viral_hook --reframe --captions
    </code>
  </header>

  <!-- Fixture selector -->
  <nav class="flex flex-wrap gap-2 justify-center mb-3 text-sm">
    <span class="text-zinc-500 self-center mr-2 text-xs uppercase tracking-widest">Source:</span>
    <template x-for="f in fixtures" :key="f.key">
      <button
        @click="activeFixture = f.key"
        :class="activeFixture === f.key ? 'bg-zinc-100 text-zinc-950 font-semibold' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'"
        class="px-3 py-1.5 rounded-full"
        x-text="f.label">
      </button>
    </template>
  </nav>

  <!-- Template selector -->
  <nav class="flex flex-wrap gap-2 justify-center mb-10 text-sm border-b border-zinc-800 pb-6">
    <span class="text-zinc-500 self-center mr-2 text-xs uppercase tracking-widest">Template:</span>
    <template x-for="t in templates" :key="t.key">
      <button
        @click="activeTemplate = t.key"
        :class="activeTemplate === t.key ? 'bg-amber-500 text-zinc-950 font-semibold' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'"
        class="px-3 py-1.5 rounded-full"
        x-text="t.label">
      </button>
    </template>
  </nav>

  <!-- Active cell: video + rationale + stats -->
  <template x-if="cell(activeFixture, activeTemplate)">
    <section class="grid md:grid-cols-2 gap-8 items-start mb-12">
      <div class="flex justify-center">
        <video
          :src="cell(activeFixture, activeTemplate).video_url"
          controls preload="metadata" class="vid-vert glow ring-amber"></video>
      </div>
      <div class="space-y-5">
        <div>
          <div class="text-xs uppercase tracking-widest text-amber-400 mb-2"
               x-text="templates.find(t => t.key === activeTemplate).label"></div>
          <p class="text-zinc-300 text-sm" x-text="templates.find(t => t.key === activeTemplate).description"></p>
        </div>
        <div class="bg-zinc-900/60 border-l-2 border-amber-500 px-4 py-3 rounded-r">
          <div class="text-xs uppercase tracking-widest text-zinc-500 mb-1">Gemini's rationale</div>
          <p class="text-sm text-zinc-200 leading-relaxed" x-text="cell(activeFixture, activeTemplate).rationale"></p>
        </div>
        <div class="text-sm text-zinc-400 space-y-1 font-mono">
          <div>Source: <span class="text-zinc-200" x-text="Math.round(cell(activeFixture, activeTemplate).in_dur) + 's'"></span></div>
          <div>Output: <span class="text-amber-400" x-text="Math.round(cell(activeFixture, activeTemplate).out_dur) + 's'"></span></div>
          <div>Sentences kept: <span class="text-zinc-200" x-text="cell(activeFixture, activeTemplate).n_kept + ' / ' + cell(activeFixture, activeTemplate).n_total"></span></div>
        </div>
      </div>
    </section>
  </template>

  <template x-if="!cell(activeFixture, activeTemplate)">
    <section class="text-center py-16 text-zinc-500">
      No render for this combination yet.
    </section>
  </template>

  <!-- Methodology -->
  <section class="mt-16 max-w-3xl mx-auto pb-12 border-t border-zinc-800 pt-10">
    <h2 class="text-2xl font-bold mb-6 text-zinc-100">Why "remix"?</h2>
    <p class="text-zinc-300 mb-4 leading-relaxed">
      The default <code class="font-mono text-amber-300 text-sm">avc pipeline</code> keeps cut sentences in source order — good for "compress to highlights" but boring for short-form. Real editors don't keep things in order. They put the punchline first, then loop back to setup, then close on the climax.
    </p>
    <p class="text-zinc-300 mb-6 leading-relaxed">
      Remix asks Gemini to classify each sentence by narrative role, then assemble per a template. ffmpeg concat doesn't care about order — sentence 43 can come before sentence 14.
    </p>

    <h3 class="text-xl font-semibold mb-4 text-zinc-100">Templates shipping in v0.4</h3>
    <div class="space-y-3 text-zinc-300">
      <template x-for="t in templates" :key="t.key">
        <div class="flex gap-4">
          <span class="text-amber-400 font-mono w-32 flex-shrink-0" x-text="t.label"></span>
          <div class="text-sm" x-text="t.description"></div>
        </div>
      </template>
    </div>

    <h3 class="text-xl font-semibold mb-4 mt-8 text-zinc-100">CLI</h3>
    <pre class="bg-zinc-900 p-4 rounded text-amber-300 text-sm overflow-x-auto"><code># Single template
avc remix talk.mp4 --out viral.mp4 --template viral_hook --reframe --captions

# Reuse transcript across templates (skip re-ASR)
avc remix talk.mp4 --out top3.mp4 --template top3 \
    --cached-transcript reports/assets/v0.3/talk.transcript.json \
    --reframe --captions
</code></pre>
  </section>

  <footer class="text-center text-xs text-zinc-500 pb-12 border-t border-zinc-800 pt-6">
    <a href="https://github.com/when2buy/auto-video-cut" class="underline hover:text-amber-400">github.com/when2buy/auto-video-cut</a>
    · v0.4 · MIT
  </footer>
</div>
</body>
</html>
"""


def build_html() -> str:
    rows = collect()
    if not rows:
        return ""
    fixtures = [{"key": k, "label": v["label"]} for k, v in FIXTURE_META.items()
                if any(r["fixture"] == k for r in rows)]
    templates = [{"key": k, "label": v["label"], "description": v["description"]}
                 for k, v in TEMPLATE_META.items() if any(r["template"] == k for r in rows)]

    rows_json = json.dumps(rows, ensure_ascii=False).replace("</script", "<\\/script")
    fixtures_json = json.dumps(fixtures, ensure_ascii=False).replace("</script", "<\\/script")
    templates_json = json.dumps(templates, ensure_ascii=False).replace("</script", "<\\/script")

    return (
        HTML_TEMPLATE
        .replace("__ROWS_JSON__", rows_json)
        .replace("__FIXTURES_JSON__", fixtures_json)
        .replace("__TEMPLATES_JSON__", templates_json)
    )


def main() -> None:
    html = build_html()
    if not html:
        print("⚠️  no remix outputs found in reports/assets/v0.4/")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"✅ {OUT}")
    print(f"   {size_kb:.0f} KB HTML (videos co-deployed via assets/v0.4/)")


if __name__ == "__main__":
    main()
