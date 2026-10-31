#!/usr/bin/env python3
"""V4.2 original painterly raster layers. Deterministic: no network/AI API needed.
Changes are confined to the isolated V4.2 CI checkout, not the V3 branch.
"""
from pathlib import Path
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parent.parent/"living_scroll_v3"/"assets"
W,H=540,960
SEED=420026
R=random.Random(SEED)

def noise(w,h,seed,octaves=((9,8,1.),(24,24,.50),(75,69,.20),(230,230,.09))):
    gen=np.random.default_rng(seed)
    acc=np.zeros((h,w),np.float32)
    weight=0.
    for nx,ny,amp in octaves:
        a=gen.integers(0,256,size=(ny,nx),dtype=np.uint8)
        im=Image.fromarray(a).resize((w,h),Image.Resampling.BICUBIC)
        aa=np.array(im).astype(np.float32)/127.5-1
        acc+=amp*aa; weight+=amp
    return acc/weight

def make_ridge(seed,horizon,intensity):
    rng=np.random.default_rng(seed)
    X=np.arange(W,dtype=np.float32)
    signal=np.zeros((W,),np.float32)
    centers=[(-80,125,120),(85,90,140),(235,100,155),(410,75,130),(550,105,90)]
    # Broad distinct peaks with shoulders, not triangle primitives.
    for x0,spread,height in centers:
        h=height*float(rng.uniform(.45,1.28))*intensity
        c=x0+float(rng.uniform(-38,38))
        signal+=h*np.exp(-.5*((X-c)/spread)**2)
    n=noise(W,1,seed+8,((8,1,1),(32,1,.35),(112,1,.13),(330,1,.05)))[0]
    ridge=horizon-signal-23*n
    return ridge

def pine(draw,x,y,scale,tone,rng):
    """Native brush-like black pine, trunk and irregular leaf strokes."""
    col=(tone,tone+4,tone+3,208)
    trunk_h=27*scale
    draw.line((x,y,x+1.5*scale,y-trunk_h),fill=col,width=max(1,round(2.7*scale)))
    for level in (0.2,.42,.64,.84):
        yy=y-trunk_h*level
        sign=-1 if rng.random()<.5 else 1
        xx=x+sign*rng.uniform(7,16)*scale
        draw.line((x,yy+3*scale,xx,yy-3*scale),fill=col,width=max(1,round(1.4*scale)))
        for _ in range(6):
            px=xx+rng.gauss(0,6)*scale
            py=yy+rng.gauss(0,2.8)*scale
            draw.line((px-5*scale,py,px+5*scale,py+1*scale),
                      fill=(tone,tone+4,tone+3,int(rng.uniform(110,205))),
                      width=max(1,round(1.5*scale)))

def create_mountains(name,seed,horizon,level,amp,alpha):
    rng=np.random.default_rng(seed)
    jag=noise(W,H,seed+41)
    pigment=noise(W,H,seed+82,((20,22,1),(60,65,.6),(160,225,.2)))
    ridge=make_ridge(seed,horizon,amp)
    X=np.arange(W)[None,:]
    Y=np.arange(H)[:,None]
    # Ridge silhouette and soft capillary edge, no black horizontal cutoffs.
    signed=Y-ridge[None,:]-13*jag
    opacity=np.clip((signed+2.5)/12.0,0,1)
    # Washed ink extends downwards but remains textured and translucent.
    textured=.68+.36*pigment+.14*np.sin(Y*.019+jag*8)
    edge_bloom=np.exp(-(signed/23)**2)
    opacity=np.clip(opacity*textured+0.12*edge_bloom*opacity,0,1)*alpha
    gray=np.clip(level+28*(pigment+.28*jag)+.010*np.maximum(signed,0),8,219)
    img=np.empty((H,W,4),np.uint8)
    img[:,:,0]=np.uint8(np.clip(gray+5,0,255))
    img[:,:,1]=np.uint8(np.clip(gray+10,0,255))
    img[:,:,2]=np.uint8(np.clip(gray+8,0,255))
    img[:,:,3]=np.uint8(np.clip(opacity,0,255))
    base=Image.fromarray(img,"RGBA")
    marks=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(marks,"RGBA")
    rnd=random.Random(seed+9)
    # Shattered ink ledges, fissures, and dry-brush ridges (restricted to the silhouette).
    for _ in range(300):
        x=rnd.randrange(W)
        y0=float(ridge[x])
        y=y0+rnd.uniform(7,290)
        if y>=H-3:continue
        depth=(y-y0)/max(1,H-y0)
        n=int(rnd.uniform(2,10)*(1+depth))
        dx=rnd.uniform(-16,14)
        length=rnd.uniform(8,48)*(0.7+depth)
        val=max(12,level-rnd.randint(18,34))
        d.line((x,y,x+dx,y+length),fill=(val,val+5,val+4,rnd.randrange(24,108)),width=rnd.choice((1,1,2,3)))
        if rnd.random()<.2:
            d.arc((x-10,y-4,x+11,y+12),0,160,fill=(220,214,198,rnd.randrange(25,65)),width=1)
    # Pine tufts on selected ridgelines, smallest toward far layer.
    if name!="far_mountains.png":
        for _ in range(26 if name=="mid_mountains.png" else 42):
            x=rnd.randint(5,W-5)
            yy=float(ridge[x])+rnd.uniform(-3,20)
            if yy>H-55:continue
            pine(d,x,yy,rnd.uniform(.35,.78) if name=="mid_mountains.png" else rnd.uniform(.5,1.1),
                 max(13,level-rnd.randint(12,26)),rnd)
    mask=np.array(base)[:,:,3]
    markarray=np.array(marks)
    # Do not allow free-floating brush strokes above ridge.
    markarray[:,:,3]=np.uint8(markarray[:,:,3].astype(float)*np.minimum(1,mask.astype(float)/58))
    base=Image.alpha_composite(base,Image.fromarray(markarray,"RGBA"))
    base.save(ROOT/name,optimize=True)
    return base

def build_background():
    paper=Image.open(ROOT/"paper.png").convert("RGBA")
    sun=Image.new("RGBA",(W,H))
    pixels=np.zeros((H,W,4),np.uint8)
    yy,xx=np.mgrid[:H,:W]
    radial=np.sqrt((xx-389)**2+(yy-272)**2)
    rough=noise(W,H,441)
    opacity=np.clip((78-radial+rough*11)/9,0,1)
    pigment=np.clip(.70+.27*rough,0,1)
    pixels[:,:,0]=171;pixels[:,:,1]=61;pixels[:,:,2]=43
    pixels[:,:,3]=np.uint8(np.clip(210*opacity*pigment,0,255))
    sun=Image.fromarray(pixels,"RGBA")
    paper=Image.alpha_composite(paper,sun)
    dr=ImageDraw.Draw(paper,"RGBA")
    rnd=random.Random(615)
    # Sparse sky brush ribbons—kept below the red sun.
    for i in range(34):
        y=rnd.randrange(225,520)
        x=rnd.randrange(-75,W)
        length=rnd.randrange(28,130)
        shade=rnd.randint(122,175)
        dr.arc((x,y,x+length,y+18),190,345,fill=(shade,shade+5,shade+3,rnd.randint(24,60)),width=rnd.choice((1,2,2,3)))
    # Delicate light river glimmers, not opaque foreground stripes.
    for i in range(50):
        x=rnd.randrange(40,W)
        y=rnd.randrange(730,945)
        dr.line((x,y,x+rnd.randrange(12,65),y),fill=(158,133,104,rnd.randrange(13,38)),width=1)
    paper.convert("RGB").save(ROOT/"landscape_master.png",optimize=True)

def main():
    for needed in ("paper.png",):
        if not (ROOT/needed).exists():raise RuntimeError("Run V3 generate_assets.py first: "+needed)
    build_background()
    create_mountains("far_mountains.png",731,558,144,.85,157)
    create_mountains("mid_mountains.png",741,696,100,1.13,188)
    create_mountains("near_mountains.png",751,824,50,1.15,222)
    print("V4.2_BRUSH_LAYERS_OK",[(p.name,p.stat().st_size) for p in ROOT.glob("*mountains.png")])

if __name__=="__main__":main()
