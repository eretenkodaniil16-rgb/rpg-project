#!/usr/bin/env python3
"""The Living Scroll V4.10.0: preserve rose watercolor on detached petals.

Observed in actual 360x640 Blender frames: V4.9.9 successfully separates
seven 650-vertex lotus laminae in 3D but prematurely dyes them gray. A gray
detached scrap reads as an artifact, not a naturally transforming pink petal.

Only the existing seven individual Blender material animation tracks change:
  (1) defer original pink-to-ink pigment factor until after outward departure;
  (2) keep the pigment-bearing mesh mostly opaque until it is recognizably
      detached, then disperse it as the seven real swallow rigs emerge.

This preserves the exact original lamina/shader at f132/f133, untouched bird
positions and articulation, all 21 nonflying petals, the camera, world-space
petal movement and 12s/288f film.
"""
import bpy
from v495_staggered_swallows import OFFSET, INK_EVENTS
from v497_ink_release import STAGES

N=7
REVISED_WASH=((1,0.),(132,0.),(133,0.),(141,0.),
              (147,.02),(153,.11),(159,.43),(165,.87),
              (170,1.),(181,1.),(288,1.))
REVISED_PIGMENT=((145,.015),(155,.16),(162,.53),(170,1.))

def retime_socket(socket,old,new):
    for f,_ in old:
        if not socket.keyframe_delete(data_path="default_value",frame=f):
            raise RuntimeError("Existing pigment keyframe not found at "+str(f))
    for f,v in new:
        socket.default_value=v
        if not socket.keyframe_insert(data_path="default_value",frame=f):
            raise RuntimeError("Could not animate pigment at "+str(f))

def retime_value(output,old,new):
    for f,_ in old:
        if not output.keyframe_delete(data_path="default_value",frame=f):
            raise RuntimeError("Original transparent wash frame missing "+str(f))
    for f,v in new:
        output.default_value=v
        if not output.keyframe_insert(data_path="default_value",frame=f):
            raise RuntimeError("Could not animate wash transparency at "+str(f))

def build():
    scene=bpy.context.scene
    for ordinal in range(N):
        obj=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%ordinal)
        if obj is None or len(obj.data.vertices)!=650:
            raise RuntimeError("Source lamina/carrier topology changed "+str(ordinal))
        mat=obj.data.materials[0] if obj.data.materials else None
        if not mat or not mat.use_nodes:
            raise RuntimeError("Missing original watercolor material "+str(ordinal))
        node=mat.node_tree.nodes.get("V49_Lotus_To_Ink_%02d"%ordinal)
        fade=mat.node_tree.nodes.get("V497_Progress_%02d"%ordinal)
        if node is None or fade is None:
            raise RuntimeError("Missing predecessor V4.9.7 shader tracks "+str(ordinal))
        pigment=node.inputs[0]
        transparency=fade.outputs[0]
        delta=OFFSET[ordinal]
        old_ink=((1,0.),(132,0.),(133,0.))+tuple(
            (f+delta,value) for f,value in INK_EVENTS)+((288,1.),)
        new_ink=((1,0.),(132,0.),(133,0.))+tuple(
            (f+delta,value) for f,value in REVISED_PIGMENT)+((288,1.),)
        retime_socket(pigment,old_ink,new_ink)
        retime_value(transparency,STAGES,REVISED_WASH)

    snapshots=[]
    for f in (132,133,145,153,159,165,170,175):
        scene.frame_set(f)
        colors=[]
        fades=[]
        for i in range(N):
            mat=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].data.materials[0]
            colors.append(float(mat.node_tree.nodes["V49_Lotus_To_Ink_%02d"%i].inputs[0].default_value))
            fades.append(float(mat.node_tree.nodes["V497_Progress_%02d"%i].outputs[0].default_value))
        snapshots.append({"frame":f,"mean_ink_factor":round(sum(colors)/N,5),
                          "mean_wash_dissolution":round(sum(fades)/N,5)})
        if f in (132,133) and (max(colors)>1e-6 or max(fades)>1e-6):
            raise RuntimeError("V410 changed original watercolor at exact handoff")
        if f==153 and (max(colors)>.29 or max(fades)>.12):
            raise RuntimeError("V410 petals prematurely become gray or invisible")
        if f==165 and min(fades)<.86:
            raise RuntimeError("V410 leaves large 3D laminae hiding articulated birds")
        if f==175 and min(fades)<.999:
            raise RuntimeError("V410 wash carrier persists beyond real swallows")
    scene.frame_set(165)
    visible=sum(max(bpy.data.objects["BIRD_%02d_RIG"%i].scale)>.04
                for i in range(N))
    if visible!=N:
        raise RuntimeError("V410 true bird rigs are not in sync with ink release")
    scene.frame_set(1)
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("V410 timeline was modified")
    result={"retimed_independent_petal_materials":7,
            "source_to_carrier_frame_132_133_untouched":True,
            "material_timelines":snapshots,
            "all_real_bird_rigs_at_frame_165":visible,
            "carrier_vertices_each":650,"frames":288,"fps":24}
    print("V410_WATERCOLOR_PETAL_IDENTITY_QA_PASS",result,flush=True)
    return result
