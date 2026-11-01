#!/usr/bin/env python3
"""Render one disjoint, real Blender-5.2 chunk of The Living Scroll V4.12.

Twelve chunks of 24 individual frames reconstruct the original 288-frame,
24-fps edit exactly. Every chunk loads/builds the SAME immutable scene and
samples native absolute timeline frames, with no post-hoc interpolation or
artificial video frames. Validated master is available in every chunk.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v49

FPS=24
FRAMES=288
CHUNK=24
COUNT=12
WIDTH=144
HEIGHT=256
OUT=HERE/"full_v412"
FRAMES_DIR=OUT/"frames"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--chunk",type=int,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    n=args.chunk
    if not 0 <= n < COUNT:
        raise RuntimeError("Chunk must be in 0..11")
    first=n*CHUNK+1
    last=first+CHUNK-1
    FRAMES_DIR.mkdir(parents=True,exist_ok=True)

    v49.build("probe")
    scene=bpy.context.scene
    if (scene.frame_start,scene.frame_end,scene.render.fps)!=(1,FRAMES,FPS):
        raise RuntimeError("Original master 288f at 24fps changed")
    scene.render.resolution_percentage=100
    scene.render.resolution_x=WIDTH
    scene.render.resolution_y=HEIGHT
    scene.render.image_settings.file_format="PNG"
    info=[]
    for frame in range(first,last+1):
        scene.frame_set(frame)
        file=FRAMES_DIR/("frame_%04d.png"%frame)
        scene.render.filepath=str(file)
        bpy.ops.render.render(write_still=True)
        if not file.exists() or file.stat().st_size<2000:
            raise RuntimeError("Blender failed to render frame "+str(frame))
        info.append({"frame":frame,"sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
                     "bytes":file.stat().st_size})
        print("V412_FULL_PROOF_TRUE_FRAME",frame,flush=True)
    result={"version":"V4.12.0","chunk":n,"first":first,"last":last,
            "original_master_first":1,"original_master_last":FRAMES,
            "fps":FPS,"resolution":[WIDTH,HEIGHT],
            "true_native_blender_frames":len(info),"interpolation_used":False,
            "frames":info}
    (OUT/("part_%02d.json"%n)).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("V412_FULL_24FPS_CHUNK_PASS",n,first,last,flush=True)

if __name__=="__main__":
    main()
