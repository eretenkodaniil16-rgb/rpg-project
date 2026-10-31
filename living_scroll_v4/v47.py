#!/usr/bin/env python3
"""Living Scroll V4.7: verified scene + clean GP morph + preview movie."""
import argparse
import sys
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v46
import v47_morph

RENDERS=HERE/"renders_v47"
STILLS=RENDERS/"stills"
CLIP=RENDERS/"clip"
STILLS.mkdir(parents=True,exist_ok=True)
CLIP.mkdir(parents=True,exist_ok=True)

def render_frame(scene,frame,path):
    scene.frame_set(frame)
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)

def main(probe=False,smoke=False,full=False):
    if sum((probe,smoke,full))!=1:
        raise ValueError("Choose exactly one mode")
    v46.build(probe=True)
    q=v47_morph.build()
    scene=bpy.context.scene
    if scene.frame_end!=288 or scene.render.fps!=24:
        raise RuntimeError("288f/24fps film contract changed")
    scene.frame_set(1)
    scene.render.resolution_x=360 if smoke else 720
    scene.render.resolution_y=640 if smoke else 1280
    scene.render.resolution_percentage=100
    bpy.ops.file.pack_all()
    path=HERE/"living_scroll_v47.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print("V47_SCENE_QA_PASS",q,path,flush=True)
    if probe:return
    if smoke:
        frames=(145,155,165,175,185,205)
        for frame in frames:
            render_frame(scene,frame,STILLS/("smoke_%03d"%frame))
            print("V47_SMOKE_FRAME",frame,flush=True)
        # All 48 frames are rendered, no synthetic or optical-flow frames:
        # a true 24fps 2-second sample of the morph for motion QA.
        scene.render.resolution_x=180
        scene.render.resolution_y=320
        for frame in range(148,196):
            render_frame(scene,frame,CLIP/("clip_%04d"%frame))
            if frame%8==0:
                print("V47_CONTINUOUS_CLIP",frame,flush=True)
        print("V47_SMOKE_AND_48_FRAME_CLIP_OK",flush=True)
    else:
        for frame in range(1,289):
            render_frame(scene,frame,RENDERS/("frame_%04d"%frame))
            if frame%24==0:print("V47_FULL_PROGRESS",frame,flush=True)
    scene.render.filepath="//"
    print("V47_RENDER_COMPLETE",path,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true")
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--full",action="store_true")
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    o=p.parse_args(a)
    main(probe=o.probe,smoke=o.smoke,full=o.full)
