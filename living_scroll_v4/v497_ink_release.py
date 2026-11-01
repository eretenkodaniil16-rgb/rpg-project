#!/usr/bin/env python3
"""Living Scroll V4.9.7: disperse interim 3D ink silhouettes like pigment on paper.

Actual high-resolution V4.9.6 Blender frames showed that folded petal geometry
still turns into large, dark, star-like shapes at frame 165. The 650-vertex
source-to-carrier handoff is correct, and the later V4.6 small swallows are good.
Only the conspicuous intermediate carrier is adjusted here: its material gets
a time-keyed, mildly granulated translucent paper-wash release.

The two sources of apparent motion remain physically sampled 3D animation;
the dithered wash uses a true Blender shader graph and is present in the .blend.
Seven rigs, meshes, mesh keyframe tracks, camera, other 21 petals and
12-second 24fps timeline are not touched.
"""
import math
import bpy

BIRDS=7
OUTER=(0,2,4,6,8,10,12)
# Blender frame/time; no change whatsoever before original frame-133 swap.
STAGES=((1,0.),(132,0.),(133,0.),(141,0.),(148,.09),
        (153,.30),(159,.68),(165,.92),(170,1.),
        (181,1.),(288,1.))

def blend_shader(material,ordinal):
    if not material.use_nodes:
        raise RuntimeError("Expected original painterly material nodes")
    if hasattr(material,"surface_render_method"):
        material.surface_render_method="DITHERED"
    elif hasattr(material,"blend_method"):
        material.blend_method="HASHED"
    else:
        raise RuntimeError("Transparent dither blending unavailable")

    nodes=material.node_tree.nodes
    links=material.node_tree.links
    output=next((n for n in nodes
                 if n.type=="OUTPUT_MATERIAL" and n.is_active_output),None)
    if output is None or len(output.inputs["Surface"].links)!=1:
        raise RuntimeError("Missing single existing material output")
    old=output.inputs["Surface"].links[0].from_socket

    progress=nodes.new("ShaderNodeValue")
    progress.name="V497_Progress_%02d"%ordinal
    progress.label="Lotus-pigment dissolution over timeline"
    for frame,value in STAGES:
        progress.outputs[0].default_value=value
        progress.outputs[0].keyframe_insert(data_path="default_value",frame=frame)

    texture=nodes.new("ShaderNodeTexNoise")
    texture.name="V497_Irregular_Wash_%02d"%ordinal
    texture.inputs["Scale"].default_value=10.5
    texture.inputs["Detail"].default_value=2.0
    texture.inputs["Roughness"].default_value=.68
    coord=next((n for n in nodes if n.type=="TEX_COORD"),None)
    if coord is None:
        coord=nodes.new("ShaderNodeTexCoord")
    links.new(coord.outputs["UV"],texture.inputs["Vector"])

    def calc(name,operation,a=None,b=None):
        node=nodes.new("ShaderNodeMath")
        node.name=name
        node.operation=operation
        node.use_clamp=operation=="ADD"
        for index,sock in enumerate((a,b)):
            if sock is None:
                continue
            if isinstance(sock,(float,int)):
                node.inputs[index].default_value=float(sock)
            else:
                links.new(sock,node.inputs[index])
        return node.outputs[0]

    p=progress.outputs[0]
    one_minus=calc("V497_1_minus_P_%02d"%ordinal,"SUBTRACT",1.,p)
    bell=calc("V497_Fade_Mid_Envelope_%02d"%ordinal,"MULTIPLY",p,one_minus)
    centered=calc("V497_Granular_Centered_%02d"%ordinal,"SUBTRACT",texture.outputs["Fac"],.5)
    jitter=calc("V497_Jitter_Weight_%02d"%ordinal,"MULTIPLY",centered,.70)
    modulation=calc("V497_Only_During_Dissolve_%02d"%ordinal,"MULTIPLY",jitter,bell)
    alpha=calc("V497_Dissolve_Factor_%02d"%ordinal,"ADD",p,modulation)
    clear=nodes.new("ShaderNodeBsdfTransparent")
    clear.name="V497_Clear_Paper_%02d"%ordinal
    mix=nodes.new("ShaderNodeMixShader")
    mix.name="V497_Dispersed_Lotus_To_Swallow_%02d"%ordinal
    links.new(alpha,mix.inputs[0])
    links.new(old,mix.inputs[1])
    links.new(clear.outputs["BSDF"],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs["Surface"])
    return progress

def build():
    scene=bpy.context.scene
    report=[]
    for i,source_idx in enumerate(OUTER):
        carrier=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%i)
        source=bpy.data.objects.get("V44_LOTUS_R0_P%02d"%source_idx)
        if carrier is None or source is None or len(carrier.data.vertices)!=650:
            raise RuntimeError("Missing original petal-to-bird carrier "+str(i))
        mat=carrier.data.materials[0]
        if not mat.name.startswith("V49_Continuous_Wash_To_Ink_"):
            raise RuntimeError("Unrecognized original source-pigment transition")
        progress=blend_shader(mat,i)
        report.append({"carrier":carrier.name,"material":mat.name,
                       "progress_node":progress.name})
    # Render changes only after the precise frame 132/133 source handoff.
    for f,expected in ((132,0.),(133,0.),(153,.30),(165,.92),(170,1.)):
        scene.frame_set(f)
        for i in range(BIRDS):
            mat=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].data.materials[0]
            node=mat.node_tree.nodes["V497_Progress_%02d"%i]
            value=node.outputs[0].default_value
            if abs(value-expected)>.005:
                raise RuntimeError("Pigment progression wrong at %d: %.6f"%(f,value))
    scene.frame_set(132)
    for i in range(BIRDS):
        carrier=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
        if carrier.data.shape_keys.key_blocks["Ink_Wing"].value>1e-6:
            raise RuntimeError("Geometry at source handoff changed")
    scene.frame_set(1)
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("Master 12-second film timing was changed")
    out={"granulated_wash_carriers":BIRDS,
         "transparent_at_165":.92,"fully_released_at_frame":170,
         "original_mesh_vertices":650,
         "preserves_unchanged_seven_bird_rigs":True,
         "preserves_unchanged_other_twenty_one_petals":True,
         "unchanged_timeline_frames":288,"fps":24,
         "materials":report}
    print("V497_MATTE_INK_RELEASE_QA_PASS",out,flush=True)
    return out
