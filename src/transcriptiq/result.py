"""Data structures describing a completed transcription."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


def format_timestamp(seconds: float) -> str:
    """Format a number of seconds as ``HH:MM:SS.mmm``."""
    if seconds < 0:
        seconds = 0.0
    milliseconds = round(seconds * 1000.0)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


@dataclass
class TranscriptionResult:
    """The outcome of transcribing a single audio file.

    Attributes:
        text: The full transcript as a single string.
        source_path: Path to the audio file that was transcribed.
        model: Name of the Whisper model used.
        language: Detected (or forced) spoken language, if known.
        processing_seconds: Wall-clock time spent transcribing.
        segments: Raw Whisper segments (each with ``start``/``end``/``text``),
            used to produce timestamped output.
    """

    text: str
    source_path: Path
    model: str
    language: Optional[str] = None
    processing_seconds: Optional[float] = None
    segments: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.source_path = Path(self.source_path)

    def default_output_path(self, suffix: str = "_transcribed") -> Path:
        """Path next to the source file, e.g. ``interview_transcribed.txt``."""
        return self.source_path.with_name(self.source_path.stem + suffix + ".txt")

    def to_timestamped_text(self) -> str:
        """Render the transcript with ``[start --> end]`` markers per segment.

        Falls back to the plain text when segment data is unavailable.
        """
        if not self.segments:
            return self.text
        lines = []
        for segment in self.segments:
            start = format_timestamp(float(segment.get("start", 0.0)))
            end = format_timestamp(float(segment.get("end", 0.0)))
            lines.append(f"[{start} --> {end}] {str(segment.get('text', '')).strip()}")
        return "\n".join(lines)

    def save(
        self,
        path: Optional[Path | str] = None,
        *,
        with_timestamps: bool = False,
        encoding: str = "utf-8",
    ) -> Path:
        """Write the transcript to ``path`` (creating parent folders).

        When ``path`` is omitted, writes alongside the source audio using
        :meth:`default_output_path`. Returns the path written to.
        """
        out_path = Path(path) if path is not None else self.default_output_path()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_timestamped_text() if with_timestamps else self.text
        out_path.write_text(content, encoding=encoding)
        return out_path
