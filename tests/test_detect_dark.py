"""Dark / brown backdrops: profile selection, per-profile settings, and detection accuracy."""
import os, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
import faketk
from PIL import Image
from legacy import b
from gen import photo
from gen_dark import CD, dark_photo

DEF = dict(b.DEFAULTS)

def metrics(im, tb, p):
    W, H = im.size
    px = (p[0]*W, p[1]*H, p[2]*W, p[3]*H); tw, th = tb[2]-tb[0], tb[3]-tb[1]
    cut = [max(0, c)*100 for c in ((px[0]-tb[0])/tw, (px[1]-tb[1])/th, (tb[2]-px[2])/tw, (tb[3]-px[3])/th)]
    ext = [max(0, e)*100 for e in ((tb[0]-px[0])/tw, (tb[1]-px[1])/th, (px[2]-tb[2])/tw, (px[3]-tb[3])/th)]
    return cut, ext

# 1. profile selection (Auto / Light / Dark)
dark_im, tb, _ = dark_photo(parts=[dict(box=(520, 260, 1080, 960), color=(235, 225, 205), kind="round")])
light_im, _, _ = photo(parts=[dict(box=(520, 260, 1080, 960), gray=120, kind="round")])
assert b.classify_background(dark_im) == "dark" and b.classify_background(light_im) == "light"
assert b.profile_for(dark_im, DEF)[0] == "dark" and b.profile_for(light_im, DEF)[0] == "light"
assert b.profile_for(light_im, dict(DEF, bg_mode="Dark"))[0] == "dark"
assert b.profile_for(dark_im, dict(DEF, bg_mode="Light"))[0] == "light"
k, tol, sh = b.profile_for(dark_im, dict(DEF, tol_dark=31, shadow_dark=True, tolerance=9))
assert (k, tol, sh) == ("dark", 31, True)
k, tol, sh = b.profile_for(light_im, dict(DEF, tol_dark=31, shadow_dark=True, tolerance=9))
assert (k, tol, sh) == ("light", 9, False)
assert b.tolerance_for_bg((88, 58, 40), dict(DEF, tol_dark=31)) == 31 and b.tolerance_for_bg((255, 255, 255), dict(DEF, tolerance=9)) == 9
print("profile selection ok")

# 2. accuracy on the dark suite (Auto mode, default settings)
LOOSE = {"walnut/cream wide rect + shadow": 18, "tan-kraft/black + seam + shadow": 10}
worst_cut = 0; t_tot = 0
for name, kw in CD:
    im, tb, _ = dark_photo(**kw)
    t0 = time.time(); det = b.detect_for_settings(im, DEF); t_tot += time.time() - t0
    assert det.kind == "dark", (name, det.kind)
    assert det.prod is not None, name
    cut, ext = metrics(im, tb, det.prod)
    assert max(cut) <= 1.0, (name, cut)
    assert max(ext) <= LOOSE.get(name, 6.0), (name, ext)
    worst_cut = max(worst_cut, max(cut))
print(f"dark suite: {len(CD)} cases, worst cut {worst_cut:.2f}%, avg detect {t_tot/len(CD):.2f}s")

# 3. light photos are unchanged by the new code path (Auto still picks the light profile)
det = b.detect_for_settings(light_im, DEF)
assert det.kind == "light" and det.bg == (255, 255, 255)
# 4. the whole pipeline on a dark photo: product centred on the backdrop colour, no white fill
out = b.process_image(dark_im, dict(DEF, rotate=0, flip_h=False, flip_v=False, resize_mode="None"), b.Levels())
px = out.getpixel((2, 2)); assert max(px) < 140, px             # corner is brown, not white
print("pipeline on dark photo ok, corner pixel", px)
print("DARK DETECTION TESTS PASSED")
