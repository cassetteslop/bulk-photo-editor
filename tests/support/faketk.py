"""Minimal fake tkinter so the App logic can run headless."""
import sys, types

class TclError(Exception): pass

class Var:
    def __init__(self, master=None, value=None):
        self._v = value; self._cbs = []
    def get(self): return self._v
    def set(self, v):
        self._v = v
        for cb in list(self._cbs): cb()
    def trace_add(self, mode, cb): self._cbs.append(cb)
class StringVar(Var):
    def __init__(self, master=None, value=""): super().__init__(master, value)
class BooleanVar(Var):
    def __init__(self, master=None, value=False): super().__init__(master, value)
    def get(self): return bool(self._v)
class IntVar(Var):
    def __init__(self, master=None, value=0): super().__init__(master, value)
    def get(self): return int(float(self._v))
class DoubleVar(Var):
    def __init__(self, master=None, value=0.0): super().__init__(master, value)
    def get(self): return float(self._v)

class W:
    def __init__(self, *a, **k): self.kw = k
    def __getattr__(self, name):
        if name.startswith("__"): raise AttributeError(name)
        return lambda *a, **k: None

class Canvas(W):
    def winfo_width(self): return 900
    def winfo_height(self): return 700

class Listbox(W):
    def __init__(self, *a, **k): self.items = []; self.sel = []
    def insert(self, idx, text):
        if idx == "end": self.items.append(text)
        else: self.items.insert(idx, text)
    def delete(self, a, b=None):
        if a == 0 and b == "end": self.items.clear(); self.sel = []; return
        del self.items[a]; self.sel = [i for i in self.sel if i != a]
    def curselection(self): return tuple(sorted(self.sel))
    def selection_set(self, i):
        if i not in self.sel: self.sel.append(i)
    def selection_clear(self, a, b=None): self.sel = []

class Tk(W):
    def __init__(self, *a, **k): self._pending = []; self._n = 0; self.binds = {}; self._focus = None
    def after(self, ms, fn=None, *args):
        self._n += 1; self._pending.append((self._n, fn)); return self._n
    def after_cancel(self, i): self._pending = [(n, f) for n, f in self._pending if n != i]
    def bind(self, seq, fn=None, add=None): self.binds[seq] = fn
    def focus_get(self): return self._focus
    def pump(self, limit=200):
        for _ in range(limit):
            if not self._pending: return
            n, f = self._pending.pop(0); f()

class Style(W): pass
class Menu(W): pass

tk = types.ModuleType("tkinter"); ttk = types.ModuleType("tkinter.ttk")
fd = types.ModuleType("tkinter.filedialog"); mb = types.ModuleType("tkinter.messagebox")
for n in ("StringVar","BooleanVar","IntVar","DoubleVar","Canvas","Listbox","Tk","TclError","Menu"):
    setattr(tk, n, globals()[n])
for n in ("Frame","Label","Button","Radiobutton","Checkbutton","Combobox","Scale","Spinbox","Entry",
          "Notebook","Scrollbar","Progressbar","Separator","LabelFrame"):
    setattr(ttk, n, type(n, (W,), {}))
ttk.Style = Style
tk.ttk, tk.filedialog, tk.messagebox = ttk, fd, mb
MSGS = []
mb.showinfo = lambda *a, **k: MSGS.append(("info", a))
mb.showerror = lambda *a, **k: MSGS.append(("error", a))
mb.askyesno = lambda *a, **k: True
fd.askopenfilenames = lambda **k: []
fd.askdirectory = lambda **k: ""
imgtk = types.ModuleType("PIL.ImageTk")
imgtk.PhotoImage = lambda img: img
import PIL; PIL.ImageTk = imgtk
sys.modules.update({"tkinter": tk, "tkinter.ttk": ttk, "tkinter.filedialog": fd,
                    "tkinter.messagebox": mb, "PIL.ImageTk": imgtk})
