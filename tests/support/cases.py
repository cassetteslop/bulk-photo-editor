from gen import photo
def P(**k): return dict(k)
C = []
def add(name, parts, **kw): C.append((name, dict(parts=parts, **kw)))

# gray level sweep: round bottle-ish with lit rim + highlight
for g in (60, 120, 160, 190, 210, 225, 235):
    add(f"round gray{g}", [P(box=(520, 260, 1080, 960), gray=g, kind="round")])
for g in (120, 190, 220):
    add(f"square gray{g} no-rim/no-hl", [P(box=(450, 250, 1150, 900), gray=g, kind="sq", rim=0, highlight=False, shade=False)])
    add(f"tall rect gray{g}", [P(box=(600, 120, 1000, 1000), gray=g, kind="rect", rim=0.03)])
    add(f"wide rect gray{g}", [P(box=(250, 400, 1350, 800), gray=g, kind="rect", rim=0.03)])
# sizes
add("small gray200", [P(box=(650, 420, 950, 780), gray=200, kind="sq")])
add("large gray200", [P(box=(180, 110, 1420, 1060), gray=200, kind="sq")])
# lighting artefacts
add("gray200 + shadow", [P(box=(520, 260, 1080, 900), gray=200, kind="sq")], shadow=True)
add("gray200 + vignette", [P(box=(520, 260, 1080, 900), gray=200, kind="sq")], vignette=55)
add("gray210 seam", [P(box=(450, 250, 1150, 900), gray=210, kind="sq", seam=True)])
add("gray200 white cap inside", [P(box=(560, 200, 1040, 1000), gray=170, kind="rect", rim=0.03, white_inside=(560, 200, 1040, 380))])
# multiple parts / thin parts
add("two parts gap", [P(box=(380, 300, 740, 900), gray=180, kind="sq"), P(box=(860, 380, 1200, 900), gray=150, kind="sq")])
add("body + thin handle", [P(box=(500, 350, 1000, 900), gray=190, kind="sq"), P(box=(1000, 480, 1260, 500), gray=110, kind="rect", rim=0, shade=False, highlight=False)])
add("bottle + small cap apart", [P(box=(600, 330, 1000, 1000), gray=190, kind="sq"), P(box=(740, 180, 860, 310), gray=140, kind="sq")])
# background clutter on top of gray products
add("gray190 + clutter", [P(box=(520, 260, 1080, 900), gray=190, kind="sq")], band=True, frame=True)
add("gray215 + touching line", [P(box=(520, 260, 1080, 900), gray=215, kind="sq")], touch_line=True, band=True)
add("gray200 offcentre", [P(box=(880, 350, 1380, 850), gray=200, kind="sq")])
add("gray200 offwhite bg 246", [P(box=(520, 260, 1080, 900), gray=200, kind="sq")], bg=246)
add("gray225 offwhite bg 240", [P(box=(520, 260, 1080, 900), gray=215, kind="sq")], bg=240)
add("black30 + clutter", [P(box=(520, 260, 1080, 900), gray=30, kind="round")], band=True, frame=True)

# --- harder / more realistic ---
add("full-width gray bar", [P(box=(0, 470, 1600, 740), gray=170, kind="rect", rim=0.04, highlight=False)])
add("full-height gray bar", [P(box=(700, 0, 900, 1200), gray=170, kind="rect", rim=0.04, highlight=False)])
add("ring (hole at centre)", [P(box=(450, 150, 1150, 1050), gray=170, kind="round", rim=0.03),])
add("gray190 jpeg q70", [P(box=(520, 260, 1080, 900), gray=190, kind="sq")], jpeg=70, noise=3.0)
add("gray215 jpeg q60 clutter", [P(box=(520, 260, 1080, 900), gray=215, kind="sq")], jpeg=60, noise=3.0, band=True, frame=True)
add("gray170 jpeg warm bg", [P(box=(520, 260, 1080, 900), gray=170, kind="round")], jpeg=75, bg=250, bgtint=(0, -2, -7))
add("tiny knob far", [P(box=(560, 380, 1040, 980), gray=185, kind="sq"), P(box=(780, 300, 820, 365), gray=130, kind="rect", rim=0, highlight=False)])
add("three items", [P(box=(300, 450, 580, 900), gray=190), P(box=(660, 350, 940, 900), gray=160), P(box=(1020, 480, 1300, 900), gray=200)])
add("gray240-ish very light", [P(box=(520, 260, 1080, 900), gray=234, kind="sq", rim=0.02, highlight=False)])

add("gray190 noisy sigma5 jpeg85", [P(box=(520, 260, 1080, 900), gray=190, kind="sq")], noise=5.0, jpeg=85)
add("full-width bar noisy", [P(box=(0, 470, 1600, 740), gray=170, kind="rect", rim=0.04, highlight=False)], noise=4.0, jpeg=80)
add("hi-res 3000 gray200 clutter", [P(box=(1000, 480, 2000, 1700), gray=200, kind="sq")], size=(3000, 2250), band=True, frame=True, jpeg=88)
add("portrait 1200x1800 gray190", [P(box=(380, 500, 820, 1300), gray=190, kind="rect", rim=0.03)], size=(1200, 1800))
