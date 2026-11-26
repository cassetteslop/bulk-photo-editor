"""Product detection for shots on light (white / off-white / gray) or dark (brown, black, coloured)
backdrops (no GUI)."""

import math
import numpy as np
from PIL import Image
from collections import namedtuple

from photo_editor.core.constants import ANALYSIS_SIDE, OBST_GRID, WORK_SIDE

# --------------------------------------------------------------------------
SHADOW_MULT = {"light": 2.2, "dark": 1.5}   # contrast boost used by "ignore soft shadow"
DARK_LUMINANCE = 110     # ring brightness (0-255) below which a backdrop counts as "dark"
# bbox (normalised), backdrop colour, keep-out grid, which profile ("light" / "dark") was used
Detection = namedtuple("Detection", "prod bg obst kind", defaults=("light",))
NO_DETECTION = Detection(None, None, None)
Picked = namedtuple("Picked", "cells touch ok area")


def _box_sum(a, k):
    """Sum over a k x k window (k odd, zero padded) using an integral image."""
    r = k // 2
    p = np.pad(a.astype(np.int32), ((r + 1, r), (r + 1, r)))
    c = p.cumsum(0).cumsum(1)
    h, w = a.shape
    return c[k:k + h, k:k + w] - c[:h, k:k + w] - c[k:k + h, :w] + c[:h, :w]


def _dilate(mask, k):
    return _box_sum(mask, k) > 0


def _erode(mask, k):
    return ~_dilate(~mask, k)        # outside the frame counts as "set", so border objects keep their edge


def _open(mask, k):
    """Removes anything thinner than k pixels (lines, specks)."""
    return _dilate(_erode(mask, k), k)


def _close(mask, k):
    """Bridges gaps narrower than k (seams, highlights splitting a product in two)."""
    return _erode(_dilate(mask, k), k)


def _pool_cells(mask, cell):
    h, w = mask.shape
    gh, gw = -(-h // cell), -(-w // cell)
    pad = np.zeros((gh * cell, gw * cell), np.int32)
    pad[:h, :w] = mask
    counts = pad.reshape(gh, cell, gw, cell).sum(axis=(1, 3))
    return counts > 0, counts


def _upsample(grid, cell, h, w):
    return np.repeat(np.repeat(grid, cell, axis=0), cell, axis=1)[:h, :w]


def _pool_norm(mask, g):
    """Pool a mask into a g x g grid covering the whole photo (cell is True if any pixel is)."""
    h, w = mask.shape
    ii = np.pad(mask.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    ys = (np.arange(g) * h) // g
    ye = np.maximum(((np.arange(g) + 1) * h) // g, ys + 1)
    xs = (np.arange(g) * w) // g
    xe = np.maximum(((np.arange(g) + 1) * w) // g, xs + 1)
    s = ii[np.ix_(ye, xe)] - ii[np.ix_(ys, xe)] - ii[np.ix_(ye, xs)] + ii[np.ix_(ys, xs)]
    return s > 0


def _label(cells):
    """8-connected component labelling of a small boolean grid."""
    gh, gw = cells.shape
    g = cells.tolist()
    lab = [[0] * gw for _ in range(gh)]
    n = 0
    for sy in range(gh):
        row = g[sy]
        for sx in range(gw):
            if row[sx] and not lab[sy][sx]:
                n += 1
                lab[sy][sx] = n
                stack = [(sy, sx)]
                while stack:
                    y, x = stack.pop()
                    for yy in range(max(0, y - 1), min(gh, y + 2)):
                        gy, ly = g[yy], lab[yy]
                        for xx in range(max(0, x - 1), min(gw, x + 2)):
                            if gy[xx] and not ly[xx]:
                                ly[xx] = n
                                stack.append((yy, xx))
    return np.array(lab, dtype=np.int32).reshape(gh, gw), n


def _comp_stats(lab, n, margin=1):
    """Per-component size, bounding box (grid cells) and fraction of the grid border touched
    (the border being the outer `margin` rows / columns of cells)."""
    gh, gw = lab.shape
    ys, xs = np.nonzero(lab)
    ls = lab[ys, xs]
    weight = np.bincount(ls, minlength=n + 1).astype(np.float64)
    big = 1 << 30
    x0, y0 = np.full(n + 1, big, np.int64), np.full(n + 1, big, np.int64)
    x1, y1 = np.full(n + 1, -1, np.int64), np.full(n + 1, -1, np.int64)
    np.minimum.at(x0, ls, xs)
    np.maximum.at(x1, ls, xs)
    np.minimum.at(y0, ls, ys)
    np.maximum.at(y1, ls, ys)
    edge = np.zeros((gh, gw), bool)
    edge[:margin] = edge[-margin:] = True
    edge[:, :margin] = edge[:, -margin:] = True
    contact = np.bincount(lab[edge], minlength=n + 1) / float(edge.sum())
    contact[0] = 0.0
    return weight, x0, y0, x1, y1, contact


def _fill_small_holes(cells, max_frac=0.25):
    """Fill background-coloured gaps that are completely enclosed by the object
    (a bright highlight or a white label inside a gray product)."""
    gh, gw = cells.shape
    free = ~cells
    out = np.zeros_like(cells)
    out[0, :], out[-1, :] = free[0, :], free[-1, :]
    out[:, 0], out[:, -1] = free[:, 0], free[:, -1]
    prev = -1
    while True:
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        g &= free
        s = int(g.sum())
        if s == prev:
            break
        prev, out = s, g
    holes = free & ~out
    if not holes.any():
        return cells
    hl, hn = _label(holes)
    sizes = np.bincount(hl.ravel(), minlength=hn + 1)
    fill = sizes <= max_frac * gh * gw       # a huge "hole" is really the background inside a frame
    fill[0] = False
    return cells | fill[hl]


def _edge_run(flags, tol=3):
    """Length of a run of True flags that starts within `tol` entries of the start."""
    n = len(flags)
    lim = min(tol, n)
    i = 0
    while i < lim and not flags[i]:
        i += 1
    if i >= lim:
        return 0
    j = i
    while j < n and flags[j]:
        j += 1
    return j


def _strip_border_bands(m, frac=0.85):
    """Remove full-width / full-height bands that start at the photo edge (table edge, scanner
    border, gray strip). A product in the middle of the frame is never touched, even if it
    spans the whole width."""
    h, w = m.shape
    rows = m.mean(axis=1) > frac
    cols = m.mean(axis=0) > frac
    if rows.mean() >= 0.5 or cols.mean() >= 0.5:
        return m
    out = m.copy()
    t, b = _edge_run(rows), _edge_run(rows[::-1])
    l, r = _edge_run(cols), _edge_run(cols[::-1])
    if t:
        out[:t, :] = False
    if b:
        out[h - b:, :] = False
    if l:
        out[:, :l] = False
    if r:
        out[:, w - r:] = False
    return out


def _strip_thin_lines(m, frac=0.9, max_thick=0.03):
    """Remove thin full-width / full-height lines anywhere in the frame (table seams, shelf edges,
    ruled lines). A product that spans the frame is a long run of such rows, so it is kept."""
    h, w = m.shape
    out = m
    for axis, n in ((1, h), (0, w)):
        flags = m.mean(axis=axis) > frac
        if not flags.any():
            continue
        lim = max(3, int(max_thick * n))
        i = 0
        while i < n:
            if flags[i]:
                j = i
                while j < n and flags[j]:
                    j += 1
                if j - i <= lim:
                    if out is m:
                        out = m.copy()
                    if axis == 1:
                        out[i:j, :] = False
                    else:
                        out[:, i:j] = False
                i = j
            else:
                i += 1
    return out


def _pick_object(E, cell=4):
    """
    Pick the product out of a "not background" mask E.
      * thin lines / specks are removed (opening) and so are bands along the photo edge,
      * gaps inside the product are bridged and enclosed highlights are filled,
      * of the blobs left, the one at the centre of the photo wins; blobs touching the
        photo border are background features (gray areas, frame edges) and lose,
      * then every other piece near the product - thin handles, small caps, a lit rim that
        is separated from the body by a near-white highlight - is added, unless it runs to
        the photo border (that is a line) or is a speck of dust.
    Returns Picked(cells, touch, ok, area) or None. `cells` is a boolean grid of 4x4-pixel cells.
    """
    Eo = _strip_border_bands(_strip_thin_lines(_open(E, 5)))
    co, _ = _pool_cells(Eo, cell)
    if not co.any():
        return None
    core = _fill_small_holes(_close(co, 3))
    lab, n = _label(core)
    if n == 0:
        return None
    gh, gw = core.shape
    weight, x0, y0, x1, y1, contact = _comp_stats(lab, n)
    ccx, ccy = gw / 2.0, gh / 2.0
    contains = (x0[1:] <= ccx) & (x1[1:] + 1 >= ccx) & (y0[1:] <= ccy) & (y1[1:] + 1 >= ccy)
    free = contact[1:] == 0
    cand = np.nonzero(contains & free)[0]
    if len(cand):
        main = int(cand[np.argmax(weight[1:][cand])]) + 1
    else:
        cand = np.nonzero(contains)[0]
        if len(cand):
            main = int(min(cand, key=lambda i: (round(float(contact[i + 1]), 3), -weight[i + 1]))) + 1
        else:
            tot = weight[1:].sum()
            ok_ = [i for i in range(n) if weight[i + 1] >= 0.02 * tot] or list(range(n))
            ok_ = [i for i in ok_ if contact[i + 1] == 0] or ok_

            def dist(i):
                dx = max(x0[i + 1] - ccx, 0, ccx - (x1[i + 1] + 1))
                dy = max(y0[i + 1] - ccy, 0, ccy - (y1[i + 1] + 1))
                return math.hypot(dx, dy)
            main = int(min(ok_, key=dist)) + 1

    main_mask = lab == main
    touch = float(contact[main])
    ec, _ = _pool_cells(E, cell)               # everything that is not background, thin parts included
    allc = ec | core
    obj = main_mask.copy()
    rest = allc & ~main_mask
    rlab, rn = _label(rest)
    if rn:
        pw, px0, py0, px1, py1, pcontact = _comp_stats(rlab, rn, margin=max(2, int(round(0.03 * max(gh, gw)))))
        mw = float(main_mask.sum())
        bx0, by0, bx1, by1 = int(x0[main]), int(y0[main]), int(x1[main]), int(y1[main])
        biggest = max(gh, gw)
        gap = 0.10 * biggest
        used = set()
        changed = True
        while changed:
            changed = False
            side = max(bx1 - bx0 + 1, by1 - by0 + 1)
            for k in range(1, rn + 1):
                if k in used or pcontact[k] > 0:
                    continue
                ext = max(px1[k] - px0[k] + 1, py1[k] - py0[k] + 1)
                if ext > side and pw[k] < 0.3 * ext * ext:      # longer than the product and thin: a line
                    continue
                if not (pw[k] >= 0.008 * mw or ext >= 0.06 * biggest):   # dust
                    continue
                pwid, phei = px1[k] - px0[k] + 1, py1[k] - py0[k] + 1
                if min(pwid, phei) <= 3 and max(pwid, phei) >= 8:       # a thin piece: handle or line?
                    # a line runs ALONG the product's edge, crosses part of it and continues past its end
                    # (table seam, shelf edge); a handle / cap / antenna starts at the product and sticks OUT.
                    if pwid >= phei and (py0[k] >= by1 - 2 or py1[k] <= by0 + 2):
                        crosses = min(px1[k], bx1) - max(px0[k], bx0) + 1 >= 2      # runs alongside the product
                        if crosses and max(bx0 - px0[k], px1[k] - bx1, 0) > 0.25 * (bx1 - bx0 + 1):
                            continue
                    elif phei > pwid and (px0[k] >= bx1 - 2 or px1[k] <= bx0 + 2):
                        crosses = min(py1[k], by1) - max(py0[k], by0) + 1 >= 2
                        if crosses and max(by0 - py0[k], py1[k] - by1, 0) > 0.25 * (by1 - by0 + 1):
                            continue
                dx = max(px0[k] - bx1, bx0 - px1[k], 0)
                dy = max(py0[k] - by1, by0 - py1[k], 0)
                if max(dx, dy) <= gap:
                    used.add(k)
                    bx0, by0 = min(bx0, int(px0[k])), min(by0, int(py0[k]))
                    bx1, by1 = max(bx1, int(px1[k])), max(by1, int(py1[k]))
                    changed = True
        for k in used:
            obj |= rlab == k
    ys, xs = np.nonzero(obj)
    fills = ((xs.max() - xs.min() + 1) / gw > 0.95) and ((ys.max() - ys.min() + 1) / gh > 0.95)
    return Picked(obj, touch, bool(touch <= 0.12 and not fills), int(obj.sum()))


def classify_background(img):
    """Return "dark" or "light" by looking at the photo's outer ring (where the backdrop is)."""
    sm = img.convert("RGB")
    sc = 160.0 / max(sm.size)
    if sc < 1:
        sm = sm.resize((max(1, round(sm.width * sc)), max(1, round(sm.height * sc))), Image.Resampling.BILINEAR)
    a = np.asarray(sm, dtype=np.float32)
    h, w, _ = a.shape
    r = max(1, int(round(0.06 * min(h, w))))
    ring = np.concatenate([a[:r].reshape(-1, 3), a[-r:].reshape(-1, 3),
                           a[r:-r, :r].reshape(-1, 3), a[r:-r, -r:].reshape(-1, 3)])
    lum = ring.mean(axis=1)
    return "dark" if float(np.median(lum)) < DARK_LUMINANCE else "light"


def _blur3(a):
    """3x3 mean of an HxWxC float array (tames grain / JPEG noise on textured backdrops)."""
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    h, w = a.shape[:2]
    return sum(p[i:i + h, j:j + w] for i in range(3) for j in range(3)) / 9.0


def _fit_backdrop(a):
    """Model a dark backdrop as colour + plane gradient + vignette, fitted robustly to the outer ring
    (the product is in the middle, so the ring is almost always pure backdrop).
    Returns (model HxWx3 float32, ring median colour)."""
    h, w, _ = a.shape
    st = 2
    sub = a[::st, ::st]
    sh, sw = sub.shape[:2]
    r = max(2, int(round(0.05 * min(sh, sw))))
    mask = np.zeros((sh, sw), bool)
    mask[:r] = mask[-r:] = True
    mask[:, :r] = mask[:, -r:] = True
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    nx, ny = (xx - sw / 2) / (sw / 2), (yy - sh / 2) / (sh / 2)
    X = np.stack([np.ones_like(nx), nx, ny, nx * nx + ny * ny], axis=-1)[mask]
    Y = sub[mask].astype(np.float32)
    med = np.median(Y, axis=0)
    gy, gx = np.mgrid[0:h, 0:w].astype(np.float32)
    gnx, gny = (gx - w / 2) / (w / 2), (gy - h / 2) / (h / 2)

    def evaluate(coef, terms):
        out = np.empty((h, w, 3), np.float32)
        basis = [np.ones_like(gnx), gnx, gny, gnx * gnx + gny * gny][:terms]
        for c in range(3):
            acc = np.zeros((h, w), np.float32)
            for k, bs in enumerate(basis):
                acc += coef[k, c] * bs
            out[..., c] = acc
        return out

    for terms in (4, 3):                    # vignette + plane first, then plane only if that looks wild
        keep = np.ones(len(X), bool)
        coef = None
        for _ in range(4):
            if keep.sum() < 40:
                coef = None
                break
            coef = np.linalg.lstsq(X[keep][:, :terms], Y[keep], rcond=None)[0]
            res = np.abs(X[:, :terms] @ coef - Y).max(axis=1)
            thr = max(8.0, 3.0 * 1.4826 * float(np.median(res[keep])))
            new_keep = res <= thr
            if (new_keep == keep).all():
                break
            keep = new_keep
        if coef is None:
            continue
        centre = coef[0]                    # model value at the photo centre
        if np.abs(centre - med).max() <= 45:
            return np.clip(evaluate(coef, terms), 0, 255), np.round(med).astype(np.int16)
    return np.broadcast_to(med.astype(np.float32), (h, w, 3)), np.round(med).astype(np.int16)


def detect_product(img, tol=20, ignore_shadow=False, kind="light"):
    """
    Find the product at the centre of a photo with a (mostly) white / off-white background.

    Returns Detection(prod, bg, obst):
      prod  - (x0, y0, x1, y1) normalised box around the product,
      bg    - background colour,
      obst  - square boolean grid marking gray areas / lines / borders OUTSIDE the product,
              used to keep the crop away from them.
    `tol` is how far from the background colour (0-255) a pixel must be to count as
    "not background". Everything that belongs to the product - light-gray areas, highlights,
    a lit edge fading into the background, thin or small parts - is then included; the box
    is only trimmed by lines, gray areas and dust that are not part of the product.
    With ignore_shadow the product is found at a higher contrast and its faint surroundings
    are not added, so soft shadows around it do not widen the box.
    """
    W, H = img.size
    sc = min(1.0, WORK_SIDE / max(W, H))
    work = img.convert("RGB")
    if sc < 1:
        work = work.resize((max(1, round(W * sc)), max(1, round(H * sc))), Image.Resampling.BILINEAR)
    a = np.asarray(work, dtype=np.int16)
    if kind == "dark":                  # brown / black / coloured backdrop: model it from the outer ring
        model, bg = _fit_backdrop(a.astype(np.float32))
        D = np.rint(np.abs(_blur3(a.astype(np.float32)) - model).max(axis=2)).astype(np.int16)
    else:                               # white / off-white / light gray: background = brightest quarter
        sub = a[::3, ::3]
        lum = sub.sum(axis=2)
        bright = sub[lum >= np.percentile(lum, 75)]
        bg = np.round(np.median(bright.reshape(-1, 3), axis=0)).astype(np.int16)
        D = np.abs(a - bg).max(axis=2)
    h, w = D.shape
    f = max(1, int(math.ceil(max(h, w) / ANALYSIS_SIDE)))
    if f > 1:                       # max-pool so thin faint lines keep their contrast
        h2, w2 = -(-h // f) * f, -(-w // f) * f
        pad = np.zeros((h2, w2), np.int16)
        pad[:h, :w] = D
        D = pad.reshape(h2 // f, f, w2 // f, f).max(axis=(1, 3))
    h, w = D.shape

    shadow_mult = SHADOW_MULT[kind]
    base = max(tol, 3) * (shadow_mult if ignore_shadow else 1.0)
    nz = min(2.5 * float(np.median(D)), 0.35 * base)           # background noise level
    t_lo = min(max(0.4 * base, nz + 1.0, 5.0), base)           # "faint" threshold for edges / lit rims
    if ignore_shadow:
        t_lo = max(t_lo, float(tol))

    cands = []
    for mult in (1.0, 1.6, 2.5):        # raise the contrast only if the object will not separate
        thr = min(base * mult, 200.0)
        r = _pick_object(D > thr)
        if r is None:
            continue
        cands.append(r)
        if r.ok:
            break
    if not cands:                       # nothing found: a very light product - look at fainter contrast
        for mult in (0.65, 0.45):
            r = _pick_object(D > max(base * mult, 6.0))
            if r is not None:
                cands.append(r)
                break
    if not cands:
        return NO_DETECTION
    chosen = next((c for c in cands if c.ok), None)
    if chosen is None:                  # least border contact, but never one that shrank the product a lot
        viable = [c for c in cands if c.area >= 0.55 * cands[0].area]
        chosen = min(viable, key=lambda c: (c.touch, -c.area))

    cell = 4
    Mo = _upsample(chosen.cells, cell, h, w)
    weak = D > t_lo
    P = Mo & weak
    if not P.any():
        P = Mo
    r_rim = max(2, int(round(0.006 * max(h, w))))       # rims hug the product, lines crawl: keep it short
    if not ignore_shadow:               # win back the faint lit edge of the product (not far, not along lines)
        coherent = weak & (_box_sum(weak, 3) >= 3)      # isolated noise pixels cannot chain outwards
        for _ in range(r_rim):
            P = P | (_dilate(P, 3) & coherent)
    ys, xs = np.nonzero(P)
    if len(xs) == 0:
        return NO_DETECTION
    m = 2
    x0, y0 = max(0, xs.min() - m), max(0, ys.min() - m)
    x1, y1 = min(w, xs.max() + 1 + m), min(h, ys.max() + 1 + m)
    prod = (float(x0) / w, float(y0) / h, float(x1) / w, float(y1) / h)

    # Everything else that is not background and is big / long enough to matter
    O = (D > tol) & ~_dilate(Mo | P, 2 * (r_rim + 5) + 1)
    ocells, ocounts = _pool_cells(O, 4)
    olab, on = _label(ocells)
    if on:
        ow, ox0, oy0, ox1, oy1, _ = _comp_stats(olab, on)
        ext = np.maximum(ox1 - ox0 + 1, oy1 - oy0 + 1) * 4
        cnt = np.bincount(olab.ravel(), weights=ocounts.ravel(), minlength=on + 1)
        keep = np.zeros(on + 1, bool)
        keep[1:] = (cnt[1:] >= max(30, 0.0003 * h * w)) | (ext[1:] >= 0.05 * max(h, w))
        O = O & _upsample(keep[olab], 4, h, w)
    else:
        O = np.zeros_like(O)
    bgc = tuple(int(v) for v in bg)
    if kind != "dark" and min(bgc) >= 248:
        bgc = (255, 255, 255)
    return Detection(prod, bgc, _pool_norm(O, OBST_GRID), kind)


def profile_for(img, s):
    """Pick the detector profile for a photo. Returns (kind, tolerance, ignore_shadow).
    Each profile has its own settings: light -> tolerance / shadow, dark -> tol_dark / shadow_dark."""
    mode = str(s.get("bg_mode", "Auto")).lower()
    kind = mode if mode in ("light", "dark") else classify_background(img)
    if kind == "dark":
        return "dark", s["tol_dark"], s["shadow_dark"]
    return "light", s["tolerance"], s["shadow"]


def detect_for_settings(img, s):
    """detect_product() with the profile chosen by settings `s` (see profile_for)."""
    kind, tol, shadow = profile_for(img, s)
    return detect_product(img, tol, shadow, kind)


def tolerance_for_bg(bg, s):
    """Edge-clean-up tolerance matching the profile that produced background colour `bg`."""
    dark = bg is not None and sum(bg) / 3.0 < DARK_LUMINANCE
    return s["tol_dark"] if dark else s["tolerance"]
