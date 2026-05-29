"""Acceptance tests for the full pipeline orchestrator.

Spec: docs/plans/2026-05-29-v0.3-overnight-demo.md (Phase 4)
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


def test_pipeline_smoke_no_extras(tmp_path: Path) -> None:
    """ASR + pick + cut only (no reframe, no captions). Smoke level."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    fixture = ROOT / "eval" / "data" / "ted-cn-90s.mp4"
    if not fixture.exists():
        pytest.skip("ted fixture missing")

    from avc.pipeline import run

    out = tmp_path / "result.mp4"
    res = run(
        input_video=fixture,
        output_video=out,
        target_ratio=0.5,
        reframe=False,
        captions=False,
        verbose=True,
    )
    assert out.exists()
    assert res["stages"] == ["asr", "llm_pick", "cut"]
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(out)],
        check=True, capture_output=True, text=True,
    ).stdout)
    assert float(info["format"]["duration"]) > 5.0
