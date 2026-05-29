"""avc CLI — entry point for `avc cut`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .asr_cut import asr_cut
from .silence import silence_cut


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="avc",
        description="auto-video-cut: trim long videos to tight cuts",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    cut = sub.add_parser("cut", help="cut a video (silence or ASR mode)")
    cut.add_argument("input", type=Path, help="input video path")
    cut.add_argument("--out", type=Path, required=True, help="output video path")
    cut.add_argument(
        "--mode",
        choices=["silence", "asr"],
        default="silence",
        help="silence: ffmpeg silencedetect (v0.1). asr: Whisper+Gemini (v0.2).",
    )
    cut.add_argument(
        "--silence-threshold",
        type=float,
        default=-30.0,
        help="[silence mode] dBFS below which audio is considered silent",
    )
    cut.add_argument(
        "--min-silence",
        type=float,
        default=0.4,
        help="[silence mode] minimum silence duration to cut, seconds",
    )
    cut.add_argument(
        "--margin",
        type=float,
        default=0.1,
        help="[silence mode] padding seconds around speech",
    )
    cut.add_argument(
        "--target-ratio",
        type=float,
        default=0.30,
        help="[asr mode] target output duration as fraction of input (default: 0.30)",
    )
    cut.add_argument(
        "--style",
        type=str,
        default="保留干货、punchline、关键信息；剪掉铺垫、重复、套话",
        help="[asr mode] LLM selection style prompt",
    )
    cut.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-pro",
        help="[asr mode] Gemini model to use",
    )
    cut.add_argument("-v", "--verbose", action="store_true")

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

    return 0


if __name__ == "__main__":
    sys.exit(main())
