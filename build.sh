#!/usr/bin/env sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/python" -m pip install -r "$PROJECT_DIR/requirements-build.txt"
"$PROJECT_DIR/.venv/bin/python" -m PyInstaller --noconfirm --clean "$PROJECT_DIR/Memocan.spec"
echo "Paket hazır: $PROJECT_DIR/dist/"
