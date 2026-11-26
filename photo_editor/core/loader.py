"""Open a photo for the editor: zoomable copy, preview and histogram."""

from PIL import Image, ImageOps

from photo_editor.core.constants import HI_SIDE, PREVIEW_SIDE

def load_source(path):
    """Open a photo for the editor: a zoomable copy (<= HI_SIDE), a preview and a histogram."""
    with Image.open(path) as im:
        w0, h0 = im.size
        try:
            if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):
                w0, h0 = h0, w0
        except Exception:
            pass
        sc = 1
        while sc < 8 and max(im.size) // (sc * 2) >= HI_SIDE:
            sc *= 2
        if sc > 1:
            im.draft("RGB", (im.size[0] // sc, im.size[1] // sc))   # fast JPEG down-scaling
        im = ImageOps.exif_transpose(im)
        im.load()
        if max(im.size) > HI_SIDE:
            im.thumbnail((HI_SIDE, HI_SIDE), Image.Resampling.LANCZOS)
        hi = im.copy()
    pre = hi.copy()
    pre.thumbnail((PREVIEW_SIDE, PREVIEW_SIDE), Image.Resampling.LANCZOS)
    rgb = pre.convert("RGB")
    h = rgb.histogram()
    hist = {"R": h[:256], "G": h[256:512], "B": h[512:], "RGB": rgb.convert("L").histogram()}
    return dict(hi=hi, pre=pre, hist=hist, osize=(w0, h0))
