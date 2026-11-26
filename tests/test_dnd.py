"""Drag-and-drop: payload parsing and the drop handlers (no real DnD library needed)."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
import faketk
from PIL import Image
from legacy import b

P = b.parse_drop_data
assert P("/a/b.jpg /c/d.png") == ["/a/b.jpg", "/c/d.png"]
assert P("{C:/My Photos/a b.jpg} C:/x/y.png {/Users/me/Pictures/dir with space}") == \
    ["C:/My Photos/a b.jpg", "C:/x/y.png", "/Users/me/Pictures/dir with space"]
assert P("file:///Users/me/My%20Photos/a.jpg") == ["/Users/me/My Photos/a.jpg"]
assert P("file:///C:/Users/me/a.jpg") == ["C:/Users/me/a.jpg"]
assert P("") == [] and P(None) == []
print("drop payload parsing ok")

tmp = tempfile.mkdtemp(prefix="bpe_dnd_")
os.makedirs(f"{tmp}/with space/sub")
for rel in ("one.jpg", "sub/two.png", "readme.txt"):
    p = f"{tmp}/with space/{rel}"
    Image.new("RGB", (30, 20), "white").save(p, format="PNG") if rel.endswith(("jpg", "png")) else open(p, "w").write("x")

app = b.App()

class Ev:  # what tkdnd hands to the <<Drop>> binding
    def __init__(self, data): self.data, self.action = data, "copy"

app.on_drop_enter(Ev(""))
assert "Drop" in app.status.get()
app.on_drop(Ev("{%s/with space}" % tmp))                    # a folder whose name contains a space
assert sorted(os.path.basename(p.path) for p in app.photos) == ["one.jpg", "two.png"], [p.path for p in app.photos]
app.on_drop(Ev("{%s/with space/one.jpg} %s/nope.jpg" % (tmp, tmp)))   # duplicate + missing file
assert len(app.photos) == 2
app.on_drop_leave(Ev(""))
assert b.HAS_DND in (True, False)
print("drop handlers ok (native DnD library present: %s)" % b.HAS_DND)
print("DRAG AND DROP TESTS PASSED")
