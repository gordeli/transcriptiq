# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Transcriptiq desktop app.

Run from the repository root:

    pyinstaller installers/pyinstaller/transcriptiq.spec

Expects two build assets (prepared by the CI workflow before this runs):
  * build_assets/models/base.en.pt   - the bundled Whisper model
  * build_assets/bin/ffmpeg[.exe]    - a standalone ffmpeg binary

Produces a one-folder app under dist/Transcriptiq (and Transcriptiq.app on macOS).
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all

# SPECPATH is injected by PyInstaller; entry.py lives next to this spec.
entry_script = os.path.join(SPECPATH, "entry.py")

# Build assets are staged at the repo root (two levels up from this spec).
# PyInstaller resolves relative data paths against SPECPATH, so anchor these
# to an absolute repo-root path to avoid "unable to find" errors.
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir, os.pardir))

datas = []
binaries = []
hiddenimports = []

# Whisper, its tokenizer assets, and PyTorch need their data files and dynamic
# libraries collected explicitly.
for pkg in ("whisper", "tiktoken", "tiktoken_ext", "torch"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Bundled Whisper model (works offline out of the box).
models_dir = os.path.join(REPO_ROOT, "build_assets", "models")
if os.path.isdir(models_dir):
    datas.append((models_dir, "models"))

# Bundled ffmpeg binary, placed at the bundle root so it lands on PATH at runtime.
bin_dir = os.path.join(REPO_ROOT, "build_assets", "bin")
if os.path.isdir(bin_dir):
    datas.append((bin_dir, "."))

a = Analysis(
    [entry_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter.test", "torch.test"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Transcriptiq",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Transcriptiq",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Transcriptiq.app",
        icon=None,
        bundle_identifier="com.gordeli.transcriptiq",
        info_plist={
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription": "Transcriptiq processes the audio files you select.",
        },
    )
