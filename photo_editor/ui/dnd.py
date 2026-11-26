"""Drag-and-drop of photos and folders onto the window.

Uses the optional `tkinterdnd2` package (bundles the native tkdnd library for Windows, macOS and
Linux):  pip install tkinterdnd2.   Without it the app still works - Add files / Add folder, the
command line, the Dock icon (macOS) and "Open with" / the Quick Action all keep working.
"""
import re
import tkinter as tk
from urllib.parse import unquote, urlparse

try:                                   # optional dependency
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DndTk = TkinterDnD.Tk              # a Tk root that has tkdnd loaded
    HAS_DND = True
except Exception:                      # not installed / unsupported platform
    DND_FILES, DndTk, HAS_DND = None, tk.Tk, False

_TOKEN = re.compile(r"\{([^}]*)\}|(\S+)")


def parse_drop_data(data):
    """Split the string a drop delivers into file system paths.
    Handles Tcl list quoting ({C:/My Photos/a.jpg} C:/b.jpg) and file:// URIs."""
    paths = []
    for braced, plain in _TOKEN.findall(data or ""):
        item = braced or plain
        if item.lower().startswith("file:"):
            parsed = urlparse(item)
            item = unquote(parsed.path)
            if re.match(r"^/[A-Za-z]:", item):          # file:///C:/x  ->  C:/x
                item = item[1:]
        paths.append(item)
    return paths


class DragDropMixin:
    """Registers the window, the preview and the photo list as drop targets."""

    dnd_active = False

    def setup_dnd(self):
        if not HAS_DND:
            return False
        try:
            for w in (self, self.canvas, self.listbox):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<DropEnter>>", self.on_drop_enter)
                w.dnd_bind("<<DropLeave>>", self.on_drop_leave)
                w.dnd_bind("<<Drop>>", self.on_drop)
        except Exception:                # tkdnd could not load: carry on without it
            return False
        self.dnd_active = True
        return True

    def on_drop_enter(self, event):
        self._status_before_drop = self.status.get()
        self.status.set("Drop to add these photos / folders…")
        return getattr(event, "action", "copy")

    def on_drop_leave(self, event):
        before = getattr(self, "_status_before_drop", None)
        if before is not None:
            self.status.set(before)
        return getattr(event, "action", "copy")

    def on_drop(self, event):
        self._status_before_drop = None
        self.handle_dropped_paths(parse_drop_data(getattr(event, "data", "")))
        return getattr(event, "action", "copy")

    def handle_dropped_paths(self, paths):
        """Folders are searched recursively; anything that is not an image is skipped."""
        if paths:
            self.open_paths(paths)
