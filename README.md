# Transcriptiq

**Academic audio transcription powered by [OpenAI Whisper](https://github.com/openai/whisper).**

Transcriptiq turns research audio — interviews, focus groups, lectures, podcasts —
into clean text transcripts. Run it on a single recording or point it at a whole
folder; use your GPU when you have one; add timestamps when you need them.

```python
from transcriptiq import Transcriber

t = Transcriber(model="base.en")          # auto-detects GPU/CPU
result = t.transcribe_file("interview.mp3")
print(result.text)
result.save("interview.txt")
```

---

## Why Transcriptiq?

Qualitative research generates hours of audio that has to become text before it
can be coded and analysed. Transcriptiq wraps Whisper in a small, predictable API
built for that workflow:

- **Batch a folder** of interviews or focus-group recordings in one call.
- **GPU acceleration** when CUDA is available, automatic fallback to CPU.
- **Timestamps** for jumping back to the audio while coding.
- **Many formats** — `.mp3`, `.wav`, `.m4a`, `.flac`, `.mp4`, and more.
- **A CLI and a Python API** — script it or call it from your analysis notebook.

---

## Installation

Transcriptiq depends on `openai-whisper`, which in turn requires
[**ffmpeg**](https://ffmpeg.org/) to be installed on your system.

```bash
# 1. Install ffmpeg (one-time, system dependency)
#    Windows (winget):   winget install Gyan.FFmpeg
#    macOS (homebrew):    brew install ffmpeg
#    Debian/Ubuntu:       sudo apt install ffmpeg

# 2. Install Transcriptiq (from a local clone for now)
pip install .
```

> For GPU support, install a CUDA-enabled build of PyTorch following the
> [official instructions](https://pytorch.org/get-started/locally/) before/after
> installing Transcriptiq.

---

## Command-line usage

```bash
# Transcribe one file (writes interview_transcribed.txt next to it)
transcriptiq interview.mp3

# Transcribe an entire folder into a transcripts/ directory
transcriptiq ./focus_groups --output-dir ./transcripts --model small.en

# Add timestamps and force English
transcriptiq lecture.mp4 --timestamps --language en
```

| Option | Description |
| --- | --- |
| `-m, --model` | Whisper model (`tiny`, `base`, `small`, `medium`, `large`, or `*.en`). Default: `base.en`. |
| `-o, --output-dir` | Where to write transcripts. Default: next to each source file. |
| `-l, --language` | Force the spoken language (e.g. `en`). Auto-detected if omitted. |
| `-d, --device` | `auto` (default), `cpu`, or `cuda`. |
| `-t, --timestamps` | Include `[start --> end]` markers. |
| `-r, --recursive` | Recurse into subfolders when the input is a directory. |
| `-q, --quiet` | Suppress progress output. |

---

## Python API

### Transcribe a single file

```python
from transcriptiq import Transcriber

t = Transcriber(model="small.en", device="auto")
result = t.transcribe_file("interview.mp3", language="en")

print(result.text)                 # full transcript
print(result.language)             # 'en'
print(result.processing_seconds)   # how long it took
result.save("interview.txt", with_timestamps=True)
```

### Transcribe a folder

```python
results = t.transcribe_folder(
    "focus_groups/",
    output_dir="transcripts/",
    recursive=True,
    with_timestamps=True,
)
for r in results:
    print(r.source_path.name, "->", len(r.text), "chars")
```

### Choosing a model

| Model | Speed | Accuracy | Notes |
| --- | --- | --- | --- |
| `tiny` / `tiny.en` | fastest | lowest | quick drafts |
| `base` / `base.en` | fast | good | sensible default |
| `small` / `small.en` | moderate | better | good balance |
| `medium` / `medium.en` | slow | high | strong quality |
| `large` | slowest | highest | best, needs a GPU |

The `.en` variants are English-only and a little faster/more accurate for
English audio.

---

## Output

By default each transcript is written as UTF-8 text named
`<audio-filename>_transcribed.txt`. With `--timestamps` each line is prefixed
with its segment time range:

```
[00:00:00.000 --> 00:00:04.120] Thanks for joining us today.
[00:00:04.120 --> 00:00:09.480] Could you start by telling us about your role?
```

---

## Web app (Streamlit)

A browser UI for uploading audio and downloading transcripts — no command line
needed.

```bash
streamlit run streamlit_app.py
```

It deploys as-is to **Streamlit Community Cloud** (point it at this repo, main
file `streamlit_app.py`) or Hugging Face Spaces. The bundled `packages.txt`
installs ffmpeg and `requirements.txt` installs the package. Note: free hosting
tiers are memory-limited, so prefer the `tiny`/`base` models there.

## Desktop app (Mac & Windows)

A standalone tkinter app — pick files or a folder, choose a model, transcribe.
Launch the installed version with `transcriptiq-gui`, or run from source with
`python -m transcriptiq.gui`.

Two ways to install it, both documented step by step in
[`installers/README.md`](installers/README.md):

- **Slim installer** — a small script that sets up a Python environment and the
  package on first run (`installers/slim/install-windows.ps1` /
  `install-macos.sh`).
- **Bundled installers** — self-contained, offline-ready `.exe` (Windows) and
  `.dmg` (macOS Apple Silicon) built automatically by GitHub Actions (bundles a
  static ffmpeg + the `base.en` model). Run the **Build desktop installers**
  workflow, or push a `v*` tag to attach them to a Release.

## Development

```bash
pip install -e ".[dev]"
pytest
```

The test suite mocks Whisper, so it runs fast and does **not** require ffmpeg,
a GPU, or any model download.

---

## License

[MIT](LICENSE) © Ivan Gordeliy
