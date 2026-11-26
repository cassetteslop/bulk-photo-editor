"""Text and image watermarks."""

import os
import threading
from PIL import Image, ImageDraw, ImageFont, ImageOps

def get_font(size):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


_WM_CACHE = {}
_WM_LOCK = threading.Lock()


def load_watermark(path):
    """Load a watermark image as RGBA (cached by path + mtime). None if unset/unreadable."""
    if not path:
        return None
    try:
        key = (path, os.path.getmtime(path))
    except OSError:
        return None
    with _WM_LOCK:
        if key in _WM_CACHE:
            return _WM_CACHE[key]
        try:
            with Image.open(path) as im:
                im = ImageOps.exif_transpose(im).convert("RGBA")
        except Exception:
            im = None
        _WM_CACHE.clear()
        _WM_CACHE[key] = im
        return im


def apply_watermark(rgb, s):
    """Draw the image and/or text watermark described by settings `s`."""
    text = s["wm_text"].strip()
    wm_img = load_watermark(s["wm_image"])
    if text or wm_img is not None:
        base = rgb.convert("RGBA")
        W, H = base.size
        pos = s["wm_pos"]
        a = int(255 * s["wm_opacity"] / 100)

        def place(w, h, m):
            x = m if "left" in pos else (W - w - m if "right" in pos else (W - w) // 2)
            y = m if "Top" in pos else (H - h - m if "Bottom" in pos else (H - h) // 2)
            return x, y

        if wm_img is not None:
            w = max(4, int(W * s["wm_img_size"] / 100))
            h = max(1, round(wm_img.height * w / wm_img.width))
            if h > H:                      # never taller than the photo
                h = H
                w = max(1, round(wm_img.width * h / wm_img.height))
            mark = wm_img.resize((w, h), Image.Resampling.LANCZOS)
            mark.putalpha(mark.getchannel("A").point(lambda v: v * a // 255))
            x, y = place(w, h, int(min(W, H) * 0.02))
            base.alpha_composite(mark, (max(0, x), max(0, y)))

        if text:
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(overlay)
            fs = max(10, int(H * s["wm_size"] / 100))
            font = get_font(fs)
            bb = d.textbbox((0, 0), text, font=font)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            x, y = place(tw, th, int(fs * 0.6))
            off = max(1, fs // 24)
            d.text((x - bb[0] + off, y - bb[1] + off), text, font=font, fill=(0, 0, 0, a // 2))
            d.text((x - bb[0], y - bb[1]), text, font=font, fill=(255, 255, 255, a))
            base = Image.alpha_composite(base, overlay)
        rgb = base.convert("RGB")
    return rgb
