"""Acceptance tests for v0.1 silence cut.

Spec: docs/design/v0.1-silence-cut.md
"""

from __future__ import annotations

import sys
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "tests" / "fixtures"


def _ffprobe_streams(path: Path) -> list[str]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return [s["codec_type"] for s in json.loads(out.stdout).get("streams", [])]


def _ffprobe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory) -> Path:
    """Build a 30-second test video: 10s tone, 10s silence, 10s tone.

    auto-editor should cut the middle 10s and produce ~20s of output.
    """
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")

    out = tmp_path_factory.mktemp("fixtures") / "sample-30s.mp4"

    # Build via concat: tone | silence | tone, each 10s, with synced color frames
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        # input 0: 10s of A4 tone with red video
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-f", "lavfi", "-i", "color=red:size=320x240:rate=10:duration=10",
        # input 2: 10s of silence with gray video
        "-f", "lavfi", "-i", "anullsrc=duration=10",
        "-f", "lavfi", "-i", "color=gray:size=320x240:rate=10:duration=10",
        # input 4: 10s of A5 tone with blue video
        "-f", "lavfi", "-i", "sine=frequency=880:duration=10",
        "-f", "lavfi", "-i", "color=blue:size=320x240:rate=10:duration=10",
        "-filter_complex",
        "[1:v][0:a][3:v][2:a][5:v][4:a]concat=n=3:v=1:a=1[v][a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def test_fixture_built(sample_video: Path) -> None:
    assert sample_video.exists()
    dur = _ffprobe_duration(sample_video)
    assert 29 < dur < 31, f"fixture duration off: {dur}"


def test_silence_cut_runs(sample_video: Path, tmp_path: Path) -> None:
    """Acceptance #1: avc cut exits 0 on a real video."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")

    out = tmp_path / "out.mp4"
    result = subprocess.run(
        [
            sys.executable, "-m", "avc.cli", "cut",
            str(sample_video),
            "--out", str(out),
        ],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"avc cut failed:\n{result.stdout}\n{result.stderr}"
    assert out.exists(), "output file not created"


def test_output_is_valid_video(sample_video: Path, tmp_path: Path) -> None:
    """Acceptance #2: output is a valid mp4 ffprobe can parse."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    out = tmp_path / "out.mp4"
    subprocess.run(
        [sys.executable, "-m", "avc.cli", "cut", str(sample_video), "--out", str(out)],
        check=True, capture_output=True,
    )
    dur = _ffprobe_duration(out)
    assert dur > 0


def test_output_is_shorter(sample_video: Path, tmp_path: Path) -> None:
    """Acceptance #3: output is at least 25% shorter than input."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    out = tmp_path / "out.mp4"
    subprocess.run(
        [sys.executable, "-m", "avc.cli", "cut", str(sample_video), "--out", str(out)],
        check=True, capture_output=True,
    )
    in_dur = _ffprobe_duration(sample_video)
    out_dur = _ffprobe_duration(out)
    assert out_dur <= in_dur * 0.75, (
        f"output not trimmed enough: {in_dur:.1f}s → {out_dur:.1f}s "
        f"(ratio {out_dur/in_dur:.2%})"
    )


def test_output_not_empty(sample_video: Path, tmp_path: Path) -> None:
    """Acceptance #4: output is at least 10% of input (didn't kill everything)."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    out = tmp_path / "out.mp4"
    subprocess.run(
        [sys.executable, "-m", "avc.cli", "cut", str(sample_video), "--out", str(out)],
        check=True, capture_output=True,
    )
    in_dur = _ffprobe_duration(sample_video)
    out_dur = _ffprobe_duration(out)
    assert out_dur >= in_dur * 0.10, "output suspiciously short"


def test_output_has_both_streams(sample_video: Path, tmp_path: Path) -> None:
    """Acceptance #5: output has both video and audio streams."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    out = tmp_path / "out.mp4"
    subprocess.run(
        [sys.executable, "-m", "avc.cli", "cut", str(sample_video), "--out", str(out)],
        check=True, capture_output=True,
    )
    streams = _ffprobe_streams(out)
    assert "video" in streams, f"output missing video stream: {streams}"
    assert "audio" in streams, f"output missing audio stream: {streams}"


def test_missing_input_errors_clean(tmp_path: Path) -> None:
    """Bad input → exit non-zero with sensible message, not traceback."""
    out = tmp_path / "out.mp4"
    result = subprocess.run(
        [sys.executable, "-m", "avc.cli", "cut", "/nonexistent.mp4", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()
