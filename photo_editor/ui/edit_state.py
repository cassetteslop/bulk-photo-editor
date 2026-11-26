"""Rotate / flip, settings snapshot and crop (re)detection."""

import tkinter as tk

from photo_editor.core.constants import DEFAULTS
from photo_editor.core.cropping import compute_crop
from photo_editor.core.detection import detect_for_settings
from photo_editor.core.geometry import obst_transform, rect_transform
from photo_editor.core.image_ops import oriented

class EditStateMixin:
    """Rotate / flip, settings snapshot and crop (re)detection."""

    # ---- orientation -----------------------------------------------------
    def rotate(self, delta):
        self.rot = (self.rot + delta) % 360
        self.fh, self.fv = self.fv, self.fh   # keeps "rotate, then flip" state equivalent
        self.transform_all("cw" if delta > 0 else "ccw")

    def flip(self, axis):
        if axis == "h":
            self.fh = not self.fh
        else:
            self.fv = not self.fv
        self.transform_all("fh" if axis == "h" else "fv")

    def transform_all(self, op):
        for p in self.photos:
            if p.crop:
                p.crop = rect_transform(p.crop, op)
            if p.prod:
                p.prod = rect_transform(p.prod, op)
            if p.obst is not None:
                p.obst = obst_transform(p.obst, op)
        self.zoom, self.pan = 1.0, [0.0, 0.0]
        self.schedule_preview()

    def full_size(self, p):
        w, h = p.osize
        return (h, w) if self.rot in (90, 270) else (w, h)

    def reset_color(self):
        for k in ("brightness", "contrast", "saturation", "sharpness"):
            self.v[k].set(0)
        self.v["grayscale"].set(False)
        self.v["sepia"].set(False)

    # ---- crop state ------------------------------------------------------
    def settings(self):
        s = {}
        for k, var in self.v.items():
            try:
                s[k] = var.get()
            except tk.TclError:  # e.g. an empty spinbox
                s[k] = DEFAULTS[k]
        s["rotate"], s["flip_h"], s["flip_v"] = self.rot, self.fh, self.fv
        return s

    def invalidate_crops(self, redetect):
        for p in self.photos:
            if not p.manual:
                p.crop = None
                if redetect:
                    p.prod = p.obst = None
        self.schedule_preview()

    def redetect_current(self):
        p = self.cur
        if p:
            p.crop = p.prod = p.obst = None
            p.manual = False
            self.refresh_item(self.cur_idx)
            self.schedule_preview()

    def redetect_all(self):
        for p in self.photos:
            p.crop = p.prod = p.obst = None
            p.manual = False
        for i in range(len(self.photos)):
            self.refresh_item(i)
        self.schedule_preview()

    def oriented_hi(self, s):
        key = (self.cur.path, id(self.src_hi), s["rotate"], s["flip_h"], s["flip_v"])
        if self.hi_cache and self.hi_cache[0] == key:
            return self.hi_cache[1]
        rgb, _ = oriented(self.src_hi, s)
        self.hi_cache = (key, rgb)
        return rgb

    def ensure_crop(self, rgb=None):
        p = self.cur
        if p is None or self.src_hi is None or p.crop is not None:
            return
        s = self.settings()
        if not s["crop_enabled"]:
            return
        if rgb is None:
            rgb = self.oriented_hi(s)
        if p.prod is None:
            det = detect_for_settings(rgb, s)
            p.prod, p.obst = det.prod, det.obst
            if det.prod:
                p.bg = det.bg
        if p.prod is None:
            p.crop = (0.0, 0.0, 1.0, 1.0)   # nothing found: keep the whole photo
        else:
            p.crop = compute_crop(p.prod, rgb.size, s["padding"], s["aspect"], s["extend"], p.obst, s["grow"])
