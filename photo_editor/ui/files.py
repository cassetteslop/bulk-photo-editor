"""The photo list: adding, removing, selecting and loading photos."""

import os
import tkinter as tk
from tkinter import filedialog

from photo_editor.core.constants import EXTS
from photo_editor.core.loader import load_source
from photo_editor.core.photo import Photo

class FileListMixin:
    """The photo list: adding, removing, selecting and loading photos."""

    # ---- file list -------------------------------------------------------
    @staticmethod
    def item_text(p):
        return "%s%s  %s" % ("✎" if p.lv_mode == "custom" else "·",
                             "✂" if p.manual else "·", os.path.basename(p.path))

    def refresh_item(self, idx):
        if idx is None or not (0 <= idx < len(self.photos)):
            return
        sel = self.listbox.curselection()
        self.listbox.delete(idx)
        self.listbox.insert(idx, self.item_text(self.photos[idx]))
        for i in sel:
            self.listbox.selection_set(i)

    def select_index(self, i):
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(i)
        self.listbox.see(i)
        self.on_select()

    def step(self, d):
        if not self.photos:
            return
        i = min(max((self.cur_idx or 0) + d, 0), len(self.photos) - 1)
        if i != self.cur_idx:
            self.select_index(i)

    def add_paths(self, paths):
        known = {p.path for p in self.photos}
        for path in paths:
            if os.path.splitext(path)[1].lower() in EXTS and path not in known:
                p = Photo(path)
                self.photos.append(p)
                self.listbox.insert("end", self.item_text(p))
                known.add(path)
        self.count_lbl.config(text=f"{len(self.photos)} photos")
        if self.photos and self.cur_idx is None:
            self.select_index(0)
        if self.photos and not self.out_dir.get():
            self.out_dir.set(os.path.join(os.path.dirname(self.photos[0].path), "edited"))

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select photos",
            filetypes=[("Images", " ".join("*" + e for e in sorted(EXTS))), ("All files", "*.*")])
        self.add_paths(paths)

    def add_folder(self):
        d = filedialog.askdirectory(title="Select folder")
        if d:
            self.open_paths([d])

    def open_paths(self, paths):
        """Add files and/or folders (searched recursively). Used by the dialogs, the command
        line, drag-onto-Dock-icon and the Finder Quick Action."""
        found = []
        for path in paths:
            path = os.path.abspath(os.path.expanduser(str(path)))
            if os.path.isdir(path):
                for root, dirs, names in os.walk(path):
                    dirs.sort()
                    found += [os.path.join(root, n) for n in sorted(names) if not n.startswith(".")]
            elif os.path.isfile(path):
                found.append(path)
        before = len(self.photos)
        self.add_paths(found)
        added = len(self.photos) - before
        self.status.set(f"Added {added} photo{'' if added == 1 else 's'}." if added
                        else "No new photos found.")
        try:
            self.lift()
        except tk.TclError:
            pass

    def _reset_current(self):
        self.cur_idx = None
        self.src_hi = self.preview_src = self.hist = None
        self.hi_cache = self.res_cache = None
        self.scope.set("all")
        self.update_scope_note()
        self.sync_levels_ui()
        self.draw_hist()

    def remove_selected(self):
        sel = list(self.listbox.curselection())
        if not sel:
            return
        for i in reversed(sel):
            self.listbox.delete(i)
            del self.photos[i]
        self.count_lbl.config(text=f"{len(self.photos)} photos")
        self._reset_current()
        if self.photos:
            self.select_index(min(sel[0], len(self.photos) - 1))   # the next photo takes its place
        else:
            self.schedule_preview()
        self.status.set("Removed %d photo%s from the list (the files are untouched)."
                        % (len(sel), "" if len(sel) == 1 else "s"))

    def clear_files(self):
        self.photos.clear()
        self.listbox.delete(0, "end")
        self.count_lbl.config(text="0 photos")
        self.src_cache.clear()
        self._reset_current()
        self.schedule_preview()

    def pick_out(self):
        d = filedialog.askdirectory(title="Output folder")
        if d:
            self.out_dir.set(d)

    # ---- selection / loading --------------------------------------------
    def get_source(self, path):
        if path in self.src_cache:
            self.src_cache.move_to_end(path)
            return self.src_cache[path]
        data = load_source(path)
        self.src_cache[path] = data
        while len(self.src_cache) > 6:
            self.src_cache.popitem(last=False)
        return data

    def on_select(self, *_):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == self.cur_idx and self.src_hi is not None:
            return
        self.cur_idx = idx
        p = self.photos[idx]
        try:
            data = self.get_source(p.path)
            self.src_hi, self.preview_src, self.hist = data["hi"], data["pre"], data["hist"]
            p.osize = data["osize"]
        except Exception as e:  # unreadable file
            self.src_hi = self.preview_src = self.hist = None
            self.status.set(f"Can't open {os.path.basename(p.path)}: {e}")
        self.hi_cache = self.res_cache = None
        self.zoom, self.pan = 1.0, [0.0, 0.0]
        self.scope.set("this" if p.lv_mode == "custom" else "all")
        self.update_scope_note()
        self.sync_levels_ui()
        self.draw_hist()
        self.schedule_preview()
