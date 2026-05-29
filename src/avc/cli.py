"""avc CLI — entry points for ``avc cut`` and ``avc pipeline``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .asr_cut import asr_cut
from .silence import silence_cut


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="avc",
        description="auto-video-cut: trim long videos to tight cuts (and shorts).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---------- cut ----------
    cut = sub.add_parser("cut", help="cut a video (silence or ASR mode)")
    cut.add_argument("input", type=Path)
    cut.add_argument("--out", type=Path, required=True)
    cut.add_argument(
        "--mode", choices=["silence", "asr"], default="silence",
        help="silence: ffmpeg silencedetect (v0.1). asr: Whisper+Gemini (v0.2).",
    )
    cut.add_argument("--silence-threshold", type=float, default=-30.0)
    cut.add_argument("--min-silence", type=float, default=0.4)
    cut.add_argument("--margin", type=float, default=0.1)
    cut.add_argument("--target-ratio", type=float, default=0.30)
    cut.add_argument("--style", type=str, default="保留干货、punchline、关键信息；剪掉铺垫、重复、套话")
    cut.add_argument("--model", type=str, default="gemini-2.5-pro")
    cut.add_argument("-v", "--verbose", action="store_true")

    # ---------- pipeline ----------
    pipe = sub.add_parser(
        "pipeline",
        help="full demo pipeline: transcribe → AI pick → cut → optional reframe → optional captions",
    )
    pipe.add_argument("input", type=Path)
    pipe.add_argument("--out", type=Path, required=True)
    pipe.add_argument("--target-ratio", type=float, default=0.30)
    pipe.add_argument("--style", type=str, default="保留干货、punchline、关键信息；剪掉铺垫、重复、套话")
    pipe.add_argument("--model", type=str, default="gemini-2.5-pro")
    pipe.add_argument("--reframe", action="store_true",
                      help="reframe to 9:16 with face-tracking (default off)")
    pipe.add_argument("--captions", action="store_true",
                      help="burn word-by-word opus-style captions (default off)")
    pipe.add_argument(
        "--caption-style", type=str, default="opus",
        choices=["opus", "opus-cn", "minimal", "karaoke"],
    )
    pipe.add_argument("--target-w", type=int, default=1080)
    pipe.add_argument("--target-h", type=int, default=1920)
    pipe.add_argument("-v", "--verbose", action="store_true")

    # ---------- remix ----------
    remix = sub.add_parser(
        "remix",
        help="template-driven semantic remix (non-chronological reordering by narrative role)",
    )
    remix.add_argument("input", type=Path)
    remix.add_argument("--out", type=Path, required=True)
    remix.add_argument(
        "--template", required=True,
        choices=["viral_hook", "top3", "thesis", "trailer"],
        help="which remix template to apply",
    )
    remix.add_argument("--model", type=str, default="gemini-2.5-pro")
    remix.add_argument("--reframe", action="store_true")
    remix.add_argument("--captions", action="store_true")
    remix.add_argument("--caption-style", type=str, default="opus",
                       choices=["opus", "opus-cn", "minimal", "karaoke"])
    remix.add_argument("--cached-transcript", type=Path,
                       help="reuse a previously-saved transcript.json instead of re-ASR")
    remix.add_argument("--target-w", type=int, default=1080)
    remix.add_argument("--target-h", type=int, default=1920)
    remix.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "cut":
        if not args.input.exists():
            print(f"error: input not found: {args.input}", file=sys.stderr)
            return 2
        try:
            if args.mode == "silence":
                stats = silence_cut(
                    input_path=args.input,
                    output_path=args.out,
                    silence_threshold_db=args.silence_threshold,
                    min_silence_s=args.min_silence,
                    margin_s=args.margin,
                    verbose=args.verbose,
                )
            else:  # asr
                stats = asr_cut(
                    input_path=args.input,
                    output_path=args.out,
                    target_ratio=args.target_ratio,
                    style_prompt=args.style,
                    model=args.model,
                    verbose=args.verbose,
                )
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(
            f"✓ {args.input.name} → {args.out.name}: "
            f"{stats['in_dur']:.1f}s → {stats['out_dur']:.1f}s "
            f"(kept {stats['ratio'] * 100:.0f}%)"
        )
        if args.mode == "asr":
            print(f"  {stats['n_kept']}/{stats['n_sentences']} sentences kept; "
                  f"transcript saved to {stats['transcript_path']}")
        return 0

    if args.cmd == "remix":
        if not args.input.exists():
            print(f"error: input not found: {args.input}", file=sys.stderr)
            return 2
        from .remix_cut import remix_cut
        try:
            res = remix_cut(
                input_video=args.input,
                output_video=args.out,
                template=args.template,
                model=args.model,
                reframe=args.reframe,
                captions=args.captions,
                caption_style=args.caption_style,
                cached_transcript=args.cached_transcript,
                target_w=args.target_w,
                target_h=args.target_h,
                verbose=args.verbose,
            )
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(
            f"✓ {args.input.name} → {args.out.name} ({res['template']}): "
            f"{res['in_dur']:.1f}s → {res['out_dur']:.1f}s "
            f"({res['n_kept']}/{res['n_sentences']} sentences, {res['n_segments']} segments)"
        )
        print(f"  rationale: {res['rationale']}")
        return 0

    if args.cmd == "pipeline":
        if not args.input.exists():
            print(f"error: input not found: {args.input}", file=sys.stderr)
            return 2
        from .pipeline import run as pipeline_run
        try:
            res = pipeline_run(
                input_video=args.input,
                output_video=args.out,
                target_ratio=args.target_ratio,
                style_prompt=args.style,
                model=args.model,
                reframe=args.reframe,
                captions=args.captions,
                caption_style=args.caption_style,
                target_w=args.target_w,
                target_h=args.target_h,
                verbose=args.verbose,
            )
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(
            f"✓ {args.input.name} → {args.out.name}: "
            f"{res['in_dur']:.1f}s → {res['out_dur']:.1f}s "
            f"({res['ratio'] * 100:.0f}% kept)"
        )
        print(f"  stages: {' → '.join(res['stages'])}")
        print(f"  {res['n_kept']}/{res['n_sentences']} sentences, {res['n_segments']} segments")
        if "reframe_mode" in res["artifacts"]:
            print(f"  reframe mode: {res['artifacts']['reframe_mode']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
