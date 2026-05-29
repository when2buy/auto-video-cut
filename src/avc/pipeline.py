"""Full demo pipeline: transcribe → LLM pick → cut → optional reframe → optional captions.

This is the v0.3 product surface. One function call:

    pipeline.run(input_video=..., output_video=..., reframe=True, captions=True)

Returns a PipelineResult dict with stage list + numbers + artifact paths.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import TypedDict

from .asr import transcribe
from .captions import caption_video
from .llm_pick import keeps_to_segments, pick_sentences
from .reframe import reframe_to_vertical
from .silence import extract_and_concat, ffprobe_duration


class PipelineResult(TypedDict):
    stages: list[str]
    in_dur: float
    out_dur: float
    ratio: float
    n_sentences: int
    n_kept: int
    n_segments: int
    artifacts: dict[str, str]


def run(
    *,
    input_video: Path,
    output_video: Path,
    target_ratio: float = 0.30,
    style_prompt: str = "保留干货、punchline、关键信息；剪掉铺垫、重复、套话",
    model: str = "gemini-2.5-pro",
    reframe: bool = False,
    captions: bool = False,
    caption_style: str = "opus",
    target_w: int = 1080,
    target_h: int = 1920,
    artifacts_dir: Path | None = None,
    verbose: bool = False,
) -> PipelineResult:
    if not input_video.exists():
        raise FileNotFoundError(input_video)
    output_video.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir = artifacts_dir or output_video.parent / f"{output_video.stem}.artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    stages: list[str] = []
    artifacts: dict[str, str] = {}

    # 1. ASR (with word timestamps if captions requested)
    if verbose:
        print(f"[pipeline] 1/5 transcribe (word_timestamps={captions})")
    transcript = transcribe(input_video, word_timestamps=captions, verbose=verbose)
    stages.append("asr")
    transcript_json = artifacts_dir / "transcript.json"
    transcript_json.write_text(transcript.to_json())
    artifacts["transcript"] = str(transcript_json)

    # 2. LLM pick
    if verbose:
        print(f"[pipeline] 2/5 llm_pick (target_ratio={target_ratio}, model={model})")
    keep = pick_sentences(
        transcript,
        target_ratio=target_ratio,
        style_prompt=style_prompt,
        model=model,
        verbose=verbose,
    )
    stages.append("llm_pick")
    artifacts["keep_indices"] = json.dumps(keep)

    # 3. Cut to keep-list
    segments = keeps_to_segments(transcript, keep)
    if not segments:
        raise RuntimeError("LLM returned zero kept sentences")
    if verbose:
        print(f"[pipeline] 3/5 cut ({len(segments)} segments)")
    cut_video = artifacts_dir / "cut.mp4"
    extract_and_concat(input_video, cut_video, segments, verbose=verbose)
    stages.append("cut")
    artifacts["cut"] = str(cut_video)
    current = cut_video

    # 4. Optional reframe to 9:16
    if reframe:
        if verbose:
            print(f"[pipeline] 4/5 reframe to {target_w}x{target_h}")
        reframed = artifacts_dir / "reframed.mp4"
        info = reframe_to_vertical(
            current, reframed, target_w=target_w, target_h=target_h, verbose=verbose,
        )
        stages.append("reframe")
        artifacts["reframed"] = str(reframed)
        artifacts["reframe_mode"] = info["mode"]
        current = reframed
    else:
        if verbose:
            print(f"[pipeline] 4/5 reframe SKIPPED")

    # 5. Optional captions: re-transcribe the cut video for synced timing.
    if captions:
        if verbose:
            print(f"[pipeline] 5/5 captions (re-transcribe cut, render PNGs, overlay)")
        # Re-transcribe the (already-cut, possibly already-reframed) video so word
        # timestamps align with the actual frames the viewer will see.
        cut_transcript = transcribe(current, word_timestamps=True, verbose=verbose)

        # Determine play_w / play_h from current video
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
        stages.append("captions")
        artifacts["captions_dir"] = str(artifacts_dir / "captions")
    else:
        if verbose:
            print(f"[pipeline] 5/5 captions SKIPPED — copying current to output")
        shutil.copy2(current, output_video)

    in_dur = ffprobe_duration(input_video)
    out_dur = ffprobe_duration(output_video)
    return {
        "stages": stages,
        "in_dur": in_dur,
        "out_dur": out_dur,
        "ratio": out_dur / in_dur,
        "n_sentences": len(transcript.sentences),
        "n_kept": len(keep),
        "n_segments": len(segments),
        "artifacts": artifacts,
    }
