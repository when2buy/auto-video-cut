"""Silence-based cut, v0.1.

Originally planned to wrap auto-editor (see decision in docs/design/v0.1-silence-cut.md).
Pivoted to pure ffmpeg `silencedetect` + `concat` because the auto-editor binary
requires GLIBC_2.38 which isn't on the target pod. ffmpeg-only path is more portable
and still under 200 lines.

Pipeline:
1. Run `ffmpeg -af silencedetect` to get list of (silence_start, silence_end) timestamps.
2. Compute inverse: list of (keep_start, keep_end) speech segments, padded by `margin_s`.
3. For each segment, extract via `-ss / -t` (frame-accurate with re-encode).
4. Concat the segments via ffmpeg concat demuxer.

Logged in docs/learnings.md.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TypedDict


class CutStats(TypedDict):
    in_dur: float
    out_dur: float
    ratio: float
    n_segments: int


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not on PATH")
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe not on PATH")


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def detect_silence(
    input_path: Path,
    threshold_db: float = -30.0,
    min_silence_s: float = 0.4,
) -> list[tuple[float, float]]:
    """Return list of (silence_start, silence_end) seconds via ffmpeg silencedetect.

    Uses ffmpeg's silencedetect filter; output is parsed from stderr.
    """
    _check_ffmpeg()
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats",
        "-i", str(input_path),
        "-vn",  # drop video; some ffmpeg builds lack wrapped_avframe encoder for null muxer
        "-af", f"silencedetect=noise={threshold_db}dB:d={min_silence_s}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # silencedetect logs to stderr regardless of exit
    log = result.stderr

    silences: list[tuple[float, float]] = []
    cur_start: float | None = None
    for line in log.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            cur_start = float(m.group(1))
            continue
        m = re.search(r"silence_end:\s*(-?[\d.]+)", line)
        if m and cur_start is not None:
            silences.append((max(0.0, cur_start), float(m.group(1))))
            cur_start = None

    return silences


def silences_to_keeps(
    total_duration: float,
    silences: list[tuple[float, float]],
    margin_s: float = 0.1,
) -> list[tuple[float, float]]:
    """Invert silence list to keep-list (speech segments), padded by margin_s.

    Adjacent / overlapping segments are merged.
    """
    keeps: list[tuple[float, float]] = []
    cursor = 0.0
    for s_start, s_end in silences:
        keep_end = max(0.0, s_start + margin_s)
        if keep_end > cursor:
            keeps.append((cursor, keep_end))
        cursor = max(cursor, s_end - margin_s)
    if cursor < total_duration:
        keeps.append((cursor, total_duration))

    # merge overlaps
    merged: list[tuple[float, float]] = []
    for k in keeps:
        if merged and k[0] <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], k[1]))
        else:
            merged.append(k)
    # filter zero-length
    return [(a, b) for a, b in merged if b - a > 0.05]


def _extract_and_concat(
    input_path: Path,
    output_path: Path,
    keeps: list[tuple[float, float]],
    verbose: bool = False,
) -> None:
    """Cut N segments and concat into output_path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        seg_files: list[Path] = []
        for i, (start, end) in enumerate(keeps):
            seg = tmp / f"seg-{i:04d}.mp4"
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", f"{start:.3f}",
                "-to", f"{end:.3f}",
                "-i", str(input_path),
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                str(seg),
            ]
            if verbose:
                print(f"[seg {i}] {start:.2f}-{end:.2f}s")
            subprocess.run(cmd, check=True, capture_output=not verbose)
            seg_files.append(seg)

        # concat list file
        list_file = tmp / "concat.txt"
        list_file.write_text(
            "".join(f"file '{p.as_posix()}'\n" for p in seg_files)
        )
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=not verbose)


def silence_cut(
    *,
    input_path: Path,
    output_path: Path,
    silence_threshold_db: float = -30.0,
    min_silence_s: float = 0.4,
    margin_s: float = 0.1,
    verbose: bool = False,
) -> CutStats:
    """Detect silence in input, cut to speech-only, write to output_path."""
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    _check_ffmpeg()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    in_dur = ffprobe_duration(input_path)
    silences = detect_silence(input_path, threshold_db=silence_threshold_db, min_silence_s=min_silence_s)
    if verbose:
        print(f"[silence_cut] detected {len(silences)} silence regions")
    keeps = silences_to_keeps(in_dur, silences, margin_s=margin_s)
    if verbose:
        print(f"[silence_cut] keeping {len(keeps)} speech segments")
    if not keeps:
        raise RuntimeError("no speech detected — input may be entirely silent")

    _extract_and_concat(input_path, output_path, keeps, verbose=verbose)

    if not output_path.exists():
        raise RuntimeError(f"ffmpeg returned 0 but no output at {output_path}")

    out_dur = ffprobe_duration(output_path)
    return CutStats(
        in_dur=in_dur,
        out_dur=out_dur,
        ratio=out_dur / in_dur,
        n_segments=len(keeps),
    )
