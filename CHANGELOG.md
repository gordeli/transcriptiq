# Changelog

All notable changes to Transcriptiq are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-04

Initial release.

### Added
- `Transcriber` class wrapping OpenAI Whisper with lazy model loading and
  automatic GPU/CPU device detection.
- `transcribe_file()` for single recordings and `transcribe_folder()` for batch
  processing of interviews and focus groups.
- `TranscriptionResult` with plain-text and timestamped output, plus `save()`.
- `transcriptiq` command-line interface.
- Support for common audio/video formats (mp3, wav, m4a, flac, mp4, and more).
