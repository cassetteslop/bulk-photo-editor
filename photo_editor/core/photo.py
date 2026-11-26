"""Per-photo editing state."""

class Photo:
    def __init__(self, path):
        self.path = path
        self.lv_mode = "global"        # "global" or "custom"
        self.lv = None                 # this photo's own Levels (used when lv_mode == "custom")
        self.crop = None               # normalised (x0, y0, x1, y1); may extend past 0..1
        self.manual = False            # True once the user has moved the crop box
        self.prod = None               # detected product box (normalised)
        self.obst = None               # keep-out grid (gray areas / lines around the product)
        self.bg = (255, 255, 255)      # detected background colour
        self.osize = None              # (w, h) after EXIF orientation
