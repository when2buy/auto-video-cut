#!/usr/bin/env bash
# Fetch the TED Chinese-subbed talk used as v0.1 baseline.
# License: CC BY-NC-ND 4.0 (TED). Eval only, not for redistribution.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/data"
cd "$HERE/data"
yt-dlp --quiet --no-warnings -f "best[height<=720]/best" \
    -o "ted-cn.%(ext)s" \
    "https://www.ted.com/talks/lera_boroditsky_how_language_shapes_the_way_we_think?language=zh-cn"
ffmpeg -y -loglevel error -ss 60 -t 90 -i ted-cn.mp4 -c copy ted-cn-90s.mp4
echo "✅ fixtures ready in $HERE/data/"
