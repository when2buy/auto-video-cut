#!/usr/bin/env bash
# Fetch all demo fixtures. Failures are non-fatal — log and continue.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "=== fetching all demo fixtures ==="
for f in "$HERE"/fetch_*.sh; do
    name=$(basename "$f")
    case "$name" in
        fetch_all.sh|fetch_ted.sh|fetch_bilibili.sh) continue ;;  # skip orchestrator + per-platform helpers
    esac
    echo
    echo ">>> $name"
    if bash "$f"; then
        echo "    ✓ ok"
    else
        echo "    ✗ FAILED — continuing"
    fi
done
echo
echo "=== final inventory ==="
for v in "$HERE/data"/*.mp4; do
    [[ -f "$v" ]] || continue
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v" 2>/dev/null | head -1)
    sz=$(du -h "$v" | cut -f1)
    printf "  %-32s  %6.1fs  %s\n" "$(basename $v)" "${dur:-0}" "$sz"
done
