#!/usr/bin/env bash
# Fetch Sam Harris — Can we build AI without losing control? (TED, podcast-style)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HERE/data"
cd "$HERE/data"
yt-dlp --quiet --no-warnings -f "best[height<=720]/best" \
    -o "sam-harris-ai.%(ext)s" \
    "https://www.ted.com/talks/sam_harris_can_we_build_ai_without_losing_control_over_it"
echo "✓ sam-harris-ai.mp4"
