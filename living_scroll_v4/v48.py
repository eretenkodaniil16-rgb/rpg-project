#!/usr/bin/env python3
"""V4.8: geometric petal-to-flight continuity on the proven V4.7 scene.

Probe: construct and assert seven morphing petal meshes, no render.
Smoke: six full-frame stills + 24 consecutive true Blender frames at 144x256.
Full: render all 288 frames (only for specifically invoked production runs).
"""
import argparse
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v47
import v48_morph

OUT=HERE/"renders_v48"
STILLS=OUT/"stills"
CLIP=OUT/"clip"
STILLS.mkdir(parents=True,exist_ok=True)
CLIP.mkdir(parents=True,exist_ok=True)

def frame(scene,n,path):
    scene.frame_set(n)
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)

def build(mode):
    v47.main(probe=True)
    metrics=v48_morph.build()
    scene=bpy.context.scene
    if scene.frame_end!=288 or scene.render.fps!=24:
        raise RuntimeError("V4.8 changed the original 12-second timeline")
    scene.frame_set(1)
    scene.render.resolution_percentage=100
    scene.render.resolution_x=360 if mode=="smoke" else 720
    scene.render.resolution_y=640 if mode=="smoke" else 1280
    bpy.ops.file.pack_all()
    path=HERE/"living_scroll_v48.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print("V48_SCENE_BUILD_OK",metrics,path,flush=True)
    if mode=="probe":return
    if mode=="smoke":
        for f in (132,140,153,165,175,185):
            frame(scene,f,STILLS/("smoke_%03d"%f))
            print("V48_STILL_OK",f,flush=True)
        scene.render.resolution_x=144
        scene.render.resolution_y=256
        for f in range(148,172):
            frame(scene,f,CLIP/("clip_%04d"%f))
            if (f-148)%6==0:print("V48_CONTINUOUS_PROGRESS",f,flush=True)
        print("V48_24_CONTIGUOUS_FRAMES_OK",flush=True)
    else:
        for f in range(1,289):
            frame(scene,f,OUT/("frame_%04d"%f))
            if f%24==0:print("V48_FULL_FRAME",f,flush=True)
    scene.render.filepath="//"
    print("V48_ALL_RENDERING_COMPLETE",flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--probe",action="store_true")
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--full",action="store_true")
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opts=parser.parse_args(argv)
    if sum((opts.probe,opts.smoke,opts.full))!=1:
        parser.error("Choose exactly one mode")
    build("probe" if opts.probe else "smoke" if opts.smoke else "full")
