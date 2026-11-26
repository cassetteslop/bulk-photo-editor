"""Orientation, tone/colour adjustments and crop-with-padding."""

import math
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageStat

from photo_editor.core.constants import ROT

def oriented(img, s):
    """EXIF-transpose, then apply the user's rotate/flip. Returns (rgb, alpha_or_None)."""
    img = ImageOps.exif_transpose(img)
    alpha = None
    if "A" in img.getbands() or "transparency" in img.info:
        rgba = img.convert("RGBA")
        alpha = rgba.getchannel("A")
        rgb = rgba.convert("RGB")
    else:
        rgb = img.convert("RGB")
    op = ROT.get(s["rotate"])
    if op is not None:
        rgb = rgb.transpose(op)
        alpha = alpha.transpose(op) if alpha else None
    if s["flip_h"]:
        rgb = ImageOps.mirror(rgb)
        alpha = ImageOps.mirror(alpha) if alpha else None
    if s["flip_v"]:
        rgb = ImageOps.flip(rgb)
        alpha = ImageOps.flip(alpha) if alpha else None
    return rgb, alpha


def luminance_mean(rgb, lv=None):
    """Mean brightness of the (levels-adjusted) whole photo - the pivot for Contrast."""
    small = rgb
    f = max(rgb.size) // 512
    if f > 1:
        small = rgb.reduce(f)
    if lv is not None and not lv.is_identity():
        small = small.point(lv.luts())
    return ImageStat.Stat(small.convert("L")).mean[0]


def tone_adjust(rgb, s, lv=None, ref=None):
    """Levels, then brightness / contrast / saturation / sharpness, then B&W / sepia.
    `ref` = mean brightness of the whole photo so that cropped / zoomed pieces match."""
    if lv is not None and not lv.is_identity():
        rgb = rgb.point(lv.luts())
    if s["brightness"]:
        fb = 1 + s["brightness"] / 100
        rgb = ImageEnhance.Brightness(rgb).enhance(fb)
        if ref is not None:
            ref = min(255.0, ref * fb)
    if s["contrast"]:
        mean = ref if ref is not None else ImageStat.Stat(rgb.convert("L")).mean[0]
        m = int(mean + 0.5)
        fc = 1 + s["contrast"] / 100
        lut = [min(255, max(0, int(m + fc * (x - m) + 0.5))) for x in range(256)]
        rgb = rgb.point(lut * 3)
    if s["saturation"]:
        rgb = ImageEnhance.Color(rgb).enhance(1 + s["saturation"] / 100)
    if s["sharpness"]:
        rgb = ImageEnhance.Sharpness(rgb).enhance(1 + s["sharpness"] / 100)
    if s["grayscale"]:
        rgb = ImageOps.grayscale(rgb).convert("RGB")
    elif s["sepia"]:
        g = ImageOps.grayscale(rgb)
        rgb = ImageOps.colorize(g, black="#1f1208", white="#fff1d6", mid="#a98055")
    return rgb


def clean_edges(rgb, bg, sides, tol):
    """
    Along photo edges that the crop extends past, repaint background-like pixels
    (within `tol` of `bg`) with the pure background colour. Removes faint edge
    artefacts; product pixels are untouched.
    """
    a = np.array(rgb)
    h, w = a.shape[:2]
    strip = max(4, int(min(h, w) * 0.01))
    bgv = np.array(bg, dtype=np.int16)
    views = {"left": a[:, :strip], "right": a[:, w - strip:], "top": a[:strip], "bottom": a[h - strip:]}
    for side in sides:
        v = views[side]
        near = np.abs(v.astype(np.int16) - bgv).max(axis=2) <= tol
        v[near] = bg
    return Image.fromarray(a)


def crop_pad(rgb, alpha, rect, bg, tol=None):
    """Crop to a normalised rect; any part outside the photo is filled with `bg`."""
    W, H = rgb.size
    x0 = math.floor(rect[0] * W + 1e-6)
    y0 = math.floor(rect[1] * H + 1e-6)
    x1 = math.ceil(rect[2] * W - 1e-6)
    y1 = math.ceil(rect[3] * H - 1e-6)
    if x1 - x0 < 1 or y1 - y0 < 1:
        return rgb, alpha
    if x0 >= 0 and y0 >= 0 and x1 <= W and y1 <= H:
        box = (x0, y0, x1, y1)
        return rgb.crop(box), (alpha.crop(box) if alpha else None)
    if tol:
        sides = [n for n, out_ in (("left", x0 < 0), ("top", y0 < 0), ("right", x1 > W), ("bottom", y1 > H)) if out_]
        rgb = clean_edges(rgb, bg, sides, tol)
    out = Image.new("RGB", (x1 - x0, y1 - y0), tuple(bg))
    out.paste(rgb, (-x0, -y0))
    a2 = None
    if alpha:
        a2 = Image.new("L", out.size, 0)
        a2.paste(alpha, (-x0, -y0))
    return out, a2
