#!/usr/bin/env bash
# Fetch Maz Jobrani — Saudi/Indian/Iranian walk into a Qatari bar (TED stand-up)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/data"
cd "$HERE/data"
yt-dlp --quiet --no-warnings -f "best[height<=720]/best" \
    -o "maz-jobrani-standup.%(ext)s" \
    "https://www.ted.com/talks/maz_jobrani_a_saudi_an_indian_and_an_iranian_walk_into_a_qatari_bar"
echo "✓ maz-jobrani-standup.mp4"
