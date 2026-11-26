# Packaging (macOS and Windows)

Windows: see [INSTALL.md](../INSTALL.md) (installer, portable zip, one-click-from-source) and `packaging/windows/`.

# Packaging for macOS

> Building must happen **on a Mac** (py2app cannot cross-compile). The scripts here were written without access to a Mac,
> so treat the first build as something to verify; the troubleshooting section lists the usual snags.

## 1. Build the app
Requirements: macOS 11+, a Python **with Tk** (python.org installer recommended; Homebrew: `brew install python-tk`), Xcode command-line tools.

```bash
./packaging/build_mac_app.sh              # -> dist/Bulk Photo Editor.app
./packaging/build_mac_app.sh --dmg        # also dist/BulkPhotoEditor-<version>.dmg
./packaging/build_mac_app.sh --install    # copy to /Applications and install the Quick Action
```

The script creates `.build-venv`, installs `requirements-macos.txt` (Pillow, numpy, pyobjc-Cocoa, py2app), runs
`python setup.py py2app`, applies an ad-hoc signature (`codesign -s -`) and optionally builds the `.dmg`.
`setup.py` registers the app for images and folders (`CFBundleDocumentTypes`) so Finder/Dock drops arrive as `::tk::mac::OpenDocument` events.

Quick dev loop without building: `python setup.py py2app -A` (alias mode) or just `python run.py`.

## 2. Finder Quick Action ("Open in Bulk Photo Editor")
```bash
./packaging/quick_action/install_quick_action.sh           # install into ~/Library/Services
./packaging/quick_action/install_quick_action.sh --remove  # uninstall
```
Right-click a folder → **Quick Actions → Open in Bulk Photo Editor**. The action runs `open -a "Bulk Photo Editor" <folder>` (the running
app adds the photos to its list); if the app is not installed it falls back to `python3 run.py <folder>` from this repository.
If it does not show up: *System Settings → Keyboard → Keyboard Shortcuts → Services → Files and Folders* and tick it.

**Manual alternative** (if you prefer to build it in Automator): New Document → *Quick Action* → "Workflow receives current **folders** in **Finder**" →
add *Run Shell Script* (Shell `/bin/zsh`, *Pass input* **as arguments**) with
`for f in "$@"; do open -a "Bulk Photo Editor" "$f"; done` → save as *Open in Bulk Photo Editor*.

## 3. Sharing the app with other people
An ad-hoc signed app runs on the Mac that built it. For other Macs either (a) right-click → Open the first time and approve it in
*System Settings → Privacy & Security*, or (b) sign with a Developer ID and notarise:
```bash
codesign --force --deep --options runtime --sign "Developer ID Application: YOUR NAME (TEAMID)" "dist/Bulk Photo Editor.app"
ditto -c -k --keepParent "dist/Bulk Photo Editor.app" app.zip
xcrun notarytool submit app.zip --keychain-profile "notary" --wait
xcrun stapler staple "dist/Bulk Photo Editor.app"
```

## Troubleshooting
| Symptom | Fix |
|---------|-----|
| `No module named _tkinter` | Use python.org Python or `brew install python-tk` matching your Python version |
| App opens but is light, not dark | Install pyobjc (`pip install pyobjc-framework-Cocoa`) - without it the app falls back to its own dark theme, which is still dark but not native |
| Menu bar says "Python" when run from source | Same: needs pyobjc; the built `.app` shows the right name regardless |
| Folder dropped on the Dock icon does nothing | The app must be the built `.app` (document types come from its Info.plist) |
| py2app "ImportError: No module named …" | Add the module to `packages`/`includes` in `setup.py` |
| Quick Action missing in Finder | Enable it under Keyboard → Services (see above); log out/in or `killall Finder` |
| App is huge | Normal (~100–150 MB with numpy, Pillow, Tk); `excludes` in `setup.py` already trims common extras |

## Icon
`python packaging/make_icon.py` regenerates `BulkPhotoEditor.icns` (Pillow only). Replace it with your own artwork any time.

# Packaging for Windows

Files in `packaging/windows/`: `BulkPhotoEditor.spec` (PyInstaller, windowed, one folder), `installer.iss` (Inno Setup 6), `build_windows.bat`
(does everything), `install_from_source.bat` / `uninstall_from_source.bat` / `create_shortcuts.ps1` (no-build install), `BulkPhotoEditor.ico`.

* `build_windows.bat` -> venv -> `pip install -r requirements-windows.txt` -> `pyinstaller` -> portable zip -> `ISCC.exe` (if found).
* The installer is per-user by default (no admin) and can add *Open in Bulk Photo Editor* to Explorer's right-click menu for folders, folder
  backgrounds and image files (registry keys under `Software\Classes`, removed on uninstall). Each Explorer verb starts the app with the path
  as `argv[1]`, which `run.py` forwards to `App(initial_paths=...)`.
* `tkinterdnd2` ships the native tkdnd DLLs; the spec collects them as package data. If they fail to load the app falls back to `PlainApp`.
* `photo_editor/ui/platform_win.py` makes the process DPI-aware and sets the taskbar identity.
* These scripts were written without access to a Windows machine - the first build is the real test (see INSTALL.md troubleshooting).
