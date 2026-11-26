import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
import faketk
from PIL import Image
from legacy import b

tmp = tempfile.mkdtemp(prefix="bpe_open_")
os.makedirs(f"{tmp}/shoot/sub")
for rel in ("a.jpg", "b.PNG", "sub/c.jpeg", ".hidden.jpg", "notes.txt", "sub/d.webp"):
    p = f"{tmp}/shoot/{rel}"
    if rel.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
        Image.new("RGB", (40, 30), "white").save(p, format="PNG")
    else:
        open(p, "w").write("x")

app = b.App()
app.open_paths([f"{tmp}/shoot"])
names = sorted(os.path.basename(p.path) for p in app.photos)
assert names == ["a.jpg", "b.PNG", "c.jpeg", "d.webp"], names     # recursive, no hidden, no txt
app.open_paths([f"{tmp}/shoot/a.jpg", f"{tmp}/does_not_exist"])    # duplicate + missing: ignored
assert len(app.photos) == 4
assert "No new photos" in app.status.get()
print("open_paths (folders, files, dupes, hidden) ok")

# initial paths from the command line / Quick Action
app2 = b.App(initial_paths=[f"{tmp}/shoot"])
print("initial_paths accepted")

# theme palette
p = b.DARK
assert p.canvas_rgb == (0x16, 0x16, 0x18), p.canvas_rgb
t = b.Theme(faketk.Tk())
assert t.install() is b.DARK and t.native is False
print("THEME / OPEN TESTS PASSED")
