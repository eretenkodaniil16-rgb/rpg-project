#!/usr/bin/env python3
"""Fast, deterministic 3D continuity acceptance check for The Living Scroll V4.9.

This QA probes the real animated 650-vertex petal meshes and renders two
genuine adjacent frames. It is deliberately separate from the expensive
56-frame artistic smoke run.
"""
import json
import math
from pathlib import Path
import sys

import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v49

OUT=HERE/"fast_qa_v49"
OUT.mkdir(parents=True,exist_ok=True)
PETALS=(0,2,4,6,8,10,12)

def world_vertices(obj):
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    try:
        matrix=evaluated.matrix_world
        return [matrix@v.co for v in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()

def root_mean_squared_distance(a,b):
    if len(a)!=650 or len(b)!=650:
        raise RuntimeError("Unexpected continuity topology")
    return math.sqrt(sum((v-w).length_squared for v,w in zip(a,b))/650)

def render(scene,frame):
    scene.frame_set(frame)
    scene.render.resolution_percentage=100
    scene.render.resolution_x=144
    scene.render.resolution_y=256
    scene.render.filepath=str(OUT/("handoff_%03d"%frame))
    bpy.ops.render.render(write_still=True)

def render_detail(scene,frame):
    """Film-composition checkpoint in native smoke preview resolution."""
    scene.frame_set(frame)
    scene.render.resolution_percentage=100
    scene.render.resolution_x=360
    scene.render.resolution_y=640
    scene.render.filepath=str(OUT/("detail_%03d"%frame))
    bpy.ops.render.render(write_still=True)

def main():
    v49.build("probe")
    scene=bpy.context.scene
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("12-second animation timeline regression")
    distances={}
    checks=[]
    scene.frame_set(132)
    for ordinal,petal_index in enumerate(PETALS):
        source=bpy.data.objects["V44_LOTUS_R0_P%02d"%petal_index]
        carrier=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%ordinal]
        sv=world_vertices(source)
        cv=world_vertices(carrier)
        delta=root_mean_squared_distance(sv,cv)
        # Actual evaluated-world positions, not a proxy from object transforms.
        if delta>0.002:
            raise RuntimeError("Geometry jumps at morph origin: ordinal=%d RMS=%f"%(ordinal,delta))
        distances[str(ordinal)]=round(delta,7)
        if source.hide_render or not carrier.hide_render:
            raise RuntimeError("Source petal / carrier overlap at 132")
        checks.append(carrier.name)
    scene.frame_set(133)
    for ordinal,petal_index in enumerate(PETALS):
        source=bpy.data.objects["V44_LOTUS_R0_P%02d"%petal_index]
        carrier=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%ordinal]
        if not source.hide_render or carrier.hide_render:
            raise RuntimeError("Handoff visibility state invalid at 133")
        if not carrier.data.materials[0].name.startswith("V49_Continuous_Wash_To_Ink_"):
            raise RuntimeError("Non-matching pigment on continuous carrier")
    scene.frame_set(155)
    for i in range(7):
        if max(bpy.data.objects["BIRD_%02d_RIG"%i].scale)>.025:
            raise RuntimeError("Flock appears independently before carrier morph")
    scene.frame_set(185)
    for i in range(7):
        if max(bpy.data.objects["BIRD_%02d_RIG"%i].scale)<.1:
            raise RuntimeError("Bird absent at flight reveal")
    report={"scene":"V4.9","real_meshes_checked":len(checks),
            "world_vertex_RMS_at_frame_132":distances,
            "source_handoff":132,"carrier_handoff":133,
            "motion_frames_checked":[132,133,155,185],
            "verified_timeline_frames":288,"verified_fps":24}
    (OUT/"geometry_report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("V49_GEOMETRIC_CONTINUITY_QA_PASS",report,flush=True)
    # Sample the actual transformation, not only the first handoff cut:
    # each genuine Blender still is independently evaluated at its timeline
    # frame; intermediate morph poses remain editable in the saved .blend.
    storyboard=[]
    for f in (132,133,141,153,165,175,185):
        scene.frame_set(f)
        carrier_ink=0
        birds_active=0
        wing_keys=[]
        for i in range(7):
            carrier=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            bird=bpy.data.objects["BIRD_%02d_RIG"%i]
            if not carrier.hide_render and max(carrier.scale)>.02:
                carrier_ink+=1
            if max(bird.scale)>.04:
                birds_active+=1
            wing_keys.append(float(carrier.data.shape_keys.key_blocks["Ink_Wing"].value))
        storyboard.append({"frame":f,"visible_carrier_count":carrier_ink,
                           "scaled_bird_rigs":birds_active,
                           "mean_bird_shape_key":round(sum(wing_keys)/7,4)})
        render(scene,f)
        print("V49_REAL_STORYBOARD_FRAME",f,flush=True)
    (OUT/"storyboard_report.json").write_text(
        json.dumps(storyboard,indent=2)+"\n",encoding="utf-8")
    for f in (153,165,175):
        render_detail(scene,f)
        print("V495_CINEMATIC_DETAIL_FRAME",f,flush=True)
    print("V49_FAST_QA_DONE",flush=True)

if __name__=="__main__":
    main()
