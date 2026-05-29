"""ASR with faster-whisper. Returns word-level timestamps for Chinese/English mixed audio."""

from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class WordSegment:
    start: float
    end: float
    text: str


@dataclass
class SentenceSegment:
    start: float
    end: float
    text: str
    word_count: int


@dataclass
class Transcript:
    language: str
    duration: float
    sentences: list[SentenceSegment]

    def to_json(self) -> str:
        return json.dumps(
            {
                "language": self.language,
                "duration": self.duration,
                "sentences": [asdict(s) for s in self.sentences],
            },
            ensure_ascii=False,
            indent=2,
        )


def transcribe(
    video_path: Path,
    *,
    model_size: str = "large-v3",
    language: str | None = None,
    verbose: bool = False,
) -> Transcript:
    """Extract audio + run faster-whisper. Returns sentence-level segments.

    H100: ~30-40x realtime on large-v3.
    """
    from faster_whisper import WhisperModel

    # Extract 16k mono wav (whisper's native rate)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav = Path(tmp.name)
    try:
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(video_path),
            "-vn", "-ar", "16000", "-ac", "1",
            "-c:a", "pcm_s16le", str(wav),
        ]
        subprocess.run(cmd, check=True)

        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        segments, info = model.transcribe(
            str(wav),
            language=language,  # None = auto-detect
            beam_size=5,
            vad_filter=True,    # Voice activity detection — drops silence
            word_timestamps=False,  # we use segment-level for sentences
            condition_on_previous_text=False,  # avoids drift on long audio
        )

        sentences: list[SentenceSegment] = []
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            sentences.append(SentenceSegment(
                start=float(seg.start),
                end=float(seg.end),
                text=text,
                word_count=len(text),
            ))
            if verbose:
                print(f"  [{seg.start:6.1f}-{seg.end:6.1f}] {text[:80]}")

        return Transcript(
            language=info.language,
            duration=info.duration,
            sentences=sentences,
        )
    finally:
        wav.unlink(missing_ok=True)
