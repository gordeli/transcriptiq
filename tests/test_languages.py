"""Tests for the language presets and the GUI's model-location helpers."""

from pathlib import Path

from transcriptiq import gui
from transcriptiq.languages import (
    HINDI_PROMPT,
    HINGLISH_PROMPT,
    LANGUAGE_LABELS,
    is_english_only_model,
    language_kwargs,
)


def test_default_preset_is_auto_detect():
    assert language_kwargs(LANGUAGE_LABELS[0]) == {"language": None}


def test_hindi_presets():
    assert language_kwargs("Hindi (Devanagari)") == {
        "language": "hi",
        "initial_prompt": HINDI_PROMPT,
    }
    mix = language_kwargs("Hindi + English mix (Hinglish)")
    assert mix["language"] == "hi"
    assert mix["initial_prompt"] == HINGLISH_PROMPT
    assert language_kwargs("Hindi → English translation") == {
        "language": "hi",
        "task": "translate",
    }


def test_preset_kwargs_are_copies():
    language_kwargs("English")["language"] = "fr"
    assert language_kwargs("English") == {"language": "en"}


def test_unknown_label_is_raw_code():
    assert language_kwargs("fr") == {"language": "fr"}
    assert language_kwargs("  ") == {"language": None}


def test_english_only_models():
    assert is_english_only_model("base.en")
    assert not is_english_only_model("small")


def test_gui_defaults_to_multilingual_model_from_source():
    # Not frozen -> no bundle -> multilingual default, Whisper's own cache.
    assert gui.default_gui_model() == "small"
    assert not is_english_only_model(gui.default_gui_model())
    assert gui.model_download_root("medium") is None


def test_frozen_app_uses_bundled_or_user_dir(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "models").mkdir(parents=True)
    (bundle / "models" / gui._model_filename("small")).write_bytes(b"x")
    monkeypatch.setattr(gui, "_bundle_base", lambda: bundle)
    user = tmp_path / "user_models"
    monkeypatch.setattr(gui, "user_models_dir", lambda: user)

    assert gui.default_gui_model() == "small"
    assert gui.model_download_root("small") == str(bundle / "models")
    assert gui.model_download_root("medium") == str(user)
    assert Path(user).is_dir()


def test_can_translate():
    assert gui.can_translate("small")
    assert gui.can_translate("medium")
    assert not gui.can_translate("base.en")
    assert not gui.can_translate("turbo")
