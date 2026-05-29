"""Full remix pipeline: transcribe → template-driven LLM reorder → cut → optional reframe + captions."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import TypedDict

from .asr import transcribe
from .captions import caption_video
from .reframe import reframe_to_vertical
from .remix import indices_to_ordered_segments, remix_with_template
from .silence import extract_and_concat, ffprobe_duration


class RemixCutResult(TypedDict):
    template: str
    rationale: str
    in_dur: float
    out_dur: float
    n_sentences: int
    n_kept: int
    n_segments: int
    artifacts: dict[str, str]


def remix_cut(
    *,
    input_video: Path,
    output_video: Path,
    template: str,
    model: str = "gemini-2.5-pro",
    reframe: bool = False,
    captions: bool = False,
    caption_style: str = "opus",
    target_w: int = 1080,
    target_h: int = 1920,
    cached_transcript: Path | None = None,
    artifacts_dir: Path | None = None,
    verbose: bool = False,
) -> RemixCutResult:
    """Remix a video according to the named template.

    ``cached_transcript`` (Path to JSON) skips re-transcribing — useful when
    running multiple templates against the same source.
    """
    if not input_video.exists():
        raise FileNotFoundError(input_video)
    output_video.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir = artifacts_dir or output_video.parent / f"{output_video.stem}.artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}

    # 1. ASR (or load cached)
    if cached_transcript and cached_transcript.exists():
        if verbose:
            print(f"[remix_cut] 1/5 transcript loaded from {cached_transcript}")
        from .asr import SentenceSegment, Transcript, WordSegment
        d = json.loads(cached_transcript.read_text())
        sentences = []
        for s in d["sentences"]:
            words = None
            if s.get("words"):
                words = [WordSegment(**w) for w in s["words"]]
            sentences.append(SentenceSegment(
                start=s["start"], end=s["end"], text=s["text"],
                word_count=s["word_count"], words=words,
            ))
        transcript = Transcript(language=d["language"], duration=d["duration"], sentences=sentences)
    else:
        if verbose:
            print(f"[remix_cut] 1/5 transcribing (word_timestamps={captions})")
        transcript = transcribe(input_video, word_timestamps=captions, verbose=verbose)
        out_t = artifacts_dir / "transcript.json"
        out_t.write_text(transcript.to_json())
        artifacts["transcript"] = str(out_t)

    # 2. Template remix via LLM
    if verbose:
        print(f"[remix_cut] 2/5 template '{template}' via {model}")
    result = remix_with_template(transcript, template, model=model, verbose=verbose)
    artifacts["keep_indices"] = json.dumps(result.keep_indices)
    artifacts["rationale"] = result.rationale

    # 3. Cut according to OUTPUT order (non-chronological allowed)
    segments = indices_to_ordered_segments(transcript, result.keep_indices)
    if not segments:
        raise RuntimeError("template returned zero segments after filtering")
    if verbose:
        print(f"[remix_cut] 3/5 cut ({len(segments)} segments, output order)")
        for i, (a, b) in enumerate(segments[:6]):
            print(f"  [seg {i}] {a:.2f}-{b:.2f}s")
        if len(segments) > 6:
            print(f"  ... ({len(segments) - 6} more)")
    cut_video = artifacts_dir / "cut.mp4"
    extract_and_concat(input_video, cut_video, segments, verbose=verbose)
    artifacts["cut"] = str(cut_video)
    current = cut_video

    # 4. Optional reframe
    if reframe:
        if verbose:
            print(f"[remix_cut] 4/5 reframe to {target_w}x{target_h}")
        reframed = artifacts_dir / "reframed.mp4"
        info = reframe_to_vertical(current, reframed, target_w=target_w, target_h=target_h, verbose=verbose)
        artifacts["reframed"] = str(reframed)
        artifacts["reframe_mode"] = info["mode"]
        current = reframed
    else:
        if verbose:
            print("[remix_cut] 4/5 reframe SKIPPED")

    # 5. Optional captions: re-transcribe the cut for synced timing
    if captions:
        if verbose:
            print("[remix_cut] 5/5 captions (re-transcribe + render + overlay)")
        cut_transcript = transcribe(current, word_timestamps=True, verbose=verbose)
        info = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(current)],
            check=True, capture_output=True, text=True,
        ).stdout)["streams"][0]
        caption_video(
            current, cut_transcript, output_video,
            style=caption_style,
            play_w=info["width"], play_h=info["height"],
            work_dir=artifacts_dir / "captions",
            verbose=verbose,
        )
        artifacts["captions_dir"] = str(artifacts_dir / "captions")
    else:
        if verbose:
            print("[remix_cut] 5/5 captions SKIPPED")
        shutil.copy2(current, output_video)

    return {
        "template": template,
        "rationale": result.rationale,
        "in_dur": ffprobe_duration(input_video),
        "out_dur": ffprobe_duration(output_video),
        "n_sentences": len(transcript.sentences),
        "n_kept": len(result.keep_indices),
        "n_segments": len(segments),
        "artifacts": artifacts,
    }
