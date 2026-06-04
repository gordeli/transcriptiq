"""Tests for Transcriptiq.

Whisper is mocked throughout, so these run without ffmpeg, a GPU, or any model
download.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from transcriptiq import (
    AUDIO_EXTENSIONS,
    Transcriber,
    TranscriptionResult,
    detect_device,
    format_timestamp,
)


class FakeWhisperModel:
    """Stands in for a loaded Whisper model."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def transcribe(self, path, language=None, **kwargs):
        self.calls.append(path)
        return {
            "text": "  Hello world.  ",
            "language": language or "en",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": " Hello"},
                {"start": 1.5, "end": 3.0, "text": " world."},
            ],
        }


@pytest.fixture
def transcriber(monkeypatch):
    t = Transcriber(model="base.en", device="cpu", verbose=False)
    # Inject the fake model so the `model` property never loads real Whisper.
    t._model = FakeWhisperModel()
    return t


# -- format_timestamp -------------------------------------------------------


def test_format_timestamp_basic():
    assert format_timestamp(0) == "00:00:00.000"
    assert format_timestamp(1.5) == "00:00:01.500"
    assert format_timestamp(3661.25) == "01:01:01.250"


def test_format_timestamp_clamps_negative():
    assert format_timestamp(-5) == "00:00:00.000"


# -- detect_device ----------------------------------------------------------


def test_detect_device_explicit():
    assert detect_device("cpu") == "cpu"
    assert detect_device("cuda") == "cuda"


def test_detect_device_auto_without_torch(monkeypatch):
    # Simulate torch being unavailable -> falls back to cpu.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "torch":
            raise ImportError("no torch")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert detect_device("auto") == "cpu"


# -- transcribe_file --------------------------------------------------------


def test_transcribe_file_returns_result(transcriber, tmp_path):
    audio = tmp_path / "interview.mp3"
    audio.write_bytes(b"not really audio")

    result = transcriber.transcribe_file(audio)

    assert isinstance(result, TranscriptionResult)
    assert result.text == "Hello world."  # stripped
    assert result.language == "en"
    assert result.model == "base.en"
    assert result.processing_seconds is not None
    assert len(result.segments) == 2


def test_transcribe_file_missing_raises(transcriber):
    with pytest.raises(FileNotFoundError):
        transcriber.transcribe_file("does_not_exist.mp3")


# -- TranscriptionResult ----------------------------------------------------


def test_default_output_path(tmp_path):
    result = TranscriptionResult(
        text="x", source_path=tmp_path / "rec.mp3", model="base.en"
    )
    assert result.default_output_path().name == "rec_transcribed.txt"


def test_save_plain_text(tmp_path):
    out = tmp_path / "out.txt"
    result = TranscriptionResult(text="hello", source_path=tmp_path / "a.mp3", model="m")
    written = result.save(out)
    assert written == out
    assert out.read_text(encoding="utf-8") == "hello"


def test_save_with_timestamps(tmp_path):
    result = TranscriptionResult(
        text="Hello world.",
        source_path=tmp_path / "a.mp3",
        model="m",
        segments=[
            {"start": 0.0, "end": 1.5, "text": " Hello"},
            {"start": 1.5, "end": 3.0, "text": " world."},
        ],
    )
    out = result.save(tmp_path / "ts.txt", with_timestamps=True)
    content = out.read_text(encoding="utf-8")
    assert "[00:00:00.000 --> 00:00:01.500] Hello" in content
    assert "[00:00:01.500 --> 00:00:03.000] world." in content


def test_save_creates_parent_dirs(tmp_path):
    result = TranscriptionResult(text="hi", source_path=tmp_path / "a.mp3", model="m")
    out = result.save(tmp_path / "nested" / "deep" / "x.txt")
    assert out.exists()


def test_timestamped_text_falls_back_without_segments():
    result = TranscriptionResult(text="plain", source_path=Path("a.mp3"), model="m")
    assert result.to_timestamped_text() == "plain"


# -- find_audio_files -------------------------------------------------------


def test_find_audio_files(tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"")
    (tmp_path / "b.WAV").write_bytes(b"")  # case-insensitive match
    (tmp_path / "notes.txt").write_text("ignore me")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.m4a").write_bytes(b"")

    found = Transcriber.find_audio_files(tmp_path)
    names = [p.name for p in found]
    assert names == ["a.mp3", "b.WAV"]  # sorted, non-recursive


def test_find_audio_files_recursive(tmp_path):
    (tmp_path / "a.mp3").write_bytes(b"")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.m4a").write_bytes(b"")

    found = Transcriber.find_audio_files(tmp_path, recursive=True)
    names = sorted(p.name for p in found)
    assert names == ["a.mp3", "c.m4a"]


def test_find_audio_files_not_a_dir(tmp_path):
    f = tmp_path / "x.mp3"
    f.write_bytes(b"")
    with pytest.raises(NotADirectoryError):
        Transcriber.find_audio_files(f)


# -- transcribe_folder ------------------------------------------------------


def test_transcribe_folder_saves_outputs(transcriber, tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "one.mp3").write_bytes(b"")
    (audio_dir / "two.mp3").write_bytes(b"")
    out_dir = tmp_path / "transcripts"

    results = transcriber.transcribe_folder(audio_dir, output_dir=out_dir)

    assert len(results) == 2
    assert (out_dir / "one_transcribed.txt").exists()
    assert (out_dir / "two_transcribed.txt").exists()


def test_transcribe_folder_empty(transcriber, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert transcriber.transcribe_folder(empty) == []


# -- sanity -----------------------------------------------------------------


def test_audio_extensions_lowercase():
    assert all(ext == ext.lower() for ext in AUDIO_EXTENSIONS)
    assert ".mp3" in AUDIO_EXTENSIONS
