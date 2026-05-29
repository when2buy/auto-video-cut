#!/usr/bin/env bash
# Publish all reports together to keep historical URLs alive on Cloudflare Pages.
# Each `report publish` overwrites prod with single file; this batches them.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TMP=$(mktemp -d)
cp "$ROOT/reports/"*.html "$TMP/"
echo "Publishing $(ls "$TMP" | wc -l) reports..."
source ~/.report-skill/tokens.env
wrangler pages deploy "$TMP" --project-name report-skill-demos --branch main --commit-dirty=true
echo "Verify URLs:"
for f in "$TMP"/*.html; do
    slug=$(basename "$f" .html)
    echo "  https://reports.steveouyang.com/$slug"
done
