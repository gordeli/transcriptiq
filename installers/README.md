# Transcriptiq desktop app

The desktop app is a small tkinter window around the Transcriptiq library:
pick files or a folder, choose a Whisper model, optionally add timestamps, and
transcribe. There are **two ways** to get it onto a Mac or Windows machine.

---

## Option A — Slim installer (small download, sets up on first run)

A short script creates an isolated Python environment, installs Transcriptiq
(and Whisper/PyTorch) into it, makes sure `ffmpeg` is present, and adds
shortcuts. The first install needs an internet connection; after that it runs
locally. Whisper models download the first time each is used.

### Windows — step by step
1. Download [`installers/slim/install-windows.ps1`](slim/install-windows.ps1)
   from the repo.
2. Right-click it → **Run with PowerShell** (or, in a PowerShell window):
   ```powershell
   powershell -ExecutionPolicy Bypass -File install-windows.ps1
   ```
3. The script will, as needed:
   - install Python 3.12 and ffmpeg via `winget`,
   - create a venv at `%LOCALAPPDATA%\Transcriptiq\venv`,
   - `pip install` Transcriptiq from GitHub,
   - add **Start Menu** and **Desktop** shortcuts.
4. Launch **Transcriptiq** from the Start Menu or Desktop.

### macOS — step by step
1. Download [`installers/slim/install-macos.sh`](slim/install-macos.sh).
2. In Terminal:
   ```bash
   chmod +x install-macos.sh
   ./install-macos.sh
   ```
3. The script will, as needed:
   - install Python and ffmpeg via [Homebrew](https://brew.sh),
   - create a venv under `~/Library/Application Support/Transcriptiq/venv`,
   - `pip install` Transcriptiq from GitHub,
   - create a launcher at `/Applications/Transcriptiq.command`.
4. Launch it from **/Applications/Transcriptiq.command** (first launch:
   right-click → **Open** to bypass Gatekeeper).

> **Updating:** re-run the same script — it upgrades the existing install.

---

## Option B — Bundled installers (self-contained, built by CI)

These are full one-click installers that bundle Python, PyTorch, Whisper, a
standalone **ffmpeg**, and the **base.en** model — so they work offline with no
prerequisites. They're built automatically by GitHub Actions on real Windows and
macOS runners (PyInstaller can't cross-compile, so each OS is built on its own
runner). Download size is larger (~1–3 GB depending on platform).

### How to produce them — step by step
1. Push the code to GitHub (already done for the main library).
2. Go to the repo's **Actions** tab → **Build desktop installers** →
   **Run workflow** (the `workflow_dispatch` trigger). The matrix builds:
   - **Windows** → `Transcriptiq-Setup.exe` (Inno Setup installer),
   - **macOS Apple Silicon** (`macos-14`) → `Transcriptiq-macOS-AppleSilicon.dmg`.

   > Intel Macs aren't built by default — GitHub's Intel `macos-13` runners are
   > being retired and were unavailable. The Apple Silicon `.dmg` runs on Intel
   > Macs too if Rosetta 2 is installed; to build a native Intel binary, add
   > `- os: macos-13` back to the matrix.
3. When the run finishes, download the installers from the run's **Artifacts**.
4. To publish them for end users, push a version tag — the same workflow then
   attaches all three installers to a **GitHub Release**:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

### What the build does (for reference)
- Sets up Python 3.11 and ffmpeg on the runner.
- Downloads the `base.en` model into `build_assets/models/` and copies the
  `ffmpeg` binary into `build_assets/bin/`.
- Runs PyInstaller against
  [`pyinstaller/transcriptiq.spec`](pyinstaller/transcriptiq.spec), which
  collects Whisper/PyTorch data and bundles the staged model + ffmpeg.
- Packages the result: Inno Setup `.exe` on Windows, `hdiutil` `.dmg` on macOS.

### Installing the bundled apps — for end users
- **Windows:** run `Transcriptiq-Setup.exe` and follow the wizard. Launch from
  the Start Menu / Desktop shortcut.
- **macOS:** open the `.dmg`, drag **Transcriptiq** to **Applications**. On first
  launch, right-click the app → **Open** (the build is unsigned, so Gatekeeper
  asks for confirmation once).

> **Code signing / notarization** is not set up, so macOS shows an
> "unidentified developer" prompt on first launch. To distribute without that
> prompt, add an Apple Developer ID certificate and a notarization step to the
> workflow.

---

## Building locally (advanced)

You can run the PyInstaller build yourself on your own machine:

```bash
pip install pyinstaller .
# stage assets the spec expects:
python -c "import whisper; whisper.load_model('base.en', download_root='build_assets/models')"
# copy an ffmpeg binary into build_assets/bin/ (platform-specific)
pyinstaller --noconfirm installers/pyinstaller/transcriptiq.spec
# -> dist/Transcriptiq/ (Windows/Linux) or dist/Transcriptiq.app (macOS)
```
