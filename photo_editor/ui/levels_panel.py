"""Levels logic: global vs per-photo, sliders, histogram."""

import math
from tkinter import messagebox

from photo_editor.ui.constants import HH, HIST_COLORS, HW

class LevelsMixin:
    """Levels logic: global vs per-photo, sliders, histogram."""

    # ---- levels ----------------------------------------------------------
    def levels_for(self, p):
        if p.lv_mode == "custom" and p.lv is not None:
            return p.lv
        return self.global_levels

    def edit_levels(self):
        p = self.cur
        if self.scope.get() == "this" and p is not None:
            if p.lv is None:
                p.lv = self.global_levels.copy()
            p.lv_mode = "custom"
            return p.lv
        return self.global_levels

    def update_scope_note(self):
        if self.scope.get() == "this":
            txt = "Only this photo changes. It ignores the global levels (marked ✎ in the list)."
        else:
            txt = "Changes affect every photo that doesn't have its own levels (✎)."
        self.scope_note.config(text=txt)

    def on_scope(self):
        p = self.cur
        if self.scope.get() == "this":
            if p is None:
                self.scope.set("all")
                self.status.set("Select a photo first.")
                return
            if p.lv is None:
                p.lv = self.global_levels.copy()  # start from the global values, then tweak
            p.lv_mode = "custom"
        elif p is not None:
            p.lv_mode = "global"
        self.refresh_item(self.cur_idx)
        self.update_scope_note()
        self.sync_levels_ui()
        self.schedule_preview()

    def on_channel(self):
        self.sync_levels_ui()
        self.draw_hist()

    def on_lv_slider(self, kind, val):
        if self._syncing:
            return
        if kind == "gamma":
            val = 10 ** (val / 100.0)
        self.set_level_param(kind, val)

    def set_level_param(self, kind, val):
        lv = self.edit_levels()
        ch = self.lv_channel.get()
        b, g, w = lv.d[ch]
        if kind == "black":
            b = int(round(min(max(val, 0), w - 1)))
        elif kind == "white":
            w = int(round(min(max(val, b + 1), 255)))
        else:
            g = min(max(float(val), 0.1), 9.99)
        lv.d[ch] = [b, g, w]
        self.sync_levels_ui()
        self.schedule_preview()

    def reset_param(self, kind):
        self.set_level_param(kind, {"black": 0, "gamma": 1.0, "white": 255}[kind])

    def sync_levels_ui(self):
        b, g, w = self.edit_levels().d[self.lv_channel.get()]
        self._syncing = True
        try:
            self.lv_black.set(b)
            self.lv_white.set(w)
            self.lv_gamma.set(100 * math.log10(g))
        finally:
            self._syncing = False
        self.lv_labels["black"].config(text=str(b))
        self.lv_labels["white"].config(text=str(w))
        self.lv_labels["gamma"].config(text=f"{g:.2f}")
        self.draw_markers()

    def reset_channel(self):
        self.edit_levels().reset(self.lv_channel.get())
        self.sync_levels_ui()
        self.schedule_preview()

    def reset_levels(self):
        self.edit_levels().reset()
        self.sync_levels_ui()
        self.schedule_preview()

    def auto_levels(self):
        if not self.hist:
            return
        ch = self.lv_channel.get()
        data = self.hist[ch]
        clip = sum(data) * 0.001
        acc, b = 0, 0
        for i, n in enumerate(data):
            acc += n
            if acc > clip:
                b = i
                break
        acc, w = 0, 255
        for i in range(255, -1, -1):
            acc += data[i]
            if acc > clip:
                w = i
                break
        if w - b < 2:
            return
        self.edit_levels().d[ch] = [b, 1.0, w]
        self.sync_levels_ui()
        self.schedule_preview()

    def copy_levels_to_selected(self):
        lv = self.edit_levels()
        n = 0
        for i in self.listbox.curselection():
            if i == self.cur_idx and self.scope.get() == "this":
                continue
            p = self.photos[i]
            p.lv, p.lv_mode = lv.copy(), "custom"
            self.refresh_item(i)
            n += 1
        self.status.set(f"Copied these levels to {n} photo(s) as their own.")
        p = self.cur
        if p is not None:
            self.scope.set("this" if p.lv_mode == "custom" else "all")
        self.update_scope_note()
        self.sync_levels_ui()
        self.schedule_preview()

    def make_global(self):
        p = self.cur
        if p is None or self.scope.get() != "this" or p.lv is None:
            self.status.set("Choose “This photo only” first to make its levels global.")
            return
        if not messagebox.askyesno("Make global",
                                   "Replace the global levels with this photo's levels?\n"
                                   "Every photo without its own levels will change."):
            return
        self.global_levels = p.lv.copy()
        p.lv_mode = "global"
        self.scope.set("all")
        self.refresh_item(self.cur_idx)
        self.update_scope_note()
        self.sync_levels_ui()
        self.schedule_preview()

    def drop_custom(self):
        p = self.cur
        if p is None:
            return
        p.lv, p.lv_mode = None, "global"
        self.scope.set("all")
        self.refresh_item(self.cur_idx)
        self.update_scope_note()
        self.sync_levels_ui()
        self.schedule_preview()

    # ---- histogram -------------------------------------------------------
    @staticmethod
    def hx(v):
        return 8 + v / 255.0 * (HW - 16)

    def draw_hist(self):
        c = self.hist_canvas
        c.delete("hist")
        data = self.hist.get(self.lv_channel.get()) if self.hist else None
        if data:
            mx = max(max(data[1:255]), 1)       # ignore clipped end bins when scaling
            colour = HIST_COLORS[self.lv_channel.get()]
            for i, n in enumerate(data):
                h = min(n / mx, 1.0) * (HH - 26)
                if h >= 0.5:
                    x = self.hx(i)
                    c.create_rectangle(x, HH - 20 - h, x + 1.3, HH - 20, fill=colour, outline="", tags="hist")
        self.draw_markers()

    def draw_markers(self):
        c = self.hist_canvas
        c.delete("mk")
        b, g, w = self.edit_levels().d[self.lv_channel.get()]
        y = HH - 19
        xs = ((self.hx(b), "#000000"), (self.hx(b + (w - b) * 0.5 ** g), "#888888"), (self.hx(w), "#ffffff"))
        for x, fill in xs:
            c.create_polygon(x, y, x - 6, y + 13, x + 6, y + 13, fill=fill, outline="#cccccc", tags="mk")

    def hist_press(self, e):
        b, g, w = self.edit_levels().d[self.lv_channel.get()]
        cands = {"black": self.hx(b), "gamma": self.hx(b + (w - b) * 0.5 ** g), "white": self.hx(w)}
        k = min(cands, key=lambda n: abs(cands[n] - e.x))
        self.hist_drag = k if abs(cands[k] - e.x) <= 14 else None
        self.hist_motion(e)

    def hist_motion(self, e):
        k = self.hist_drag
        if not k:
            return
        v = (e.x - 8) / (HW - 16) * 255
        b, g, w = self.edit_levels().d[self.lv_channel.get()]
        if k == "gamma":
            tpos = min(max((v - b) / max(w - b, 1), 0.01), 0.99)
            self.set_level_param("gamma", math.log(tpos) / math.log(0.5))   # marker sits at 0.5 ** gamma
        else:
            self.set_level_param(k, v)
