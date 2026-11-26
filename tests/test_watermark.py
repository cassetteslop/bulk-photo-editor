import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "support"), os.path.dirname(HERE)]
SP = tempfile.mkdtemp(prefix="bpe_tests_")
import faketk
import sys; sys.path.insert(0,'.')
from legacy import b
from PIL import Image, ImageDraw
import numpy as np
mark=Image.new("RGBA",(200,100),(0,0,0,0)); ImageDraw.Draw(mark).ellipse((0,0,199,99),fill=(255,0,0,255)); mark.save(SP+"/wm.png")
bad=SP+"/bad.png"; open(bad,"wb").write(b"junk")
base=Image.new("RGB",(1000,800),(255,255,255))
def S(**k):
    s=dict(b.DEFAULTS); s.update(rotate=0,flip_h=False,flip_v=False,resize_mode="None",crop_enabled=False); s.update(k); return s
for pos in ["Bottom right","Bottom center","Bottom left","Top right","Top center","Top left","Center"]:
    o=np.array(b.finish(base,None,S(wm_image=SP+"/wm.png",wm_pos=pos,wm_opacity=100)))
    red=(o[...,1]<100); ys,xs=np.where(red)
    cx,cy=xs.mean()/1000,ys.mean()/800
    ex={"right":0.88,"left":0.12}; exx=0.88 if "right" in pos else 0.12 if "left" in pos else 0.5
    exy=0.08 if "Top" in pos else 0.92 if "Bottom" in pos else 0.5
    assert abs(cx-exx)<0.02 and abs(cy-exy)<0.02, (pos,cx,cy)
    print(pos,round(cx,2),round(cy,2),xs.max()-xs.min()+1)
o=np.array(b.finish(base,None,S(wm_image=SP+"/wm.png",wm_opacity=50,wm_pos="Center")))
print("opacity px",o[400,500], "corner",o[5,5])
print("bad:",b.finish(base,None,S(wm_image=bad)).size, "missing:",b.finish(base,None,S(wm_image=SP+"/nope.png")).size)
t=b.finish(base,None,S(wm_image=SP+"/wm.png",wm_text="HELLO",wm_pos="Top center")); t.save(SP+"/wm_out.png")
al=Image.new("L",base.size,255); print(b.finish(base,al,S(wm_image=SP+"/wm.png")).mode)
tiny=Image.new("RGB",(60,40),"white"); print(b.finish(tiny,None,S(wm_image=SP+"/wm.png",wm_img_size=80)).size)

assert tuple(o[400,500])==(255,128,128) or abs(int(o[400,500][1])-128)<3
print("WATERMARK TESTS PASSED")
