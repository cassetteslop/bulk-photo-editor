"""The preview canvas: zoom, pan, grid, crop box editing."""

import tkinter as tk
from PIL import Image, ImageDraw, ImageEnhance, ImageTk

from photo_editor.core.constants import ASPECTS, GRIDS
from photo_editor.core.image_ops import luminance_mean, tone_adjust
from photo_editor.core.pipeline import process_image
from photo_editor.ui.constants import HANDLE_CURSORS

class ViewerMixin:
    """The preview canvas: zoom, pan, grid, crop box editing."""

    # ---- view: layout, zoom, pan ---------------------------------------------
    def on_view_mode(self):
        self.zoom, self.pan = 1.0, [0.0, 0.0]
        self.schedule_preview()

    def fit_layout(self, ia, bounds=(-0.02, -0.02, 1.02, 1.02)):
        """Where the photo goes in the canvas at 'Fit' (bounds = normalised area to show)."""
        cw, ch = self.cv_size
        bx0, by0, bx1, by1 = bounds
        vw, vh = bx1 - bx0, by1 - by0
        dw = min((cw - 20) / vw, (ch - 20) * ia / vh)
        dh = dw / ia
        ox = 10 + ((cw - 20) - vw * dw) / 2 - bx0 * dw
        oy = 10 + ((ch - 20) - vh * dh) / 2 - by0 * dh
        return (ox, oy, dw, dh)

    def update_vm(self):
        """Combine the fit layout with zoom + pan into the actual image rectangle."""
        ox0, oy0, dw0, dh0 = self.base
        cw, ch = self.cv_size
        z = self.zoom
        if z <= 1.0001:
            z, self.pan = 1.0, [0.0, 0.0]
        dw, dh = dw0 * z, dh0 * z
        ox = cw / 2 + (ox0 - cw / 2) * z + self.pan[0]
        oy = ch / 2 + (oy0 - ch / 2) * z + self.pan[1]
        margin = 60                      # never lose the photo completely
        ox = min(max(ox, margin - dw), cw - margin)
        oy = min(max(oy, margin - dh), ch - margin)
        self.pan = [ox - (cw / 2 + (ox0 - cw / 2) * z), oy - (ch / 2 + (oy0 - ch / 2) * z)]
        self.vm = dict(ox=int(round(ox)), oy=int(round(oy)), dw=max(1, int(round(dw))),
                       dh=max(1, int(round(dh))), cw=cw, ch=ch)
        self.zoom_text.set("Fit" if z <= 1.0001 and abs(dw - dw0) < 1 and self.ctx and
                           dw0 < self.ctx["size"][0] * 1.0001 and z == 1.0
                           else "%d%%" % round(dw / self.ctx["size"][0] * 100))

    def zmax(self):
        return max(4.0, 3.0 * self.ctx["size"][0] / self.base[2])

    def zoom_at(self, mx, my, z):
        if not self.ctx or not self.vm:
            return
        z = min(max(z, 1.0), self.zmax())
        if abs(z - self.zoom) < 1e-9:
            return
        vm = self.vm
        u = (mx - vm["ox"]) / vm["dw"]
        v = (my - vm["oy"]) / vm["dh"]
        ox0, oy0, dw0, dh0 = self.base
        cw, ch = self.cv_size
        self.zoom = z
        ox, oy = mx - u * dw0 * z, my - v * dh0 * z      # keep the point under the cursor fixed
        self.pan = [ox - (cw / 2 + (ox0 - cw / 2) * z), oy - (ch / 2 + (oy0 - ch / 2) * z)]
        self.view_changed()

    def zoom_step(self, factor):
        if self.ctx:
            cw, ch = self.cv_size
            self.zoom_at(cw / 2, ch / 2, self.zoom * factor)

    def zoom_fit(self):
        if self.ctx:
            self.zoom, self.pan = 1.0, [0.0, 0.0]
            self.view_changed()

    def zoom_100(self):
        if self.ctx:
            cw, ch = self.cv_size
            self.zoom_at(cw / 2, ch / 2, self.ctx["size"][0] / self.base[2])

    def view_changed(self):
        self.update_vm()
        # the Result view switches to a sharper render once you zoom past 'Fit'
        if self.ctx["mode"] == "Result" and (self.zoom > 1.0001) != self.ctx.get("hi"):
            self.render_preview()
        else:
            self.redraw()

    def on_wheel(self, e):
        if not self.ctx:
            return
        num = getattr(e, "num", None)
        if num == 4:
            d = 1
        elif num == 5:
            d = -1
        else:
            d = 1 if getattr(e, "delta", 0) > 0 else -1
        self.zoom_at(e.x, e.y, self.zoom * (1.25 ** d))

    def pan_start(self, e):
        if self.ctx:
            self.pan_drag = dict(sx=e.x, sy=e.y, px=self.pan[0], py=self.pan[1])

    def pan_move(self, e):
        d = self.pan_drag
        if not d or not self.ctx:
            return
        self.pan = [d["px"] + e.x - d["sx"], d["py"] + e.y - d["sy"]]
        self.update_vm()
        self.redraw()

    def pan_end(self, e):
        self.pan_drag = None

    # ---- preview ---------------------------------------------------------
    def schedule_preview(self):
        if self.preview_job:
            self.after_cancel(self.preview_job)
        self.preview_job = self.after(60, self.render_preview)

    @staticmethod
    def flat(img):
        """RGB / RGBA copy suitable for display."""
        if img.mode in ("RGB", "RGBA"):
            return img
        if "A" in img.getbands() or "transparency" in img.info:
            return img.convert("RGBA")
        return img.convert("RGB")

    def result_image(self, s, lv, p):
        use_hi = self.zoom > 1.0001
        src = self.src_hi if use_hi else self.preview_src
        key = (p.path, use_hi, tuple(sorted(s.items())), tuple(lv.luts()), p.crop, tuple(p.bg))
        if self.res_cache and self.res_cache[0] == key:
            return self.res_cache[1], use_hi
        img = process_image(src, s, lv, crop=p.crop, bg=p.bg, preview=True)
        self.res_cache = (key, img)
        return img, use_hi

    def render_preview(self):
        self.preview_job = None
        c = self.canvas
        cw, ch = c.winfo_width(), c.winfo_height()
        self.vm = self.ctx = None
        if cw < 40 or ch < 40:
            return
        self.cv_size = (cw, ch)
        p = self.cur
        if self.src_hi is None or p is None:
            c.delete("all")
            c.create_text(cw // 2, ch // 2, fill=self.palette.text_dim, text="Drop photos or folders here, or use Add files / Add folder")
            return
        s = self.settings()
        lv = self.levels_for(p)
        mode = self.view_mode.get()
        if mode == "Original":
            img = self.flat(self.src_hi)
            self.ctx = dict(mode=mode, img=img, size=img.size)
            self.base = self.fit_layout(img.width / img.height, (0, 0, 1, 1))
        elif mode == "Result":
            self.ensure_crop()
            img, use_hi = self.result_image(s, lv, p)
            self.ctx = dict(mode=mode, img=img, size=img.size, hi=use_hi)
            self.base = self.fit_layout(img.width / img.height, (0, 0, 1, 1))
        else:
            hi = self.oriented_hi(s)
            self.ensure_crop(hi)
            ref = luminance_mean(hi, lv) if s["contrast"] else None
            crop = p.crop if s["crop_enabled"] else None
            bounds = [-0.02, -0.02, 1.02, 1.02]        # photo, plus the crop box if it sticks out
            if crop:
                bounds = [min(bounds[0], crop[0] - 0.02), min(bounds[1], crop[1] - 0.02),
                          max(bounds[2], crop[2] + 0.02), max(bounds[3], crop[3] + 0.02)]
            self.ctx = dict(mode="Edit", hi=hi, s=s, lv=lv, ref=ref, size=hi.size)
            self.base = self.fit_layout(hi.width / hi.height, bounds)
        self.update_vm()
        self.redraw()

    def redraw(self):
        if not self.ctx or not self.vm:
            return
        if self.ctx["mode"] == "Edit":
            self.prepare_edit()
            self.draw_edit()
        else:
            self.draw_image_view()

    def view_region(self, img, vm):
        """The part of `img` that is visible in the canvas, resampled to screen size."""
        ox, oy, dw, dh = vm["ox"], vm["oy"], vm["dw"], vm["dh"]
        vx0, vy0 = max(0, ox), max(0, oy)
        vx1, vy1 = min(vm["cw"], ox + dw), min(vm["ch"], oy + dh)
        if vx1 - vx0 < 1 or vy1 - vy0 < 1:
            return None
        W, H = img.size
        box = ((vx0 - ox) / dw * W, (vy0 - oy) / dh * H, (vx1 - ox) / dw * W, (vy1 - oy) / dh * H)
        box = (max(0.0, box[0]), max(0.0, box[1]), min(float(W), box[2]), min(float(H), box[3]))
        out = img.resize((vx1 - vx0, vy1 - vy0), Image.Resampling.BILINEAR, box=box)
        return out, vx0, vy0

    def prepare_edit(self):
        ctx = self.ctx
        ctx["bright"] = None
        out = self.view_region(ctx["hi"], self.vm)
        if out is None:
            return
        vis, vx0, vy0 = out
        bright = tone_adjust(vis, ctx["s"], ctx["lv"], ctx["ref"])
        p = self.cur
        flat = dict(ctx["s"], sharpness=0)
        fill = tone_adjust(Image.new("RGB", (1, 1), tuple(p.bg)), flat, ctx["lv"], ctx["ref"]).getpixel((0, 0))
        ctx.update(bright=bright, dim=ImageEnhance.Brightness(bright).enhance(0.35),
                   vx0=vx0, vy0=vy0, fill=fill)

    def canvas_rect(self, crop):
        vm = self.vm
        return (vm["ox"] + crop[0] * vm["dw"], vm["oy"] + crop[1] * vm["dh"],
                vm["ox"] + crop[2] * vm["dw"], vm["oy"] + crop[3] * vm["dh"])

    def crop_active(self):
        p = self.cur
        return bool(p and p.crop and self.vm and self.ctx and self.ctx["mode"] == "Edit"
                    and self.v["crop_enabled"].get())

    def draw_image_view(self):
        c, vm, ctx = self.canvas, self.vm, self.ctx
        c.delete("all")
        base = Image.new("RGB", (vm["cw"], vm["ch"]), self.palette.canvas_rgb)
        out = self.view_region(ctx["img"], vm)
        if out:
            vis, vx0, vy0 = out
            if vis.mode == "RGBA":
                base.paste(vis, (vx0, vy0), vis.getchannel("A"))
            else:
                base.paste(vis, (vx0, vy0))
        self.disp = ImageTk.PhotoImage(base)
        c.create_image(0, 0, image=self.disp, anchor="nw")
        self.draw_grid((vm["ox"], vm["oy"], vm["ox"] + vm["dw"], vm["oy"] + vm["dh"]))

    def draw_grid(self, rect):
        n = GRIDS.get(self.grid_mode.get(), 0)
        if not n:
            return
        x0, y0, x1, y1 = rect
        c = self.canvas
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            y = y0 + (y1 - y0) * i / n
            for line in ((x, y0, x, y1), (x0, y, x1, y)):
                c.create_line(*line, fill="#000000", width=1)             # dark under-line + white
                c.create_line(*line, fill="#ffffff", dash=(4, 4))         # dashes: visible on any photo

    def draw_edit(self):
        c, ctx, vm, p = self.canvas, self.ctx, self.vm, self.cur
        c.delete("all")
        ox, oy, dw, dh = vm["ox"], vm["oy"], vm["dw"], vm["dh"]
        base = Image.new("RGB", (vm["cw"], vm["ch"]), self.palette.canvas_rgb)
        crop = p.crop if self.v["crop_enabled"].get() else None
        bright = ctx.get("bright")
        if bright is not None:
            vx0, vy0 = ctx["vx0"], ctx["vy0"]
            if crop:
                base.paste(ctx["dim"], (vx0, vy0))
                x0, y0, x1, y1 = [int(round(v)) for v in self.canvas_rect(crop)]
                ImageDraw.Draw(base).rectangle([x0, y0, x1 - 1, y1 - 1], fill=ctx["fill"])
                ix0, iy0 = max(x0, vx0), max(y0, vy0)
                ix1, iy1 = min(x1, vx0 + bright.width), min(y1, vy0 + bright.height)
                if ix1 > ix0 and iy1 > iy0:
                    base.paste(bright.crop((ix0 - vx0, iy0 - vy0, ix1 - vx0, iy1 - vy0)), (ix0, iy0))
            else:
                base.paste(bright, (vx0, vy0))
        self.disp = ImageTk.PhotoImage(base)
        c.create_image(0, 0, image=self.disp, anchor="nw")

        photo_rect = (ox, oy, ox + dw, oy + dh)
        if not crop:
            self.draw_grid(photo_rect)
            return
        x0, y0, x1, y1 = self.canvas_rect(crop)
        self.draw_grid(photo_rect if self.grid_whole.get() else (x0, y0, x1, y1))
        c.create_rectangle(x0, y0, x1, y1, outline="#ffffff", width=2)
        c.create_rectangle(x0, y0, x1, y1, outline=self.palette.accent, dash=(5, 5))
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        c.create_line(mx - 9, my, mx + 9, my, fill=self.palette.accent)
        c.create_line(mx, my - 9, mx, my + 9, fill=self.palette.accent)
        for hx, hy in self.handle_points((x0, y0, x1, y1)).values():
            c.create_rectangle(hx - 5, hy - 5, hx + 5, hy + 5, fill="#ffffff", outline=self.palette.accent)
        fw, fh = self.full_size(p)
        label = "%d × %d px" % (round((crop[2] - crop[0]) * fw), round((crop[3] - crop[1]) * fh))
        c.create_text(x0 + 7, y0 + 7, text=label, anchor="nw", fill="#000000")
        c.create_text(x0 + 6, y0 + 6, text=label, anchor="nw", fill="#ffffff")

    @staticmethod
    def handle_points(r):
        x0, y0, x1, y1 = r
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        return {"nw": (x0, y0), "ne": (x1, y0), "sw": (x0, y1), "se": (x1, y1),
                "n": (mx, y0), "s": (mx, y1), "w": (x0, my), "e": (x1, my)}

    # ---- mouse: crop box / pan ------------------------------------------------
    def hit(self, x, y):
        r = self.canvas_rect(self.cur.crop)
        pts = self.handle_points(r)
        for name in ("nw", "ne", "sw", "se", "n", "s", "w", "e"):
            px, py = pts[name]
            if abs(x - px) <= 9 and abs(y - py) <= 9:
                return name
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return "move"
        return None

    def lock_ratio(self):
        r = ASPECTS.get(self.v["aspect"].get())
        if r == "orig":
            return self.vm["dw"] / self.vm["dh"]
        return r

    def on_motion(self, e):
        cursor = ""
        if self.crop_active() and self.drag is None:
            cursor = HANDLE_CURSORS.get(self.hit(e.x, e.y), "")
        try:
            self.canvas.config(cursor=cursor)
        except tk.TclError:
            pass

    def on_press(self, e):
        self.canvas.focus_set()
        if self.crop_active():
            h = self.hit(e.x, e.y)
            if h:
                self.drag = dict(h=h, sx=e.x, sy=e.y, rect=self.canvas_rect(self.cur.crop))
                return
        self.pan_start(e)           # empty area (or Result / Original view): pan

    def on_drag(self, e):
        d = self.drag
        if not d:
            self.pan_move(e)
            return
        if not self.crop_active():
            return
        vm = self.vm
        x0, y0, x1, y1 = d["rect"]
        dx, dy, h = e.x - d["sx"], e.y - d["sy"], d["h"]
        ox, oy, dw, dh = vm["ox"], vm["oy"], vm["dw"], vm["dh"]
        if self.v["extend"].get():       # may go past the photo, but not unreasonably far
            bx0, by0, bx1, by1 = ox - 0.5 * dw, oy - 0.5 * dh, ox + 1.5 * dw, oy + 1.5 * dh
        else:
            bx0, by0, bx1, by1 = ox, oy, ox + dw, oy + dh

        if h == "move":
            w, hh = x1 - x0, y1 - y0
            nx0 = min(max(x0 + dx, bx0), bx1 - w)
            ny0 = min(max(y0 + dy, by0), by1 - hh)
            new = (nx0, ny0, nx0 + w, ny0 + hh)
        else:
            nx0, ny0, nx1, ny1 = x0, y0, x1, y1
            if "w" in h:
                nx0 = x0 + dx
            if "e" in h:
                nx1 = x1 + dx
            if "n" in h:
                ny0 = y0 + dy
            if "s" in h:
                ny1 = y1 + dy
            r = self.lock_ratio()
            if r:
                w, hh = nx1 - nx0, ny1 - ny0
                if h in ("n", "s"):
                    w = hh * r
                    cx = (x0 + x1) / 2
                    nx0, nx1 = cx - w / 2, cx + w / 2
                elif h in ("e", "w"):
                    hh = w / r
                    cy = (y0 + y1) / 2
                    ny0, ny1 = cy - hh / 2, cy + hh / 2
                else:
                    w = max(w, hh * r)
                    hh = w / r
                    if "w" in h:
                        nx0 = nx1 - w
                    else:
                        nx1 = nx0 + w
                    if "n" in h:
                        ny0 = ny1 - hh
                    else:
                        ny1 = ny0 + hh
            if nx1 - nx0 < 16 or ny1 - ny0 < 16:
                return
            if nx0 < bx0 - 0.5 or ny0 < by0 - 0.5 or nx1 > bx1 + 0.5 or ny1 > by1 + 0.5:
                return
            new = (nx0, ny0, nx1, ny1)

        p = self.cur
        p.crop = ((new[0] - ox) / dw, (new[1] - oy) / dh, (new[2] - ox) / dw, (new[3] - oy) / dh)
        if not p.manual:
            p.manual = True
        self.draw_edit()

    def on_release(self, e):
        if self.drag:
            self.drag = None
            self.refresh_item(self.cur_idx)
        self.pan_drag = None
