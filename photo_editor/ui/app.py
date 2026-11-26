"""The application window: composes the UI mixins into one Tk root."""
import tkinter as tk
from collections import OrderedDict

from photo_editor import APP_NAME
from photo_editor.core.batch import BatchExporter
from photo_editor.core.constants import DEFAULTS
from photo_editor.core.levels import Levels
from photo_editor.ui import macos
from photo_editor.ui.dnd import DndTk, DragDropMixin
from photo_editor.ui.edit_state import EditStateMixin
from photo_editor.ui.export import ExportMixin
from photo_editor.ui.files import FileListMixin
from photo_editor.ui.keys import KeyboardMixin
from photo_editor.ui.levels_panel import LevelsMixin
from photo_editor.ui.menu import MenuMixin
from photo_editor.ui.panels import PanelsMixin
from photo_editor.ui.theme import Theme
from photo_editor.ui.viewer import ViewerMixin


class _AppBase(PanelsMixin, MenuMixin, KeyboardMixin, FileListMixin, LevelsMixin,
               EditStateMixin, ViewerMixin, ExportMixin, DragDropMixin):
    """Main window.

    State lives here (photos, caches, tk variables); behaviour is split by concern into the mixins:
      PanelsMixin    window layout + tool tabs      MenuMixin      menu bar / shortcuts
      KeyboardMixin  arrows, Delete, zoom keys      FileListMixin  adding / removing / loading photos
      LevelsMixin    levels logic + histogram       EditStateMixin rotate/flip, settings, crop detection
      ViewerMixin    zoom, pan, grid, crop editing  ExportMixin    batch export (core.batch)
      DragDropMixin  drop photos / folders onto the window (optional tkinterdnd2)
    """

    def _setup(self, initial_paths=()):
        """Everything __init__ used to do; called by App / PlainApp once the Tk root exists."""
        self.title(APP_NAME)
        self._set_icon()
        self.geometry("1400x860")
        self.minsize(1120, 720)

        self.photos = []
        self.cur_idx = None
        self.src_hi = None
        self.preview_src = None
        self.hist = None
        self.src_cache = OrderedDict()
        self.hi_cache = None
        self.res_cache = None
        self.global_levels = Levels()
        self.rot, self.fh, self.fv = 0, False, False
        self.preview_job = None
        self.drag = None
        self.pan_drag = None
        self.hist_drag = None
        self.ctx = None
        self.vm = None
        self.base = None
        self.cv_size = (1, 1)
        self.zoom = 1.0
        self.pan = [0.0, 0.0]
        self.disp = None
        self._syncing = False
        self.exporter = BatchExporter()
        self.done_count, self.errors, self.total = 0, [], 0

        self.v = {}
        for k, val in DEFAULTS.items():
            if isinstance(val, bool):
                self.v[k] = tk.BooleanVar(value=val)
            elif isinstance(val, int):
                self.v[k] = tk.IntVar(value=val)
            else:
                self.v[k] = tk.StringVar(value=val)
        self.view_mode = tk.StringVar(value="Edit")
        self.grid_mode = tk.StringVar(value="Thirds")
        self.grid_whole = tk.BooleanVar(value=False)
        self.zoom_text = tk.StringVar(value="Fit")
        self.scope = tk.StringVar(value="all")
        self.lv_channel = tk.StringVar(value="RGB")
        self.lv_black = tk.DoubleVar(value=0)
        self.lv_gamma = tk.DoubleVar(value=0)
        self.lv_white = tk.DoubleVar(value=255)
        self.lv_labels = {}

        self.out_dir = tk.StringVar()
        self.suffix = tk.StringVar(value="_edited")
        self.fmt = tk.StringVar(value="JPEG")
        self.quality = tk.IntVar(value=90)
        self.status = tk.StringVar(value="Add photos - or drop photos and folders onto the window.")

        self.theme = Theme(self)
        self.palette = self.theme.install()
        self.build_ui()
        self.build_menu()
        macos.register_events(self, self.open_paths)
        self.setup_dnd()
        self.sync_levels_ui()
        self.draw_hist()

        for k, var in self.v.items():
            if k in ("padding", "aspect", "extend", "grow"):
                var.trace_add("write", lambda *a: self.invalidate_crops(False))
            elif k in ("tolerance", "shadow", "bg_mode", "tol_dark", "shadow_dark"):
                var.trace_add("write", lambda *a: self.invalidate_crops(True))
            else:
                var.trace_add("write", lambda *a: self.schedule_preview())
        self.view_mode.trace_add("write", lambda *a: self.on_view_mode())
        self.grid_mode.trace_add("write", lambda *a: self.redraw())
        self.grid_whole.trace_add("write", lambda *a: self.redraw())

        self.bind("<Left>", lambda e: self.on_arrow(-1))
        self.bind("<Right>", lambda e: self.on_arrow(1))
        self.bind("<Delete>", self.on_delete)
        self.bind("<BackSpace>", self.on_delete)     # the "delete" key on Mac keyboards
        self.bind("<Key>", self.on_key)
        if initial_paths:
            self.after(150, lambda: self.open_paths(initial_paths))

    def _set_icon(self):
        """Window / taskbar icon (macOS uses the .app bundle's icon instead)."""
        try:
            from photo_editor.resources import resource_path
            self._icon = tk.PhotoImage(file=resource_path("icon.png"))     # keep a reference
            self.iconphoto(True, self._icon)
        except Exception:
            pass

    @property
    def cur(self):
        if self.cur_idx is not None and 0 <= self.cur_idx < len(self.photos):
            return self.photos[self.cur_idx]
        return None


class App(DndTk, _AppBase):
    """The application window (drag-and-drop capable when tkinterdnd2 is installed)."""

    def __init__(self, initial_paths=()):
        DndTk.__init__(self)
        self._setup(initial_paths)


class PlainApp(tk.Tk, _AppBase):
    """Same window on a plain Tk root - used if the drag-and-drop library fails to load."""

    def __init__(self, initial_paths=()):
        tk.Tk.__init__(self)
        self._setup(initial_paths)
