"""Transcriptiq — Streamlit web app.

Upload research audio (interviews, focus groups, lectures), transcribe it with
OpenAI Whisper, and download clean text transcripts. Runs locally with::

    streamlit run streamlit_app.py

and deploys as-is to Streamlit Community Cloud / Hugging Face Spaces.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

# Allow running straight from a repo checkout (src/ layout) without installing.
_SRC = Path(__file__).parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from transcriptiq import Transcriber, __version__  # noqa: E402

# Models worth exposing in a memory-limited hosted environment, smallest first.
MODEL_CHOICES = [
    "tiny.en",
    "tiny",
    "base.en",
    "base",
    "small.en",
    "small",
    "medium.en",
    "medium",
    "large",
]

st.set_page_config(page_title="Transcriptiq", page_icon="🎙️", layout="wide")


@st.cache_resource(show_spinner=False)
def get_transcriber(model_name: str, device: str) -> Transcriber:
    """Load (and cache) a Whisper model for the chosen settings.

    Cached per (model, device) so switching files doesn't reload the model.
    """
    return Transcriber(model=model_name, device=device, verbose=False)


def main() -> None:
    st.title("🎙️ Transcriptiq")
    st.caption(
        f"Academic audio transcription powered by OpenAI Whisper · v{__version__}"
    )
    st.write(
        "Upload interviews, focus groups, or lectures and get clean text "
        "transcripts. Files are processed in memory and never leave this server "
        "beyond what's needed to transcribe them."
    )

    with st.sidebar:
        st.header("Settings")
        model_name = st.selectbox(
            "Whisper model",
            MODEL_CHOICES,
            index=MODEL_CHOICES.index("base.en"),
            help="Smaller = faster and lighter. Larger = more accurate but "
            "needs more memory (and ideally a GPU). On free hosting, stick to "
            "tiny/base.",
        )
        device = st.radio(
            "Device",
            ["auto", "cpu", "cuda"],
            index=0,
            help="'auto' uses a GPU when available, otherwise the CPU.",
            horizontal=True,
        )
        language = st.text_input(
            "Language code (optional)",
            value="",
            placeholder="e.g. en, fr, de",
            help="Leave blank to auto-detect.",
        ).strip() or None
        with_timestamps = st.toggle(
            "Include timestamps",
            value=False,
            help="Prefix each segment with its [start --> end] time range.",
        )
        st.divider()
        st.markdown(
            "Larger models and longer recordings take longer and use more "
            "memory. The free hosting tier is limited — for big jobs, run the "
            "desktop app or the CLI locally."
        )

    uploaded = st.file_uploader(
        "Audio / video files",
        type=["mp3", "wav", "m4a", "flac", "ogg", "opus", "aac", "mp4", "mov", "webm"],
        accept_multiple_files=True,
        help="Drag and drop one or more recordings.",
    )

    if not uploaded:
        st.info("⬆️ Upload one or more audio files to get started.")
        return

    if not st.button(
        f"Transcribe {len(uploaded)} file(s)", type="primary", use_container_width=True
    ):
        return

    transcriber = get_transcriber(model_name, device)
    progress = st.progress(0.0, text="Preparing…")

    for index, upload in enumerate(uploaded, start=1):
        progress.progress(
            (index - 1) / len(uploaded), text=f"Transcribing {upload.name} …"
        )
        try:
            with st.spinner(f"Transcribing {upload.name} (model: {model_name})…"):
                # Whisper reads from a path, so stage the upload to a temp file.
                suffix = Path(upload.name).suffix
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix
                ) as tmp:
                    tmp.write(upload.getbuffer())
                    tmp_path = Path(tmp.name)
                try:
                    result = transcriber.transcribe_file(tmp_path, language=language)
                finally:
                    tmp_path.unlink(missing_ok=True)
        except Exception as exc:  # surface a friendly error, keep going
            st.error(f"Failed to transcribe {upload.name}: {exc}")
            continue

        text = result.to_timestamped_text() if with_timestamps else result.text
        seconds = result.processing_seconds or 0.0

        with st.expander(f"📄 {upload.name}", expanded=len(uploaded) == 1):
            cols = st.columns(3)
            cols[0].metric("Characters", f"{len(result.text):,}")
            cols[1].metric("Language", result.language or "—")
            cols[2].metric("Time", f"{seconds:.1f}s")
            st.text_area("Transcript", value=text, height=300, key=f"text_{index}")
            st.download_button(
                "⬇️ Download .txt",
                data=text,
                file_name=f"{Path(upload.name).stem}_transcribed.txt",
                mime="text/plain",
                key=f"dl_{index}",
                use_container_width=True,
            )

    progress.progress(1.0, text="Done!")
    st.success(f"Transcribed {len(uploaded)} file(s).")


if __name__ == "__main__":
    main()
