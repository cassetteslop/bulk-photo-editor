"""Builds the window layout and the right-hand tool tabs."""

import os
import tkinter as tk
from tkinter import filedialog, ttk

from photo_editor.core.constants import ASPECTS, BG_MODES, DEFAULTS, GRIDS
from photo_editor.ui.constants import HH, HW

class PanelsMixin:
    """Builds the window layout and the right-hand tool tabs."""

    # ---- layout ----------------------------------------------------------
    def combo(self, parent, var, values, width=None):
        kw = {"width": width} if width else {}
        cb = ttk.Combobox(parent, textvariable=var, state="readonly", values=values, **kw)
        cb.bind("<<ComboboxSelected>>", lambda e: self.canvas.focus_set())
        return cb

    def build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Left: file list
        left = ttk.Frame(self, padding=6)
        left.grid(row=0, column=0, sticky="ns")
        bar = ttk.Frame(left)
        bar.pack(fill="x")
        ttk.Button(bar, text="Add files…", command=self.add_files).pack(side="left", padx=2)
        ttk.Button(bar, text="Add folder…", command=self.add_folder).pack(side="left", padx=2)
        bar2 = ttk.Frame(left)
        bar2.pack(fill="x", pady=4)
        ttk.Button(bar2, text="Remove", command=self.remove_selected).pack(side="left", padx=2)
        ttk.Button(bar2, text="Clear", command=self.clear_files).pack(side="left", padx=2)
        lf = ttk.Frame(left)
        lf.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(
            lf, selectmode="extended", activestyle="none", exportselection=False, width=30,
            bg=self.palette.field, fg=self.palette.text, selectbackground=self.palette.accent,
            selectforeground="#ffffff", highlightthickness=1, highlightbackground=self.palette.border,
            highlightcolor=self.palette.accent, borderwidth=0, relief="flat")
        sb = ttk.Scrollbar(lf, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.count_lbl = ttk.Label(left, text="0 photos")
        self.count_lbl.pack(anchor="w", pady=(4, 0))
        ttk.Label(left, text="✎ own levels   ✂ crop adjusted", style="Hint.TLabel").pack(anchor="w")

        # Centre: preview / crop editor
        centre = ttk.Frame(self)
        centre.grid(row=0, column=1, sticky="nsew", padx=4, pady=6)
        centre.rowconfigure(0, weight=1)
        centre.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(centre, bg=self.palette.canvas, highlightthickness=0, takefocus=1)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda e: self.schedule_preview())
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)
        for b in (2, 3):   # middle / right button always pans
            self.canvas.bind("<ButtonPress-%d>" % b, self.pan_start)
            self.canvas.bind("<B%d-Motion>" % b, self.pan_move)
            self.canvas.bind("<ButtonRelease-%d>" % b, self.pan_end)
        self.canvas.bind("<MouseWheel>", self.on_wheel)   # Windows / macOS
        self.canvas.bind("<Button-4>", self.on_wheel)     # Linux
        self.canvas.bind("<Button-5>", self.on_wheel)

        tb = ttk.Frame(centre)
        tb.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(tb, text="◀", width=3, command=lambda: self.step(-1)).pack(side="left")
        ttk.Button(tb, text="▶", width=3, command=lambda: self.step(1)).pack(side="left", padx=(2, 12))
        ttk.Label(tb, text="View:").pack(side="left")
        for name, tip in (("Edit", "Edit (crop box)"), ("Result", "Result"), ("Original", "Original")):
            ttk.Radiobutton(tb, text=tip, value=name, variable=self.view_mode).pack(side="left", padx=4)
        tb2 = ttk.Frame(centre)
        tb2.grid(row=2, column=0, sticky="ew", pady=(2, 0))
        ttk.Label(tb2, text="Grid:").pack(side="left")
        self.combo(tb2, self.grid_mode, list(GRIDS), width=7).pack(side="left", padx=4)
        ttk.Checkbutton(tb2, text="whole photo", variable=self.grid_whole).pack(side="left", padx=2)
        ttk.Label(tb2, text="Zoom:").pack(side="left", padx=(16, 2))
        ttk.Button(tb2, text="−", width=3, command=lambda: self.zoom_step(1 / 1.25)).pack(side="left")
        ttk.Button(tb2, text="+", width=3, command=lambda: self.zoom_step(1.25)).pack(side="left", padx=2)
        ttk.Button(tb2, text="Fit", width=4, command=self.zoom_fit).pack(side="left")
        ttk.Button(tb2, text="100%", width=5, command=self.zoom_100).pack(side="left", padx=2)
        ttk.Label(tb2, textvariable=self.zoom_text, width=6).pack(side="left", padx=4)
        ttk.Label(tb2, text="wheel = zoom · drag = pan · ← → = photo · Del = remove", style="Hint.TLabel").pack(side="right")

        # Right: tools
        right = ttk.Frame(self, padding=(0, 6, 6, 6))
        right.grid(row=0, column=2, sticky="ns")
        nb = ttk.Notebook(right, width=350)
        nb.pack(fill="both", expand=True)
        nb.bind("<<NotebookTabChanged>>", lambda e: self.canvas.focus_set())
        nb.add(self.tab_levels(nb), text="Levels")
        nb.add(self.tab_crop(nb), text="Crop")
        nb.add(self.tab_color(nb), text="Color")
        nb.add(self.tab_size(nb), text="Size")
        nb.add(self.tab_mark(nb), text="Mark")
        nb.add(self.tab_output(nb), text="Output")

        # Bottom bar
        bottom = ttk.Frame(self)
        bottom.grid(row=1, column=0, columnspan=3, sticky="ew", padx=8, pady=(0, 8))
        self.progress = ttk.Progressbar(bottom, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Label(bottom, textvariable=self.status, width=46).pack(side="left")
        self.cancel_btn = ttk.Button(bottom, text="Cancel", command=self.exporter.cancel, state="disabled")
        self.cancel_btn.pack(side="right", padx=4)
        self.go_btn = ttk.Button(bottom, text="Process all", style="Accent.TButton", default="active",
                                command=self.run_batch)
        self.go_btn.pack(side="right")

    def refocus(self, scale):
        scale.bind("<ButtonRelease-1>", lambda e: self.canvas.focus_set(), add="+")

    def slider(self, parent, text, key, lo, hi):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=3)
        head = ttk.Frame(f)
        head.pack(fill="x")
        ttk.Label(head, text=text).pack(side="left")
        val = ttk.Label(head, width=5, anchor="e")
        val.pack(side="right")
        var = self.v[key]

        def upd(*_):
            try:
                val.config(text=str(int(round(float(var.get())))))
            except tk.TclError:
                pass
        scale = ttk.Scale(f, from_=lo, to=hi, variable=var,
                          command=lambda x: var.set(int(round(float(x)))))
        scale.pack(fill="x")
        scale.bind("<Double-Button-1>", lambda e: var.set(DEFAULTS[key]))
        self.refocus(scale)
        var.trace_add("write", upd)
        upd()

    # ---- tab: levels -----------------------------------------------------
    def tab_levels(self, nb):
        t = ttk.Frame(nb, padding=8)
        box = ttk.LabelFrame(t, text="Apply level changes to", padding=6)
        box.pack(fill="x")
        ttk.Radiobutton(box, text="All photos (global)", value="all",
                        variable=self.scope, command=self.on_scope).pack(anchor="w")
        ttk.Radiobutton(box, text="This photo only", value="this",
                        variable=self.scope, command=self.on_scope).pack(anchor="w")
        self.scope_note = ttk.Label(box, text="", style="Hint.TLabel", wraplength=320)
        self.scope_note.pack(anchor="w", pady=(4, 0))
        self.update_scope_note()

        ch = ttk.Frame(t)
        ch.pack(fill="x", pady=(8, 2))
        ttk.Label(ch, text="Channel:").pack(side="left")
        for label, val in (("RGB", "RGB"), ("Red", "R"), ("Green", "G"), ("Blue", "B")):
            ttk.Radiobutton(ch, text=label, value=val, variable=self.lv_channel,
                            command=self.on_channel).pack(side="left", padx=4)

        self.hist_canvas = tk.Canvas(t, width=HW, height=HH, bg=self.palette.field, highlightthickness=0)
        self.hist_canvas.pack(pady=4)
        self.hist_canvas.bind("<ButtonPress-1>", self.hist_press)
        self.hist_canvas.bind("<B1-Motion>", self.hist_motion)
        self.hist_canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "hist_drag", None))

        self.lv_slider(t, "Black point", self.lv_black, 0, 254, "black")
        self.lv_slider(t, "Midtones (γ)", self.lv_gamma, -100, 100, "gamma")
        self.lv_slider(t, "White point", self.lv_white, 1, 255, "white")
        ttk.Label(t, text="Drag the triangles under the histogram, or use the sliders "
                          "(double-click a slider to reset it).",
                  style="Hint.TLabel", wraplength=320).pack(anchor="w", pady=4)

        r1 = ttk.Frame(t)
        r1.pack(fill="x", pady=2)
        ttk.Button(r1, text="Auto", width=7, command=self.auto_levels).pack(side="left", padx=2)
        ttk.Button(r1, text="Reset channel", command=self.reset_channel).pack(side="left", padx=2)
        ttk.Button(r1, text="Reset all", command=self.reset_levels).pack(side="left", padx=2)
        r2 = ttk.Frame(t)
        r2.pack(fill="x", pady=2)
        ttk.Button(r2, text="Copy to selected photos", command=self.copy_levels_to_selected).pack(side="left", padx=2)
        ttk.Button(r2, text="Make global", command=self.make_global).pack(side="left", padx=2)
        ttk.Button(t, text="Drop this photo's custom levels", command=self.drop_custom).pack(anchor="w", padx=2, pady=2)
        return t

    def lv_slider(self, parent, text, var, lo, hi, kind):
        f = ttk.Frame(parent)
        f.pack(fill="x", pady=2)
        ttk.Label(f, text=text, width=13).pack(side="left")
        lbl = ttk.Label(f, width=5, anchor="e")
        lbl.pack(side="right")
        sc = ttk.Scale(f, from_=lo, to=hi, variable=var,
                       command=lambda x, k=kind: self.on_lv_slider(k, float(x)))
        sc.pack(side="left", fill="x", expand=True, padx=4)
        sc.bind("<Double-Button-1>", lambda e, k=kind: self.reset_param(k))
        self.refocus(sc)
        self.lv_labels[kind] = lbl

    # ---- tab: crop -------------------------------------------------------
    def tab_crop(self, nb):
        t = ttk.Frame(nb, padding=10)
        ttk.Checkbutton(t, text="Crop photos", variable=self.v["crop_enabled"]).pack(anchor="w")
        ttk.Label(t, wraplength=320, style="Hint.TLabel",
                  text="Finds the product at the centre of the photo and crops where it ends. Works on light and dark backdrops. "
                       "Lines, borders and gray areas in the background are ignored and kept "
                       "out of the crop. Drag the box or its handles in the Edit view to "
                       "fine-tune each photo.").pack(anchor="w", pady=6)
        ttk.Label(t, text="Aspect ratio").pack(anchor="w")
        self.combo(t, self.v["aspect"], list(ASPECTS)).pack(fill="x", pady=4)
        self.slider(t, "Padding (% of product size)", "padding", 0, 40)
        self.slider(t, "Crop size adjust (% of photo)", "grow", -50, 50)
        ttk.Label(t, text="Makes every auto crop bigger (+) or smaller (−) by this % of the "
                          "photo's width and height, around the same centre. Crops you have "
                          "adjusted by hand (✂) are left alone.",
                  style="Hint.TLabel", wraplength=320).pack(anchor="w")
        ttk.Separator(t).pack(fill="x", pady=8)
        ttk.Label(t, text="Background type").pack(anchor="w")
        self.combo(t, self.v["bg_mode"], list(BG_MODES)).pack(fill="x", pady=4)
        ttk.Label(t, text="Auto looks at the photo's border: white / off-white / light-gray backdrops use "
                          "the Light settings, brown / black / coloured backdrops use the Dark settings. "
                          "Dark mode also follows smooth lighting gradients and vignettes.",
                  style="Hint.TLabel", wraplength=320).pack(anchor="w")
        lf = ttk.LabelFrame(t, text="Light backgrounds (white, off-white, gray)", padding=6)
        lf.pack(fill="x", pady=(10, 4))
        self.slider(lf, "Tolerance", "tolerance", 4, 80)
        ttk.Checkbutton(lf, text="Ignore soft shadow around the product",
                        variable=self.v["shadow"]).pack(anchor="w")
        df = ttk.LabelFrame(t, text="Dark backgrounds (brown, black, coloured)", padding=6)
        df.pack(fill="x", pady=4)
        self.slider(df, "Tolerance", "tol_dark", 4, 80)
        ttk.Checkbutton(df, text="Ignore soft shadow around the product",
                        variable=self.v["shadow_dark"]).pack(anchor="w")
        ttk.Label(t, text="Tolerance: how different from the backdrop a pixel must be to count as "
                          "“not background” (lower = catches fainter lines, shadows and gray areas). "
                          "Ignoring shadow may cut very light (light backdrop) or very dark (dark "
                          "backdrop) parts of a product; leave it off for those.",
                  style="Hint.TLabel", wraplength=320).pack(anchor="w", pady=(4, 0))
        ttk.Checkbutton(t, text="Add background to keep the product centred",
                        variable=self.v["extend"]).pack(anchor="w", pady=4)
        ttk.Button(t, text="Re-run auto-crop on this photo", command=self.redetect_current).pack(anchor="w", pady=2)
        ttk.Button(t, text="Re-run auto-crop on all photos", command=self.redetect_all).pack(anchor="w", pady=2)
        return t

    # ---- tab: color ------------------------------------------------------
    def tab_color(self, nb):
        t = ttk.Frame(nb, padding=10)
        self.slider(t, "Brightness", "brightness", -100, 100)
        self.slider(t, "Contrast", "contrast", -100, 100)
        self.slider(t, "Saturation", "saturation", -100, 100)
        self.slider(t, "Sharpness", "sharpness", -100, 100)
        ttk.Label(t, text="Tip: double-click a slider to reset it.", style="Hint.TLabel").pack(anchor="w", pady=4)
        ttk.Checkbutton(t, text="Black & white", variable=self.v["grayscale"]).pack(anchor="w")
        ttk.Checkbutton(t, text="Sepia", variable=self.v["sepia"]).pack(anchor="w")
        ttk.Button(t, text="Reset colour", command=self.reset_color).pack(anchor="w", pady=12)
        return t

    # ---- tab: size -------------------------------------------------------
    def tab_size(self, nb):
        t = ttk.Frame(nb, padding=10)
        ttk.Label(t, text="Orientation (all photos)").pack(anchor="w")
        r = ttk.Frame(t)
        r.pack(anchor="w", pady=4)
        ttk.Button(r, text="⟲ 90°", width=7, command=lambda: self.rotate(-90)).pack(side="left", padx=2)
        ttk.Button(r, text="⟳ 90°", width=7, command=lambda: self.rotate(90)).pack(side="left", padx=2)
        ttk.Button(r, text="Flip ↔", width=7, command=lambda: self.flip("h")).pack(side="left", padx=2)
        ttk.Button(r, text="Flip ↕", width=7, command=lambda: self.flip("v")).pack(side="left", padx=2)

        ttk.Separator(t).pack(fill="x", pady=10)
        ttk.Label(t, text="Resize (after cropping)").pack(anchor="w")
        self.combo(t, self.v["resize_mode"], ["None", "Fit within", "Percentage"]).pack(fill="x", pady=4)
        row = ttk.Frame(t)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Max W").pack(side="left")
        ttk.Spinbox(row, from_=16, to=20000, width=7, textvariable=self.v["max_w"]).pack(side="left", padx=4)
        ttk.Label(row, text="Max H").pack(side="left")
        ttk.Spinbox(row, from_=16, to=20000, width=7, textvariable=self.v["max_h"]).pack(side="left", padx=4)
        row = ttk.Frame(t)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text="Percent").pack(side="left")
        ttk.Spinbox(row, from_=1, to=400, width=7, textvariable=self.v["percent"]).pack(side="left", padx=4)
        ttk.Label(t, text="“Fit within” keeps aspect ratio and never upscales.",
                  style="Hint.TLabel", wraplength=320).pack(anchor="w", pady=6)
        return t

    # ---- tab: watermark --------------------------------------------------
    def tab_mark(self, nb):
        t = ttk.Frame(nb, padding=10)
        ttk.Label(t, text="Watermark text (leave empty for none)").pack(anchor="w")
        ttk.Entry(t, textvariable=self.v["wm_text"]).pack(fill="x", pady=4)
        ttk.Label(t, text="Position").pack(anchor="w")
        self.combo(t, self.v["wm_pos"],
                   ["Bottom right", "Bottom center", "Bottom left", "Top right", "Top center",
                    "Top left", "Center"]).pack(fill="x", pady=4)
        self.slider(t, "Text size (% of height)", "wm_size", 1, 20)
        self.slider(t, "Opacity (text and image)", "wm_opacity", 5, 100)
        ttk.Separator(t).pack(fill="x", pady=8)
        ttk.Label(t, text="Watermark image (PNG with transparency works best)").pack(anchor="w")
        r = ttk.Frame(t)
        r.pack(fill="x", pady=4)
        ttk.Button(r, text="Choose image…", command=self.pick_wm_image).pack(side="left")
        ttk.Button(r, text="Clear", command=lambda: self.v["wm_image"].set("")).pack(side="left", padx=4)
        self.wm_name = tk.StringVar(value="(none)")
        ttk.Label(r, textvariable=self.wm_name, style="Hint.TLabel").pack(side="left", padx=6)
        self.v["wm_image"].trace_add("write", lambda *_: self.wm_name.set(
            os.path.basename(self.v["wm_image"].get()) or "(none)"))
        self.slider(t, "Image width (% of photo width)", "wm_img_size", 3, 80)
        return t

    def pick_wm_image(self):
        path = filedialog.askopenfilename(
            title="Watermark image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff"), ("All files", "*.*")])
        if path:
            self.v["wm_image"].set(path)

    # ---- tab: output -----------------------------------------------------
    def tab_output(self, nb):
        t = ttk.Frame(nb, padding=10)
        ttk.Label(t, text="Output folder").pack(anchor="w")
        row = ttk.Frame(t)
        row.pack(fill="x", pady=4)
        ttk.Entry(row, textvariable=self.out_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="Browse…", command=self.pick_out).pack(side="left", padx=4)
        ttk.Label(t, text="Filename suffix").pack(anchor="w", pady=(8, 0))
        ttk.Entry(t, textvariable=self.suffix).pack(fill="x", pady=4)
        ttk.Label(t, text="Format").pack(anchor="w", pady=(8, 0))
        self.combo(t, self.fmt, ["JPEG", "PNG", "WEBP"]).pack(fill="x", pady=4)
        ttk.Label(t, text="Quality (JPEG / WEBP)").pack(anchor="w", pady=(8, 0))
        q = ttk.Scale(t, from_=40, to=100, variable=self.quality,
                      command=lambda x: self.quality.set(int(float(x))))
        q.pack(fill="x")
        self.refocus(q)
        ttk.Label(t, textvariable=self.quality).pack(anchor="e")
        ttk.Label(t, text="Originals are never modified. Existing files are not overwritten.",
                  style="Hint.TLabel", wraplength=320).pack(anchor="w", pady=8)
        return t
