#!/usr/bin/env bash
# Publish all reports together to keep historical URLs alive on Cloudflare Pages.
# Each `report publish <single-file>` overwrites prod with only that file; this
# batches them in a single wrangler deploy.
#
# Also copies reports/assets/ alongside, so reports that reference relative
# paths (e.g. v0.3 demo) resolve correctly.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TMP=$(mktemp -d)
cp "$ROOT/reports/"*.html "$TMP/"
if [[ -d "$ROOT/reports/assets" ]]; then
    cp -r "$ROOT/reports/assets" "$TMP/assets"
fi
echo "Publishing $(ls "$TMP" | grep -E '\.html$' | wc -l) reports + $(find "$TMP/assets" -type f 2>/dev/null | wc -l) assets..."
echo "Total bundle size: $(du -sh "$TMP" | cut -f1)"

# Token comes from ~/.report-skill/tokens.env (CLOUDFLARE_API_TOKEN)
set -a
# shellcheck source=/dev/null
source ~/.report-skill/tokens.env
set +a

wrangler pages deploy "$TMP" --project-name report-skill-demos --branch main --commit-dirty=true 2>&1 | tail -10

echo
echo "Verify URLs:"
for f in "$TMP"/*.html; do
    slug=$(basename "$f" .html)
    echo "  https://reports.steveouyang.com/$slug"
done
