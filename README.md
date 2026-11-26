# Bulk Photo Editor

A desktop app for editing a whole set of product photos at once: per-channel **Levels**, smart **auto-crop**
for products on white backgrounds, colour tweaks, rotate/flip, resize, **text and image watermarks**, and
batch export. Dark, macOS-native look. Originals are never modified.

![icon](packaging/BulkPhotoEditor.png)

## Quick start

```bash
pip install -r requirements.txt          # Pillow + numpy
python run.py                            # or: python run.py ~/Pictures/shoot-1 photo.jpg
```

Needs Python 3.9+ with Tk (python.org installers include it; Homebrew: `brew install python-tk`).

### On a Mac (recommended extras)

```bash
pip install -r requirements-macos.txt     # adds pyobjc (forces Dark Aqua) and py2app
./packaging/build_mac_app.sh --install    # builds "Bulk Photo Editor.app", installs it + the Finder Quick Action
```

See [docs/PACKAGING.md](docs/PACKAGING.md) for the `.app`, `.dmg` and Quick Action details, and [INSTALL.md](INSTALL.md) for Windows and all other install routes.

## Features

| Area | What it does |
|------|--------------|
| Levels | RGB / R / G / B black point, gamma, white point, with histogram; apply to all photos or one photo only |
| Auto-crop | **Light and dark (brown/black) backdrops**, Auto/Light/Dark profiles with separate settings; finds the product in the centre, ignores gray areas/lines in the white background, keeps it centred; drag the box per photo; aspect ratios; "make all crops x% bigger/smaller" |
| Viewing | Grid overlay, zoom (wheel, ⌘+ / ⌘−, ⌘0 fit, ⌘1 100 %), pan, Edit / Result / Original views |
| Colour | Brightness, contrast, saturation, sharpness, B&W, sepia |
| Size | Fit-within or percentage resize (never upscales in fit mode) |
| Watermark | Text and/or **image** (transparent PNG supported), 7 positions incl. top/bottom **centre**, opacity, size |
| Output | JPEG / PNG / WEBP, quality, filename suffix, never overwrites, multi-threaded, cancellable |
| Opening photos | **Drag and drop** photos/folders, Add files/folder, command line, Finder Quick Action (Mac), Explorer right-click (Windows) |
| Platforms | macOS (native look, Dark Mode, menu bar) and Windows (installer, portable zip) |

## Keyboard shortcuts

| Keys | Action |
|------|--------|
| ← / → | previous / next photo |
| ⌫ / Del | remove selected photo(s) from the list (files untouched) |
| ⌘O / ⇧⌘O | add photos / add folder |
| ⌘E | process all |
| ⌘+ ⌘− ⌘0 ⌘1 | zoom in / out / fit / 100 % (Ctrl on Windows & Linux) |
| ⌘[ ⌘] | rotate left / right |
| double-click a slider | reset it |

## Open a folder from Finder

Install the Quick Action (`./packaging/quick_action/install_quick_action.sh`), then right-click any folder →
**Quick Actions → Open in Bulk Photo Editor**. If the app is already running the photos are added to its list.
You can also drop folders/photos on the app's Dock icon, or run `open -a "Bulk Photo Editor" ~/Pictures/shoot`.

## Project layout

```
BulkPhotoEditor/
├── run.py                     launcher / py2app entry point
├── setup.py                   py2app configuration
├── requirements*.txt
├── photo_editor/
│   ├── core/                  image processing - no GUI imports, usable as a library
│   │   ├── constants.py  levels.py  geometry.py
│   │   ├── detection.py  cropping.py          product detection and crop maths
│   │   ├── image_ops.py  watermark.py  pipeline.py  loader.py
│   │   ├── photo.py                           per-photo state
│   │   └── batch.py                           BatchExporter (thread pool)
│   └── ui/                    Tkinter interface
│       ├── app.py             App window = composition of the mixins below
│       ├── theme.py  macos.py  menu.py
│       ├── panels.py  keys.py  files.py  levels_panel.py  edit_state.py  viewer.py  export.py
├── packaging/                 build_mac_app.sh, icon, Finder Quick Action
├── tests/                     headless test-suite (no display needed)
└── docs/                      USER_GUIDE.md, ARCHITECTURE.md, PACKAGING.md
```

## Tests

```bash
python tests/run_all.py
```

The tests run without a display (a tiny fake `tkinter` is used) and use synthetic product photos.

## Documentation

- **[BulkPhotoEditor-QuickStart.pdf](BulkPhotoEditor-QuickStart.pdf)** - 4-page quick start
- [INSTALL.md](INSTALL.md) - Windows installer, portable, from source, macOS
- [User guide](docs/USER_GUIDE.md) - every tab and control
- [Architecture](docs/ARCHITECTURE.md) - how the code is organised and how to extend it
- [Packaging](docs/PACKAGING.md) - `.app`, `.dmg`, code signing, Quick Action, troubleshooting
