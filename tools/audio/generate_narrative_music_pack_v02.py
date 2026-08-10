#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, shutil, struct, subprocess, wave
from pathlib import Path
import numpy as np

SR=48000; PPQ=480
NOTE={"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}

def note_num(name:str)->int:
    p=name[:2] if len(name)>=3 and name[1] in "#b" else name[:1]
    return 12*(int(name[len(p):])+1)+NOTE[p]
def freq(name:str)->float: return 440.0*2**((note_num(name)-69)/12)
def env(n:int,a=.01,r=.2):
    e=np.ones(n); na=min(n,max(1,int(a*SR))); nr=min(n,max(1,int(r*SR)))
    e[:na]=np.linspace(0,1,na,endpoint=False); e[-nr:]*=np.linspace(1,0,nr); return e

def tone(note:str,seconds:float,kind:str,seed:int=0)->np.ndarray:
    n=max(1,int(seconds*SR)); t=np.arange(n)/SR; f=freq(note); rng=np.random.default_rng(seed); p=2*np.pi*f*t
    if kind=="sub": x=(np.sin(p)+.16*np.sin(2*p))*env(n,.08,min(.4,seconds*.3))
    elif kind=="bowed":
        q=p+.0038*np.sin(2*np.pi*5.3*t)+.0014*np.sin(2*np.pi*6.9*t)
        x=(np.sin(q)+.43*np.sin(2*q+.15)+.18*np.sin(3*q+.4)+.009*rng.standard_normal(n))*env(n,.18,min(.65,seconds*.25))
    elif kind=="glass":
        x=(np.sin(p)*np.exp(-t*.26)+.42*np.sin(p*2.71+.2)*np.exp(-t*.48)+.22*np.sin(p*4.08+.5)*np.exp(-t*.72))*env(n,.006,min(.65,seconds*.4))
    elif kind=="celesta": x=(np.sin(p)+.32*np.sin(2.015*p)+.14*np.sin(4.03*p))*np.exp(-t*1.25)*env(n,.002,min(.25,seconds*.35))
    elif kind=="panic":
        q=p+.007*np.sin(2*np.pi*7.4*t)
        x=(np.sin(q)+.34*np.sin(2*q+.4)+.16*np.sin(3*q+.2)+.018*rng.standard_normal(n))*env(n,.015,min(.12,seconds*.18))
    elif kind=="brass":
        q=p+.002*np.sin(2*np.pi*5*t); x=np.tanh((np.sin(q)+.55*np.sin(2*q)+.28*np.sin(3*q))*1.1)*env(n,.025,min(.25,seconds*.22))
    elif kind=="choir":
        x=sum(np.sin(2*np.pi*f*(1+d)*t) for d in (-.005,-.002,.002,.005))/4 + .16*np.sin(2*p+.25)
        x*=env(n,.35,min(.7,seconds*.25))
    else: raise ValueError(kind)
    return x/(np.max(np.abs(x)) or 1)

def hit(kind:str,seconds:float,seed:int)->np.ndarray:
    n=max(1,int(seconds*SR)); t=np.arange(n)/SR; rng=np.random.default_rng(seed); noise=rng.standard_normal(n)
    if kind=="mechanical":
        hp=np.concatenate([[noise[0]],np.diff(noise)]); x=.6*hp*np.exp(-t*26)+.5*np.sin(2*np.pi*43*t)*np.exp(-t*8)
    elif kind=="whisper":
        smooth=np.convolve(noise,np.ones(25)/25,mode="same"); x=(noise-smooth)*env(n,.22,min(.5,seconds*.2))
    elif kind=="war":
        pitch=44+22*np.exp(-t*4); ph=2*np.pi*np.cumsum(pitch)/SR; x=np.sin(ph)*np.exp(-t*3.2)+.15*noise*np.exp(-t*10)
    elif kind=="fracture":
        hp=np.concatenate([[noise[0]],np.diff(noise)]); x=hp*np.exp(-t*18)+.22*np.sin(2*np.pi*117*t)*np.exp(-t*7)
    else: raise ValueError(kind)
    return x/(np.max(np.abs(x)) or 1)

def pan(m,p):
    a=(max(-1,min(1,p))+1)*np.pi/4; return np.column_stack([m*np.cos(a),m*np.sin(a)])
def add(dst,mono,start,gain,p=0):
    s=int(round(start*SR));
    if s>=len(dst): return
    st=pan(mono,p)*gain; e=min(len(dst),s+len(st));
    if e>s: dst[s:e]+=st[:e-s]
def add_note(dst,n,start,dur,kind,gain,p,seed): add(dst,tone(n,dur,kind,seed),start,gain,p)
def add_hit(dst,kind,start,gain,p,seed,dur=.5): add(dst,hit(kind,dur,seed),start,gain,p)
def reverb(a,taps):
    out=a.copy()
    for delay,g in taps:
        sh=int(delay*SR)
        if sh<len(a): out[sh:,0]+=a[:-sh,1]*g; out[sh:,1]+=a[:-sh,0]*g
    return out
def master(a,peak_db,drive):
    a=np.tanh(a*drive)/np.tanh(drive); a*=10**(peak_db/20)/(np.max(np.abs(a)) or 1); return np.clip(a,-1,1)

def render_elevator(score):
    tempo=score["tempo_bpm"]; bars=score["bars"]; secq=60/tempo; dur=bars*4*secq; a=np.zeros((int(round(dur*SR)),2))
    roots=["D2","C#2","C2","B1","Bb1","A1","Ab1","G1","Gb1","F1","E1","Eb1","D1","Db1","C1","B0","Bb0"]
    uppers=["A2","Ab2","G2","Gb2","F2","E2","Eb2","D2","Db2","C2","B1","Bb1","A1","Ab1","G1","Gb1","F1"]
    for bar in range(bars):
        bs=bar*4*secq; fear=bar/(bars-1)
        add_note(a,roots[bar],bs,4*secq*1.04,"sub",.08+.075*fear,0,100+bar)
        add_note(a,uppers[bar],bs+.18,4*secq*.95,"bowed",.045+.05*fear,-.22,200+bar)
        if bar>=5:
            dis=["Eb3","D3","Db3","C3","B2","Bb2","A2","Ab2","G2","Gb2","F2","E2"][min(bar-5,11)]
            add_note(a,dis,bs+.42,4*secq*.72,"bowed",.025+.035*fear,.27,300+bar)
        pulses=[0,1,2,3] if bar<4 else ([0,.82,1.71,2.83] if bar<10 else [0,.61,1.46,2.18,3.22])
        if bar in (11,14): pulses=pulses[:-1]
        for j,o in enumerate(pulses): add_hit(a,"mechanical",bs+o*secq,.045+.05*fear,-.48 if j%2==0 else .48,500+bar*7+j,.38)
        if bar in (1,4,7,10,13,15):
            idx=(1,4,7,10,13,15).index(bar)
            frag=[("D5","Eb5","A4"),("D5","Eb5","Ab4"),("D4","Eb4","A3"),("D4","Eb4","Ab3"),("D3","Eb3","A2"),("D3","Eb3","Ab2")][idx]
            for j,n in enumerate(frag): add_note(a,n,bs+[.15,1.05,2.35][j]*secq,.8*secq,"glass",.075+.02*fear,-.2+.2*j,700+bar*5+j)
        if bar>=8:
            count=2+(bar-8)//2; notes=["D6","Eb6","D6","Ab5","A5","Eb6"]
            for j in range(count):
                o=.32+j*(3.2/max(1,count)); add_note(a,notes[(bar+j)%len(notes)],bs+o*secq,.18*secq,"celesta",.028+.035*fear,-.65 if j%2==0 else .65,900+bar*11+j)
        if bar>=6: add_hit(a,"whisper",bs+.25*secq,.008+.03*fear,-.55 if bar%2 else .55,1100+bar,2.6)
        if bar>=12:
            seq=["D5","Eb5","D5","A4","Ab4","D5","Eb5"]
            for j,n in enumerate(seq): add_note(a,n,bs+(.42+j*.42)*secq,.22*secq,"panic",.025+.022*fear,-.45 if j%2==0 else .45,1300+bar*13+j)
    a=reverb(a,[(.17,.11),(.33,.075),(.59,.052),(.93,.034),(1.37,.02)]); fin=int(1.6*SR); a[-fin:]*=np.linspace(1,.24,fin)[:,None]
    return master(a,-1.25,1.08)

def render_act(score):
    tempo=score["tempo_bpm"]; bars=score["bars"]; secq=60/tempo; dur=bars*4*secq; a=np.zeros((int(round(dur*SR)),2))
    chords=[["D2","A2","D3","F3"],["Bb1","F2","Bb2","D3"],["C2","G2","C3","Eb3"],["A1","Eb2","A2","C#3"],["D2","Eb3","A3","Ab3"],["C2","Db3","G3","Ab3"],["Bb1","B2","F3","A3"],["A1","Eb2","G2","Db3"]]
    motif=["D5","Eb5","D5","A4","Ab4","F5"]
    for bar in range(bars):
        bs=bar*4*secq; panic=bar/(bars-1); chord=chords[(bar//2)%len(chords)]
        for i,n in enumerate(chord): add_note(a,n,bs,4*secq*.94,"bowed",.045+.022*panic,-.52+.34*i,2100+bar*9+i)
        if bar>=7: add_note(a,chord[1],bs+.08,4*secq*.86,"choir",.025+.035*panic,0,2200+bar)
        if bar in (1,4):
            for j,(n,o,d) in enumerate([("D4",0,.8),("A3",.9,.45),("C4",1.45,.45),("Eb4",2,.35),("D4",2.48,.7)]): add_note(a,n,bs+o*secq,d*secq,"glass",.07,.18,2300+bar*7+j)
        if bar>=5:
            step=.72 if bar<12 else (.48 if bar<20 else .31); t=.18; j=0
            while t<3.65:
                add_note(a,motif[(bar+j)%len(motif)],bs+t*secq,max(.10,step*.42)*secq,"panic" if bar>=12 else "celesta",.032+.035*panic,-.58 if j%2==0 else .58,2500+bar*29+j)
                t+=step; j+=1
        if bar>=6:
            hs=[0,1.55,2.28] if bar<15 else [0,.92,1.71,2.63,3.42]
            if bar in (10,17,23): hs=hs[:-1]
            for j,o in enumerate(hs): add_hit(a,"war",bs+o*secq,.052+.075*panic,-.12,3000+bar*9+j,.72)
        if bar>=11:
            st=[.45,2.45] if bar<19 else [.28,1.38,2.18,3.18]; bn=["D3","Eb3","Ab2","A2"]
            for j,o in enumerate(st): add_note(a,bn[(bar+j)%4],bs+o*secq,.25*secq,"brass",.042+.055*panic,.12 if j%2 else -.15,3300+bar*7+j)
        if bar>=13:
            alarms=[("Eb6",.62),("E6",2.12)] if bar%2==0 else [("A5",1.04),("Ab5",2.92)]
            for j,(n,o) in enumerate(alarms): add_note(a,n,bs+o*secq,.5*secq,"glass",.045+.04*panic,.48,3600+bar*5+j)
        if bar>=16:
            for j,o in enumerate((.35,1.9,3.35)): add_hit(a,"fracture",bs+o*secq,.026+.04*panic,.4 if j%2 else -.4,3900+bar*7+j,.32)
        if bar>=20: add_hit(a,"whisper",bs+.1*secq,.018+.025*panic,0,4200+bar,1.6)
    a=reverb(a,[(.105,.095),(.23,.07),(.41,.05),(.69,.034),(1.03,.019)])
    for center,width in [(23*4*secq+.95,.34),(25*4*secq+2.15,.42)]:
        s=max(0,int((center-width/2)*SR)); e=min(len(a),int((center+width/2)*SR))
        if e>s:
            x=np.linspace(0,1,e-s); notch=np.minimum(1,np.abs(x-.5)*5.2); a[s:e]*=notch[:,None]*.18
    tail=int(.85*SR); a[-tail:]*=np.linspace(1,.32,tail)[:,None]
    return master(a,-.9,1.18)

def write_wav(path,a):
    pcm=np.round(np.clip(a,-1,1)*32767).astype("<i2")
    with wave.open(str(path),"wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
def vlq(n):
    b=[n&0x7f]; n>>=7
    while n: b.append((n&0x7f)|0x80); n>>=7
    return bytes(reversed(b))
def write_diag_midi(path,score):
    tempo=score["tempo_bpm"]; seq=["D4","Eb4","D4","A3","Ab3","F4"]; tr=bytearray(); us=int(round(60_000_000/tempo)); tr.extend(b"\x00\xff\x51\x03"+us.to_bytes(3,"big")); last=0
    timeline=[]
    for i,n in enumerate(seq*4):
        st=i*PPQ//2; en=st+PPQ//3; nn=note_num(n); timeline += [(st,1,nn),(en,0,nn)]
    timeline.sort()
    for tick,on,nn in timeline:
        tr.extend(vlq(tick-last)); last=tick; tr.extend(bytes([(0x90 if on else 0x80),nn,86 if on else 0]))
    tr.extend(b"\x00\xff\x2f\x00"); path.write_bytes(b"MThd"+struct.pack(">IHHH",6,0,1,PPQ)+b"MTrk"+struct.pack(">I",len(tr))+bytes(tr))
def pcm_sig(a):
    pcm=np.round(np.clip(a,-1,1)*32767).astype(np.int16); reduced=(pcm.astype(np.int32)>>8).astype(np.int16); return hashlib.sha256(reduced.tobytes()).hexdigest()
def render(score_path:Path,out:Path):
    score=json.loads(score_path.read_text(encoding="utf-8")); cid=score["composition_id"]
    if cid=="elevator_descent_floor01_v01": a=render_elevator(score)
    elif cid=="act01_plan_broken_v01": a=render_act(score)
    else: raise ValueError(f"renderer v02 does not handle {cid}")
    out.mkdir(parents=True,exist_ok=True); wav=out/f"{cid}_master.wav"; ogg=out/f"{cid}_master.ogg"; mp3=out/f"{cid}_preview.mp3"; mid=out/f"{cid}.mid"
    write_wav(wav,a); write_diag_midi(mid,score)
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(wav),"-c:a","libvorbis","-q:a","5",str(ogg)],check=True)
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(wav),"-c:a","libmp3lame","-b:a","192k",str(mp3)],check=True)
    peak=float(np.max(np.abs(a))); rms=float(np.sqrt(np.mean(a*a)))
    m={"composition_id":cid,"score_sha256":hashlib.sha256(score_path.read_bytes()).hexdigest(),"renderer":"procedural_narrative_music_renderer_v02","arrangement_revision":2,"numpy_version":np.__version__,"sample_rate":SR,"channels":2,"duration_seconds":round(len(a)/SR,6),"tempo_bpm":score["tempo_bpm"],"time_signature":score["time_signature"],"bars":score["bars"],"loop":False,"pcm_signature_shift_bits":8,"pcm_signature_sha256":pcm_sig(a),"peak_dbfs":round(20*math.log10(peak),4),"rms_dbfs":round(20*math.log10(rms),4),"boundary_value_delta":0.0,"boundary_slope_delta":0.0,"wav_sha256":hashlib.sha256(wav.read_bytes()).hexdigest(),"midi_sha256":hashlib.sha256(mid.read_bytes()).hexdigest()}
    if ogg.exists(): m.update(ogg_sha256=hashlib.sha256(ogg.read_bytes()).hexdigest(),ogg_size_bytes=ogg.stat().st_size)
    if mp3.exists(): m["mp3_sha256"]=hashlib.sha256(mp3.read_bytes()).hexdigest()
    (out/f"{cid}_master_manifest.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return m

def main():
    p=argparse.ArgumentParser(); p.add_argument("--score",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); print(json.dumps(render(a.score,a.output),ensure_ascii=False,indent=2))
if __name__=="__main__": main()
