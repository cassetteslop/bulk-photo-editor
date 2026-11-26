"""The full per-photo pipeline: orient -> crop -> tone -> resize -> watermark -> save."""

from PIL import Image

from photo_editor.core.cropping import compute_crop
from photo_editor.core.detection import detect_for_settings, tolerance_for_bg
from photo_editor.core.image_ops import crop_pad, luminance_mean, oriented, tone_adjust
from photo_editor.core.watermark import apply_watermark

def finish(rgb, alpha, s, preview=False):
    """Resize + watermark + re-attach alpha."""
    if not preview and s["resize_mode"] != "None":
        w, h = rgb.size
        if s["resize_mode"] == "Fit within":
            ratio = min(s["max_w"] / w, s["max_h"] / h, 1.0)  # never upscale
        else:
            ratio = max(s["percent"], 1) / 100
        if abs(ratio - 1) > 1e-6:
            size = (max(1, round(w * ratio)), max(1, round(h * ratio)))
            rgb = rgb.resize(size, Image.Resampling.LANCZOS)
            alpha = alpha.resize(size, Image.Resampling.LANCZOS) if alpha else None

    rgb = apply_watermark(rgb, s)

    if alpha is not None:
        rgb = rgb.convert("RGBA")
        rgb.putalpha(alpha)
    return rgb


def process_image(img, s, lv, crop=None, bg=(255, 255, 255), prod=None, obst=None, preview=False):
    """
    Full pipeline: orient -> crop -> levels/colour -> resize -> watermark.
    If cropping is on and `crop` is None, the product is detected (or `prod`/`obst` reused).
    """
    rgb, alpha = oriented(img, s)
    ref = luminance_mean(rgb, lv) if s["contrast"] else None
    if s["crop_enabled"]:
        if crop is None:
            if prod is None:
                det = detect_for_settings(rgb, s)
                prod, obst = det.prod, det.obst
                if prod:
                    bg = det.bg
            if prod:
                crop = compute_crop(prod, rgb.size, s["padding"], s["aspect"], s["extend"], obst, s["grow"])
        if crop is not None:
            rgb, alpha = crop_pad(rgb, alpha, crop, bg, tol=tolerance_for_bg(bg, s))
    rgb = tone_adjust(rgb, s, lv, ref)
    return finish(rgb, alpha, s, preview)


def save_image(img, path, fmt, quality):
    if fmt == "JPEG":
        if img.mode == "RGBA":  # flatten transparency onto white
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.getchannel("A"))
            img = bg
        img.save(path, "JPEG", quality=quality, optimize=True)
    elif fmt == "PNG":
        img.save(path, "PNG", optimize=True)
    else:
        img.save(path, "WEBP", quality=quality)
