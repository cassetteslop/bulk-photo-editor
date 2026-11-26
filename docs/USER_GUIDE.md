# User guide

## Workflow
1. **Add photos** (drag and drop photos/folders onto the window, ⌘O), **Add folder** (⇧⌘O; sub-folders are included), drop a folder on the Dock icon, or use the Finder Quick Action.
2. Pick a photo in the list. ← / → moves between photos.
3. Adjust the tabs on the right. The centre shows the photo; switch **View**: *Edit* (crop box), *Result*, *Original*.
4. Choose an output folder in **Output**, then **Process all** (⌘E).

The list marks photos with ✎ (own levels) and ✂ (crop box adjusted by hand).

## Levels
- Choose the channel (RGB, R, G, B) and set **black point**, **midtones (gamma)** and **white point**; drag the triangles under the histogram or use the sliders.
- **Apply level changes to**: *All photos* edits the shared levels; *Only this photo* gives the current photo its own levels, leaving the others alone.
- *Auto* sets points from the histogram. *Copy to selected photos* pushes this photo's levels to the selection. *Make global* promotes them. *Drop this photo's custom levels* returns it to the shared levels.

## Crop (auto-crop)
- **Background type** - *Auto* picks per photo from its border: light (white/off-white/gray) or dark (brown/black/coloured). Force *Light* or *Dark* if needed. Each profile has its own **Tolerance** and **Ignore soft shadow**; the dark profile also follows lighting gradients and vignettes.
- The product is found at the centre of the photo; the crop ends where the product ends plus **padding**. Gray areas, lines and borders in the (white/off-white) background are kept out of the crop.
- **Crop size adjust** makes every auto-crop x % bigger or smaller (percent of the photo).
- **Tolerance** - how far from the background colour counts as "not background"; lower catches fainter shadows/lines.
- **Ignore soft shadow** - leaves pale shadows out (may cut very light gray parts of a product).
- **Aspect** presets lock the box ratio; **Add background to keep the product centred** extends the canvas with the background colour instead of shifting the crop.
- Drag the box or its handles in *Edit* view. *Re-run auto-crop* resets one or all photos.

## Colour, Size, Mark, Output
- **Colour**: brightness, contrast, saturation, sharpness, black & white, sepia. Rotate / flip buttons.
- **Size**: none, *Fit within* W×H (never upscales) or *Percent*.
- **Mark** (watermark): text and/or image. Image: *Choose image…* (PNG with transparency works best), width as % of the photo, shared opacity. Positions: bottom/top × left/centre/right, and centre.
- **Output**: folder, filename suffix (default `_edited`), JPEG/PNG/WEBP, quality. Existing files are never overwritten (`name_1.jpg`, …).

## Viewing
Mouse wheel / ⌘+ ⌘− zoom, drag (or right/middle drag) pans, ⌘0 fits, ⌘1 is 100 %. **Grid** overlays thirds, 4×4 or 8×8 on the crop (or the whole photo).

## Limits to know about
- Auto-crop is tuned for products on white/off-white backgrounds; busy backgrounds need a manual box.
- Gray regions touching a product can be included in the crop.
- The preview uses a reduced-size copy for speed; exports use the full-resolution original.
