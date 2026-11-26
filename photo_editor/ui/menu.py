"""Native-style menu bar with keyboard shortcuts (⌘ on macOS, Ctrl elsewhere)."""
import tkinter as tk

from photo_editor import APP_NAME, __version__
from photo_editor.ui import macos


class MenuMixin:
    """File / Edit / View / Window / Help menus. On macOS the first menu becomes the application menu."""

    def build_menu(self):
        mac = macos.IS_MAC
        mod = "Command" if mac else "Control"
        sym = "⌘" if mac else "Ctrl+"
        shift = "⇧⌘" if mac else "Ctrl+Shift+"
        bar = tk.Menu(self)

        if mac:
            app = tk.Menu(bar, name="apple")
            app.add_command(label=f"About {APP_NAME}", command=self.show_about)
            bar.add_cascade(menu=app)

        def add(menu, label, command, accel=None, key=None):
            menu.add_command(label=label, command=command, accelerator=accel)
            if key:
                self.bind(f"<{mod}-{key}>", lambda e, c=command: (c(), "break")[1])

        f = tk.Menu(bar, tearoff=0)
        add(f, "Add Photos…", self.add_files, f"{sym}O", "o")
        add(f, "Add Folder…", self.add_folder, f"{shift}O", "O")
        f.add_separator()
        add(f, "Choose Output Folder…", self.pick_out)
        add(f, "Process All", self.run_batch, f"{sym}E", "e")
        if not mac:
            f.add_separator()
            add(f, "Quit", self.destroy, "Ctrl+Q", "q")
        bar.add_cascade(label="File", menu=f)

        e = tk.Menu(bar, tearoff=0)
        add(e, "Remove Selected Photos", self.remove_selected, "⌫" if mac else "Del")
        add(e, "Clear Photo List", self.clear_files)
        e.add_separator()
        add(e, "Rotate Left", lambda: self.rotate(-90), f"{sym}[", "bracketleft")
        add(e, "Rotate Right", lambda: self.rotate(90), f"{sym}]", "bracketright")
        add(e, "Flip Horizontal", lambda: self.flip("h"))
        add(e, "Flip Vertical", lambda: self.flip("v"))
        e.add_separator()
        add(e, "Re-run Auto-crop on This Photo", self.redetect_current)
        add(e, "Re-run Auto-crop on All Photos", self.redetect_all)
        bar.add_cascade(label="Edit", menu=e)

        v = tk.Menu(bar, tearoff=0)
        add(v, "Zoom In", lambda: self.zoom_step(1.25), f"{sym}+", "equal")
        self.bind(f"<{mod}-plus>", lambda e: (self.zoom_step(1.25), "break")[1])
        add(v, "Zoom Out", lambda: self.zoom_step(1 / 1.25), f"{sym}−", "minus")
        add(v, "Fit to Window", self.zoom_fit, f"{sym}0", "0")
        add(v, "Actual Size", self.zoom_100, f"{sym}1", "1")
        v.add_separator()
        add(v, "Previous Photo", lambda: self.step(-1), "←")
        add(v, "Next Photo", lambda: self.step(1), "→")
        bar.add_cascade(label="View", menu=v)

        if mac:
            bar.add_cascade(label="Window", menu=tk.Menu(bar, name="window", tearoff=0))
        h = tk.Menu(bar, name="help", tearoff=0) if mac else tk.Menu(bar, tearoff=0)
        if not mac:
            add(h, f"About {APP_NAME}", self.show_about)
        bar.add_cascade(label="Help", menu=h)
        self.config(menu=bar)
        self.menubar = bar

    def show_about(self):
        from tkinter import messagebox
        messagebox.showinfo(f"About {APP_NAME}",
                            f"{APP_NAME} {__version__}\n\nBatch levels, auto-crop, colour, resize and "
                            "watermark for product photos.\nOriginals are never modified.")
