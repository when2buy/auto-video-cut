#!/usr/bin/env bash
# Fetch Tim Urban — Inside the mind of a master procrastinator (TED)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/data"
cd "$HERE/data"
yt-dlp --quiet --no-warnings -f "best[height<=720]/best" \
    -o "tim-urban-procrast.%(ext)s" \
    "https://www.ted.com/talks/tim_urban_inside_the_mind_of_a_master_procrastinator"
echo "✓ tim-urban-procrast.mp4"
