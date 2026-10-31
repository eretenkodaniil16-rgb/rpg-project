#!/usr/bin/env python3
"""V4.9 continuity correction: match source shader before ink conversion.

The evaluated carrier duplicates the petal at frame 132. At the 133 handoff
the *same* watercolor material is used; only then does pigment become ink.
This addresses the formerly abrupt cream/pink-to-beige material jump.
"""
import math
import bpy

INDICES=(0,2,4,6,8,10,12)

def make_flight_material(source_mat,index):
    mat=source_mat.copy()
    mat.name="V49_Continuous_Wash_To_Ink_%02d"%index
    mat.use_nodes=True
    tree=mat.node_tree
    nodes=tree.nodes
    links=tree.links
    shader=nodes.get("Principled BSDF")
    if shader is None:
        raise RuntimeError("Petal material without Principled BSDF: "+source_mat.name)
    existing=shader.inputs["Base Color"].links
    if len(existing)!=1:
        raise RuntimeError("Expected single source-pigment color link")
    original=existing[0].from_socket
    pigment=nodes.new("ShaderNodeTexNoise")
    pigment.name="Charcoal_Granulation_%02d"%index
    pigment.inputs["Scale"].default_value=14.0
    pigment.inputs["Detail"].default_value=3.0
    pigment.inputs["Roughness"].default_value=.72
    tex=nodes.get("Texture Coordinate")
    if tex is None:
        tex=next((n for n in nodes if n.type=="TEX_COORD"),None)
    if tex is not None:
        links.new(tex.outputs["UV"],pigment.inputs["Vector"])
    ink=nodes.new("ShaderNodeValToRGB")
    ink.name="V49_Granulated_Ink_%02d"%index
    ink.color_ramp.elements[0].position=.18
    ink.color_ramp.elements[0].color=(.052,.061,.058,1.)
    ink.color_ramp.elements[1].position=.82
    ink.color_ramp.elements[1].color=(.14,.15,.135,1.)
    links.new(pigment.outputs["Fac"],ink.inputs["Fac"])
    blend=nodes.new("ShaderNodeMixRGB")
    blend.name="V49_Lotus_To_Ink_%02d"%index
    blend.blend_type="MIX"
    blend.use_clamp=True
    links.new(original,blend.inputs[1])
    links.new(ink.outputs["Color"],blend.inputs[2])
    links.new(blend.outputs[0],shader.inputs["Base Color"])
    # A material per carrier allows future independent offsets, and guarantees
    # an *identical* source pigment at the exact handoff (mix factor = 0).
    for frame,val in ((1,0.),(132,0.),(133,0.),(141,.06),
                      (151,.34),(164,.86),(172,1.),(288,1.)):
        blend.inputs[0].default_value=val
        blend.inputs[0].keyframe_insert(data_path="default_value",frame=frame)
    shader.inputs["Roughness"].default_value=.98
    return mat,blend

def build():
    scene=bpy.context.scene
    result=[]
    for i,petal_id in enumerate(INDICES):
        source=bpy.data.objects.get("V44_LOTUS_R0_P%02d"%petal_id)
        carrier=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%i)
        if source is None or carrier is None:
            raise RuntimeError("Missing original petal/carrier "+str(i))
        if len(carrier.data.vertices)!=650:
            raise RuntimeError("Unexpected carrier topology")
        mat,blend=make_flight_material(source.data.materials[0],i)
        carrier.data.materials.clear()
        carrier.data.materials.append(mat)
        # Frame 133 is the one-frame visibility swap from V4.9.
        # Prevent carrier movement within that swap, while keeping later keys.
        scene.frame_set(132)
        carrier_origin=carrier.location.copy()
        carrier.location=carrier_origin
        carrier.keyframe_insert(data_path="location",frame=133)
        for f in (132,133,141,151,164,172):
            scene.frame_set(f)
            if not all(math.isfinite(float(v)) for v in carrier.location):
                raise RuntimeError("Nonfinite carrier translation")
            if f==133 and (source.hide_render is not True or carrier.hide_render is not False):
                raise RuntimeError("Visibility mismatch during petal handoff")
            if f==133 and abs(float(blend.inputs[0].default_value))>1e-6:
                raise RuntimeError("Handoff pigment discontinuity")
        result.append(carrier.name)
    scene.frame_set(1)
    print("V49_CONTINUOUS_WATERCOLOR_PIGMENT_QA_PASS",len(result),flush=True)
    return {"matching_source_materials":len(result),"handoff_frame":133,
            "original_topology_unchanged":True}
