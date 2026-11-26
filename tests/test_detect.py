import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
SP = tempfile.mkdtemp(prefix="bpe_tests_")
import time, io
import faketk
import numpy as np
from PIL import Image, ImageDraw
from legacy import b
from gen import photo
from cases import C

def metrics(im, tb, det):
    W, H = im.size; p = det.prod
    px = (p[0]*W, p[1]*H, p[2]*W, p[3]*H); tw, th = tb[2]-tb[0], tb[3]-tb[1]
    cut = [max(0, c)*100 for c in ((px[0]-tb[0])/tw, (px[1]-tb[1])/th, (tb[2]-px[2])/tw, (tb[3]-px[3])/th)]
    ext = [max(0, e)*100 for e in ((tb[0]-px[0])/tw, (tb[1]-px[1])/th, (px[2]-tb[2])/tw, (px[3]-tb[3])/th)]
    return cut, ext

# 1. synthetic suite: never cut the product; stay tight except for known ambiguous cases
LOOSE_OK = {"large gray200": 16, "gray200 + shadow": 40, "full-width gray bar": 9, "full-height gray bar": 14, "full-width bar noisy": 9}
worst_cut = 0; t_total = 0
for name, kw in C:
    im, tb, truth = photo(**kw)
    t0 = time.time(); det = b.detect_product(im, 20); t_total += time.time() - t0
    assert det.prod is not None, name
    cut, ext = metrics(im, tb, det)
    assert max(cut) <= 1.0, (name, cut)
    assert max(ext) <= LOOSE_OK.get(name, 6.0), (name, ext)
    worst_cut = max(worst_cut, max(cut))
print(f"synthetic suite: {len(C)} cases, worst cut {worst_cut:.2f}%, avg detect time {t_total/len(C):.2f}s")

# 2. degenerate inputs
assert b.detect_product(Image.new("RGB", (300, 300), "white"), 20) == b.NO_DETECTION
assert b.detect_product(Image.new("RGB", (300, 300), (240, 240, 238)), 20).prod is None
b.detect_product(Image.new("RGB", (50, 40), "white"), 20)
b.detect_product(Image.new("RGB", (8, 8), "white"), 20)
b.detect_product(Image.new("L", (400, 300), 250), 20)
b.detect_product(Image.new("RGBA", (400, 300), (255, 255, 255, 255)), 20)
all_black = b.detect_product(Image.new("RGB", (400, 300), "black"), 20)     # no background at all: must not crash
for tol in (4, 10, 40, 80):          # slider extremes
    d = b.detect_product(photo(parts=[dict(box=(520, 260, 1080, 900), gray=190)], jpeg=70, noise=3)[0], tol)
    assert d.prod is None or (0 <= d.prod[0] < d.prod[2] <= 1 and 0 <= d.prod[1] < d.prod[3] <= 1), tol
print("degenerate inputs + tolerance extremes ok")

# 3. classic v2-style scene: red product with a stripe, dust and a faint edge strip
def make(size, bg, box, seed=1):
    rnd = np.random.default_rng(seed); W, H = size
    a = np.empty((H, W, 3), np.uint8); a[:] = bg
    a = np.clip(a + rnd.normal(0, 2, a.shape), 0, 255).astype(np.uint8)
    im = Image.fromarray(a); d = ImageDraw.Draw(im); x0, y0, x1, y1 = box
    d.ellipse(box, fill=(200, 30, 30)); d.rectangle((x0 + 10, y1 - 30, x1 - 10, y1 - 10), fill=(30, 30, 160))
    for _ in range(25):
        x, y = rnd.integers(0, W - 4), rnd.integers(0, H - 4)
        if not (x0 - 20 < x < x1 + 20 and y0 - 20 < y < y1 + 20): d.ellipse((x, y, x + 3, y + 3), fill=(120, 120, 120))
    d.rectangle((0, 0, 3, H), fill=(235, 235, 235))
    return im
im = make((1600, 1200), (255, 255, 255), (1000, 600, 1450, 1100))
det = b.detect_product(im, 20); p = [det.prod[0]*1600, det.prod[1]*1200, det.prod[2]*1600, det.prod[3]*1200]
assert p[0] <= 1000 and p[1] <= 600 and p[2] >= 1450 and p[3] >= 1100 and p[0] > 970 and p[1] > 570 and p[2] < 1480 and p[3] < 1130, p
assert det.bg == (255, 255, 255)
im2 = make((900, 1300), (246, 246, 244), (100, 80, 500, 700)); bio = io.BytesIO(); im2.save(bio, "JPEG", quality=80); bio.seek(0); im2 = Image.open(bio)
d2 = b.detect_product(im2, 20); assert d2.prod[0]*900 <= 100 and d2.prod[1]*1300 <= 80 and d2.prod[2]*900 >= 500 and d2.prod[3]*1300 >= 700
print("classic scenes ok, bg of off-white photo:", d2.bg)

# 4. orientation symmetry: detection on a rotated / flipped photo == transformed box
im, tb, _ = photo(parts=[dict(box=(380, 300, 740, 900), gray=180), dict(box=(860, 380, 1200, 900), gray=150)], band=True)
p0 = b.detect_product(im, 20).prod
for op, f in (("cw", Image.Transpose.ROTATE_270), ("ccw", Image.Transpose.ROTATE_90), ("fh", Image.Transpose.FLIP_LEFT_RIGHT), ("fv", Image.Transpose.FLIP_TOP_BOTTOM)):
    pr = b.detect_product(im.transpose(f), 20).prod; want = b.rect_transform(p0, op)
    assert all(abs(x - y) < 0.03 for x, y in zip(pr, want)), (op, pr, want)
print("orientation symmetry ok")

# 5. product at centre wins over bigger gray things at the edge; dark product separates from a faint touching band
im, tb, _ = photo(parts=[dict(box=(640, 380, 960, 820), gray=120)], area=False)
d = ImageDraw.Draw(im); d.rectangle((0, 1000, 1600, 1200), fill=(215, 215, 215)); d.rectangle((0, 0, 260, 1200), fill=(225, 225, 225))
det = b.detect_product(im, 20); cut, ext = metrics(im, tb, det); assert max(cut) <= 1 and max(ext) <= 6, (cut, ext)
im, tb, _ = photo(parts=[dict(box=(560, 300, 1040, 1000), gray=60)], area=False, lines=False)
ImageDraw.Draw(im).rectangle((0, 990, 1600, 1200), fill=(222, 222, 222))      # faint band that touches the product
det = b.detect_product(im, 20); cut, ext = metrics(im, tb, det); print("dark product on a touching faint band: cut/ext", [round(v, 1) for v in cut], [round(v, 1) for v in ext])
assert max(cut) <= 1 and max(ext) <= 8, (cut, ext)
print("centre object selection ok")

# 6. obstacle map marks lines / areas but not the product
im, tb, _ = photo(parts=[dict(box=(520, 260, 1080, 900), gray=190)], band=True)
det = b.detect_product(im, 20); g = det.obst.shape[0]
assert det.obst.any() and not det.obst[int(.3*g):int(.7*g), int(.38*g):int(.62*g)].any()
print("obstacle grid ok: %d cells marked" % det.obst.sum())

# 7. speed on a big photo
im, tb, _ = photo(parts=[dict(box=(1000, 480, 2000, 1700), gray=200)], size=(3000, 2250), jpeg=88)
t0 = time.time(); b.detect_product(im, 20); dt = time.time() - t0
print("3000x2250 detect: %.2fs" % dt); assert dt < 4
print("DETECTOR TESTS PASSED")
