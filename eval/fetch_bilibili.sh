#!/usr/bin/env bash
# Fetch a Bilibili video using bilibili-api-python (handles wbi signing).
# yt-dlp returns HTTP 412 on this pod (anti-bot); the python lib + iPhone UA works.
# Usage: bash eval/fetch_bilibili.sh <BVID> [output-slug]
# Example: bash eval/fetch_bilibili.sh BV1XJDKBhEyE marketing-bili
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <BVID> [slug]"
    echo "  e.g. $0 BV1XJDKBhEyE marketing-bili"
    exit 1
fi

BVID="$1"
SLUG="${2:-${BVID,,}}"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/data"
mkdir -p "$OUT"

pip show bilibili-api-python >/dev/null 2>&1 || pip install --quiet bilibili-api-python

python3 - "$BVID" "$OUT/$SLUG" <<'PY'
import asyncio, json, sys, requests
from pathlib import Path
from bilibili_api import video as bv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

bvid = sys.argv[1]
out_base = Path(sys.argv[2])
out_dir = out_base.parent
out_dir.mkdir(parents=True, exist_ok=True)

async def main():
    v = bv.Video(bvid=bvid)
    info = await v.get_info()
    print(f"title: {info.get('title')} ({info.get('duration')}s, {info.get('stat',{}).get('view',0)} views)")
    
    durl = await v.get_download_url(0)
    dash = durl["dash"]
    best_v = sorted(dash["video"], key=lambda x: -x.get("bandwidth", 0))[0]
    best_a = sorted(dash["audio"], key=lambda x: -x.get("bandwidth", 0))[0]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Referer": f"https://www.bilibili.com/video/{bvid}",
    }
    sess = requests.Session()
    sess.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1.0)))
    
    for tag, url in [("video.m4s", best_v.get("baseUrl") or best_v.get("base_url")),
                     ("audio.m4s", best_a.get("baseUrl") or best_a.get("base_url"))]:
        path = out_base.with_suffix(f".{tag}")
        print(f"  fetching {tag}...")
        with sess.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=256 * 1024):
                    f.write(chunk)
        print(f"    -> {path.stat().st_size/1024/1024:.1f} MB")
    
    # mux
    import subprocess
    mp4 = out_base.with_suffix(".mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(out_base.with_suffix(".video.m4s")),
        "-i", str(out_base.with_suffix(".audio.m4s")),
        "-c", "copy", str(mp4),
    ], check=True)
    out_base.with_suffix(".video.m4s").unlink()
    out_base.with_suffix(".audio.m4s").unlink()
    
    meta = {
        "source": f"https://www.bilibili.com/video/{bvid}",
        "bvid": bvid,
        "title": info.get("title"),
        "author": info.get("owner", {}).get("name"),
        "duration_s": info.get("duration"),
        "view_count": info.get("stat", {}).get("view"),
        "license": "Bilibili UGC — eval-only fair use, not redistributed",
    }
    out_base.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"✅ {mp4} ({mp4.stat().st_size/1024/1024:.1f} MB)")
    print(f"   metadata: {out_base.with_suffix('.json')}")

asyncio.run(main())
PY
