"""Shared constants and the default value of every user setting."""

from PIL import Image

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}
ROT = {
    90: Image.Transpose.ROTATE_270,   # clockwise
    180: Image.Transpose.ROTATE_180,
    270: Image.Transpose.ROTATE_90,
}
ASPECTS = {  # name -> width/height ("orig" = same ratio as the photo)
    "Free": None, "Original": "orig", "1:1": 1.0, "4:5": 0.8, "3:4": 0.75,
    "2:3": 2 / 3, "5:4": 1.25, "4:3": 4 / 3, "3:2": 1.5, "16:9": 16 / 9,
}
GRIDS = {"Off": 0, "Thirds": 3, "4 × 4": 4, "8 × 8": 8}
BG_MODES = ("Auto", "Light", "Dark")   # which detector profile to use; Auto looks at the photo's border

DEFAULTS = dict(
    brightness=0, contrast=0, saturation=0, sharpness=0,
    grayscale=False, sepia=False,
    resize_mode="None", max_w=1920, max_h=1080, percent=50,
    wm_text="", wm_pos="Bottom right", wm_size=4, wm_opacity=70,
    wm_image="", wm_img_size=20,
    crop_enabled=True, padding=5, tolerance=20, bg_mode="Auto", tol_dark=18, shadow_dark=False, aspect="Free", extend=True, shadow=False, grow=0,
)

HI_SIDE = 3000             # longest side of the zoomable copy kept in memory
PREVIEW_SIDE = 1100
WORK_SIDE = 1920           # detection works at this size...
ANALYSIS_SIDE = 640        # ...and is pooled down to this
OBST_GRID = 160            # resolution of the stored "keep out" map
