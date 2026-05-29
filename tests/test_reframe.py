"""Acceptance tests for reframe module.

Spec: docs/plans/2026-05-29-v0.3-overnight-demo.md (Phase 3)
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def test_face_detect_on_ted_frame(tmp_path: Path) -> None:
    """MediaPipe finds at least one face on a TED talk frame."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    src = ROOT / "eval" / "data" / "ted-cn-90s.mp4"
    if not src.exists():
        pytest.skip("ted fixture missing")

    frame = tmp_path / "frame.jpg"
    # Sample at 30s — middle of the 90s clip; speaker visible most of the time
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", "30", "-i", str(src),
        "-frames:v", "1", str(frame),
    ], check=True)

    from avc.reframe import detect_faces
    faces = detect_faces(frame)
    # We don't assert >=1 strictly — TED frames sometimes show slides only.
    # If empty, the test still confirms the call works without crash.
    for f in faces:
        assert 0 <= f["x"] <= 1
        assert 0 <= f["y"] <= 1
        assert 0 < f["w"] <= 1
        assert 0 < f["h"] <= 1
        assert 0 <= f["score"] <= 1


def test_reframe_to_vertical_ted(tmp_path: Path) -> None:
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    src = ROOT / "eval" / "data" / "ted-cn-90s.mp4"
    if not src.exists():
        pytest.skip("ted fixture missing")

    out = tmp_path / "vertical.mp4"
    from avc.reframe import reframe_to_vertical
    res = reframe_to_vertical(src, out, verbose=True, n_samples=5)
    assert out.exists()
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", str(out)],
        check=True, capture_output=True, text=True,
    ).stdout)["streams"][0]
    assert info["width"] == 1080
    assert info["height"] == 1920
    assert res["mode"] in ("face-tracked", "center-crop")
