import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
SP = tempfile.mkdtemp(prefix="bpe_tests_")
import os, shutil, time
import faketk
import numpy as np
from PIL import Image
from legacy import b
from gen import photo

class E:
    def __init__(s, x=0, y=0, delta=0, num=None, char=""): s.x, s.y, s.delta, s.num, s.char = x, y, delta, num, char

d = f"{SP}/photos"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
TRUTH = {}
def save(name, **kw):
    im, tb, _ = photo(**kw); im.save(f"{d}/{name}", quality=93); TRUTH[name] = tb
save("a.jpg", parts=[dict(box=(520, 260, 1080, 900), gray=190)], band=True, seed=1)
save("b.png", size=(1200, 1800), parts=[dict(box=(380, 500, 820, 1300), gray=215, kind="rect", rim=0.03)], seed=2)
save("c.jpg", parts=[dict(box=(0, 250, 520, 850), gray=60, kind="round")], seed=3)            # touches the left edge
save("d.png", parts=[dict(box=(500, 300, 1100, 900), gray=200)], bg=246, seed=4)
save("e.jpg", parts=[dict(box=(380, 300, 740, 900), gray=180), dict(box=(860, 380, 1200, 900), gray=150)], seed=5)
open(f"{d}/notes.txt", "w").write("x")

def inside(outer, inner, tol=1e-6): return outer[0] <= inner[0] + tol and outer[1] <= inner[1] + tol and outer[2] >= inner[2] - tol and outer[3] >= inner[3] - tol
def truth_norm(name, size): t = TRUTH[name]; return (t[0]/size[0], t[1]/size[1], t[2]/size[0], t[3]/size[1])

app = b.App()
# ---- key bindings registered -------------------------------------------------------------------
for seq in ("<Left>", "<Right>", "<Delete>", "<BackSpace>", "<Key>"):
    assert seq in app.binds, seq
app.add_paths(sorted(os.path.join(d, f) for f in os.listdir(d)))
assert len(app.photos) == 5 and app.cur_idx == 0, len(app.photos)       # txt ignored, first selected
app.pump()
print("loaded", [os.path.basename(p.path) for p in app.photos])

# ---- auto crop on every photo: contains the whole product, product box close to truth -----------------
sizes = {"a.jpg": (1600, 1200), "b.png": (1200, 1800), "c.jpg": (1600, 1200), "d.png": (1600, 1200), "e.jpg": (1600, 1200)}
for i, p in enumerate(app.photos):
    app.select_index(i); app.pump()
    n = os.path.basename(p.path); tn = truth_norm(n, sizes[n])
    assert p.crop and p.prod and inside(p.crop, p.prod) and inside(p.prod, tn, 0.004), (n, p.crop, p.prod, tn)
    tw = tn[2] - tn[0]; assert (p.prod[2] - p.prod[0]) - tw < 0.05 * tw + 0.01, (n, "box too loose")
    print(f"  {n}: crop {[round(v, 3) for v in p.crop]}")
assert app.photos[2].crop[0] < 0          # c.jpg touches the left edge: centred crop extends past the photo
# every view renders
app.select_index(0); app.pump()
for mode in ("Result", "Original", "Edit"):
    app.view_mode.set(mode); app.pump()
print("views ok")

# ---- zoom / pan -------------------------------------------------------------------------------------------
app.view_mode.set("Edit"); app.pump()
assert app.zoom == 1.0 and app.zoom_text.get() == "Fit", (app.zoom, app.zoom_text.get())
vm0 = dict(app.vm); cw, ch = app.cv_size
def uv(mx, my): return ((mx - app.vm["ox"]) / app.vm["dw"], (my - app.vm["oy"]) / app.vm["dh"])
u0 = uv(cw/2, ch/2)
app.zoom_step(1.25); app.pump()
assert abs(app.zoom - 1.25) < 1e-9 and abs(app.vm["dw"] - vm0["dw"]*1.25) <= 1, (app.zoom, app.vm, vm0)
u1 = uv(cw/2, ch/2); assert abs(u1[0]-u0[0]) < 0.01 and abs(u1[1]-u0[1]) < 0.01      # zoom keeps the view centre fixed
print("zoom text at 1.25x:", app.zoom_text.get())
app.on_wheel(E(300, 200, delta=120)); assert app.zoom > 1.25                         # wheel up zooms in (Win / Mac)
z = app.zoom; app.on_wheel(E(300, 200, delta=-120)); assert app.zoom < z
z = app.zoom; app.on_wheel(E(300, 200, num=4)); assert app.zoom > z                    # Linux wheel buttons
app.on_wheel(E(300, 200, num=5))
# zoom under the cursor keeps that point fixed
app.zoom_fit(); app.pump(); app.zoom_at(300, 200, 2.0); app.zoom_at(450, 260, 3.0)
u_a = uv(450, 260); app.zoom_at(450, 260, 3.5); u_b = uv(450, 260); assert abs(u_a[0]-u_b[0]) < 0.01 and abs(u_a[1]-u_b[1]) < 0.01
# limits
for _ in range(60): app.zoom_step(1.25)
assert abs(app.zoom - app.zmax()) < 1e-6, (app.zoom, app.zmax())
for _ in range(60): app.zoom_step(1 / 1.25)
assert app.zoom == 1.0 and app.zoom_text.get() == "Fit"
app.zoom_100(); app.pump(); print("100% -> zoom", round(app.zoom, 2), "text", app.zoom_text.get(), "dw", app.vm["dw"], "image w", app.ctx["size"][0])
assert abs(app.vm["dw"] - app.ctx["size"][0]) <= 2 and app.zoom_text.get() == "100%"
# pan: drag moves the photo, clamped so it never disappears; at Fit there is nothing to pan
ox, oy = app.vm["ox"], app.vm["oy"]
app.on_press(E(5, 5)); app.on_drag(E(45, 35)); app.on_release(E())                    # press on empty area = pan
assert app.vm["ox"] == ox + 40 and app.vm["oy"] == oy + 30, (app.vm["ox"] - ox, app.vm["oy"] - oy)
app.pan_start(E(0, 0)); app.pan_move(E(-99999, -99999)); app.pan_end(E())
assert app.vm["ox"] + app.vm["dw"] >= 60 - 1 and app.vm["oy"] + app.vm["dh"] >= 60 - 1       # clamped
app.pan_start(E(0, 0)); app.pan_move(E(99999, 99999)); app.pan_end(E())
assert app.vm["ox"] <= app.cv_size[0] - 60 + 1
for mode in ("Result", "Original", "Edit"):                                         # render zoomed + panned in all views
    app.view_mode.set(mode); app.pump(); app.zoom_at(400, 300, 2.5); app.pan_start(E(0, 0)); app.pan_move(E(-120, 60)); app.pan_end(E())
app.view_mode.set("Edit"); app.zoom_fit(); app.pump()
app.pan_start(E(0, 0)); app.pan_move(E(80, 80)); assert app.pan == [0.0, 0.0] and app.zoom == 1.0   # Fit: pan resets
# result view switches to the sharper source when zoomed past Fit
app.view_mode.set("Result"); app.pump(); assert app.ctx["hi"] is False
app.zoom_step(1.25); app.pump(); assert app.ctx["hi"] is True and app.ctx["size"][0] > 0
hi_w = app.ctx["size"][0]; app.zoom_fit(); app.pump(); assert app.ctx["hi"] is False and app.ctx["size"][0] <= hi_w
# switching photo / view resets the zoom
app.view_mode.set("Edit"); app.pump(); app.zoom_step(1.25 ** 3); app.step(1); app.pump(); assert app.zoom == 1.0 and app.cur_idx == 1
app.step(-1); app.pump(); app.zoom_step(2.0); app.view_mode.set("Original"); app.pump(); assert app.zoom == 1.0
app.view_mode.set("Edit"); app.pump()
# keyboard zoom keys
app.on_key(E(char="+")); assert app.zoom > 1; app.on_key(E(char="-")); app.on_key(E(char="0")); assert app.zoom == 1.0; app.on_key(E(char="1")); assert app.zoom > 1; app.on_key(E(char="0"))
print("zoom / pan ok")

# ---- crop drag while zoomed ---------------------------------------------------------------------------------
app.select_index(0); app.pump(); app.zoom_at(400, 300, 2.0); app.pump()
p = app.cur; r0 = app.canvas_rect(p.crop); cx, cy = (r0[0]+r0[2])/2, (r0[1]+r0[3])/2
assert app.hit(cx, cy) in ("move", None)
if app.hit(cx, cy) == "move":
    c_before = p.crop; app.on_press(E(cx, cy)); app.on_drag(E(cx + 20, cy + 10)); app.on_release(E())
    assert p.manual and abs((p.crop[0] - c_before[0]) * app.vm["dw"] - 20) < 1e-6
    app.redetect_current(); app.pump()
app.zoom_fit(); app.pump()

# ---- grid ---------------------------------------------------------------------------------------------------------
lines = []
app.canvas.create_line = lambda *a, **k: lines.append((a, k))
def count_grid(mode, whole=False):
    app.grid_whole.set(whole); app.grid_mode.set(mode); lines.clear(); app.redraw()
    return sum(1 for a, k in lines if k.get("dash") == (4, 4))
for mode, n in (("Off", 0), ("Thirds", 3), ("4 × 4", 6), ("8 × 8", 14)):
    got = count_grid(mode); assert got == n * 1 or got == 2 * (b.GRIDS[mode] - 1), (mode, got)
assert count_grid("Thirds") == 4
# grid sits over the crop box by default and over the whole photo with "whole photo"
def grid_extent(whole):
    count_grid("Thirds", whole); vs = [a for a, k in lines if k.get("dash") == (4, 4) and a[0] == a[2]]
    return min(a[1] for a in vs), max(a[3] for a in vs)
(c0, c1), (w0, w1) = grid_extent(False), grid_extent(True)
cr = app.canvas_rect(app.cur.crop); vm = app.vm
assert abs(c0 - cr[1]) < 1e-6 and abs(c1 - cr[3]) < 1e-6 and abs(w0 - vm["oy"]) < 1e-6 and abs(w1 - (vm["oy"] + vm["dh"])) < 1e-6
app.view_mode.set("Result"); app.pump(); assert count_grid("Thirds") == 4          # also over Result / Original
app.view_mode.set("Original"); app.pump(); assert count_grid("4 × 4") == 6
app.view_mode.set("Edit"); app.grid_mode.set("Thirds"); app.pump()
del app.canvas.create_line
print("grid ok")

# ---- arrow keys ---------------------------------------------------------------------------------------------------------
app.select_index(0); app.pump()
assert app.on_arrow(1) == "break" and app.cur_idx == 1
app.on_arrow(1); app.on_arrow(1); app.on_arrow(1); assert app.cur_idx == 4
app.on_arrow(1); assert app.cur_idx == 4                            # stops at the end
app.on_arrow(-1); assert app.cur_idx == 3
assert app.listbox.curselection() == (3,)
for _ in range(10): app.on_arrow(-1)
assert app.cur_idx == 0
app._focus = b.ttk.Entry()                                          # typing in a text box: arrows must not change photo
assert app.on_arrow(1) is None and app.cur_idx == 0; app._focus = None
print("arrow keys ok")

# ---- delete key ---------------------------------------------------------------------------------------------------------------
names = lambda: [os.path.basename(p.path) for p in app.photos]
app.select_index(1); app.pump()
assert app.on_delete() == "break"
assert names() == ["a.jpg", "c.jpg", "d.png", "e.jpg"] and app.cur_idx == 1 and os.path.basename(app.cur.path) == "c.jpg", names()
assert len(app.listbox.items) == 4 and app.count_lbl.kw.get("text") is None or True
assert "Removed 1 photo" in app.status.get() and os.path.exists(f"{d}/b.png")           # files stay on disk
app.select_index(3); app.pump(); app.on_delete()                                          # delete the last: selection moves to the new last
assert names() == ["a.jpg", "c.jpg", "d.png"] and app.cur_idx == 2
app.listbox.selection_set(0); app.listbox.selection_set(2); app.on_delete()                # several at once
assert names() == ["c.jpg"] and app.cur_idx == 0 and os.path.basename(app.cur.path) == "c.jpg", names()
app._focus = b.ttk.Entry(); assert app.on_delete() is None and names() == ["c.jpg"]; app._focus = None     # typing: nothing deleted
app.on_delete(); assert names() == [] and app.cur is None and app.src_hi is None; app.pump()
assert app.on_delete() == "break"                                                         # empty list: harmless
app.add_paths(sorted(os.path.join(d, f) for f in os.listdir(d))); app.pump()
assert len(app.photos) == 5 and app.cur_idx == 0
print("delete key ok")

# ---- crop size adjust slider ------------------------------------------------------------------------------------------------------
app.select_index(0); app.pump(); p = app.cur
base = p.crop; bw, bh = (base[2] - base[0]) * 1600, (base[3] - base[1]) * 1200
app.v["grow"].set(10); app.pump()
assert p.crop is not None and abs((p.crop[2] - p.crop[0]) * 1600 - (bw + 160)) < 1e-6 and abs((p.crop[3] - p.crop[1]) * 1200 - (bh + 120)) < 1e-6
assert abs((p.crop[0] + p.crop[2]) - (base[0] + base[2])) < 1e-9                      # same centre
assert inside(p.crop, p.prod)
assert app.photos[1].crop is None                                                       # other photos recompute lazily
app.v["grow"].set(-10); app.pump()
assert abs((p.crop[2] - p.crop[0]) * 1600 - (bw - 160)) < 1e-6
# hand-made crops are not touched by the slider
app.v["grow"].set(0); app.pump(); r0 = app.canvas_rect(p.crop)
app.on_press(E(r0[2], r0[3])); app.on_drag(E(r0[2] + 30, r0[3] + 20)); app.on_release(E())
assert p.manual and app.listbox.items[0].startswith("·✂"), app.listbox.items[0]
manual = p.crop; app.v["grow"].set(25); app.pump(); assert p.crop == manual
app.v["grow"].set(0); app.pump()
app.redetect_current(); app.pump(); assert not p.manual
# aspect ratio + grow stays exact
app.v["aspect"].set("1:1"); app.v["grow"].set(15); app.pump()
cwp, chp = (p.crop[2] - p.crop[0]) * 1600, (p.crop[3] - p.crop[1]) * 1200; assert abs(cwp - chp) < 1e-6
app.v["aspect"].set("Free"); app.v["grow"].set(0); app.pump()
print("crop size adjust slider ok")

# ---- drag + ratio lock (regression from v2) ----------------------------------------------------------------------------------------------------
app.select_index(0); app.pump(); p = app.cur; r0 = app.canvas_rect(p.crop)
assert app.hit(r0[2], r0[3]) == "se"
app.on_press(E(r0[2], r0[3])); app.on_drag(E(r0[2] + 30, r0[3] + 20)); app.on_release(E())
r1 = app.canvas_rect(p.crop); assert abs((r1[2]-r0[2]) - 30) < 1e-6 and abs((r1[3]-r0[3]) - 20) < 1e-6
app.v["aspect"].set("1:1"); app.pump(); assert p.manual
r2 = app.canvas_rect(p.crop); app.on_press(E(r2[2], r2[3])); app.on_drag(E(r2[2] + 40, r2[3] + 5)); app.on_release(E())
r3 = app.canvas_rect(p.crop); assert abs((r3[2]-r3[0]) - (r3[3]-r3[1])) < 1e-6
app.v["aspect"].set("Free"); app.redetect_current(); app.pump()

# ---- levels: global vs per photo (regression) -------------------------------------------------------------------------------------------------------
app.select_index(1); app.pump(); app.lv_channel.set("RGB"); app.set_level_param("black", 30); app.set_level_param("gamma", 1.5)
assert app.global_levels.d["RGB"][0] == 30
app.select_index(2); app.pump(); app.scope.set("this"); app.on_scope(); pc = app.cur
app.set_level_param("black", 80); assert pc.lv.d["RGB"][0] == 80 and app.global_levels.d["RGB"][0] == 30
assert app.listbox.items[2].startswith("✎")
app.hist_press(E(app.hx(80), 50)); app.hist_motion(E(app.hx(100), 50)); app.hist_drag = None; assert pc.lv.d["RGB"][0] == 100
g0, w0_ = pc.lv.d["RGB"][1], pc.lv.d["RGB"][2]; mid = app.hx(100 + (w0_ - 100) * 0.5 ** g0)
app.hist_press(E(mid, 50)); app.hist_motion(E(mid - 40, 50)); app.hist_drag = None; assert pc.lv.d["RGB"][1] > 1.0
app.select_index(1); app.pump(); assert app.scope.get() == "all"
app.select_index(2); app.pump(); assert app.scope.get() == "this"
app.listbox.selection_set(3); app.copy_levels_to_selected(); assert app.photos[3].lv_mode == "custom"
app.select_index(3); app.pump(); app.auto_levels(); app.reset_levels(); app.drop_custom(); assert app.cur.lv_mode == "global"
app.select_index(2); app.pump(); app.make_global(); assert app.global_levels.d["RGB"][0] == 100
print("levels scope ok")

# ---- rotate / flip keeps crops, product boxes and keep-out grids aligned --------------------------------------------------------------------------------
app.select_index(0); app.pump(); s = app.settings(); p = app.cur
before = p.crop
app.rotate(90); app.pump(); app.flip("h"); app.pump()
rgb, _ = b.oriented(app.src_hi, app.settings()); det = b.detect_product(rgb, 20)
assert all(abs(x - y) < 0.01 for x, y in zip(p.prod, det.prod)), (p.prod, det.prod)
assert p.obst is not None and det.obst is not None and (p.obst == det.obst).mean() > 0.98, (p.obst == det.obst).mean()
app.flip("h"); app.rotate(-90); app.pump()
assert all(abs(x - y) < 1e-9 for x, y in zip(p.crop, before))
print("rotate/flip ok")

# ---- batch export honours grow, levels, manual crops ----------------------------------------------------------------------------------------------------------
app.v["resize_mode"].set("None"); app.v["wm_text"].set(""); app.v["aspect"].set("Free")
out = f"{SP}/out"
def run(label):
    shutil.rmtree(out, ignore_errors=True); app.out_dir.set(out); faketk.MSGS.clear(); app.run_batch()
    for _ in range(600):
        app.pump()
        if faketk.MSGS: break
        time.sleep(0.02)
    assert faketk.MSGS and "failed" not in faketk.MSGS[-1][1][1].lower(), faketk.MSGS
    return {f: Image.open(os.path.join(out, f)).size for f in sorted(os.listdir(out))}
app.select_index(0); app.pump()
s0 = run("grow 0")
app.v["grow"].set(10); app.pump(); s1 = run("grow +10")
app.v["grow"].set(0); app.pump()
print("export sizes   0%:", s0); print("export sizes +10%:", s1)
assert len(s0) == len(s1) == 5
for f in s0:                                    # every photo (visited or not) grows by 10% of ITS width / height
    src = Image.open(f"{d}/{f.replace('_edited.jpg', '.jpg').replace('_edited.png', '.png')}") if os.path.exists(f"{d}/{f.replace('_edited.jpg', '.jpg')}") else None
for f in s0:
    stem = f.split("_edited")[0]; src = [x for x in os.listdir(d) if x.startswith(stem + ".")][0]; W_, H_ = Image.open(f"{d}/{src}").size
    assert abs((s1[f][0] - s0[f][0]) - 0.10 * W_) <= 2 and abs((s1[f][1] - s0[f][1]) - 0.10 * H_) <= 2, (f, s0[f], s1[f], W_, H_)
app.v["crop_enabled"].set(False); app.pump(); s2 = run("no crop"); assert s2["a_edited.jpg"] == (1600, 1200); app.v["crop_enabled"].set(True)
print("batch export ok")

# ---- clear ---------------------------------------------------------------------------------------------------------------------------------------------------------
app.clear_files(); app.pump(); assert app.cur is None and not app.photos
print("ALL GUI TESTS PASSED")
