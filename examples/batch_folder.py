"""Transcribe a folder of research recordings to timestamped transcripts.

Mirrors a common qualitative-research workflow: drop all your interview or
focus-group audio into one folder and produce one transcript per recording.

Run:
    python examples/batch_folder.py ./recordings ./transcripts
"""

from __future__ import annotations

import sys

from transcriptiq import Transcriber


def main() -> None:
    audio_folder = sys.argv[1] if len(sys.argv) > 1 else "recordings"
    output_folder = sys.argv[2] if len(sys.argv) > 2 else "transcripts"

    transcriber = Transcriber(model="base.en")  # auto GPU/CPU
    results = transcriber.transcribe_folder(
        audio_folder,
        output_dir=output_folder,
        with_timestamps=True,
    )

    print(f"\nTranscribed {len(results)} recording(s):")
    for result in results:
        seconds = result.processing_seconds or 0.0
        print(f"  - {result.source_path.name}: {len(result.text)} chars in {seconds:.1f}s")


if __name__ == "__main__":
    main()
