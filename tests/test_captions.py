"""Acceptance tests for captions module.

Spec: docs/plans/2026-05-29-v0.3-overnight-demo.md (Phase 2)
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


def test_build_caption_assets_minimal(tmp_path: Path) -> None:
    from avc.asr import SentenceSegment, Transcript, WordSegment
    from avc.captions import build_caption_assets

    transcript = Transcript(
        language="en",
        duration=3.0,
        sentences=[
            SentenceSegment(
                start=0.0, end=1.5, text="hello world", word_count=2,
                words=[
                    WordSegment(0.0, 0.7, "hello"),
                    WordSegment(0.8, 1.5, "world"),
                ],
            ),
            SentenceSegment(
                start=1.7, end=3.0, text="goodbye now", word_count=2,
                words=[
                    WordSegment(1.7, 2.3, "goodbye"),
                    WordSegment(2.4, 3.0, "now"),
                ],
            ),
        ],
    )
    assets = build_caption_assets(transcript, tmp_path, style="opus", play_w=320, play_h=240, chunk_size=2)
    # 4 words → 2 chunks of 2 → 4 caption assets (one per word w/ active highlight)
    assert len(assets) == 4
    for a in assets:
        assert Path(a.png_path).exists()
        assert a.end > a.start


def test_build_caption_assets_no_words_raises(tmp_path: Path) -> None:
    from avc.asr import SentenceSegment, Transcript
    from avc.captions import build_caption_assets

    transcript = Transcript(
        language="en", duration=1.0,
        sentences=[SentenceSegment(start=0.0, end=1.0, text="hi", word_count=1, words=None)],
    )
    with pytest.raises(ValueError):
        build_caption_assets(transcript, tmp_path)


def test_caption_video_on_short_clip(tmp_path: Path) -> None:
    """End-to-end on a real fixture (skipped if not available)."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not on PATH")
    fixture = ROOT / "eval" / "data" / "ted-cn-90s.mp4"
    if not fixture.exists():
        pytest.skip(f"fixture missing: {fixture}")

    from avc.asr import transcribe
    from avc.captions import caption_video

    # 3s sample
    clip = tmp_path / "clip.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", "30", "-t", "3", "-i", str(fixture),
        "-c", "copy", str(clip),
    ], check=True)

    t = transcribe(clip, word_timestamps=True)
    if not any(s.words for s in t.sentences):
        pytest.skip("transcript came back without word timestamps (whisper edge case)")

    out = tmp_path / "burned.mp4"
    caption_video(clip, t, out, style="opus", verbose=True)

    assert out.exists() and out.stat().st_size > 0
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(out)],
        check=True, capture_output=True, text=True,
    ).stdout)
    assert abs(float(info["format"]["duration"]) - 3.0) < 0.5
