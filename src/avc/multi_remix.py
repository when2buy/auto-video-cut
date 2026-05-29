"""Multi-source mashup: weave N input videos into ONE coherent edit.

Where ``remix.py`` reorders sentences inside one video, ``multi_remix.py``
selects sentences across MANY videos and produces a single supercut. Use case:

    > "Throw a bunch of long videos at the tool. Find the relationships.
    >  Cut me a coherent video out of them."

Pipeline:
    1. transcribe each source (or load cached transcripts)
    2. send all N transcripts to Gemini in a single call
       — ask it to either (a) discover a theme or (b) honor a user-given theme
       — it returns: theme statement, ordered list of (video_id, sentence_idx)
    3. for each chosen sentence, extract a clip from its source video
    4. reframe-first to align all clips to target_w x target_h
    5. concat the reframed clips into one output
    6. (optional) re-transcribe the concat for synced captions

The output's segment order = LLM's editorial choice (cross-source, possibly
non-chronological within each source).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from .asr import SentenceSegment, Transcript, WordSegment, transcribe
from .captions import caption_video
from .reframe import reframe_to_vertical
from .silence import ffprobe_duration


def _ensure_token() -> None:
    token_path = Path.home() / ".secrets/pluto-auth-token-steve-train.txt"
    if "PLUTO_AUTH_TOKEN" not in os.environ and token_path.exists():
        os.environ["PLUTO_AUTH_TOKEN"] = token_path.read_text().strip()


@dataclass
class MultiSource:
    """One input source with cached or fresh transcript."""
    video_id: str          # filename-safe slug for the source
    video_path: Path
    transcript: Transcript
    label: str             # human-friendly name shown in rationale ("Tim Urban")


@dataclass
class MultiPick:
    """One sentence selected from one source, in OUTPUT order."""
    video_id: str
    sentence_idx: int
    start: float           # source timestamps (with margin applied)
    end: float


@dataclass
class MultiRemixResult:
    theme: str
    rationale: str
    picks: list[MultiPick]


def _load_transcript_json(path: Path) -> Transcript:
    d = json.loads(path.read_text())
    sentences: list[SentenceSegment] = []
    for s in d["sentences"]:
        words = None
        if s.get("words"):
            words = [WordSegment(**w) for w in s["words"]]
        sentences.append(SentenceSegment(
            start=s["start"], end=s["end"], text=s["text"],
            word_count=s["word_count"], words=words,
        ))
    return Transcript(language=d["language"], duration=d["duration"], sentences=sentences)


def gather_sources(
    inputs: list[tuple[Path, str | None, Path | None]],
    *,
    word_timestamps: bool = False,
    verbose: bool = False,
) -> list[MultiSource]:
    """Build MultiSource list from (video_path, label_or_none, cached_transcript_or_none).

    If cached_transcript is provided and exists, load it; otherwise re-transcribe.
    """
    sources: list[MultiSource] = []
    for video_path, label, cached in inputs:
        if not video_path.exists():
            raise FileNotFoundError(video_path)
        video_id = video_path.stem
        if cached is not None and cached.exists():
            if verbose:
                print(f"[multi] {video_id}: loaded transcript from {cached}")
            t = _load_transcript_json(cached)
        else:
            if verbose:
                print(f"[multi] {video_id}: transcribing (word_timestamps={word_timestamps})…")
            t = transcribe(video_path, word_timestamps=word_timestamps, verbose=verbose)
        sources.append(MultiSource(
            video_id=video_id,
            video_path=video_path,
            transcript=t,
            label=label or video_id,
        ))
    return sources


def discover_and_pick(
    sources: list[MultiSource],
    *,
    theme: str | None = None,
    target_duration_s: float = 80.0,
    model: str = "gemini-2.5-pro",
    verbose: bool = False,
) -> MultiRemixResult:
    """Send all transcripts to Gemini in one call. Get back theme + ordered picks.

    If theme is None, the LLM discovers one. Otherwise the user-given theme is honored.
    """
    _ensure_token()
    from foundry_aws_gateway.llm import get_google_genai
    client = get_google_genai(location="global")

    # Build the prompt block with all transcripts side by side, each with a video_id tag
    blocks: list[str] = []
    for src in sources:
        head = f"### Source: video_id={src.video_id} | label={src.label!r} | duration={src.transcript.duration:.0f}s | sentences={len(src.transcript.sentences)}"
        lines = [head]
        for i, s in enumerate(src.transcript.sentences):
            lines.append(f"  [{src.video_id}:{i}] {s.start:6.1f}-{s.end:6.1f}s  {s.text}")
        blocks.append("\n".join(lines))
    transcripts_block = "\n\n".join(blocks)

    if theme:
        theme_instruction = f"""You are given a THEME by the user — find sentences across the {len(sources)} sources that, woven together, tell that theme as ONE coherent argument or story.

USER-GIVEN THEME: "{theme}"
"""
    else:
        theme_instruction = f"""You are given {len(sources)} TED-talk-like transcripts from DIFFERENT speakers. Your job:

1. **Discover** a single THEME that connects all {len(sources)} sources — something each speaker contributes a piece to.
2. **Build** a ~{target_duration_s:.0f}s supercut that uses pieces from EACH source to tell that theme as one story.

The theme should be specific and intellectually meaningful, not generic ("communication", "thinking" are too broad — try "the mind's hidden negotiations" or "why our intuitions about the future are wrong").
"""

    prompt = f"""You are an expert documentary editor doing a CROSS-SOURCE SUPERCUT.

{theme_instruction}

## Constraints

- Output total duration: ~{target_duration_s:.0f} seconds
- Use sentences from AT LEAST 2 of the sources (ideally all {len(sources)})
- Order is by NARRATIVE (intro → development → conclusion), NOT by source-time
- Within each source you pick from, prefer adjacent sentences (2-4 in a row) so each "moment" lands

## Output format (strict JSON only)

{{
  "theme": "<one-sentence theme statement>",
  "rationale": "<2-4 sentences explaining the editorial choice — what each source contributes>",
  "picks": [
    {{"video_id": "<src1>", "indices": [10, 11, 12]}},
    {{"video_id": "<src2>", "indices": [42, 43]}},
    {{"video_id": "<src1>", "indices": [55]}},
    ...
  ]
}}

The "picks" list is the OUTPUT ORDER — segments will be concatenated in this order. Each pick is a contiguous run of sentence indices from one source. You can switch between sources freely.

## Transcripts ({len(sources)} sources)

{transcripts_block}
"""

    if verbose:
        print(f"[multi] sending prompt to {model} ({len(prompt)} chars across {len(sources)} sources)…")

    resp = client.models.generate_content(model=model, contents=prompt)
    raw = resp.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise RuntimeError(f"LLM returned no JSON object:\n{raw[:500]}")
    obj = json.loads(m.group(0))

    # Build src_by_id index for validation
    src_by_id = {s.video_id: s for s in sources}

    picks: list[MultiPick] = []
    margin = 0.15
    for item in obj.get("picks", []):
        vid = item.get("video_id")
        indices = item.get("indices", [])
        src = src_by_id.get(vid)
        if not src:
            if verbose:
                print(f"[multi] warning: pick references unknown video_id={vid}")
            continue
        for idx in indices:
            try:
                idx = int(idx)
            except (TypeError, ValueError):
                continue
            if not (0 <= idx < len(src.transcript.sentences)):
                continue
            s = src.transcript.sentences[idx]
            picks.append(MultiPick(
                video_id=vid,
                sentence_idx=idx,
                start=max(0.0, s.start - margin),
                end=min(src.transcript.duration, s.end + margin),
            ))

    if not picks:
        raise RuntimeError("LLM returned no valid picks")

    result = MultiRemixResult(
        theme=obj.get("theme", ""),
        rationale=obj.get("rationale", ""),
        picks=picks,
    )

    if verbose:
        total = sum(p.end - p.start for p in picks)
        per_src: dict[str, float] = {}
        for p in picks:
            per_src[p.video_id] = per_src.get(p.video_id, 0) + (p.end - p.start)
        print(f"[multi] theme: {result.theme}")
        print(f"[multi] rationale: {result.rationale}")
        print(f"[multi] {len(picks)} picks, ~{total:.0f}s total, per-source:")
        for vid, dur in per_src.items():
            print(f"  {vid}: {dur:.0f}s")

    return result


def render_multi_remix(
    sources: list[MultiSource],
    picks: list[MultiPick],
    output_video: Path,
    *,
    target_w: int = 1080,
    target_h: int = 1920,
    artifacts_dir: Path | None = None,
    verbose: bool = False,
) -> dict:
    """Cross-source extract + reframe-to-target + concat.

    Each pick becomes a clip cut from its source, then reframed to the target
    aspect, then all clips are concatenated. Reframe-first ensures all clips
    have identical dimensions/codec params so concat works with stream-copy.

    Adjacent picks from the same source are merged where contiguous.
    """
    output_video.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir = artifacts_dir or output_video.parent / f"{output_video.stem}.artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    src_by_id = {s.video_id: s for s in sources}

    # 1. Merge contiguous picks from the same source for cleaner clips
    merged: list[MultiPick] = []
    for p in picks:
        if (
            merged
            and merged[-1].video_id == p.video_id
            and p.start <= merged[-1].end + 0.4
            and p.sentence_idx == merged[-1].sentence_idx + 1
        ):
            merged[-1] = MultiPick(
                video_id=p.video_id,
                sentence_idx=p.sentence_idx,
                start=merged[-1].start,
                end=p.end,
            )
        else:
            merged.append(p)
    if verbose:
        print(f"[multi-render] {len(picks)} picks merged to {len(merged)} clips")

    # 2. For each clip: cut from source → reframe to target
    clip_files: list[Path] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for i, pick in enumerate(merged):
            src = src_by_id[pick.video_id]
            # 2a. raw cut (re-encode to common codec params for clean concat downstream)
            raw_clip = tmp / f"raw-{i:03d}.mp4"
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", f"{pick.start:.3f}",
                "-to", f"{pick.end:.3f}",
                "-i", str(src.video_path),
                "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k",
                str(raw_clip),
            ]
            subprocess.run(cmd, check=True, capture_output=not verbose)

            # 2b. reframe to target — saves to artifacts dir for inspection
            reframed = artifacts_dir / f"clip-{i:03d}-{pick.video_id}.mp4"
            reframe_to_vertical(
                raw_clip, reframed,
                target_w=target_w, target_h=target_h,
                n_samples=4, verbose=False,
            )
            clip_files.append(reframed)
            if verbose:
                src_label = src.label
                print(f"  [{i:2d}] {src_label} {pick.start:.1f}-{pick.end:.1f}s "
                      f"({pick.end - pick.start:.1f}s) → reframed")

        # 3. Concat list. ffmpeg's concat demuxer resolves "file" entries
        # relative to the LIST FILE's directory, so we must use either absolute
        # paths or paths relative to artifacts_dir (where list_file lives).
        # Using absolute is simpler and bulletproof.
        list_file = artifacts_dir / "concat.txt"
        list_file.write_text(
            "".join(f"file '{p.resolve().as_posix()}'\n" for p in clip_files)
        )

        # 4. Concat with stream-copy (all clips have identical params now)
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(output_video),
        ]
        subprocess.run(cmd, check=True, capture_output=not verbose)

    return {
        "n_clips": len(merged),
        "output": str(output_video),
        "artifacts_dir": str(artifacts_dir),
    }


# ---------------------------------------------------------------------------

class MultiRemixResultDict(TypedDict):
    theme: str
    rationale: str
    in_total: float
    out_dur: float
    n_picks: int
    n_clips: int
    per_source_seconds: dict[str, float]
    artifacts: dict[str, str]


def multi_remix(
    *,
    inputs: list[tuple[Path, str | None, Path | None]],
    output_video: Path,
    theme: str | None = None,
    target_duration_s: float = 80.0,
    model: str = "gemini-2.5-pro",
    reframe_target_w: int = 1080,
    reframe_target_h: int = 1920,
    captions: bool = False,
    caption_style: str = "opus",
    artifacts_dir: Path | None = None,
    verbose: bool = False,
) -> MultiRemixResultDict:
    """Top-level entry: gather → discover → render → optional captions."""
    output_video.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir = artifacts_dir or output_video.parent / f"{output_video.stem}.artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"[multi_remix] {len(inputs)} sources, theme={theme!r}, target={target_duration_s:.0f}s")

    sources = gather_sources(inputs, word_timestamps=False, verbose=verbose)
    pick_result = discover_and_pick(
        sources, theme=theme, target_duration_s=target_duration_s,
        model=model, verbose=verbose,
    )

    # Save the LLM result for the demo HTML to read
    plan_path = artifacts_dir / "plan.json"
    plan_path.write_text(json.dumps({
        "theme": pick_result.theme,
        "rationale": pick_result.rationale,
        "picks": [
            {
                "video_id": p.video_id,
                "sentence_idx": p.sentence_idx,
                "start": p.start,
                "end": p.end,
                "text": next(
                    (s.transcript.sentences[p.sentence_idx].text for s in sources if s.video_id == p.video_id),
                    "",
                ),
            }
            for p in pick_result.picks
        ],
    }, ensure_ascii=False, indent=2))

    # Render
    if captions:
        intermediate = artifacts_dir / "concat.mp4"
    else:
        intermediate = output_video
    render_info = render_multi_remix(
        sources, pick_result.picks, intermediate,
        target_w=reframe_target_w, target_h=reframe_target_h,
        artifacts_dir=artifacts_dir, verbose=verbose,
    )

    # Optional captions on the concatenated output
    if captions:
        if verbose:
            print("[multi_remix] captions: re-transcribe + render PNGs + overlay")
        cut_transcript = transcribe(intermediate, word_timestamps=True, verbose=verbose)
        info = json.loads(subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(intermediate)],
            check=True, capture_output=True, text=True,
        ).stdout)["streams"][0]
        caption_video(
            intermediate, cut_transcript, output_video,
            style=caption_style,
            play_w=info["width"], play_h=info["height"],
            work_dir=artifacts_dir / "captions",
            verbose=verbose,
        )

    in_total = sum(s.transcript.duration for s in sources)
    out_dur = ffprobe_duration(output_video)
    per_src: dict[str, float] = {}
    for p in pick_result.picks:
        per_src[p.video_id] = per_src.get(p.video_id, 0) + (p.end - p.start)

    return {
        "theme": pick_result.theme,
        "rationale": pick_result.rationale,
        "in_total": in_total,
        "out_dur": out_dur,
        "n_picks": len(pick_result.picks),
        "n_clips": render_info["n_clips"],
        "per_source_seconds": per_src,
        "artifacts": {"plan": str(plan_path), "dir": str(artifacts_dir)},
    }
