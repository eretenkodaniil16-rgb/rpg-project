#!/usr/bin/env python3
"""V4.6 final-film bird LOD composition.

Build from proven V4.5.2 Blender scene, retain detailed hidden bird library,
replace only the on-screen seven birds. Four timeline comparison frames.
"""
import argparse
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v45
import v46_birds as lod

OUTPUT=HERE/"renders_v46"
OUTPUT.mkdir(parents=True,exist_ok=True)

def build(probe=False,smoke=False,full=False):
    if sum((probe,smoke,full))!=1:
        raise RuntimeError("Specify exactly one of --probe/--smoke/--full")
    v45.build(probe=True)
    metrics=lod.build()
    scene=bpy.context.scene
    scene.render.resolution_x=360 if smoke else 720
    scene.render.resolution_y=640 if smoke else 1280
    if scene.frame_end!=288 or scene.render.fps!=24:
        raise RuntimeError("Timeline regression")
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    result=HERE/"living_scroll_v46.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(result))
    print("V46_COMPOSITION_QA_PASS",metrics,"file",result)
    if probe:return
    frames=[155,175,205,235] if smoke else range(1,289)
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath=str(OUTPUT/(("smoke_%03d"%f) if smoke else ("frame_%04d"%f)))
        bpy.ops.render.render(write_still=True)
    print("V46_SMOKE_OK",len(frames),result)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true")
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--full",action="store_true")
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    a=p.parse_args(args)
    build(probe=a.probe,smoke=a.smoke,full=a.full)
