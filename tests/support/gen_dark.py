"""Synthetic product photos on DARK / brown backdrops, with ground-truth product boxes.

Backdrop: base colour + plane gradient + vignette + soft low-frequency mottling + grain, optionally
a table seam (lighter band), a gray block / dust (not part of the product) and a soft shadow."""
import io

import numpy as np
from PIL import Image


def _smooth_noise(rnd, H, W, scale, amp):
    small = rnd.normal(0, 1, (max(2, H // scale), max(2, W // scale)))
    img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8))
    n = np.asarray(img.resize((W, H), Image.Resampling.BICUBIC), np.float32) / 255.0
    return (n - n.mean()) * 2 * amp


def dark_photo(size=(1600, 1200), parts=(), bg=(88, 58, 40), grad=(0, 0), vignette=0, mottle=3.0,
               grain=2.5, shadow=0, seam=False, seam_y=0.82, block=False, dust=True, jpeg=0, seed=0):
    """parts: dicts(box=(x0,y0,x1,y1), color=(r,g,b), kind='round'|'sq'|'rect', rim=0.04, shade=18)
    Returns (PIL image, truth bbox (x0,y0,x1,y1), truth mask)."""
    rnd = np.random.default_rng(seed)
    W, H = size
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    base = np.array(bg, np.float32)
    img = np.empty((H, W, 3), np.float32)
    field = grad[0] * nx + grad[1] * ny - vignette * (nx ** 2 + ny ** 2) / 2 + _smooth_noise(rnd, H, W, 160, mottle)
    for c in range(3):
        img[..., c] = base[c] + field * (0.5 + 0.5 * base[c] / base.max())
    if shadow:
        for p in parts:
            x0, y0, x1, y1 = p["box"]
            sh = np.exp(-(((xx - (x0 + x1) / 2) / ((x1 - x0) * 0.62)) ** 2 + ((yy - (y1 + 6)) / 40.0) ** 2))
            img -= (sh * shadow)[..., None] * (base / base.max())
    truth = np.zeros((H, W), bool)
    boxes = []
    for p in parts:
        x0, y0, x1, y1 = p["box"]
        u = (xx - (x0 + x1) / 2) / ((x1 - x0) / 2)
        v = (yy - (y0 + y1) / 2) / ((y1 - y0) / 2)
        kind = p.get("kind", "sq")
        d = (np.sqrt(u ** 2 + v ** 2) if kind == "round" else
             (np.abs(u) ** 6 + np.abs(v) ** 6) ** (1 / 6) if kind == "sq" else np.maximum(np.abs(u), np.abs(v)))
        m = d <= 1.0
        col = np.array(p["color"], np.float32)
        shade = p.get("shade", 18)
        lit = (-shade * u + shade * 0.5 * v)[..., None]
        prod = col[None, None, :] + lit
        rim = p.get("rim", 0.04)
        if rim:
            t = np.clip((d - (1 - rim)) / rim, 0, 1)[..., None]
            prod = prod * (1 - 0.8 * t) + img * 0.8 * t       # edge fades toward the backdrop
        img = np.where(m[..., None], prod, img)
        truth |= m
        ys, xs = np.nonzero(m)
        boxes.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    if seam:                                   # table / wall seam: lighter full-width band
        y = int(H * seam_y)
        img[y:y + 8] += 22
        img[y + 8:] -= 6
    if block:                                  # unrelated lighter block in a corner
        img[0:int(H * .14), int(W * .82):] += 32
    img += rnd.normal(0, grain, img.shape)
    if dust:
        for _ in range(25):
            x, y = rnd.integers(0, W - 4), rnd.integers(0, H - 4)
            near = any(b[0] - 40 < x < b[2] + 40 and b[1] - 40 < y < b[3] + 40 for b in boxes)
            if not near:
                img[y:y + 3, x:x + 3] += 45
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if jpeg:
        bio = io.BytesIO()
        out.save(bio, "JPEG", quality=jpeg)
        bio.seek(0)
        out = Image.open(bio)
        out.load()
    ys, xs = np.nonzero(truth)
    return out, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1), truth


def P(**k):
    return dict(k)


# (name, kwargs) - the suite
CD = []


def add(name, parts, **kw):
    CD.append((name, dict(parts=parts, **kw)))


BROWNS = {"milk-choc": (88, 58, 40), "walnut": (62, 42, 30), "tan-kraft": (140, 100, 66), "red-brown": (104, 56, 40)}
PRODUCTS = {"cream": (235, 225, 205), "silver": (190, 192, 198), "black": (22, 20, 20), "gold": (205, 165, 75),
            "navy": (35, 50, 95), "white": (248, 248, 246), "mid-gray": (125, 125, 128), "dark-brown": (45, 30, 22),
            "teal": (30, 120, 125)}
for bn, bgc in BROWNS.items():
    for pn, pc in PRODUCTS.items():
        if bn not in ("milk-choc", "walnut") and pn not in ("cream", "black", "gold", "teal"):
            continue
        # a product nearly the same brightness as its backdrop is genuinely ambiguous; skip identical-ish pairs
        if sum(abs(a - b) for a, b in zip(bgc, pc)) < 70:
            continue
        add(f"{bn}/{pn} round", [P(box=(520, 260, 1080, 960), color=pc, kind="round")], bg=bgc)
add("walnut/cream wide rect + shadow", [P(box=(250, 400, 1350, 800), color=(235, 225, 205), kind="rect", rim=0.03)],
    bg=BROWNS["walnut"], shadow=40)
add("milk-choc/silver tall + gradient", [P(box=(600, 120, 1000, 1000), color=(190, 192, 198), kind="rect")],
    bg=BROWNS["milk-choc"], grad=(14, -10))
add("milk-choc/cream + vignette", [P(box=(520, 260, 1080, 960), color=(235, 225, 205), kind="round")],
    bg=BROWNS["milk-choc"], vignette=30)
add("walnut/gold + seam + block", [P(box=(480, 220, 1120, 980), color=(205, 165, 75), kind="sq")],
    bg=BROWNS["walnut"], seam=True, block=True)
add("tan-kraft/black + seam + shadow", [P(box=(560, 280, 1040, 940), color=(22, 20, 20), kind="sq")],
    bg=BROWNS["tan-kraft"], seam=True, shadow=35)
add("milk-choc/two parts", [P(box=(380, 380, 760, 900), color=(235, 225, 205), kind="round"),
                            P(box=(860, 300, 1220, 900), color=(190, 192, 198), kind="sq")],
    bg=BROWNS["milk-choc"])
add("walnut/cream jpeg60 + mottle", [P(box=(520, 260, 1080, 960), color=(235, 225, 205), kind="round")],
    bg=BROWNS["walnut"], jpeg=60, mottle=6, grain=4)
add("red-brown/white small centred", [P(box=(660, 420, 940, 780), color=(248, 248, 246), kind="round")],
    bg=BROWNS["red-brown"])
add("tan-kraft/navy gradient+vignette+seam", [P(box=(500, 250, 1100, 950), color=(35, 50, 95), kind="sq")],
    bg=BROWNS["tan-kraft"], grad=(-12, 12), vignette=24, seam=True, jpeg=75)
