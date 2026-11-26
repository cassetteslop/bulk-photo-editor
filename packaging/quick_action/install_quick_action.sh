#!/usr/bin/env bash
# Install the Finder Quick Action "Open in Bulk Photo Editor" (right-click a folder > Quick Actions).
#   ./packaging/quick_action/install_quick_action.sh            install
#   ./packaging/quick_action/install_quick_action.sh --remove   uninstall
set -euo pipefail

[[ "$(uname)" == "Darwin" ]] || { echo "This script must be run on macOS."; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
NAME="Open in Bulk Photo Editor"
DEST="$HOME/Library/Services/${NAME}.workflow"

if [[ "${1:-}" == "--remove" ]]; then
  rm -rf "$DEST"
  /System/Library/CoreServices/pbs -flush 2>/dev/null || true
  echo "Removed $DEST"; exit 0
fi

mkdir -p "$HOME/Library/Services"
rm -rf "$DEST"
cp -R "$HERE/${NAME}.workflow" "$DEST"
# fallback used when the app is not installed: run from source in this repo
/usr/bin/sed -i '' "s|__REPO_PATH__|${REPO}|g" "$DEST/Contents/document.wflow"
/usr/bin/plutil -lint "$DEST/Contents/document.wflow" "$DEST/Contents/Info.plist"

/System/Library/CoreServices/pbs -flush 2>/dev/null || true
/System/Library/CoreServices/pbs -update 2>/dev/null || true
echo "Installed: $DEST"
echo
echo "Use it: in Finder, right-click (or Control-click) a folder > Quick Actions > '${NAME}'."
echo "If it is not listed: System Settings > Keyboard > Keyboard Shortcuts > Services > Files and Folders,"
echo "tick '${NAME}'  (macOS 12 and older: System Preferences > Extensions > Finder)."
