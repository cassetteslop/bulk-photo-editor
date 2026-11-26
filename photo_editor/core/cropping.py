"""Turn a detected product box into a crop rectangle (padding, aspect, grow)."""

import math

from photo_editor.core.geometry import aspect_ratio

def _fit_1d(lo, hi, limit):
    if hi - lo >= limit:
        return 0.0, float(limit)
    if lo < 0:
        hi -= lo
        lo = 0.0
    if hi > limit:
        lo -= hi - limit
        hi = float(limit)
    return lo, hi


def _raw_crop(prod, size, padding, aspect, extend):
    W, H = size
    bx0, by0, bx1, by1 = prod[0] * W, prod[1] * H, prod[2] * W, prod[3] * H
    bw, bh = max(bx1 - bx0, 1.0), max(by1 - by0, 1.0)
    pad = padding / 100.0 * max(bw, bh)
    cw, ch = bw + 2 * pad, bh + 2 * pad
    r = aspect_ratio(aspect, size)
    if r:
        if cw / ch < r:
            cw = ch * r
        else:
            ch = cw / r
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    x0, x1 = cx - cw / 2, cx + cw / 2
    y0, y1 = cy - ch / 2, cy + ch / 2
    if not extend:
        x0, x1 = _fit_1d(x0, x1, W)
        y0, y1 = _fit_1d(y0, y1, H)
    return (x0 / W, y0 / H, x1 / W, y1 / H)


def _cells_inside(c, g):
    """Index ranges of grid cells whose centres lie inside normalised box c."""
    x0 = max(0, int(math.ceil(c[0] * g - 0.5)))
    x1 = min(g, int(math.floor(c[2] * g - 0.5)) + 1)
    y0 = max(0, int(math.ceil(c[1] * g - 0.5)))
    y1 = min(g, int(math.floor(c[3] * g - 0.5)) + 1)
    return x0, y0, max(x0, x1), max(y0, y1)


def apply_grow(box, size, grow, aspect, extend):
    """
    Make a crop box bigger (grow > 0) or smaller (grow < 0) around its centre by `grow` % of
    the photo: the width changes by grow % of the photo's width and the height by grow % of
    its height. With a fixed aspect ratio the width decides and the height follows it.
    """
    if not grow:
        return box
    W, H = size
    x0, y0, x1, y1 = box[0] * W, box[1] * H, box[2] * W, box[3] * H
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    g = grow / 100.0
    cw = max((x1 - x0) + g * W, 0.02 * W)
    ch = max((y1 - y0) + g * H, 0.02 * H)
    r = aspect_ratio(aspect, size)
    if r:
        ch = max(cw / r, 0.02 * H)
        cw = ch * r
    x0, x1 = cx - cw / 2, cx + cw / 2
    y0, y1 = cy - ch / 2, cy + ch / 2
    if not extend:
        x0, x1 = _fit_1d(x0, x1, W)
        y0, y1 = _fit_1d(y0, y1, H)
    return (x0 / W, y0 / H, x1 / W, y1 / H)


def compute_crop(prod, size, padding, aspect, extend, obst=None, grow=0):
    """
    Crop box (normalised) containing the whole product, centred on it, with `padding` %
    margin and an optional aspect ratio (the box only grows to meet the ratio, so the
    product is never cut). If `obst` marks gray areas / lines around the product, the
    padding is reduced - symmetrically, so the product stays centred - until the box no
    longer contains any of them.
    With extend=True the box may go past the photo edges (export fills it with the
    background colour); otherwise it is kept inside the photo.
    `grow` (% of the photo, may be negative) then makes the finished box bigger / smaller.
    """
    return apply_grow(_auto_crop(prod, size, padding, aspect, extend, obst), size, grow, aspect, extend)


def _auto_crop(prod, size, padding, aspect, extend, obst):
    full = _raw_crop(prod, size, padding, aspect, extend)
    if obst is None or not obst.any():
        return full
    g = obst.shape[0]
    base = _raw_crop(prod, size, 0.0, aspect, extend)
    eff = obst.copy()
    bx0, by0, bx1, by1 = _cells_inside(base, g)
    eff[by0:by1, bx0:bx1] = False          # anything inside the product's own box is unavoidable

    def clear(c):
        x0, y0, x1, y1 = _cells_inside(c, g)
        return not eff[y0:y1, x0:x1].any()

    if clear(full):
        return full
    lo, hi = 0.0, float(padding)
    for _ in range(14):
        mid = (lo + hi) / 2
        if clear(_raw_crop(prod, size, mid, aspect, extend)):
            lo = mid
        else:
            hi = mid
    return _raw_crop(prod, size, lo, aspect, extend)
