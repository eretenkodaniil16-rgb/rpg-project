#!/usr/bin/env python3
"""V4.9.5 experiment: an uneven, legible seven-petal-to-swallow release.

V4.9.3/V4.9.4 shape-key and ink-color tracks were identical for all seven
650-vertex carriers. That makes the flock read as seven synchronized black
crosses. Stagger only the intermediate deformation and pigment-conversion
keys by a few frames per bird, keeping the original geometry at the exact
132/133 handoff and leaving the actual 3D swallow-rig movement unchanged.

This artistic pass is deliberately isolated and reversible. It does NOT
retime source petals, the other 21 dissolve materials, flight positions,
camera, visibility swap, master scene, or geometry topology.
"""
import math
import bpy

# Natural irregular rhythm, not left-to-right serial staggering. All offsets
# fit between the preserved 133 handoff and the fixed 182 carrier visibility.
OFFSET=(-4,2,0,4,-2,3,-1)
SHAPE_EVENTS=((143,.16),(153,.64),(165,1.0))
INK_EVENTS=((141,.06),(151,.34),(164,.86),(172,1.0))

def replace_keys(socket,events,delta):
    for frame,value in events:
        if not socket.keyframe_delete(data_path="default_value",frame=frame):
            raise RuntimeError("Original ink keyframe missing "+str(frame))
    for frame,value in events:
        socket.default_value=value
        if not socket.keyframe_insert(data_path="default_value",frame=frame+delta):
            raise RuntimeError("Failed ink material retiming "+str(frame+delta))

def retime_shape(key,delta):
    for frame,value in SHAPE_EVENTS:
        if not key.keyframe_delete(data_path="value",frame=frame):
            raise RuntimeError("Original wing shape keyframe missing "+str(frame))
    for frame,value in SHAPE_EVENTS:
        key.value=value
        if not key.keyframe_insert(data_path="value",frame=frame+delta):
            raise RuntimeError("Failed wing shape keyframe retiming "+str(frame+delta))

def build():
    scene=bpy.context.scene
    report=[]
    for i,delay in enumerate(OFFSET):
        carrier=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%i)
        if carrier is None or len(carrier.data.vertices)!=650:
            raise RuntimeError("Morph carrier topology regression "+str(i))
        keys=carrier.data.shape_keys
        if keys is None or "Ink_Wing" not in keys.key_blocks:
            raise RuntimeError("Missing animated wing destination "+str(i))
        mat=carrier.data.materials[0] if carrier.data.materials else None
        if mat is None or not mat.use_nodes:
            raise RuntimeError("Missing V4.9 pigment material "+str(i))
        pigment=mat.node_tree.nodes.get("V49_Lotus_To_Ink_%02d"%i)
        if pigment is None or pigment.type!="MIX_RGB":
            raise RuntimeError("Unrecognized independent ink conversion "+str(i))
        retime_shape(keys.key_blocks["Ink_Wing"],delay)
        replace_keys(pigment.inputs[0],INK_EVENTS,delay)
        report.append({"bird":i,"shape_delay_frames":delay,
                       "wing_complete_frame":165+delay,
                       "pigment_complete_frame":172+delay})

    # The original petal and each carrier have identical evaluated geometry
    # on 132 and stay watercolor-colored on 133, before ANY new morph key.
    for f in (132,133):
        scene.frame_set(f)
        for i in range(7):
            ob=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            ink=ob.data.materials[0].node_tree.nodes[
                "V49_Lotus_To_Ink_%02d"%i].inputs[0]
            if abs(ob.data.shape_keys.key_blocks["Ink_Wing"].value)>1e-6:
                raise RuntimeError("Morph begins before handoff frame")
            if abs(ink.default_value)>1e-6:
                raise RuntimeError("Ink appears before handoff frame")
    scene.frame_set(153)
    levels=[bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            .data.shape_keys.key_blocks["Ink_Wing"].value for i in range(7)]
    if max(levels)-min(levels)<.08:
        raise RuntimeError("Failed to diversify seven synchronized morphs")
    scene.frame_set(180)
    if any(bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
           .data.shape_keys.key_blocks["Ink_Wing"].value<.99 for i in range(7)):
        raise RuntimeError("A swallow still unformed at transition end")
    scene.frame_set(1)
    result={"independent_phase_tracks":report,
            "morph_spread_at_153":round(max(levels)-min(levels),4),
            "unchanged_carrier_topology":650,
            "preserved_original_24fps_film":(scene.frame_end,scene.render.fps)==(288,24)}
    if not result["preserved_original_24fps_film"]:
        raise RuntimeError("Master timeline modified")
    print("V495_ASYNCHRONOUS_SWALLOW_QA_PASS",result,flush=True)
    return result
