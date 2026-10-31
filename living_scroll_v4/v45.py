#!/usr/bin/env python3
"""V4.5: hero swallow models in the existing V4.4 Hybrid Realism shot.

Blender 5.2, 12 seconds, 24fps. Six smoke frames: 155/175/205/235
plus two targeted single-bird close-ups, 175/205. V4.4 files are untouched.
"""
import argparse
from pathlib import Path
import sys
import bpy
import v44
import v45_birds as birds

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"renders_v45"
OUT.mkdir(exist_ok=True,parents=True)

def build(probe=False,smoke=False,full=False):
    if sum((probe,smoke,full))!=1:
        raise ValueError("Choose probe, smoke or full")
    # Reuse validated real V4.4 lotus + GP/ink-wash/pavilions before birds.
    v44.build(probe=True)
    result=birds.build()
    if result["birds"]!=7 or result["flight_feathers"]!=280:
        raise RuntimeError("Hero bird contracts not met")
    scene=bpy.context.scene
    if scene.frame_end!=288 or scene.render.fps!=24:
        raise RuntimeError("Animation duration regression")
    # Deliberately keep smoke 360×640 to compare with existing iterations.
    scene.render.resolution_x=360 if smoke else 720
    scene.render.resolution_y=640 if smoke else 1280
    scene.render.resolution_percentage=100
    original=scene.camera
    if original is None:raise RuntimeError("No camera")
    # A dedicated close-up camera in the saved editable .blend. Does not steal
    # the main shot's animated ortho scale or its keyframes.
    macro=original.copy()
    macro.data=original.data.copy()
    scene.collection.objects.link(macro)
    macro.name="V45_SWALLOW_QA_CLOSEUP_CAMERA"
    macro.animation_data_clear()
    macro.data.animation_data_clear()
    macro.data.type="ORTHO"
    macro.data.ortho_scale=3.45
    macro.location=(0,-13,.30)
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    dest=ROOT/"living_scroll_v45.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dest))
    print("V45_BUILD_QA_PASS",result,"saved",dest)
    if probe:return dest
    for f in ((155,175,205,235) if smoke else range(1,289)):
        scene.frame_set(f)
        scene.camera=original
        scene.render.filepath=str(OUT/(("smoke_%03d"%f) if smoke else ("frame_%04d"%f)))
        bpy.ops.render.render(write_still=True)
    if smoke:
        for f in (175,205):
            scene.frame_set(f)
            hero=bpy.data.objects["BIRD_03_RIG"]
            bpy.context.view_layer.update()
            pos=hero.matrix_world.translation
            macro.location=(pos.x,-13,pos.z)
            macro.data.ortho_scale=3.45
            scene.camera=macro
            scene.render.filepath=str(OUT/("detail_%03d"%f))
            bpy.ops.render.render(write_still=True)
        scene.camera=original
    print("V45_RENDER_COMPLETE",dest)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--smoke",action="store_true")
    parser.add_argument("--full",action="store_true")
    parser.add_argument("--probe",action="store_true")
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opt=parser.parse_args(a)
    build(probe=opt.probe,smoke=opt.smoke,full=opt.full)
