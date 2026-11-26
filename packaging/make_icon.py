"""Draw the app icon and write .icns (macOS), .ico (Windows) and PNGs. Needs only Pillow.
    python packaging/make_icon.py"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024


def draw():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # rounded square with a vertical gradient (macOS icon grid: ~824px square centred)
    m, r = 100, 185
    grad = Image.new("RGB", (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / S
        gd.line([(0, y), (S, y)], fill=(int(46 - 20 * t), int(52 - 22 * t), int(66 - 26 * t)))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((m, m, S - m, S - m), r, fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    # "photo": mountains + sun inside a frame
    x0, y0, x1, y1 = 250, 290, 774, 700
    d.rounded_rectangle((x0, y0, x1, y1), 34, fill=(236, 240, 247))
    d.ellipse((560, 345, 680, 465), fill=(255, 190, 70))
    d.polygon([(x0, y1), (x0 + 150, 520), (x0 + 270, 640), (x0 + 360, 560), (x1, y1)], fill=(60, 120, 215))
    d.polygon([(x0 + 250, y1), (x0 + 360, 590), (x0 + 470, y1)], fill=(40, 90, 175))
    # crop brackets in the accent blue
    c, w, L = (10, 132, 255), 30, 120
    for (cx, cy, sx, sy) in ((x0 - 40, y0 - 40, 1, 1), (x1 + 40, y0 - 40, -1, 1),
                             (x0 - 40, y1 + 40, 1, -1), (x1 + 40, y1 + 40, -1, -1)):
        for ex, ey in ((cx + sx * L, cy + sy * w), (cx + sx * w, cy + sy * L)):
            d.rectangle((min(cx, ex), min(cy, ey), max(cx, ex), max(cy, ey)), fill=c)
    return img


if __name__ == "__main__":
    icon = draw()
    icon.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(HERE, "BulkPhotoEditor.png"))
    res = os.path.join(HERE, "..", "photo_editor", "resources")
    os.makedirs(res, exist_ok=True)
    icon.resize((256, 256), Image.Resampling.LANCZOS).save(os.path.join(res, "icon.png"))   # window icon (all OSes)
    icon.save(os.path.join(HERE, "windows", "BulkPhotoEditor.ico"),
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    icon.save(os.path.join(HERE, "BulkPhotoEditor.icns"),
              sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])
    print("wrote BulkPhotoEditor.icns / .ico / .png and photo_editor/resources/icon.png")
