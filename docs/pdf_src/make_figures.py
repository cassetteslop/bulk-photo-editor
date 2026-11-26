"""Render the example images used in the PDF (synthetic photos; run from the project root)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path[:0] = [os.path.join(ROOT, "tests", "support"), ROOT]
import faketk  # noqa: F401  (tests' tkinter stand-in; the figures need no GUI)
from PIL import Image, ImageDraw
from legacy import b
from gen import photo
from gen_dark import dark_photo

OUT = os.path.join(ROOT, "docs", "img")
os.makedirs(OUT, exist_ok=True)
DEF = dict(b.DEFAULTS, rotate=0, flip_h=False, flip_v=False, resize_mode="None", padding=8)


def example(name, im):
    det = b.detect_for_settings(im, DEF)
    crop = b.compute_crop(det.prod, im.size, DEF["padding"], DEF["aspect"], DEF["extend"], det.obst, DEF["grow"])
    W, H = im.size
    over = im.copy().convert("RGB")
    d = ImageDraw.Draw(over)
    pr = det.prod
    d.rectangle((pr[0] * W, pr[1] * H, pr[2] * W, pr[3] * H), outline=(255, 160, 0), width=5)          # detected product
    d.rectangle((crop[0] * W, crop[1] * H, crop[2] * W, crop[3] * H), outline=(10, 132, 255), width=9)  # crop box
    over.thumbnail((900, 700))
    over.save(os.path.join(OUT, f"{name}_detect.jpg"), quality=88)
    res = b.process_image(im, DEF, b.Levels())
    res.thumbnail((520, 520))
    res.save(os.path.join(OUT, f"{name}_result.jpg"), quality=90)
    print(name, det.kind, [round(v, 2) for v in crop])


light, _, _ = photo(parts=[dict(box=(500, 260, 1100, 980), gray=150, kind="round")], shadow=False, seed=3)
example("light", light)
dark, _, _ = dark_photo(parts=[dict(box=(500, 260, 1100, 980), color=(228, 218, 196), kind="round")],
                        bg=(88, 58, 40), grad=(10, -8), vignette=22, seam=True, seam_y=0.9, block=True, jpeg=80, seed=5)
example("dark", dark)
