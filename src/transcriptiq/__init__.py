"""Transcriptiq — academic audio transcription powered by OpenAI Whisper.

Transcribe interviews, focus groups, lectures, and other research audio to
text, individually or in bulk, with optional timestamps and GPU acceleration.

Quick start:
    >>> from transcriptiq import Transcriber
    >>> t = Transcriber(model="base.en")
    >>> result = t.transcribe_file("interview.mp3")
    >>> print(result.text)
    >>> result.save("interview.txt")
"""

from __future__ import annotations

from .result import TranscriptionResult, format_timestamp
from .transcriber import (
    AUDIO_EXTENSIONS,
    DEFAULT_MODEL,
    Transcriber,
    detect_device,
)

__version__ = "0.1.0"

__all__ = [
    "Transcriber",
    "TranscriptionResult",
    "detect_device",
    "format_timestamp",
    "AUDIO_EXTENSIONS",
    "DEFAULT_MODEL",
    "__version__",
]
