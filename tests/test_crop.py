import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
SP = tempfile.mkdtemp(prefix="bpe_tests_")
import faketk
import numpy as np
from PIL import Image
from legacy import b
from gen import photo

W, H = 1600, 1200
prod = (0.35, 0.30, 0.70, 0.78)                       # normalised product box
pw, ph = (prod[2]-prod[0])*W, (prod[3]-prod[1])*H
S = (W, H)
def dims(c): return (c[2]-c[0])*W, (c[3]-c[1])*H
def centre(c): return ((c[0]+c[2])/2*W, (c[1]+c[3])/2*H)

# grow == 0 is exactly the old behaviour
base = b.compute_crop(prod, S, 5, "Free", True)
assert b.compute_crop(prod, S, 5, "Free", True, None, 0) == base
# positive grow: +x% of the photo's width / height, same centre
for g in (5, 10, 25, 50):
    c = b.compute_crop(prod, S, 5, "Free", True, None, g)
    (bw, bh), (cw, ch) = dims(base), dims(c)
    assert abs((cw - bw) - g/100*W) < 1e-6 and abs((ch - bh) - g/100*H) < 1e-6, g
    assert abs(centre(c)[0]-centre(base)[0]) < 1e-6 and abs(centre(c)[1]-centre(base)[1]) < 1e-6
    # never cuts the product when growing
    assert c[0] <= prod[0] and c[1] <= prod[1] and c[2] >= prod[2] and c[3] >= prod[3]
# negative grow shrinks, same centre, floor keeps a sane minimum
for g in (-5, -20):
    c = b.compute_crop(prod, S, 5, "Free", True, None, g); (bw, bh), (cw, ch) = dims(base), dims(c)
    assert abs((cw - bw) - g/100*W) < 1e-6 and abs((ch - bh) - g/100*H) < 1e-6 and centre(c) == centre(base) or abs(centre(c)[0]-centre(base)[0]) < 1e-6
c = b.compute_crop(prod, S, 5, "Free", True, None, -50); cw, ch = dims(c); assert cw >= 0.02*W - 1e-6 and ch >= 0.02*H - 1e-6
# locked aspect ratio stays exact after grow (both directions), including 'Original'
for asp, r in (("1:1", 1.0), ("4:5", 0.8), ("3:2", 1.5), ("16:9", 16/9), ("Original", W/H)):
    for g in (-15, 0, 12, 40):
        c = b.compute_crop(prod, S, 5, asp, True, None, g); cw, ch = dims(c)
        assert abs(cw/ch - r) < 1e-6, (asp, g, cw/ch)
        if g >= 0: assert c[0] <= prod[0] + 1e-9 and c[1] <= prod[1] + 1e-9 and c[2] >= prod[2] - 1e-9 and c[3] >= prod[3] - 1e-9, (asp, g)
# extend=False keeps the box inside the photo, even for big grow
for g in (0, 20, 50):
    c = b.compute_crop(prod, S, 5, "Free", False, None, g)
    assert c[0] >= -1e-9 and c[1] >= -1e-9 and c[2] <= 1 + 1e-9 and c[3] <= 1 + 1e-9, (g, c)
# extend=True may go beyond the photo
c = b.compute_crop((0.05, 0.1, 0.45, 0.9), S, 5, "Free", True, None, 30); assert c[0] < 0
# grow applies on top of the obstacle-limited padding
obst = np.zeros((160, 160), bool); obst[:, 130:] = True                    # gray area right of x = 0.81
tight = b.compute_crop(prod, S, 40, "Free", True, obst, 0)
assert tight[2] <= 0.82 + 1e-6, tight                                       # padding shrank to avoid the gray area
grown = b.compute_crop(prod, S, 40, "Free", True, obst, 10)
assert abs(dims(grown)[0] - dims(tight)[0] - 0.10*W) < 1e-6                 # then +10% of the photo width on top
print("compute_crop / apply_grow ok")

# full pipeline: output pixel size follows grow
S0 = dict(b.DEFAULTS, rotate=0, flip_h=False, flip_v=False, crop_enabled=True, padding=5, aspect="Free", extend=True)
im, tb, _ = photo(parts=[dict(box=(520, 260, 1080, 900), gray=190)], band=True)
o0 = b.process_image(im, dict(S0, grow=0), None)
o1 = b.process_image(im, dict(S0, grow=10), None)
oN = b.process_image(im, dict(S0, grow=-10), None)
print("output sizes  -10%:", oN.size, "  0%:", o0.size, " +10%:", o1.size)
assert abs((o1.size[0] - o0.size[0]) - 160) <= 2 and abs((o1.size[1] - o0.size[1]) - 120) <= 2
assert abs((oN.size[0] - o0.size[0]) + 160) <= 2 and abs((oN.size[1] - o0.size[1]) + 120) <= 2
# grown crop is centred: margins left/right and top/bottom match (clean photo, so only the product is dark)
im, tb, _ = photo(parts=[dict(box=(520, 260, 1080, 900), gray=120)], lines=False, area=False, dust=False)
o1 = b.process_image(im, dict(S0, grow=10), None)
a = np.asarray(o1.convert("RGB")).astype(int); m = np.abs(a - 255).max(axis=2) > 40; ys, xs = np.nonzero(m)
l, r, t, bt = xs.min(), a.shape[1]-1-xs.max(), ys.min(), a.shape[0]-1-ys.max()
assert abs(l - r) <= 8 and abs(t - bt) <= 8, (l, r, t, bt)
print("pipeline grow ok; margins l/r/t/b:", l, r, t, bt)
print("CROP TESTS PASSED")
