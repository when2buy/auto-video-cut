"""ASR-driven cut: Whisper transcribe -> Gemini pick -> ffmpeg concat."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from .asr import Transcript, transcribe
from .llm_pick import keeps_to_segments, pick_sentences
from .silence import extract_and_concat, ffprobe_duration


class AsrCutStats(TypedDict):
    in_dur: float
    out_dur: float
    ratio: float
    n_sentences: int
    n_kept: int
    n_segments: int
    transcript_path: str


def asr_cut(
    *,
    input_path: Path,
    output_path: Path,
    target_ratio: float = 0.30,
    style_prompt: str = "保留干货、punchline、关键信息；剪掉铺垫、重复、套话",
    model: str = "gemini-2.5-pro",
    transcript_out: Path | None = None,
    verbose: bool = False,
) -> AsrCutStats:
    """Full v0.2 pipeline."""
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"[asr_cut] 1/3 transcribing {input_path.name}…")
    transcript = transcribe(input_path, verbose=verbose)
    if verbose:
        print(f"[asr_cut]    -> {len(transcript.sentences)} sentences, lang={transcript.language}")

    if transcript_out is None:
        transcript_out = output_path.with_suffix(".transcript.json")
    transcript_out.write_text(transcript.to_json())

    if verbose:
        print(f"[asr_cut] 2/3 picking sentences via {model} (target ratio={target_ratio})…")
    keep = pick_sentences(
        transcript,
        target_ratio=target_ratio,
        style_prompt=style_prompt,
        model=model,
        verbose=verbose,
    )

    segments = keeps_to_segments(transcript, keep)
    if verbose:
        print(f"[asr_cut] 3/3 ffmpeg cut+concat ({len(segments)} segments)…")
    if not segments:
        raise RuntimeError("LLM kept zero sentences")
    extract_and_concat(input_path, output_path, segments, verbose=verbose)

    in_dur = ffprobe_duration(input_path)
    out_dur = ffprobe_duration(output_path)
    return AsrCutStats(
        in_dur=in_dur,
        out_dur=out_dur,
        ratio=out_dur / in_dur,
        n_sentences=len(transcript.sentences),
        n_kept=len(keep),
        n_segments=len(segments),
        transcript_path=str(transcript_out),
    )
