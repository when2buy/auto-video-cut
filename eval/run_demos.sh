#!/usr/bin/env bash
# Run the full pipeline on all fixtures (D-variant: cut + reframe + captions)
# Skips ted-cn-90s (sample) and uses the full fixtures only.
set -o pipefail
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
mkdir -p "$HERE/runs"

echo "=== run_demos.sh started at $(date -Iseconds) ==="

for src in "$HERE/data/"*.mp4; do
    name=$(basename "$src" .mp4)
    case "$name" in
        ted-cn-90s) continue ;;          # sample only, skip
    esac
    out="$HERE/runs/$name-D-final.mp4"
    log="$HERE/runs/$name-D.log"
    if [[ -f "$out" ]] && [[ "$out" -nt "$src" ]]; then
        echo ">>> $name: cached, skipping"
        continue
    fi
    echo ""
    echo ">>> $name"
    # Pick caption-style based on language: zh fixtures get opus-cn
    style="opus"
    case "$name" in
        marketing-bili|ted-cn|he-tongxue-5g|bi-dao-science) style="opus-cn" ;;
    esac
    if (cd "$ROOT" && python3 -m avc.cli pipeline "$src" \
        --out "$out" \
        --target-ratio 0.30 \
        --reframe --captions --caption-style "$style" \
        -v 2>&1 | tee "$log") ; then
        echo "    ✓ ok"
    else
        echo "    ✗ FAILED, see $log"
    fi
done

echo ""
echo "=== final outputs ==="
for v in "$HERE/runs/"*-D-final.mp4; do
    [[ -f "$v" ]] || continue
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v" 2>/dev/null | head -1)
    sz=$(du -h "$v" | cut -f1)
    printf "  %-36s  %6.1fs  %s\n" "$(basename $v)" "${dur:-0}" "$sz"
done

echo "=== run_demos.sh finished at $(date -Iseconds) ==="
