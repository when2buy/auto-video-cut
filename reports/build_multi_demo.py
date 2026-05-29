#!/usr/bin/env python3
"""Generate the v0.5 multi-source mashup demo report.

Reads:
  reports/assets/v0.5/<run>-output.mp4    (compressed cross-source supercut)
  reports/assets/v0.5/<run>.json          (theme + rationale + per-source seconds)
  reports/assets/v0.3/<source>-input.mp4  (small input previews, reused)

Writes:
  reports/2026-05-30-v0.5-multi-demo.html
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS_V5 = ROOT / "reports" / "assets" / "v0.5"
OUT = ROOT / "reports" / "2026-05-30-v0.5-multi-demo.html"


def collect_runs() -> list[dict]:
    runs: list[dict] = []
    for meta_path in sorted(ASSETS_V5.glob("*.json")):
        run_id = meta_path.stem
        out_video = ASSETS_V5 / f"{run_id}-output.mp4"
        if not out_video.exists():
            continue
        meta = json.loads(meta_path.read_text())
        runs.append({
            "id": run_id,
            "label": meta.get("label", run_id),
            "user_theme": meta.get("user_theme"),
            "discovered_theme": meta.get("theme"),
            "rationale": meta.get("rationale", ""),
            "out_dur": meta.get("out_dur"),
            "n_clips": meta.get("n_clips"),
            "per_source_seconds": meta.get("per_source_seconds", {}),
            "source_labels": meta.get("source_labels", {}),
            "output_url": f"assets/v0.5/{out_video.name}",
            "sources": [
                {
                    "video_id": vid,
                    "label": meta.get("source_labels", {}).get(vid, vid),
                    "preview_url": f"assets/v0.3/{vid}-input.mp4",
                    "kept_seconds": dur,
                }
                for vid, dur in meta.get("per_source_seconds", {}).items()
            ],
        })
    return runs


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>auto-video-cut · v0.5 multi-source mashup</title>
<script src="https://cdn.tailwindcss.com"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<style>
  body { font-feature-settings: "ss01","cv11"; }
  .vid-vert { aspect-ratio: 9/16; max-height: 70vh; background: #0a0a0a; border-radius: 12px; }
  .vid-horiz { aspect-ratio: 16/9; background: #0a0a0a; border-radius: 8px; width: 100%; }
  .glow { box-shadow: 0 0 60px rgba(245,158,11,0.15); }
  .ring-amber { box-shadow: 0 0 0 2px rgba(245, 158, 11, .35); }
</style>
</head>
<body class="bg-zinc-950 text-zinc-100">

<script id="runs" type="application/json">__RUNS_JSON__</script>

<div x-data="{
    runs: JSON.parse(document.getElementById('runs').textContent),
    active: 0
  }" class="max-w-6xl mx-auto p-6">

  <header class="text-center pt-10 pb-8">
    <div class="text-xs uppercase tracking-widest text-amber-400 mb-3">auto-video-cut · v0.5 — multi-source mashup</div>
    <h1 class="text-4xl md:text-5xl font-bold tracking-tight leading-tight">
      Throw a pile of videos in.<br/>
      <span class="text-amber-400">Get one coherent edit out.</span>
    </h1>
    <p class="mt-5 text-base md:text-lg text-zinc-300 max-w-2xl mx-auto leading-relaxed">
      Gemini reads all the transcripts together. Finds the theme connecting them.
      Picks pieces from every source. Weaves them into one supercut where each speaker carries part of the argument.
    </p>
    <code class="mt-5 inline-block px-4 py-2 bg-zinc-800/80 rounded-lg text-xs text-amber-300 font-mono">
      avc multi-remix --inputs vid1 vid2 vid3 --out mashup.mp4 [--theme &quot;...&quot;]
    </code>
  </header>

  <nav class="flex flex-wrap gap-2 justify-center mb-10 border-b border-zinc-800 pb-6">
    <template x-for="(r, i) in runs" :key="r.id">
      <button
        @click="active = i"
        :class="active === i ? 'bg-amber-500 text-zinc-950 font-semibold' : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'"
        class="px-4 py-2 rounded-full text-sm"
        x-text="r.label">
      </button>
    </template>
  </nav>

  <template x-for="(r, i) in runs" :key="r.id">
    <section x-show="active === i" class="grid md:grid-cols-3 gap-6 mb-12">
      <div class="space-y-4">
        <div class="text-xs uppercase tracking-widest text-zinc-500 mb-2">3 inputs</div>
        <template x-for="src in r.sources" :key="src.video_id">
          <div class="bg-zinc-900/40 rounded-lg p-3">
            <div class="text-xs text-amber-400 mb-2 font-medium" x-text="src.label"></div>
            <video :src="src.preview_url" controls preload="metadata" class="vid-horiz"></video>
            <div class="mt-2 text-xs text-zinc-500 font-mono">
              <span x-text="'kept: ' + Math.round(src.kept_seconds) + 's'"></span>
            </div>
          </div>
        </template>
      </div>

      <div class="md:col-span-2 space-y-5">
        <div class="bg-amber-500/10 border-l-2 border-amber-500 px-5 py-4 rounded-r">
          <div class="text-xs uppercase tracking-widest text-amber-400 mb-2">
            <span x-show="r.user_theme">User-given theme</span>
            <span x-show="!r.user_theme">Theme discovered by Gemini</span>
          </div>
          <p class="text-zinc-100 text-base leading-relaxed font-medium" x-text="r.discovered_theme"></p>
          <div class="mt-3 text-sm text-zinc-300 leading-relaxed" x-text="r.rationale"></div>
        </div>

        <div>
          <div class="text-xs uppercase tracking-widest text-amber-400 mb-2">Cross-source supercut output</div>
          <div class="text-sm text-zinc-400 mb-3 font-mono">
            <span x-text="Math.round(r.out_dur) + 's'"></span>
            · <span x-text="r.n_clips + ' clips'"></span>
            · <span x-text="Object.keys(r.per_source_seconds).length + ' sources'"></span>
          </div>
        </div>
        <div class="flex justify-center">
          <video :src="r.output_url" controls preload="metadata" class="vid-vert glow ring-amber"></video>
        </div>
      </div>
    </section>
  </template>

  <section class="mt-16 max-w-3xl mx-auto pb-12 border-t border-zinc-800 pt-10">
    <h2 class="text-2xl font-bold mb-5 text-zinc-100">How it works</h2>
    <ol class="space-y-4 text-zinc-300 leading-relaxed">
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">1</span>
        <div><b class="text-zinc-100">Transcribe each source</b> — faster-whisper, multi-language. Cached if you've already run a single-source pipeline on it.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">2</span>
        <div><b class="text-zinc-100">Single Gemini call across ALL transcripts</b> — each tagged with a video_id. Asks Gemini to either (a) discover a unifying theme or (b) honor a user-given theme, then return ordered <code class="font-mono text-amber-300 text-sm">{video_id, indices}</code> tuples.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">3</span>
        <div><b class="text-zinc-100">Cut from each source</b> — adjacent indices from the same source merge into one clip; switching sources starts a new clip.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">4</span>
        <div><b class="text-zinc-100">Reframe each clip BEFORE concat</b> — each becomes 9:16 with face-tracking. Identical dimensions/codec params means concat works clean across speakers.</div>
      </li>
      <li class="flex gap-4">
        <span class="text-amber-400 font-mono w-6 flex-shrink-0">5</span>
        <div><b class="text-zinc-100">Single concat</b> — output is one continuous video that flows from one speaker to another in narrative order.</div>
      </li>
    </ol>

    <h3 class="text-xl font-semibold mb-4 mt-8 text-zinc-100">CLI</h3>
    <pre class="bg-zinc-900 p-4 rounded text-amber-300 text-sm overflow-x-auto"><code># Auto-discover theme across N sources
avc multi-remix \
  --inputs vid1.mp4 vid2.mp4 vid3.mp4 \
  --label "Speaker A" "Speaker B" "Speaker C" \
  --out mashup.mp4 --target-s 80 --captions

# Or honor a user-given theme
avc multi-remix --inputs vid1.mp4 vid2.mp4 vid3.mp4 \
  --theme "the ways our intuitions about the future fail us" \
  --out themed.mp4 --captions
</code></pre>
  </section>

  <footer class="text-center text-xs text-zinc-500 pb-12 border-t border-zinc-800 pt-6">
    <a href="https://github.com/when2buy/auto-video-cut" class="underline hover:text-amber-400">github.com/when2buy/auto-video-cut</a>
    · v0.5 · MIT
  </footer>
</div>
</body>
</html>
"""


def main() -> None:
    runs = collect_runs()
    if not runs:
        print("⚠️  no v0.5 outputs found in reports/assets/v0.5/")
        return
    runs_json = json.dumps(runs, ensure_ascii=False).replace("</script", "<\\/script")
    html = HTML.replace("__RUNS_JSON__", runs_json)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"✅ {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {len(runs)} runs)")


if __name__ == "__main__":
    main()
