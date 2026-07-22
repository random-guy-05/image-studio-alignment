#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This project currently requires macOS for ImageStudio automation." >&2
  exit 1
fi

command -v "$PYTHON" >/dev/null || {
  echo "Python 3 was not found. Install Python 3 and rerun ./install.sh." >&2
  exit 1
}

"$PYTHON" -m venv "$ROOT_DIR/.venv"
"$ROOT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$ROOT_DIR/.venv/bin/python" -m pip install -r "$ROOT_DIR/requirements.txt"

chmod +x "$ROOT_DIR/image_studio.py"
chmod +x "$ROOT_DIR/install.sh"

echo
echo "Installed. Use:"
echo "  $ROOT_DIR/image_studio.py --help"
echo "  $ROOT_DIR/image_studio.py detect"
