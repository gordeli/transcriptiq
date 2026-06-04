"""The :class:`Transcriber` — a thin, friendly wrapper around OpenAI Whisper.

Designed for academic workflows: transcribing interviews, focus groups, and
other research audio in bulk, with optional timestamps and GPU acceleration.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from .result import TranscriptionResult

DEFAULT_MODEL = "base.en"

#: Audio/video container extensions Whisper (via ffmpeg) can read.
AUDIO_EXTENSIONS: tuple[str, ...] = (
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
    ".oga",
    ".opus",
    ".wma",
    ".aac",
    ".mp4",
    ".m4v",
    ".mov",
    ".webm",
)


def detect_device(prefer: Optional[str] = None) -> str:
    """Resolve the compute device.

    ``prefer`` may be ``"cuda"``, ``"cpu"``, or ``"auto"``/``None`` to
    auto-detect (CUDA when available, otherwise CPU). Torch not being
    importable is treated as "no GPU".
    """
    if prefer and prefer != "auto":
        return prefer
    try:
        import torch  # imported lazily so the package loads without torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


class Transcriber:
    """Loads a Whisper model once and transcribes files or whole folders.

    The model is loaded lazily on first use, so constructing a ``Transcriber``
    is cheap and importing the package never requires Whisper to be installed.

    Example:
        >>> t = Transcriber(model="base.en")
        >>> result = t.transcribe_file("interview.mp3")
        >>> result.save("interview.txt")
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        device: str = "auto",
        download_root: Optional[Path | str] = None,
        verbose: bool = True,
    ) -> None:
        self.model_name = model
        self.device = detect_device(device)
        self.download_root = str(download_root) if download_root is not None else None
        self.verbose = verbose
        self._model: Any = None

    # -- model loading --------------------------------------------------

    @property
    def model(self) -> Any:
        """The underlying Whisper model, loaded on first access."""
        if self._model is None:
            try:
                import whisper
            except ImportError as exc:  # pragma: no cover - depends on env
                raise ImportError(
                    "openai-whisper is required to transcribe audio. "
                    "Install it with: pip install transcriptiq[whisper]"
                ) from exc
            self._log(f"Loading Whisper model '{self.model_name}' on {self.device} ...")
            self._model = whisper.load_model(
                self.model_name, device=self.device, download_root=self.download_root
            )
        return self._model

    # -- core API -------------------------------------------------------

    def transcribe_file(
        self,
        audio_path: Path | str,
        *,
        language: Optional[str] = None,
        **whisper_kwargs: Any,
    ) -> TranscriptionResult:
        """Transcribe a single audio/video file.

        Extra keyword arguments are forwarded to ``whisper.transcribe``
        (e.g. ``initial_prompt``, ``temperature``, ``fp16``).
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        self._log(f"Transcribing: {path.name}")
        start = time.time()
        raw = self.model.transcribe(str(path), language=language, **whisper_kwargs)
        elapsed = time.time() - start

        result = TranscriptionResult(
            text=str(raw.get("text", "")).strip(),
            source_path=path,
            model=self.model_name,
            language=raw.get("language", language),
            processing_seconds=elapsed,
            segments=list(raw.get("segments", [])),
        )
        self._log(f"  finished in {elapsed:.1f}s ({len(result.text)} characters)")
        return result

    def transcribe_folder(
        self,
        folder: Path | str,
        *,
        output_dir: Optional[Path | str] = None,
        recursive: bool = False,
        extensions: Sequence[str] = AUDIO_EXTENSIONS,
        save: bool = True,
        with_timestamps: bool = False,
        language: Optional[str] = None,
        **whisper_kwargs: Any,
    ) -> list[TranscriptionResult]:
        """Transcribe every supported audio file in ``folder``.

        When ``save`` is true, each transcript is written to ``output_dir``
        (or next to its source file if ``output_dir`` is None). Returns the
        list of :class:`TranscriptionResult` objects in processing order.
        """
        files = self.find_audio_files(folder, recursive=recursive, extensions=extensions)
        if not files:
            self._log(f"No audio files found in {folder}")
            return []

        out_dir = Path(output_dir) if output_dir is not None else None
        if out_dir is not None:
            out_dir.mkdir(parents=True, exist_ok=True)

        results: list[TranscriptionResult] = []
        self._log(f"Found {len(files)} file(s) to transcribe.")
        for index, audio_file in enumerate(files, start=1):
            self._log(f"[{index}/{len(files)}]")
            result = self.transcribe_file(
                audio_file, language=language, **whisper_kwargs
            )
            if save:
                target = (
                    out_dir / (audio_file.stem + "_transcribed.txt")
                    if out_dir is not None
                    else None
                )
                written = result.save(target, with_timestamps=with_timestamps)
                self._log(f"  saved -> {written}")
            results.append(result)

        total = sum(r.processing_seconds or 0.0 for r in results)
        self._log(f"Done. Transcribed {len(results)} file(s) in {total:.1f}s total.")
        return results

    # -- helpers --------------------------------------------------------

    @staticmethod
    def find_audio_files(
        folder: Path | str,
        *,
        recursive: bool = False,
        extensions: Sequence[str] = AUDIO_EXTENSIONS,
    ) -> list[Path]:
        """Return supported audio files in ``folder`` sorted by name."""
        base = Path(folder)
        if not base.is_dir():
            raise NotADirectoryError(f"Not a directory: {base}")
        wanted = {ext.lower() for ext in extensions}
        candidates: Iterable[Path] = base.rglob("*") if recursive else base.iterdir()
        return sorted(
            p for p in candidates if p.is_file() and p.suffix.lower() in wanted
        )

    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)
