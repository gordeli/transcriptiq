#!/usr/bin/env bash
#
# Slim installer for Transcriptiq on macOS.
#
# Creates a self-contained Python virtual environment under
# ~/Library/Application Support/Transcriptiq, installs Transcriptiq (and
# Whisper) into it, ensures ffmpeg is present (via Homebrew), and drops a
# double-clickable launcher in /Applications. Small download; dependencies are
# fetched on first run.
#
# Usage:
#   chmod +x install-macos.sh && ./install-macos.sh
#
set -euo pipefail

APP_NAME="Transcriptiq"
INSTALL_DIR="$HOME/Library/Application Support/$APP_NAME"
VENV_DIR="$INSTALL_DIR/venv"
PY="$VENV_DIR/bin/python"
GUI="$VENV_DIR/bin/transcriptiq-gui"
PACKAGE="git+https://github.com/gordeli/transcriptiq.git"
LAUNCHER="/Applications/$APP_NAME.command"

echo "=== Installing $APP_NAME ==="

# 1. Ensure Python 3 --------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 not found."
  if command -v brew >/dev/null 2>&1; then
    echo "Installing Python via Homebrew..."
    brew install python
  else
    echo "Please install Python 3 from https://www.python.org/downloads/ and re-run."
    exit 1
  fi
fi
echo "Using Python: $(command -v python3)"

# 2. Ensure ffmpeg ----------------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "Installing ffmpeg via Homebrew..."
    brew install ffmpeg
  else
    echo "WARNING: ffmpeg not found and Homebrew is unavailable."
    echo "Install Homebrew (https://brew.sh) then run: brew install ffmpeg"
  fi
fi

# 3. Create venv and install ------------------------------------------------
mkdir -p "$INSTALL_DIR"
if [ ! -x "$PY" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
fi
echo "Installing Transcriptiq (this downloads PyTorch + Whisper)..."
"$PY" -m pip install --upgrade pip --quiet
"$PY" -m pip install --upgrade "$PACKAGE"

# 4. Create a double-clickable launcher -------------------------------------
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
exec "$GUI"
EOF
chmod +x "$LAUNCHER"

echo ""
echo "=== $APP_NAME installed! ==="
echo "Launch it from /Applications/$APP_NAME.command, or run:"
echo "    $GUI"
