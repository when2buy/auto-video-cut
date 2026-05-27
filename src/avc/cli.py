"""avc CLI — entry point for `avc cut`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .silence import silence_cut


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="avc",
        description="auto-video-cut: trim long videos to tight cuts",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    cut = sub.add_parser("cut", help="silence-based cut (v0.1)")
    cut.add_argument("input", type=Path, help="input video path")
    cut.add_argument("--out", type=Path, required=True, help="output video path")
    cut.add_argument(
        "--silence-threshold",
        type=float,
        default=-30.0,
        help="dBFS below which audio is considered silent (default: -30)",
    )
    cut.add_argument(
        "--min-silence",
        type=float,
        default=0.4,
        help="minimum silence duration to cut, seconds (default: 0.4)",
    )
    cut.add_argument(
        "--margin",
        type=float,
        default=0.1,
        help="seconds of padding to keep around speech (default: 0.1)",
    )
    cut.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "cut":
        if not args.input.exists():
            print(f"error: input not found: {args.input}", file=sys.stderr)
            return 2
        try:
            stats = silence_cut(
                input_path=args.input,
                output_path=args.out,
                silence_threshold_db=args.silence_threshold,
                min_silence_s=args.min_silence,
                margin_s=args.margin,
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
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
