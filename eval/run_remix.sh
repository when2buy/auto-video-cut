#!/usr/bin/env bash
# Run remix on 2 fixtures x 3 templates = 6 outputs.
# Reuse cached transcripts from D-final artifacts to save ~3 min/fixture.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
mkdir -p "$HERE/remix"

FIXTURES=("tim-urban-procrast" "maz-jobrani-standup")
TEMPLATES=("viral_hook" "top3" "thesis")

for fix in "${FIXTURES[@]}"; do
    src="$HERE/data/${fix}.mp4"
    transcript="$HERE/runs/${fix}-D-final.artifacts/transcript.json"
    [[ -f "$src" ]] || { echo "skip $fix: no source"; continue; }
    [[ -f "$transcript" ]] || { echo "skip $fix: no cached transcript"; continue; }

    for tpl in "${TEMPLATES[@]}"; do
        out="$HERE/remix/${fix}-${tpl}.mp4"
        log="$HERE/remix/${fix}-${tpl}.log"
        if [[ -f "$out" ]] && [[ "$out" -nt "$transcript" ]]; then
            echo ">>> $fix / $tpl: cached, skipping"
            continue
        fi
        echo ""
        echo ">>> $fix / $tpl"
        # Caption style: opus for both these (English)
        if (cd "$ROOT" && python3 -m avc.cli remix "$src" \
            --out "$out" \
            --template "$tpl" \
            --cached-transcript "$transcript" \
            --reframe --captions --caption-style opus \
            -v 2>&1 | tee "$log") ; then
            echo "    ✓ ok"
        else
            echo "    ✗ FAILED"
        fi
    done
done

echo ""
echo "=== final remix outputs ==="
for v in "$HERE/remix/"*.mp4; do
    [[ -f "$v" ]] || continue
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v" 2>/dev/null | head -1)
    sz=$(du -h "$v" | cut -f1)
    printf "  %-50s  %5.1fs  %s\n" "$(basename $v)" "${dur:-0}" "$sz"
done
