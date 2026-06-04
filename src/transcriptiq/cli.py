"""Command-line interface for Transcriptiq.

Usage examples:
    transcriptiq interview.mp3
    transcriptiq ./focus_groups --output-dir ./transcripts --model small.en
    transcriptiq lecture.mp4 --timestamps --language en
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .transcriber import DEFAULT_MODEL, Transcriber


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcriptiq",
        description="Transcribe research audio (interviews, focus groups, "
        "lectures) to text using OpenAI Whisper.",
    )
    parser.add_argument(
        "input",
        help="Path to an audio file or a folder of audio files.",
    )
    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        help=f"Whisper model name (default: {DEFAULT_MODEL}). "
        "E.g. tiny, base, small, medium, large, or *.en variants.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory to write transcripts to. "
        "Defaults to alongside each source file.",
    )
    parser.add_argument(
        "-l",
        "--language",
        default=None,
        help="Force the spoken language (e.g. 'en'). Auto-detected if omitted.",
    )
    parser.add_argument(
        "-d",
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Compute device (default: auto-detect).",
    )
    parser.add_argument(
        "-t",
        "--timestamps",
        action="store_true",
        help="Include [start --> end] timestamps in the output.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="When the input is a folder, recurse into subfolders.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress output.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"error: input not found: {input_path}", file=sys.stderr)
        return 2

    transcriber = Transcriber(
        model=args.model,
        device=args.device,
        verbose=not args.quiet,
    )

    try:
        if input_path.is_dir():
            transcriber.transcribe_folder(
                input_path,
                output_dir=args.output_dir,
                recursive=args.recursive,
                with_timestamps=args.timestamps,
                language=args.language,
            )
        else:
            result = transcriber.transcribe_file(
                input_path, language=args.language
            )
            target = None
            if args.output_dir:
                out_dir = Path(args.output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                target = out_dir / (input_path.stem + "_transcribed.txt")
            written = result.save(target, with_timestamps=args.timestamps)
            if not args.quiet:
                print(f"saved -> {written}")
    except KeyboardInterrupt:  # pragma: no cover
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as exc:  # surface a clean message, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
