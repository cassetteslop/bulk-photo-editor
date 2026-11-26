# Architecture

```
core/  (pure Python, Pillow + numpy)          ui/  (Tkinter)
  constants ─┐                                  app.App  ◀── composes mixins
  levels     │                                   ├─ PanelsMixin     window layout, tool tabs
  geometry   │                                   ├─ MenuMixin       menu bar, shortcuts
  detection ─┼─▶ cropping ─┐                     ├─ KeyboardMixin   arrows / delete / zoom keys
  image_ops ─┤             ├─▶ pipeline ─▶ batch ├─ FileListMixin   add/remove/open_paths/select
  watermark ─┘  loader     │                     ├─ LevelsMixin     levels logic + histogram
  photo ──────────────────-┘                     ├─ EditStateMixin  rotate/flip, settings(), crop detect
                                                 ├─ ViewerMixin     zoom, pan, grid, crop-box editing
                                                 └─ ExportMixin     drives core.batch.BatchExporter
  ui/theme.py   Theme + Palette (native Aqua dark on Mac, styled "clam" elsewhere)
  ui/macos.py   pyobjc / Apple-event hooks (no-ops off macOS)
```

**Rule:** `core` never imports `tkinter`. It can be used from scripts:

```python
from PIL import Image
from photo_editor.core.constants import DEFAULTS
from photo_editor.core.levels import Levels
from photo_editor.core.pipeline import process_image, save_image

s = dict(DEFAULTS, rotate=0, flip_h=False, flip_v=False, wm_text="© Me")
out = process_image(Image.open("in.jpg"), s, Levels())
save_image(out, "out.jpg", "JPEG", 90)
```

## Data flow
`settings()` (EditStateMixin) snapshots every Tk variable into a plain dict `s` (keys of `DEFAULTS` plus rotate/flip).
`process_image(img, s, levels, crop, bg, prod, obst)` runs: `oriented` → (`detect_product` → `compute_crop` → `crop_pad`) →
`tone_adjust` (levels, colour) → `finish` (resize, `apply_watermark`, alpha).

- **Preview**: `ViewerMixin.result_image` caches the processed preview, keyed on the settings dict, levels, crop and photo.
- **Export**: `ExportMixin.run_batch` snapshots `ExportJob`s (path, levels copy, crop, bg, product, keep-out map), and `BatchExporter`
  runs them on a thread pool, posting `("item", name, error)` / `("done", dir)` to a queue that the UI polls. Workers never touch Tk.

## Adding a setting
1. Add a key + default to `core/constants.py: DEFAULTS` (type decides the Tk variable: bool → BooleanVar, int → IntVar, else StringVar).
2. Use it in the pipeline (`core/…`), reading `s["key"]`.
3. Add a control in `ui/panels.py` (`self.slider(...)`, `self.combo(...)`, …). Every variable change already schedules a preview refresh;
   crop-related keys are listed in `App.__init__` to invalidate crops instead.

## Theming
`Theme.install()` returns a `Palette`. On macOS it selects the native `aqua` theme and asks AppKit (via optional pyobjc) for Dark Aqua;
if the resulting window colour is not dark it falls back to the hand-styled dark `clam` theme so the UI is never half-light.
Plain Tk widgets (canvas, listbox) read colours from `self.palette`; secondary text uses the `Hint.TLabel` style.

## Tests
`tests/support/faketk.py` replaces `tkinter` with a recording stub, `tests/support/gen.py` renders synthetic product photos with known
bounding boxes, `tests/support/legacy.py` exposes the whole package as one namespace (`b`) for the scripts.
