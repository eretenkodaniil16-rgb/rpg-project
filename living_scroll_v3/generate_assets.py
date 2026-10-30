#!/usr/bin/env python3
"""Deterministic, dependency-light fallback art for Living Scroll V3.
The full artistic PNGs from the optional ZIP take precedence when present.
All files are generated locally; no external image models or credentials.
"""
from pathlib import Path
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT=Path(__file__).resolve().parent
A=ROOT/"assets"
A.mkdir(parents=True,exist_ok=True)
W,H=540,960
R=random.Random(30310)

def paper():
    rng=np.random.default_rng(301026)
    y,x=np.mgrid[:H,:W]
    grain=rng.normal(0,4,(H,W))
    veins=3*np.sin(x*.033+y*.009)+2*np.cos(x*.012-y*.023)
    vignette=5*((x-W/2)**2/(W/2)**2+(y-H/2)**2/(H/2)**2)
    v=grain+veins-vignette
    base=np.array([236,222,195],dtype=float)
    rgb=np.uint8(np.clip(base[None,None,:]+v[:,:,None],0,255))
    Image.fromarray(rgb,"RGB").save(A/"paper.png")

def mountain_layer(seed, horizon, darkness, count=10, shift=0):
    rng=random.Random(seed)
    im=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(im,"RGBA")
    for j in range(count):
        y0=horizon+int((j-count/2)*14)
        cx=rng.randrange(-100,W+100)
        wide=rng.randint(80,245)
        peak=y0-rng.randrange(100,350)
        points=[]
        for k in range(35):
            xx=cx-wide+2*wide*k/34
            triangular=(1-abs((xx-cx)/wide))
            ridge=y0-(y0-peak)*max(triangular,0)**(rng.uniform(.7,1.1))
            ridge+=rng.uniform(-14,14)
            points.append((xx,ridge))
        points.extend([(cx+wide,H+20),(cx-wide,H+20)])
        v=darkness+rng.randint(-11,11)
        d.polygon(points,fill=(v+8,v+12,v+9,rng.randint(115,194)))
        for _ in range(13):
            xx=cx+rng.randrange(-wide,wide)
            yy=peak+rng.randint(16,150)
            w=rng.randint(1,3)
            d.line((xx,yy,xx-rng.randrange(3,23),yy+rng.randrange(25,100)),fill=(18,24,22,rng.randint(14,65)),width=w)
    # warm mist to give depth and prevent hard stacked ridges
    mist=Image.new("RGBA",(W,H));md=ImageDraw.Draw(mist,"RGBA")
    for _ in range(36):
        cx=rng.randrange(-100,W+100);cy=horizon+rng.randrange(-80,170)
        md.ellipse((cx-140,cy-24,cx+140,cy+24),fill=(237,224,204,rng.randint(8,20)))
    mist=mist.filter(ImageFilter.GaussianBlur(34))
    im=Image.alpha_composite(im,mist)
    return im

def branch(d,x,y,dx,dy,depth,seed):
    if depth<1:return
    rng=random.Random(seed+depth*33+int(x))
    nx=x+dx;ny=y+dy
    d.line((x,y,nx,ny), fill=(21,25,24,200),width=max(1,depth*2))
    for _ in range(3):
        xx=nx+rng.uniform(-12,12); yy=ny+rng.uniform(-9,9)
        d.ellipse((xx-9,yy-3,xx+9,yy+3),fill=(29,37,33,rng.randint(80,170)))
    branch(d,nx,ny,dx*.62+rng.uniform(-8,8),dy*.72,depth-1,seed+7)
    branch(d,nx,ny,dx*.4-rng.uniform(5,16),dy*.64,depth-2,seed+19)

def temple(d,x,y,s=1):
    dark=(29,31,29,230)
    def poly(points,color=dark):
        d.polygon([(x+px*s,y+py*s) for px,py in points],fill=color)
    poly([(-50,0),(50,0),(50,-8),(-50,-8)])
    for k in range(-2,3):
        poly([(k*18-3,-8),(k*18+3,-8),(k*18+3,-46),(k*18-3,-46)])
    poly([(-66,-47),(66,-47),(51,-59),(36,-62),(0,-63),(-36,-62),(-51,-59)],(27,31,29,235))
    poly([(-45,-65),(45,-65),(37,-75),(-37,-75)])
    poly([(-62,-77),(62,-77),(38,-91),(0,-96),(-38,-91)])
    poly([(-4,-96),(4,-96),(3,-104),(-3,-104)])

def red_sun(im,x,y,r):
    sun=Image.new("RGBA",(W,H))
    sd=ImageDraw.Draw(sun)
    for i in range(r,0,-1):
        t=i/r
        sd.ellipse((x-i,y-i,x+i,y+i),fill=(143+int(35*(1-t)),47+int(13*t),34, max(2,int(2.8*(1-t)))))
    im.alpha_composite(sun)

def landscape():
    bg=Image.open(A/"paper.png").convert("RGBA")
    red_sun(bg,390,240,80)
    far=mountain_layer(14,510,108,9)
    mid=mountain_layer(26,650,75,9)
    near=mountain_layer(38,790,32,6)
    # decorate separate layers with natural strokes and detail
    d=ImageDraw.Draw(mid,"RGBA")
    temple(d,330,670,.58)
    d=ImageDraw.Draw(near,"RGBA")
    temple(d,120,810,1.12)
    for x in [70,115,480]:
        branch(d,x,880,R.uniform(-32,-8),-52,4,int(x))
    for layer,name in [(far,"far_mountains.png"),(mid,"mid_mountains.png"),(near,"near_mountains.png")]:
        layer.save(A/name,optimize=True)
        bg=Image.alpha_composite(bg,layer)
    bg.convert("RGB").save(A/"landscape_master.png")

def lotus():
    bg=Image.open(A/"paper.png").convert("RGBA")
    ink=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(ink,"RGBA")
    cx,cy=270,400
    # ink tendrils radiating out from the seed drop
    for i in range(180):
        a=R.uniform(0,2*math.pi)
        r=R.uniform(5,340)
        px=cx+math.cos(a)*r;py=cy+math.sin(a)*r*.57
        d.ellipse((px-1.7,py-1.7,px+1.7,py+1.7),fill=(20,25,24,R.randrange(25,105)))
    for k in range(6):
        r=92+k*19
        d.arc((cx-r,cy-r*.42,cx+r,cy+r*.42),0,180,fill=(36,40,37,70),width=2)
    # layered petals: thick outlines, translucent brush fills and cinnabar tips
    for i in range(13):
        a=math.pi*2*i/13
        rx=math.cos(a);ry=math.sin(a)
        px=cx+rx*18;py=cy+ry*12
        tx=cx+rx*R.randrange(93,141);ty=cy+ry*R.randrange(110,160)
        nx=-ry*R.randrange(26,41);ny=rx*R.randrange(25,35)
        path=[(px,py),(cx+rx*65+nx,cy+ry*55+ny),(tx,ty),(cx+rx*65-nx,cy+ry*55-ny)]
        d.polygon(path,fill=(248,243,227,194))
        d.line(path+[path[0]],fill=(23,28,27,175),width=3,joint="curve")
        d.line((cx+rx*20,cy+ry*12,tx,ty),fill=(80,82,73,95),width=2)
        d.ellipse((tx-4,ty-4,tx+4,ty+4),fill=(162,49,36,183))
    d.ellipse((cx-22,cy-19,cx+22,cy+19),fill=(166,117,63,230),outline=(51,42,29,240),width=2)
    ink=ink.filter(ImageFilter.GaussianBlur(.4))
    bg=Image.alpha_composite(bg,ink)
    # lotus_focus is a full-screen, transparent image, not a masked rectangular crop
    ink.save(A/"lotus_focus.png",optimize=True)
    bg.convert("RGB").save(A/"lotus_master.png")

def main():
    paper()
    # Existing authored artwork wins when mounted from the original ZIP.
    if not (A/"landscape_master.png").exists(): landscape()
    if not (A/"lotus_master.png").exists(): lotus()
    required=("paper.png","far_mountains.png","mid_mountains.png","near_mountains.png","lotus_focus.png")
    if not all((A/n).exists() for n in required):
        landscape();lotus()
    print("Prepared Living Scroll art",[(p.name,p.stat().st_size) for p in A.glob("*.png")])

if __name__=="__main__":main()
