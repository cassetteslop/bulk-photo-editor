"""Keyboard handling: arrows, Delete / Backspace, zoom keys."""

import tkinter as tk
from tkinter import ttk

class KeyboardMixin:
    """Keyboard handling: arrows, Delete / Backspace, zoom keys."""

    # ---- keyboard --------------------------------------------------------
    def typing_focus(self):
        try:
            w = self.focus_get()
        except (KeyError, tk.TclError):
            return False
        return isinstance(w, (ttk.Entry, ttk.Combobox, ttk.Spinbox, ttk.Scale))

    def on_arrow(self, d):
        if self.typing_focus():
            return None
        self.step(d)
        return "break"

    def on_delete(self, e=None):
        if self.typing_focus():
            return None
        if self.listbox.curselection():
            self.remove_selected()
        return "break"

    def on_key(self, e):
        if self.typing_focus():
            return
        if getattr(e, "state", 0) & 0x4 or getattr(e, "state", 0) & 0x8:   # Ctrl / Command: menu shortcuts
            return
        ch = getattr(e, "char", "")
        if ch in ("+", "="):
            self.zoom_step(1.25)
        elif ch in ("-", "_"):
            self.zoom_step(1 / 1.25)
        elif ch == "0":
            self.zoom_fit()
        elif ch == "1":
            self.zoom_100()
