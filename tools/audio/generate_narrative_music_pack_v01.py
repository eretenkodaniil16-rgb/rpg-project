#!/usr/bin/env python3
"""Deterministic original narrative music pack renderer.

Four original tracks for Chronicles of the Wanderer:
- mad_wizard_theme_v01
- tavern_commonroom_v01
- elevator_descent_floor01_v01
- act01_plan_broken_v01

No external samples or third-party melodies are used. The renderer produces
48 kHz stereo WAV/Ogg/MP3 previews plus a simple MIDI diagnostic and manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

PPQ = 480
SAMPLE_RATE = 48_000
NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

@dataclass
class MidiEvent:
    start_q: float
    duration_q: float
    note: int
    velocity: int
    channel: int = 0
    program: int = 0


def note_number(name: str) -> int:
    if len(name) < 2:
        raise ValueError(name)
    pitch = name[:2] if len(name) >= 3 and name[1] in "#b" else name[:1]
    octave = int(name[len(pitch):])
    return 12 * (octave + 1) + NOTE_TO_SEMITONE[pitch]


def freq(name: str) -> float:
    return 440.0 * (2.0 ** ((note_number(name) - 69) / 12.0))


def env_adsr(n: int, sr: int, attack: float, decay: float, sustain: float, release: float) -> np.ndarray:
    if n <= 1:
        return np.ones(n, dtype=np.float64)
    a = min(n, max(1, int(attack * sr)))
    d = min(max(0, n - a), max(1, int(decay * sr)))
    r = min(max(0, n - a - d), max(1, int(release * sr)))
    s = max(0, n - a - d - r)
    parts = []
    parts.append(np.linspace(0.0, 1.0, a, endpoint=False))
    if d:
        parts.append(np.linspace(1.0, sustain, d, endpoint=False))
    if s:
        parts.append(np.full(s, sustain))
    if r:
        parts.append(np.linspace(sustain, 0.0, r, endpoint=True))
    out = np.concatenate(parts)
    if len(out) < n:
        out = np.pad(out, (0, n - len(out)))
    return out[:n]


def one_pole_lowpass(x: np.ndarray, cutoff: float, sr: int) -> np.ndarray:
    cutoff = max(20.0, min(cutoff, sr * 0.45))
    alpha = 1.0 - math.exp(-2.0 * math.pi * cutoff / sr)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def instrument(note: str, seconds: float, kind: str, sr: int, seed: int = 0) -> np.ndarray:
    n = max(1, int(seconds * sr))
    t = np.arange(n, dtype=np.float64) / sr
    f = freq(note)
    rng = np.random.default_rng(seed)
    phase = 2.0 * math.pi * f * t

    if kind == "celesta":
        sig = (np.sin(phase) + 0.38*np.sin(2.01*phase) + 0.18*np.sin(3.97*phase))
        sig *= np.exp(-t * 1.45)
        sig *= env_adsr(n, sr, 0.003, 0.06, 0.8, min(0.5, seconds*0.45))
    elif kind == "glass":
        sig = np.zeros(n)
        for ratio, gain, decay in [(1.0,1.0,0.34),(2.72,0.42,0.55),(4.11,0.25,0.78),(6.36,0.12,1.1)]:
            sig += gain*np.sin(2*math.pi*f*ratio*t + ratio*0.13)*np.exp(-t*decay)
        sig *= env_adsr(n, sr, 0.01, 0.1, 0.72, min(0.7, seconds*0.4))
    elif kind == "bowed":
        vib = 0.0045*np.sin(2*math.pi*5.15*t) + 0.0018*np.sin(2*math.pi*6.7*t)
        p = phase + vib
        sig = np.sin(p) + 0.46*np.sin(2*p+0.2) + 0.23*np.sin(3*p+0.4) + 0.08*np.sin(5*p)
        sig += 0.015*rng.standard_normal(n)
        sig = one_pole_lowpass(sig, min(6800.0, 850.0 + f*8.0), sr)
        sig *= env_adsr(n, sr, 0.17, 0.2, 0.8, min(0.5, seconds*0.35))
    elif kind == "fiddle":
        vib = 0.011*np.sin(2*math.pi*5.8*t)
        p = 2*math.pi*f*(1.0+vib*0.002)*t
        sig = np.zeros(n)
        for h in range(1, 8):
            sig += (1.0/h)*np.sin(h*p + 0.11*h)
        sig += 0.012*rng.standard_normal(n)
        sig = one_pole_lowpass(sig, 5200.0, sr)
        sig *= env_adsr(n, sr, 0.045, 0.1, 0.86, min(0.24, seconds*0.3))
    elif kind == "flute":
        vib = 0.012*np.sin(2*math.pi*5.3*t)
        p = phase + vib
        breath = one_pole_lowpass(rng.standard_normal(n), 4600.0, sr)
        sig = np.sin(p) + 0.12*np.sin(2*p+0.2) + 0.025*breath
        sig *= env_adsr(n, sr, 0.07, 0.08, 0.92, min(0.25, seconds*0.3))
    elif kind == "reed":
        p = phase + 0.004*np.sin(2*math.pi*4.9*t)
        sig = np.sin(p) + 0.34*np.sin(2*p) + 0.14*np.sin(3*p) + 0.06*np.sin(5*p)
        sig = one_pole_lowpass(sig, 4300.0, sr)
        sig *= env_adsr(n, sr, 0.045, 0.09, 0.84, min(0.24, seconds*0.25))
    elif kind == "lute":
        noise = rng.standard_normal(n)
        sig = np.sin(phase) + 0.55*np.sin(2*phase+0.1) + 0.28*np.sin(3*phase+0.25)
        sig += 0.035*one_pole_lowpass(noise, 7800.0, sr)
        sig *= np.exp(-t*(2.0+0.0012*f))
        sig *= env_adsr(n, sr, 0.002, 0.035, 0.85, min(0.13, seconds*0.3))
    elif kind == "choir":
        sig = np.zeros(n)
        for det in (-0.006,-0.002,0.002,0.006):
            p = 2*math.pi*f*(1.0+det)*t
            sig += np.sin(p) + 0.22*np.sin(2*p+0.3)
        sig /= 4.0
        sig = one_pole_lowpass(sig, 3300.0, sr)
        sig *= env_adsr(n, sr, 0.55, 0.25, 0.78, min(0.8, seconds*0.3))
    elif kind == "brass":
        p = phase + 0.003*np.sin(2*math.pi*5.0*t)
        sig = np.sin(p)+0.58*np.sin(2*p)+0.31*np.sin(3*p)+0.15*np.sin(4*p)
        sig = np.tanh(sig*0.8)
        sig = one_pole_lowpass(sig, 3100.0, sr)
        sig *= env_adsr(n, sr, 0.08, 0.12, 0.88, min(0.35, seconds*0.25))
    elif kind == "sub":
        sig = np.sin(phase) + 0.18*np.sin(2*phase)
        sig *= env_adsr(n, sr, 0.08, 0.1, 0.9, min(0.35, seconds*0.25))
    else:
        raise ValueError(kind)

    peak = float(np.max(np.abs(sig))) or 1.0
    return sig/peak


def percussive(kind: str, seconds: float, sr: int, seed: int) -> np.ndarray:
    n = max(1, int(seconds*sr))
    t = np.arange(n)/sr
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    if kind == "frame":
        pitch = 92*np.exp(-t*8)+56
        ph = 2*math.pi*np.cumsum(pitch)/sr
        sig = 0.95*np.sin(ph)*np.exp(-t*7.0) + 0.22*one_pole_lowpass(noise, 4200, sr)*np.exp(-t*18)
    elif kind == "shaker":
        sig = one_pole_lowpass(noise, 8500, sr) - one_pole_lowpass(noise, 1800, sr)
        sig *= np.exp(-t*15)
    elif kind == "war":
        pitch = 55*np.exp(-t*3)+36
        ph = 2*math.pi*np.cumsum(pitch)/sr
        sig = np.sin(ph)*np.exp(-t*3.8)+0.18*one_pole_lowpass(noise,2200,sr)*np.exp(-t*9)
    elif kind == "mechanical":
        click = (noise - one_pole_lowpass(noise, 1800, sr))*np.exp(-t*24)
        low = np.sin(2*math.pi*43*t)*np.exp(-t*8)
        sig = 0.55*click+low
    elif kind == "whisper":
        sig = one_pole_lowpass(noise, 6500, sr)
        sig -= one_pole_lowpass(noise, 600, sr)
        sig *= env_adsr(n, sr, 0.2, 0.1, 0.7, min(0.4, seconds*0.25))
    else:
        raise ValueError(kind)
    peak = float(np.max(np.abs(sig))) or 1.0
    return sig/peak


def pan(mono: np.ndarray, p: float) -> np.ndarray:
    p = max(-1.0,min(1.0,p))
    ang = (p+1)*math.pi/4
    return np.column_stack([mono*math.cos(ang), mono*math.sin(ang)])


def add(target: np.ndarray, stereo: np.ndarray, start_s: float, gain: float):
    start = int(round(start_s*SAMPLE_RATE))
    if start >= target.shape[0] or start+stereo.shape[0] <= 0:
        return
    src0 = 0
    if start < 0:
        src0 = -start
        start = 0
    end = min(target.shape[0], start + stereo.shape[0]-src0)
    if end > start:
        target[start:end] += stereo[src0:src0+(end-start)]*gain


def add_note(audio, note, start, dur, kind, gain, p, seed, midi, channel=0, program=0):
    tail = 0.75 if kind in ("bowed","choir","glass","brass") else 0.32
    sig = instrument(note, max(0.05,dur+tail), kind, SAMPLE_RATE, seed)
    add(audio, pan(sig,p), start, gain)
    midi.append(MidiEvent(start, dur, note_number(note), int(max(1,min(127,50+gain*150))), channel, program))


def add_hit(audio, kind, start, gain, p, seed, dur=0.7):
    sig = percussive(kind,dur,SAMPLE_RATE,seed)
    add(audio, pan(sig,p), start,gain)


def circular_reverb(audio: np.ndarray, taps=None) -> np.ndarray:
    if taps is None:
        taps=[(0.113,0.12),(0.197,0.095),(0.337,0.07),(0.563,0.05),(0.887,0.032)]
    wet=np.zeros_like(audio)
    for d,g in taps:
        sh=int(d*SAMPLE_RATE)
        wet[:,0]+=np.roll(audio[:,1],sh)*g
        wet[:,1]+=np.roll(audio[:,0],sh)*g
    return audio+wet


def linear_reverb(audio: np.ndarray, taps=None) -> np.ndarray:
    if taps is None:
        taps=[(0.137,0.13),(0.251,0.09),(0.409,0.065),(0.701,0.04),(1.013,0.025)]
    out=audio.copy()
    for d,g in taps:
        sh=int(d*SAMPLE_RATE)
        if sh < len(audio):
            out[sh:]+=audio[:-sh,::-1]*g
    return out


def soft_master(audio: np.ndarray, target_peak_db: float, drive: float=1.1) -> np.ndarray:
    audio=np.tanh(audio*drive)/math.tanh(drive)
    peak=float(np.max(np.abs(audio))) or 1.0
    target=10**(target_peak_db/20.0)
    audio=audio*(target/peak)
    return np.clip(audio,-1.0,1.0)


def write_wav(path: Path, audio: np.ndarray):
    pcm=np.round(np.clip(audio,-1,1)*32767).astype("<i2")
    with wave.open(str(path),"wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SAMPLE_RATE); w.writeframes(pcm.tobytes())


def run_ffmpeg(wav: Path, ogg: Path, mp3: Path):
    if shutil.which("ffmpeg") is None:
        return
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(wav),"-c:a","libvorbis","-q:a","5",str(ogg)],check=True)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(wav),"-c:a","libmp3lame","-b:a","192k",str(mp3)],check=True)


def vlq(n: int) -> bytes:
    buf=[n & 0x7F]
    n >>= 7
    while n:
        buf.append((n & 0x7F)|0x80)
        n >>= 7
    return bytes(reversed(buf))


def write_midi(path: Path, events: list[MidiEvent], tempo_bpm: float):
    timeline=[]
    for ev in events:
        st=int(round(ev.start_q*PPQ))
        en=int(round((ev.start_q+ev.duration_q)*PPQ))
        timeline.append((st,1,ev))
        timeline.append((en,0,ev))
    timeline.sort(key=lambda x:(x[0],x[1]))
    tr=bytearray()
    us=int(round(60_000_000/tempo_bpm))
    tr.extend(b"\x00\xff\x51\x03"+us.to_bytes(3,"big"))
    last=0
    for tick,on,ev in timeline:
        tr.extend(vlq(max(0,tick-last))); last=tick
        status=(0x90 if on else 0x80)|(ev.channel & 0x0F)
        tr.extend(bytes([status, ev.note & 0x7F, ev.velocity if on else 0]))
    tr.extend(b"\x00\xff\x2f\x00")
    head=b"MThd"+struct.pack(">IHHH",6,0,1,PPQ)
    chunk=b"MTrk"+struct.pack(">I",len(tr))+bytes(tr)
    path.write_bytes(head+chunk)


def meter_quarters(score: dict) -> float:
    n,d=score["time_signature"]
    return n*(4.0/d)


def duration_seconds(score: dict) -> float:
    return score["bars"]*meter_quarters(score)*60.0/score["tempo_bpm"]


def q_to_s(q: float, tempo: float) -> float:
    return q*60.0/tempo


def render_mad_wizard(score: dict) -> tuple[np.ndarray,list[MidiEvent]]:
    tempo=score["tempo_bpm"]; qbar=meter_quarters(score); dur=duration_seconds(score)
    audio=np.zeros((int(round(dur*SAMPLE_RATE)),2),dtype=np.float64); midi=[]
    # 7/8, grouped 3+2+2. D Phrygian / chromatic mirrors.
    harmony=[
        ("D2","Eb3","A3"),("D2","Ab2","Eb3"),("C2","D3","F3"),("Bb1","E3","A3"),
        ("D2","F3","A3"),("Eb2","A2","D3"),("C2","Ab2","D3"),("A1","Eb3","G3")
    ]
    motif=[("D4",0.0,0.5),("Eb4",0.5,0.5),("A4",1.0,1.0),("Ab4",2.0,0.5),("F4",2.5,0.5),("D4",3.0,0.5)]
    for bar in range(score["bars"]):
        bq=bar*qbar; bs=q_to_s(bq,tempo)
        chord=harmony[bar%len(harmony)]
        # slow moving low bowed/drone
        for i,n in enumerate(chord):
            add_note(audio,n,bs,q_to_s(qbar*0.96,tempo),"bowed",0.07+0.018*i,-0.45+0.45*i,1000+bar*9+i,midi,1,48)
        # asymmetric pulse and glass punctuation
        for k,off in enumerate([0.0,1.5,2.5]):
            add_note(audio,["D3","Eb3","A3"][(bar+k)%3],q_to_s(bq+off,tempo),q_to_s(0.34,tempo),
                     "celesta",0.095,-0.25+0.25*k,2000+bar*7+k,midi,2,8)
        if bar%2==0:
            trans=0 if (bar//8)%2==0 else -12
            for j,(n,off,du) in enumerate(motif):
                nn_num=note_number(n)+trans
                # convert midi num back by using fixed note list transpositions only
                names={note_number("D4"):"D4",note_number("Eb4"):"Eb4",note_number("A4"):"A4",note_number("Ab4"):"Ab4",note_number("F4"):"F4"}
                if trans==-12:
                    lower={"D4":"D3","Eb4":"Eb3","A4":"A3","Ab4":"Ab3","F4":"F3"}[n]
                    nn=lower
                else:
                    nn=n
                add_note(audio,nn,q_to_s(bq+off,tempo),q_to_s(du*0.92,tempo),
                         "glass" if bar<16 else "flute",0.12,0.20 if j%2 else -0.12,3000+bar*11+j,midi,0,9)
        # whisper swells appear irregularly
        if bar in [3,7,10,14,19,23,26,30]:
            add_hit(audio,"whisper",bs+q_to_s(0.4,tempo),0.026,(-1)**bar*0.45,4000+bar,2.2)
        # low choir enters in middle/final
        if 12 <= bar < 28 and bar%2==0:
            add_note(audio,"D3",bs,q_to_s(qbar*1.9,tempo),"choir",0.055,0.0,5000+bar,midi,3,52)
    audio=circular_reverb(audio,[(0.127,0.15),(0.241,0.10),(0.419,0.072),(0.733,0.048),(1.071,0.028)])
    return soft_master(audio,-1.2,1.05),midi


def render_tavern(score: dict) -> tuple[np.ndarray,list[MidiEvent]]:
    tempo=score["tempo_bpm"]; qbar=meter_quarters(score); dur=duration_seconds(score)
    audio=np.zeros((int(round(dur*SAMPLE_RATE)),2),dtype=np.float64); midi=[]
    prog=[
        (["D2","A2","D3","F#3"],["D4","F#4","A4"]),
        (["G2","D3","G3","B3"],["B3","D4","G4"]),
        (["A2","E3","A3","C#4"],["A3","C#4","E4"]),
        (["D2","A2","D3","F#3"],["F#3","A3","D4"]),
        (["Bm2","F#3","B3","D4"] if False else ["B2","F#3","B3","D4"],["D4","F#4","B4"]),
        (["G2","D3","G3","B3"],["G3","B3","D4"]),
        (["A2","E3","A3","C#4"],["E4","A4","C#5"]),
        (["D2","A2","D3","F#3"],["D4","F#4","A4"]),
    ]
    melody_patterns=[
        [("F#4",0,0.5),("A4",0.5,0.5),("D5",1.0,0.75),("A4",1.75,0.25),("F#4",2.0,0.5),("E4",2.5,0.5)],
        [("G4",0,0.5),("B4",0.5,0.5),("D5",1.0,0.5),("B4",1.5,0.5),("A4",2.0,0.5),("G4",2.5,0.5)],
        [("A4",0,0.5),("C#5",0.5,0.5),("E5",1.0,0.75),("D5",1.75,0.25),("C#5",2.0,0.5),("A4",2.5,0.5)],
        [("F#4",0,0.5),("E4",0.5,0.5),("D4",1.0,1.0),("A4",2.0,0.5),("D5",2.5,0.5)],
    ]
    for bar in range(score["bars"]):
        bq=bar*qbar
        # Lute broken chords in 6/8
        chord,_=prog[bar%len(prog)]
        for step in range(6):
            n=chord[step%len(chord)]
            add_note(audio,n,q_to_s(bq+step*0.5,tempo),q_to_s(0.42,tempo),"lute",0.10,-0.34+0.12*(step%3),
                     7000+bar*17+step,midi,0,24)
        # Fiddle lead most bars
        patt=melody_patterns[bar%4]
        if bar not in [0,8,16,24]:
            for j,(n,off,du) in enumerate(patt):
                add_note(audio,n,q_to_s(bq+off,tempo),q_to_s(du*0.92,tempo),"fiddle",0.10,0.22,
                         8000+bar*13+j,midi,1,40)
        # Flute answer every 4 bars
        if bar%4==3:
            answer=[("A4",0,0.5),("B4",0.5,0.5),("A4",1.0,0.5),("F#4",1.5,0.5),("E4",2.0,0.5),("D4",2.5,0.5)]
            for j,(n,off,du) in enumerate(answer):
                add_note(audio,n,q_to_s(bq+off,tempo),q_to_s(du*0.9,tempo),"flute",0.075,0.48,9000+bar+j,midi,2,73)
        # bass beats 1 and 4
        root=chord[0]
        for off in [0.0,1.5]:
            add_note(audio,root,q_to_s(bq+off,tempo),q_to_s(0.65,tempo),"lute",0.13,-0.08,10000+bar*3+int(off*2),midi,3,32)
        # frame drum: strong 1, light 3/5 and shaker
        for idx,off in enumerate([0,1.0,1.5,2.5]):
            add_hit(audio,"frame",q_to_s(bq+off,tempo),0.095 if idx in [0,2] else 0.045,-0.05,11000+bar*5+idx,0.45)
        for step in range(6):
            add_hit(audio,"shaker",q_to_s(bq+step*0.5,tempo),0.022,0.5,12000+bar*7+step,0.2)
    audio=circular_reverb(audio,[(0.091,0.08),(0.173,0.06),(0.311,0.04),(0.527,0.022)])
    return soft_master(audio,-1.0,1.08),midi


def render_elevator(score: dict) -> tuple[np.ndarray,list[MidiEvent]]:
    tempo=score["tempo_bpm"]; qbar=meter_quarters(score); dur=duration_seconds(score)
    audio=np.zeros((int(round(dur*SAMPLE_RATE)),2),dtype=np.float64); midi=[]
    # One-way descent, gradually darker register and denser dissonance.
    descent_roots=["D2","C#2","C2","B1","Bb1","A1","Ab1","G1","Gb1","F1","E1","Eb1","D1","Db1","C1","B0"]
    motif_frag=[("D4",0.0,0.5),("Eb4",1.0,0.5),("A3",2.25,0.5)]
    for bar in range(score["bars"]):
        bq=bar*qbar; bs=q_to_s(bq,tempo); darkness=bar/(score["bars"]-1)
        rootn=descent_roots[min(bar,len(descent_roots)-1)]
        add_note(audio,rootn,bs,q_to_s(qbar*1.08,tempo),"sub",0.085+0.06*darkness,0.0,13000+bar,midi,0,43)
        # dyad creeps closer to minor-second cluster
        upper=["A2","Ab2","G2","Gb2","F2","E2","Eb2","D2","Db2","C2","B1","Bb1","A1","Ab1","G1","Gb1"][bar]
        add_note(audio,upper,bs+q_to_s(0.25,tempo),q_to_s(qbar*0.9,tempo),"bowed",0.045+0.035*darkness,-0.22,13100+bar,midi,1,48)
        # metallic lift mechanism: 8th/quarter pulses decelerating perceptually by omissions
        pulses=[0.0,1.0,2.0,3.0] if bar<8 else [0.0,2.0] if bar<13 else [0.0]
        for j,off in enumerate(pulses):
            add_hit(audio,"mechanical",q_to_s(bq+off,tempo),0.055+0.035*darkness,0.35 if j%2 else -0.35,13200+bar*6+j,0.45)
        # descending bell every two bars
        if bar%2==0:
            bells=["D5","A4","Eb4","C4","Ab3","F3","D3","Bb2"]
            n=bells[min(bar//2,len(bells)-1)]
            add_note(audio,n,bs+q_to_s(0.45,tempo),q_to_s(1.6,tempo),"glass",0.10,0.18,13300+bar,midi,2,9)
        # wizard motif fragment increasingly low/blurred
        if bar in [1,5,9,12]:
            shift={1:0,5:-12,9:-12,12:-24}[bar]
            name_map={
                0:{"D4":"D4","Eb4":"Eb4","A3":"A3"},
                -12:{"D4":"D3","Eb4":"Eb3","A3":"A2"},
                -24:{"D4":"D2","Eb4":"Eb2","A3":"A1"},
            }[shift]
            for j,(n,off,du) in enumerate(motif_frag):
                add_note(audio,name_map[n],q_to_s(bq+off,tempo),q_to_s(du*1.3,tempo),"glass",0.055,(-0.2+0.2*j),
                         13400+bar*3+j,midi,3,10)
        if bar>=10:
            add_hit(audio,"whisper",bs+q_to_s(0.5,tempo),0.012+0.012*darkness,0.0,13500+bar,2.8)
    audio=linear_reverb(audio,[(0.19,0.12),(0.37,0.08),(0.73,0.052),(1.21,0.028)])
    # cinematic fade-in/out but leave an unresolved low tail
    n=len(audio)
    fade_in=min(n,int(1.5*SAMPLE_RATE)); fade_out=min(n,int(2.2*SAMPLE_RATE))
    audio[:fade_in]*=np.linspace(0,1,fade_in)[:,None]
    audio[-fade_out:]*=np.linspace(1,0.18,fade_out)[:,None]
    return soft_master(audio,-1.4,1.0),midi


def render_act01(score: dict) -> tuple[np.ndarray,list[MidiEvent]]:
    tempo=score["tempo_bpm"]; qbar=meter_quarters(score); dur=duration_seconds(score)
    audio=np.zeros((int(round(dur*SAMPLE_RATE)),2),dtype=np.float64); midi=[]
    # Narrative arc: disbelief -> fracture -> revelation -> unresolved collapse.
    chords=[
        ["D2","A2","D3","F3"],["Bb1","F2","Bb2","D3"],["C2","G2","C3","E3"],["A1","E2","A2","C#3"],
        ["D2","Eb3","A3","C4"],["C2","Ab2","D3","F3"],["Bb1","E2","A2","D3"],["A1","Eb2","G2","C#3"]
    ]
    wizard_motif=[("D4",0,0.5),("Eb4",0.5,0.5),("A4",1.0,1.0),("Ab4",2.0,0.5),("F4",2.5,0.5),("D4",3.0,0.75)]
    for bar in range(score["bars"]):
        bq=bar*qbar; bs=q_to_s(bq,tempo); phase=bar/score["bars"]
        chord=chords[(bar//2)%len(chords)]
        # strings / choir bed
        for i,n in enumerate(chord):
            add_note(audio,n,bs,q_to_s(qbar*0.98,tempo),"bowed",0.055+0.025*phase,-0.55+0.36*i,14000+bar*9+i,midi,0,48)
        if bar>=8:
            add_note(audio,chord[1],bs,q_to_s(qbar*0.98,tempo),"choir",0.035+0.045*phase,0.0,14100+bar,midi,1,52)
        # familiar clean phrase early, corrupted motif later
        if bar in [2,6]:
            hero=[("D4",0,1.0),("A3",1.0,0.5),("C4",1.5,0.5),("Eb4",2.0,0.5),("D4",2.5,1.0)]
            for j,(n,off,du) in enumerate(hero):
                add_note(audio,n,q_to_s(bq+off,tempo),q_to_s(du,tempo),"flute",0.10,0.18,14200+bar*7+j,midi,2,73)
        if bar in [10,14,18,22]:
            for j,(n,off,du) in enumerate(wizard_motif):
                add_note(audio,n,q_to_s(bq+off,tempo),q_to_s(du*0.9,tempo),
                         "glass" if bar<18 else "brass",0.09+0.025*(bar>=18),0.08 if j%2 else -0.18,
                         14300+bar*8+j,midi,3,61)
        # percussion emerges after fracture
        if bar>=9:
            for j,off in enumerate([0.0,2.0]):
                add_hit(audio,"war",q_to_s(bq+off,tempo),0.065+0.065*phase,-0.1,14400+bar*3+j,0.9)
        if bar>=16:
            for off in [1.0,3.0]:
                add_hit(audio,"mechanical",q_to_s(bq+off,tempo),0.035+0.03*phase,0.35,14500+bar*3+int(off),0.35)
        # high unresolved glass 'alarm' in last third
        if bar>=18 and bar%2==0:
            add_note(audio,["Eb5","A5","Ab5","D6"][(bar//2)%4],bs+q_to_s(0.75,tempo),q_to_s(1.5,tempo),
                     "glass",0.08,0.4,14600+bar,midi,4,9)
    audio=linear_reverb(audio,[(0.12,0.11),(0.29,0.08),(0.51,0.055),(0.83,0.037),(1.31,0.021)])
    # Last 3 seconds withdraw low frequencies but do not cadence.
    fade=int(2.6*SAMPLE_RATE)
    audio[-fade:]*=np.linspace(1.0,0.12,fade)[:,None]
    return soft_master(audio,-1.1,1.13),midi


RENDERERS={
    "mad_wizard_labyrinthine":render_mad_wizard,
    "tavern_folk":render_tavern,
    "elevator_dark_descent":render_elevator,
    "act01_failure_finale":render_act01,
}


def pcm_signature(audio: np.ndarray, shift_bits: int=8) -> str:
    pcm=np.round(np.clip(audio,-1,1)*32767).astype(np.int16)
    reduced=(pcm.astype(np.int32)>>shift_bits).astype(np.int16)
    return hashlib.sha256(reduced.tobytes()).hexdigest()


def metrics(audio: np.ndarray, loop: bool) -> dict:
    peak=float(np.max(np.abs(audio))) or 1e-12
    rms=float(np.sqrt(np.mean(np.square(audio)))) or 1e-12
    if loop:
        value=float(np.max(np.abs(audio[0]-audio[-1])))
        slope=float(np.max(np.abs((audio[1]-audio[0])-(audio[-1]-audio[-2]))))
    else:
        value=0.0; slope=0.0
    return {
        "peak_dbfs": round(20*math.log10(peak),4),
        "rms_dbfs": round(20*math.log10(rms),4),
        "boundary_value_delta": round(value,8),
        "boundary_slope_delta": round(slope,8),
    }


def seam_lock(audio: np.ndarray) -> np.ndarray:
    # Short smooth correction to exact periodic value and slope without changing arrangement.
    n=len(audio); window=min(n//4,int(0.7*SAMPLE_RATE))
    if window < 4: return audio
    out=audio.copy()
    target0=out[0].copy()
    target_slope=out[1]-out[0]
    end0=out[-1].copy()
    end_slope=out[-1]-out[-2]
    dv=target0-end0
    ds=target_slope-end_slope
    x=np.linspace(0,1,window)
    smooth=x*x*(3-2*x)
    # correction grows near end, plus slope correction concentrated final samples
    out[-window:]+=smooth[:,None]*dv[None,:]
    out[-2]=target0-target_slope
    out[-1]=target0
    return out


def render(score_path: Path, output_dir: Path):
    score=json.loads(score_path.read_text(encoding="utf-8"))
    renderer=RENDERERS[score["render_profile"]]
    audio,midi=renderer(score)
    if score.get("loop",False):
        audio=seam_lock(audio)
    output_dir.mkdir(parents=True,exist_ok=True)
    cid=score["composition_id"]
    wav=output_dir/f"{cid}_master.wav"
    ogg=output_dir/f"{cid}_master.ogg"
    mp3=output_dir/f"{cid}_preview.mp3"
    mid=output_dir/f"{cid}.mid"
    write_wav(wav,audio)
    run_ffmpeg(wav,ogg,mp3)
    # Midi times are stored as seconds by add_note; convert to quarter notes now.
    sec_per_q=60.0/score["tempo_bpm"]
    midi_q=[MidiEvent(e.start_q/sec_per_q,e.duration_q/sec_per_q,e.note,e.velocity,e.channel,e.program) for e in midi]
    write_midi(mid,midi_q,score["tempo_bpm"])
    m=metrics(audio,bool(score.get("loop",False)))
    manifest={
        "composition_id":cid,
        "score_sha256":hashlib.sha256(score_path.read_bytes()).hexdigest(),
        "renderer":"procedural_narrative_music_renderer_v01",
        "arrangement_revision":int(score.get("arrangement_revision",1)),
        "numpy_version":np.__version__,
        "sample_rate":SAMPLE_RATE,
        "channels":2,
        "duration_seconds":round(len(audio)/SAMPLE_RATE,6),
        "tempo_bpm":score["tempo_bpm"],
        "time_signature":score["time_signature"],
        "bars":score["bars"],
        "loop":bool(score.get("loop",False)),
        "pcm_signature_shift_bits":8,
        "pcm_signature_sha256":pcm_signature(audio,8),
        **m,
        "wav_sha256":hashlib.sha256(wav.read_bytes()).hexdigest(),
        "midi_sha256":hashlib.sha256(mid.read_bytes()).hexdigest(),
    }
    if ogg.exists():
        manifest["ogg_sha256"]=hashlib.sha256(ogg.read_bytes()).hexdigest()
        manifest["ogg_size_bytes"]=ogg.stat().st_size
    if mp3.exists():
        manifest["mp3_sha256"]=hashlib.sha256(mp3.read_bytes()).hexdigest()
    (output_dir/f"{cid}_master_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--score",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    manifest=render(args.score,args.output)
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
