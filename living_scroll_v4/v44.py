#!/usr/bin/env python3
"""Living Scroll V4.4.1: hero lotus realism within the ink-wash film.
Reuses tested V4.3 atmosphere, camera, pavilion, birds, GPv3. Replaces only
the V4 petal render with an anatomically informed 28-petal model.
"""
import argparse
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v43
import v44_lotus as lotus

OUT=HERE/"renders_v44"
OUT.mkdir(parents=True,exist_ok=True)

def hide_previous_flower():
    old=bpy.data.collections.get("V4_03_LOTUS")
    if old is None:raise RuntimeError("V4 lotus collection not found")
    hidden=0
    for ob in old.objects:
        # Keep controller with its tested keyframes, hide only rendered meshes/lines.
        if ob.type in {"MESH","CURVE"}:
            ob.hide_render=True
            hidden+=1
    if hidden<50:raise RuntimeError("V4 inherited petal kit missing")
    return hidden

def build(probe=False,smoke=False,full=False):
    # Use tested V4.3 procedural scene but defer rendering until after replacement.
    v43.v42.v4.build(False,False)
    v43.v42.spread_flock()
    v43.v42.scatter_to_birds()
    v43.v42.add_sky_ink_particles()
    v43.ink_washed_petals()
    v43.shape_key_petals()
    v43.subtle_bird_feathering()
    gp,num=v43.make_grease_pencil()
    old=hide_previous_flower()
    parent=bpy.data.objects.get("LOTUS_HERO_CTRL")
    if parent is None:raise RuntimeError("Existing lotus animation controller missing")
    details=lotus.build(parent)
    if details["petals"]!=28 or details["stamens"]!=84:
        raise RuntimeError("V4.4 lotus topology contract broken")
    # Keep the blossom's physical disassembly coordinated with the V4.3 ink flock.
    hero=bpy.data.objects[details["root"]]
    for fr,sz in ((1,1.0),(120,1.0),(138,.99),(149,.85),
                  (155,.69),(164,.43),(174,.12),(183,.001),(288,.001)):
        hero.scale=(sz,sz,sz)
        hero.keyframe_insert(data_path="scale",frame=fr)
    new_petals=[o for o in bpy.data.objects if o.name.startswith("V44_LOTUS_R") and o.type=="MESH"]
    if len(new_petals)!=28:
        raise RuntimeError("Expected 28 distinct editable V4.4 petals")
    for obj in new_petals:
        blocks=obj.data.shape_keys
        if not blocks:
            raise RuntimeError("V4.4 mesh missing deformation shapes: "+obj.name)
        if any(n not in blocks.key_blocks for n in ("BudFold","WindFlex","InkDeparture")):
            raise RuntimeError("Missing animated shape on "+obj.name)
    scene=bpy.context.scene
    scene.render.resolution_x=360 if smoke else 720
    scene.render.resolution_y=640 if smoke else 1280
    scene.render.resolution_percentage=100
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    file=HERE/"living_scroll_v44.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
    print("V44_LOTUS_QA_PASS",details,"old hidden",old,"GP frames",num)
    if probe:
        return
    if not (smoke or full):
        raise RuntimeError("Specify --probe, --smoke or --full")
    frames=(48,88,115,155) if smoke else range(1,289)
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath=str(OUT/(("smoke_%03d"%f) if smoke else ("frame_%04d"%f)))
        bpy.ops.render.render(write_still=True)
    if smoke:
        # A separate camera datablock avoids animated ortho_scale overriding the
        # artistic QA zoom during scene evaluation.
        original_camera=scene.camera
        detail_camera=original_camera.copy()
        detail_camera.data=original_camera.data.copy()
        scene.collection.objects.link(detail_camera)
        detail_camera.name="QA_Closeup_IndependentCamera"
        detail_camera.animation_data_clear()
        detail_camera.data.animation_data_clear()
        detail_camera.data.ortho_scale=4.15
        detail_camera.location=(0,-13,0)
        scene.camera=detail_camera
        for f in (88,115):
            scene.frame_set(f)
            detail_camera.data.ortho_scale=4.15
            scene.render.filepath=str(OUT/("detail_%03d"%f))
            bpy.ops.render.render(write_still=True)
        scene.camera=original_camera
        bpy.data.objects.remove(detail_camera,do_unlink=True)
    print("V44_RENDER_COMPLETE",file)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true")
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--full",action="store_true")
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    o=p.parse_args(args)
    if sum((o.probe,o.smoke,o.full))!=1:p.error("Choose one render mode")
    build(o.probe,o.smoke,o.full)
