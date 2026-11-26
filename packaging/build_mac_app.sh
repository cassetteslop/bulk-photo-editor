#!/usr/bin/env bash
# Build "Bulk Photo Editor.app" (and optionally a .dmg) on a Mac.
#   ./packaging/build_mac_app.sh            -> dist/Bulk Photo Editor.app
#   ./packaging/build_mac_app.sh --dmg      -> also dist/BulkPhotoEditor-<version>.dmg
#   ./packaging/build_mac_app.sh --install  -> also copy the app to /Applications and install the Quick Action
#   PYTHON=/path/to/python3 ./packaging/build_mac_app.sh     (default: python3 on PATH)
set -euo pipefail

[[ "$(uname)" == "Darwin" ]] || { echo "This script must be run on macOS."; exit 1; }
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
APP_NAME="Bulk Photo Editor"
VERSION="$("$PY" -c 'import re;print(re.search(r"__version__ = \"([^\"]+)\"",open("photo_editor/__init__.py").read()).group(1))')"

"$PY" -c "import tkinter" 2>/dev/null || {
  echo "This Python has no Tk. Use the python.org installer (https://www.python.org/downloads/macos/)"
  echo "or: brew install python-tk"; exit 1; }

echo "==> virtual environment (.build-venv)"
"$PY" -m venv .build-venv
source .build-venv/bin/activate
pip install --upgrade pip wheel setuptools >/dev/null
pip install -r requirements-macos.txt

echo "==> icon"
[[ -f packaging/BulkPhotoEditor.icns ]] || python packaging/make_icon.py

echo "==> py2app"
rm -rf build dist
python setup.py py2app

APP="dist/${APP_NAME}.app"
echo "==> ad-hoc code signature (lets it run on this Mac; see docs/PACKAGING.md for distributing)"
codesign --force --deep --sign - "$APP" || echo "codesign failed (the app may still run locally)"

if [[ " $* " == *" --dmg "* ]]; then
  echo "==> disk image"
  STAGE="$(mktemp -d)"
  cp -R "$APP" "$STAGE/"
  ln -s /Applications "$STAGE/Applications"
  hdiutil create -volname "$APP_NAME" -srcfolder "$STAGE" -ov -format UDZO "dist/BulkPhotoEditor-${VERSION}.dmg"
  rm -rf "$STAGE"
fi

if [[ " $* " == *" --install "* ]]; then
  echo "==> installing to /Applications"
  rm -rf "/Applications/${APP_NAME}.app"
  cp -R "$APP" /Applications/
  ./packaging/quick_action/install_quick_action.sh
fi

echo
echo "Done: $APP"
