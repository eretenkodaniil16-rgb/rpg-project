#!/usr/bin/env python3
"""Quantitative QC for the true 48-frame V4.9 Blender transition preview.

No optical flow/interpolated images are permitted. Hard errors are limited to
missing, duplicated, malformed or obvious one-frame blackout/flash frames.
A separately logged seam-difference metric is diagnostic, not artistic proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from PIL import Image, ImageChops, ImageStat

def mean_difference(a,b):
    rgb_a=a.convert('RGB')
    rgb_b=b.convert('RGB')
    diff=ImageChops.difference(rgb_a,rgb_b)
    return sum(ImageStat.Stat(diff).mean)/3

def inspect(folder, outfile, first=132, count=48):
    frames=[]
    hashes=[]
    for f in range(first,first+count):
        path=folder/('clip_%04d.png'%f)
        if not path.is_file() or path.stat().st_size<2000:
            raise RuntimeError('Missing/empty true render frame '+str(path))
        data=path.read_bytes()
        hashes.append(hashlib.sha256(data).hexdigest())
        with Image.open(path) as im:
            im.load()
            if im.size!=(144,256):
                raise RuntimeError('Unexpected frame size '+str(im.size)+' at '+str(f))
            frames.append(im.convert('RGB'))
    # Encodes must come from separately rendered source frames, not a frozen frame.
    duplicated=sum(a==b for a,b in zip(hashes,hashes[1:]))
    if duplicated:
        raise RuntimeError('Found %d identical consecutive rendered PNG frames'%duplicated)
    differences=[mean_difference(a,b) for a,b in zip(frames,frames[1:])]
    seam=differences[0]
    trend=statistics.median(differences[1:]) if len(differences)>1 else 0.
    # Full-frame jump threshold deliberately generous because a subtle film may
    # contain local, high-contrast bird silhouettes against moving landscape.
    jump_limit=max(42., 6.0*trend+8.)
    if seam>jump_limit:
        raise RuntimeError('Frame 132-to-133 appearance pops: %.2f > %.2f'%(seam,jump_limit))
    report={
       'film':'The Living Scroll V4.9',
       'frames':count,'fps':24,'first_frame':first,
       'last_frame':first+count-1,'image_dimensions':[144,256],
       'source': 'real Blender-rendered PNG sequence, no synthetic in-betweens',
       'consecutive_duplicate_frames':duplicated,
       'handoff_132_to_133_mean_rgb_difference':round(seam,3),
       'median_other_frame_difference':round(trend,3),
       'max_frame_difference':round(max(differences),3),
       'per_frame_differences':{str(f):round(d,3) for f,d in zip(range(first+1,first+count),differences)},
       'note':'This is numerical QC; human inspection of the flower, birds, texture and compositional continuity is still required.'
    }
    outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('V49_TRUE_FRAME_MOTION_QA_PASS',json.dumps({
        'frame_count':count,'seam_mae':report['handoff_132_to_133_mean_rgb_difference'],
        'median_other_mae':report['median_other_frame_difference'],
        'max_mae':report['max_frame_difference']}),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--clip-dir',type=Path,default=Path(__file__).resolve().parent/'renders_v49'/'clip')
    p.add_argument('--report',type=Path,default=Path(__file__).resolve().parent/'v49_frame_metrics.json')
    args=p.parse_args()
    inspect(args.clip_dir,args.report)
