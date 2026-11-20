"""Language presets for transcription, including Hindi and Hindi-English mixes.

Whisper accepts a ``language`` code and a ``task`` ("transcribe" or
"translate"). Research interviews in India are often code-mixed: Hindi
sentences with English business terms ("GST", "supplier", "margin"). A
short ``initial_prompt`` written in that same mixed style nudges Whisper to keep
English words in Latin script instead of transliterating them into Devanagari.

Each preset maps a human-readable label to the keyword arguments passed to
``Transcriber.transcribe_file``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

#: Prompt used for Hindi-English code-mixed speech. It is only a style hint:
#: Whisper continues "in the style of" the prompt; it is not inserted in output.
HINGLISH_PROMPT = (
    "नमस्ते। आज हम business, market और GST के बारे में बात करेंगे। "
    "Supplier का price बढ़ गया है, dealer का margin कम हो गया है।"
)

#: Devanagari-only style hint. Without any prompt, multilingual Whisper models
#: (especially ``small``) often drift into other scripts on Hindi audio.
HINDI_PROMPT = "नमस्ते। आज हम दुकान, व्यापार और बाज़ार के बारे में बात करेंगे।"

#: (label, whisper kwargs). The first entry is the default.
LANGUAGE_PRESETS: List[Tuple[str, Dict[str, Any]]] = [
    ("Auto-detect", {"language": None}),
    ("English", {"language": "en"}),
    ("Hindi (Devanagari)", {"language": "hi", "initial_prompt": HINDI_PROMPT}),
    (
        "Hindi + English mix (Hinglish)",
        {"language": "hi", "initial_prompt": HINGLISH_PROMPT},
    ),
    ("Hindi → English translation", {"language": "hi", "task": "translate"}),
]

LANGUAGE_LABELS: List[str] = [label for label, _ in LANGUAGE_PRESETS]


def language_kwargs(label: str) -> Dict[str, Any]:
    """Return the Whisper keyword arguments for a preset label.

    Unknown labels are treated as a raw Whisper language code (e.g. ``"fr"``),
    and an empty label means auto-detect.
    """
    for name, kwargs in LANGUAGE_PRESETS:
        if name == label:
            return dict(kwargs)
    code = (label or "").strip()
    return {"language": code or None}


def is_english_only_model(model: str) -> bool:
    """True for Whisper's English-only checkpoints (``*.en``)."""
    return model.endswith(".en")
