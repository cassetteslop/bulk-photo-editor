"""Dark theme with macOS look-and-feel.

On a Mac the *native* Aqua widgets are used (real buttons, tabs, sliders, scroll bars) and the app is
switched to Dark Aqua. If that is not possible (pyobjc missing, old Tk) - and on Windows / Linux - a
hand-styled dark "clam" theme with the same palette is used instead, so the app always looks dark.
"""
import sys
from dataclasses import dataclass
from tkinter import ttk

from photo_editor.ui import macos


@dataclass(frozen=True)
class Palette:
    window: str = "#1e1e20"
    panel: str = "#28282b"
    field: str = "#161618"
    control: str = "#3a3a3d"
    control_hover: str = "#48484c"
    control_active: str = "#5a5a5f"
    border: str = "#3d3d41"
    text: str = "#f5f5f7"
    text_dim: str = "#98989f"
    accent: str = "#0a84ff"
    accent_hover: str = "#3395ff"
    accent_text: str = "#ffffff"
    canvas: str = "#161618"

    @property
    def canvas_rgb(self):
        h = self.canvas.lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


DARK = Palette()


def _system_font():
    if sys.platform == "darwin":
        return ".AppleSystemUIFont", 13
    if sys.platform.startswith("win"):
        return "Segoe UI", 10
    return None, None


class Theme:
    """Install with `Theme(root).install()`; returns the Palette to use for plain tk widgets."""

    def __init__(self, root):
        self.root = root
        self.palette = DARK
        self.native = False          # True when the real Aqua theme is in use

    # ------------------------------------------------------------------
    def install(self):
        style = ttk.Style(self.root)
        if macos.IS_MAC:
            macos.set_process_name("Bulk Photo Editor")
            macos.force_dark_appearance()
            self.root.update_idletasks()
            try:
                style.theme_use("aqua")
                self.native = self._looks_dark()
            except Exception:
                self.native = False
        if self.native:
            self._style_native(style)
        else:
            self._style_clam(style)
        self.root.configure(background=self.palette.window)
        return self.palette

    def _looks_dark(self):
        try:
            r, g, b = self.root.winfo_rgb("systemWindowBackgroundColor")
            return (0.299 * r + 0.587 * g + 0.114 * b) / 65535 < 0.5
        except Exception:
            return False

    # ------------------------------------------------------------------
    def _style_native(self, style):
        p = self.palette
        style.configure("Hint.TLabel", foreground=p.text_dim)
        style.configure("Accent.TButton")           # real default-button look comes from default="active"

    def _style_clam(self, style):
        p, root = self.palette, self.root
        try:
            style.theme_use("clam")
        except Exception:
            pass
        fam, size = _system_font()
        if fam:
            import tkinter.font as tkfont
            for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                         "TkCaptionFont", "TkFixedFont"):
                try:
                    tkfont.nametofont(name).configure(family=fam, size=size)
                except Exception:
                    pass

        style.configure(".", background=p.window, foreground=p.text, fieldbackground=p.field,
                        bordercolor=p.border, lightcolor=p.window, darkcolor=p.window,
                        troughcolor=p.field, focuscolor=p.accent, selectbackground=p.accent,
                        selectforeground=p.accent_text, insertcolor=p.text)
        style.map(".", foreground=[("disabled", p.text_dim)])
        style.configure("TFrame", background=p.window)
        style.configure("TLabel", background=p.window, foreground=p.text)
        style.configure("Hint.TLabel", foreground=p.text_dim)
        style.configure("TLabelframe", background=p.window, bordercolor=p.border, relief="solid")
        style.configure("TLabelframe.Label", background=p.window, foreground=p.text_dim)
        style.configure("TSeparator", background=p.border)

        style.configure("TButton", background=p.control, foreground=p.text, bordercolor=p.border,
                        lightcolor=p.control, darkcolor=p.control, padding=(10, 4), relief="flat")
        style.map("TButton", background=[("pressed", p.control_active), ("active", p.control_hover),
                                         ("disabled", p.panel)],
                  lightcolor=[("pressed", p.control_active), ("active", p.control_hover)],
                  darkcolor=[("pressed", p.control_active), ("active", p.control_hover)])
        style.configure("Accent.TButton", background=p.accent, foreground=p.accent_text,
                        lightcolor=p.accent, darkcolor=p.accent, bordercolor=p.accent,
                        font=(fam or "TkDefaultFont", (size or 10), "bold"), padding=(14, 5))
        style.map("Accent.TButton", background=[("pressed", "#0060c8"), ("active", p.accent_hover),
                                                ("disabled", p.control)],
                  lightcolor=[("pressed", "#0060c8"), ("active", p.accent_hover)],
                  darkcolor=[("pressed", "#0060c8"), ("active", p.accent_hover)],
                  foreground=[("disabled", p.text_dim)])

        style.configure("TEntry", fieldbackground=p.field, foreground=p.text, bordercolor=p.border,
                        lightcolor=p.field, darkcolor=p.field, padding=4)
        style.map("TEntry", bordercolor=[("focus", p.accent)])
        style.configure("TSpinbox", fieldbackground=p.field, foreground=p.text, arrowcolor=p.text,
                        background=p.control, bordercolor=p.border, padding=3)
        style.configure("TCombobox", fieldbackground=p.control, background=p.control, foreground=p.text,
                        arrowcolor=p.text, bordercolor=p.border, lightcolor=p.control,
                        darkcolor=p.control, padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", p.control)],
                  background=[("active", p.control_hover)], bordercolor=[("focus", p.accent)],
                  foreground=[("readonly", p.text)], selectbackground=[("readonly", p.control)],
                  selectforeground=[("readonly", p.text)])
        root.option_add("*TCombobox*Listbox.background", p.control)
        root.option_add("*TCombobox*Listbox.foreground", p.text)
        root.option_add("*TCombobox*Listbox.selectBackground", p.accent)
        root.option_add("*TCombobox*Listbox.selectForeground", p.accent_text)

        style.configure("TCheckbutton", background=p.window, foreground=p.text,
                        indicatorbackground=p.field, indicatorforeground=p.accent_text)
        style.map("TCheckbutton", background=[("active", p.window)],
                  indicatorbackground=[("selected", p.accent), ("pressed", p.control_active)])
        style.configure("TRadiobutton", background=p.window, foreground=p.text,
                        indicatorbackground=p.field, indicatorforeground=p.accent_text)
        style.map("TRadiobutton", background=[("active", p.window)],
                  indicatorbackground=[("selected", p.accent), ("pressed", p.control_active)])

        style.configure("TNotebook", background=p.window, bordercolor=p.border, tabmargins=(2, 4, 2, 0))
        style.configure("TNotebook.Tab", background=p.window, foreground=p.text_dim,
                        padding=(10, 5), bordercolor=p.border, lightcolor=p.window, darkcolor=p.window)
        style.map("TNotebook.Tab", background=[("selected", p.panel), ("active", p.control)],
                  foreground=[("selected", p.text), ("active", p.text)],
                  lightcolor=[("selected", p.panel)], darkcolor=[("selected", p.panel)])

        style.configure("Horizontal.TScale", background=p.window, troughcolor=p.control,
                        bordercolor=p.window, lightcolor=p.window, darkcolor=p.window)
        style.configure("TScrollbar", background=p.control, troughcolor=p.window, bordercolor=p.window,
                        arrowcolor=p.text_dim, lightcolor=p.control, darkcolor=p.control)
        style.map("TScrollbar", background=[("active", p.control_hover)])
        style.configure("Horizontal.TProgressbar", background=p.accent, troughcolor=p.field,
                        bordercolor=p.border, lightcolor=p.accent, darkcolor=p.accent)

        # plain tk widgets (menus, dialogs' listboxes, tooltips)
        root.option_add("*Menu.background", p.panel)
        root.option_add("*Menu.foreground", p.text)
        root.option_add("*Menu.activeBackground", p.accent)
        root.option_add("*Menu.activeForeground", p.accent_text)
        root.option_add("*Menu.borderWidth", 0)
