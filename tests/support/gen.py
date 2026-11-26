"""Synthetic product photos with GROUND-TRUTH product boxes."""
import numpy as np
from PIL import Image

def shape_d(kind, u, v):
    if kind == "round": return np.sqrt(u**2 + v**2)
    if kind == "sq":    return (np.abs(u)**6 + np.abs(v)**6) ** (1/6)
    if kind == "rect":  return np.maximum(np.abs(u), np.abs(v))

def part(W, H, box, kind="sq"):
    x0, y0, x1, y1 = box
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u = (xx - (x0 + x1) / 2) / ((x1 - x0) / 2); v = (yy - (y0 + y1) / 2) / ((y1 - y0) / 2)
    return shape_d(kind, u, v), u, v

def photo(size=(1600, 1200), parts=None, bg=255, noise=2.0, seed=0, shadow=False, vignette=0,
          lines=True, area=True, dust=True, band=False, frame=False, touch_line=False, jpeg=0, bgtint=(0, 0, 0)):
    """
    parts: list of dict(box=(x0,y0,x1,y1), gray=170, kind='sq'|'round'|'rect', rim=0.06, shade=True,
                        highlight=True, seam=False, white_inside=None)
    Returns (PIL image, truth bbox of ALL parts, truth mask)
    """
    rnd = np.random.default_rng(seed)
    W, H = size
    img = np.full((H, W), float(bg), np.float32)[..., None].repeat(3, axis=2)
    truth = np.zeros((H, W), bool)
    allboxes = []
    if shadow:
        for p in parts:
            x0, y0, x1, y1 = p["box"]
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            sh = np.exp(-(((xx - (x0 + x1) / 2) / ((x1 - x0) * 0.6)) ** 2 + ((yy - (y1 + 8)) / 38.0) ** 2))
            img -= (sh * 95)[..., None]
    for p in parts:
        gray = p.get("gray", 170); rim = p.get("rim", 0.06)
        d, u, v = part(W, H, p["box"], p.get("kind", "sq"))
        m = d <= 1.0
        col = np.full((H, W), float(gray), np.float32)
        amp = min(35, max(0, 240 - gray))      # the lit side never gets brighter than the background
        if p.get("shade", True): col = col - amp * u + amp * 0.55 * v
        if rim:
            t = np.clip((d - (1 - rim)) / rim, 0, 1)
            col = col * (1 - t * 0.92) + (bg - 8) * t * 0.92          # lit rim fades toward the background
        if p.get("highlight", True):
            hl = np.exp(-((u + 0.35) / 0.07) ** 2) * (np.abs(v) < 0.75)
            col = col * (1 - hl * .92) + 252 * hl * .92
        if p.get("seam"):
            seam = np.exp(-((u) / 0.03) ** 2)
            col = col * (1 - seam) + 253 * seam
        if p.get("white_inside"):       # a near-white component inside the outline (cap, label)
            x0, y0, x1, y1 = p["white_inside"]
            yy, xx = np.mgrid[0:H, 0:W]
            wm = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1) & m
            col = np.where(wm, 250.0, col)
        for c in range(3):
            img[..., c] = np.where(m, col + (c - 1) * 4, img[..., c])
        truth |= m
        ys, xs = np.nonzero(m); allboxes.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    if vignette:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        img -= (np.clip(r - 0.85, 0, 1) * vignette)[..., None]
    if lines:
        img[int(H * 0.88):int(H * 0.88) + 3, :, :] = 205        # horizontal full-width line
        img[:, 30:33, :] = 215                                   # vertical line near the left
    if area:
        img[0:int(H * .13), int(W * .84):, :] = 222              # gray block in the top-right corner
    if band:
        img[int(H * .93):, :, :] = 200                           # gray band along the bottom (table edge)
    if frame:
        img[:6, :, :] = 190; img[-6:, :, :] = 190; img[:, :6, :] = 190; img[:, -6:, :] = 190
    if touch_line:   # a faint line that runs right up to the product (shelf edge)
        x0, y0, x1, y1 = parts[0]["box"]
        img[int(y1 - 6):int(y1 - 3), :int(x0 + 40), :] = 200
    img = img + rnd.normal(0, noise, img.shape)
    if dust:
        for _ in range(25):
            x, y = rnd.integers(0, W - 4), rnd.integers(0, H - 4)
            near = any(b[0] - 30 < x < b[2] + 30 and b[1] - 30 < y < b[3] + 30 for b in allboxes)
            if not near and y < H * .86: img[y:y + 3, x:x + 3] = 140
    img = img + np.array(bgtint, np.float32) * ((np.abs(img - bg).max(axis=2) < 6)[..., None])
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if jpeg:
        import io
        bio = io.BytesIO(); out.save(bio, 'JPEG', quality=jpeg); bio.seek(0); out = Image.open(bio); out.load()
    ys, xs = np.nonzero(truth)
    return out, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1), truth
