#!/usr/bin/env bash
# Fetch Julian Treasure — How to speak so that people want to listen (TED)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/data"
cd "$HERE/data"
yt-dlp --quiet --no-warnings -f "best[height<=720]/best" \
    -o "julian-treasure-speak.%(ext)s" \
    "https://www.ted.com/talks/julian_treasure_how_to_speak_so_that_people_want_to_listen"
echo "✓ julian-treasure-speak.mp4"
