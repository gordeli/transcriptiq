# Changelog

All notable changes to Transcriptiq are documented here. This project adheres to
[Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-20

### Added
- Desktop app: **Language** menu with presets for English, Hindi (Devanagari),
  Hindi + English mix (Hinglish, keeps English terms in Latin script) and
  Hindi → English translation (`transcriptiq.languages`).
- Desktop app: "Also save an English translation" option writes a second
  `…_english.txt` file next to each Hindi transcript.
- The detected language is shown in the progress log.

### Changed
- Desktop installers bundle the multilingual `small` model instead of the
  English-only `base.en`, so Hindi works offline out of the box.
- Models picked in the app that are not bundled download to a per-user folder
  (`~/Library/Application Support/Transcriptiq/models` on macOS).
- The app refuses English-only (`*.en`) models for Hindi presets.
- `fp16` is turned off automatically on CPU (no more Whisper warning on Macs).

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
