#!/usr/bin/env python3
"""V4.9.4 experiment: watercolor fade for the 21 non-flying lotus petals.

The source V4.4 blossom has 13+9+6=28 petals, while exactly seven outer
petals are cloned into the existing 650-vertex V4.9.3 3D bird carriers.
Previous versions merely shrank the 21 other petals with the flower root.
Here each of those 21 petals gradually dissolves with staggered, dithered
transparency. The seven physical carrier objects, shared camera and actual
flight paths remain untouched. Scene's full contract stays 288f/24fps.
"""
import re
import bpy

SEVEN_FLYING_OUTER=(0,2,4,6,8,10,12)
PETAL_PATTERN=re.compile(r"^V44_LOTUS_R([012])_P(\d\d)$")

def keyed_dissolve(petal,number,ring):
    if not petal.data.materials or not petal.data.materials[0].use_nodes:
        raise RuntimeError("Expected painted petal material: "+petal.name)
    mat=petal.data.materials[0].copy()
    mat.name="V494_Staggered_Ink_Dissolve_R%d_P%02d"%(ring,number)
    mat.use_nodes=True
    if hasattr(mat,"surface_render_method"):
        mat.surface_render_method="DITHERED"
    elif hasattr(mat,"blend_method"):
        mat.blend_method="HASHED"
    else:
        raise RuntimeError("Blender material missing transparent blending capability")
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    output=next((n for n in nodes if n.type=="OUTPUT_MATERIAL" and n.is_active_output),None)
    if output is None or len(output.inputs["Surface"].links)!=1:
        raise RuntimeError("Unexpected painterly output on "+mat.name)
    pigment=output.inputs["Surface"].links[0].from_socket
    transparent=nodes.new("ShaderNodeBsdfTransparent")
    transparent.name="V494_Translucent_Paper_Fade"
    mixer=nodes.new("ShaderNodeMixShader")
    mixer.name="V494_21_Petal_Dissolve"
    links.new(pigment,mixer.inputs[1])
    links.new(transparent.outputs["BSDF"],mixer.inputs[2])
    links.new(mixer.outputs[0],output.inputs["Surface"])
    # Slightly displaced staging lets every ring become light calligraphy,
    # rather than all 21 leaves blinking out simultaneously.
    start=138+(number*5+ring*11)%14
    finish=166+(number*7+ring*9)%12
    for frame,value in ((1,0.),(132,0.),(start,0.),
                        (start+7,.20),(finish-5,.78),(finish,1.),
                        (288,1.)):
        mixer.inputs[0].default_value=value
        mixer.inputs[0].keyframe_insert(data_path="default_value",frame=frame)
    petal.data.materials[0]=mat
    return mat.name,start,finish

def build():
    scene=bpy.context.scene
    petals=[]
    for obj in bpy.data.objects:
        m=PETAL_PATTERN.match(obj.name)
        if m and obj.type=="MESH":
            petals.append((obj,int(m.group(1)),int(m.group(2))))
    if len(petals)!=28:
        raise RuntimeError("Expected exactly 28 V4.4 lotus petals, found "+str(len(petals)))
    animated=[]
    protected=[]
    for obj,ring,num in sorted(petals,key=lambda a:(a[1],a[2])):
        if ring==0 and num in SEVEN_FLYING_OUTER:
            protected.append(obj.name)
        else:
            animated.append((obj.name,*keyed_dissolve(obj,num,ring)))
    if len(animated)!=21 or len(protected)!=7:
        raise RuntimeError("Incorrect staggered dissolve assignment")

    # Keep 132/133 world-space source-to-carrier identity unchanged.
    # Longer flowering phase and dithered ink fade replace over-rapid scale
    # contraction of 21 surviving petals; stamens/seed receptacle shrink
    # with the same conserved root rather than receiving a second material.
    root=bpy.data.objects.get("V44_HERO_LOTUS_ROOT")
    if root is None:
        raise RuntimeError("V4.4 hero root missing")
    for f,s in ((1,1.),(120,1.),(132,1.),(138,.99),
                (149,.94),(155,.82),(164,.57),
                (174,.18),(183,.001),(288,.001)):
        root.scale=(s,s,s)
        root.keyframe_insert(data_path="scale",frame=f)
    scene.frame_set(132)
    if abs(root.scale.x-1.)>1e-6:
        raise RuntimeError("Root scale changed at source-carrier swap")
    for i in range(7):
        carrier=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%i)
        if carrier is None or len(carrier.data.vertices)!=650:
            raise RuntimeError("Flying petal morph topology unexpectedly altered")
    scene.frame_set(170)
    if root.scale.x<.20:
        raise RuntimeError("Lotus still shrinks too quickly for dissolve")
    scene.frame_set(183)
    if root.scale.x>.002:
        raise RuntimeError("Residual stamen/seed geometry visible after retreat")
    scene.frame_set(1)
    result={"staggered_transparent_petals":len(animated),
            "untouched_flying_petal_sources":len(protected),
            "scene_frames":scene.frame_end,"fps":scene.render.fps,
            "retained_true_bird_rigs":7,
            "first_dissolve_frame":min(a[2] for a in animated),
            "last_dissolve_frame":max(a[3] for a in animated)}
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("Master 12-second film timing changed")
    print("V494_21_PETAL_DISSOLVE_QA_PASS",result,flush=True)
    return result
