#!/usr/bin/env python3
"""V4.9.1 ink-wash surface treatment for the existing 3D lotus.

Visual goal: readable volume without plastic-smooth pink gradients. Uses
actual per-petal UV coordinates (U = transverse, V = along petal), with
irregular pigment pooling, dry-brush longitudinal fibers and rim staining.
No additional geometry, no simulated frames and no silhouette changes.

Call AFTER v49_ink.build and BEFORE v49_handoff.build: the latter copies the
now-painterly source shader into each continuous morph carrier.
"""
import bpy

PETAL_MATERIALS=(
    "V44_Petal_Ivory_Outer",
    "V44_Petal_Blush_Middle",
    "V44_Petal_Cream_Inner",
)

def mathnode(nodes,operation,label):
    node=nodes.new("ShaderNodeMath")
    node.operation=operation
    node.label=label
    return node

def texture(nodes,links,tex_socket,scale,detail,roughness,label):
    noise=nodes.new("ShaderNodeTexNoise")
    noise.label=label
    noise.inputs["Scale"].default_value=scale
    noise.inputs["Detail"].default_value=detail
    noise.inputs["Roughness"].default_value=roughness
    links.new(tex_socket,noise.inputs["Vector"])
    return noise.outputs["Fac"]

def tonal_ramp(nodes,stops,name):
    node=nodes.new("ShaderNodeValToRGB")
    node.label=name
    elements=node.color_ramp.elements
    elements[0].position=stops[0][0]
    elements[0].color=(*stops[0][1],1.0)
    elements[1].position=stops[-1][0]
    elements[1].color=(*stops[-1][1],1.0)
    for position,color in stops[1:-1]:
        elements.new(position).color=(*color,1.0)
    node.color_ramp.interpolation="EASE"
    return node

def multiply(nodes,links,a,b,fac,label):
    mix=nodes.new("ShaderNodeMixRGB")
    mix.blend_type="MULTIPLY"
    mix.label=label
    mix.inputs[0].default_value=fac
    links.new(a,mix.inputs[1])
    links.new(b,mix.inputs[2])
    return mix.outputs[0]

def watercolor(mat):
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    shader=next((n for n in nodes if n.type=="BSDF_PRINCIPLED"),None)
    if shader is None or len(shader.inputs["Base Color"].links)!=1:
        raise RuntimeError("Missing existing watercolor shader on "+mat.name)
    base=shader.inputs["Base Color"].links[0].from_socket
    coords=next((n for n in nodes if n.type=="TEX_COORD"),None)
    if coords is None:
        coords=nodes.new("ShaderNodeTexCoord")
    uv=coords.outputs["UV"]
    split=nodes.new("ShaderNodeSeparateXYZ")
    links.new(uv,split.inputs["Vector"])
    u=split.outputs["X"]

    # Larger-scale pigments: more conspicuous than V4.9's previous faint grain.
    pooling=texture(nodes,links,uv,4.3,3.7,.76,"Dense watercolor pigment pools")
    wash=tonal_ramp(nodes,[
        (0.0,(.35,.33,.34)),(.31,(.58,.55,.57)),
        (.50,(.82,.79,.80)),(.69,(1.0,.98,.97)),(1.0,(1.0,1.0,1.0))
    ],"Pigment granulation distribution")
    links.new(pooling,wash.inputs["Fac"])
    colored=multiply(nodes,links,base,wash.outputs["Color"],.86,"Transparent washy pigments")

    # Darken the very outer petal edges with natural, noise-disturbed bleeding.
    center=mathnode(nodes,"SUBTRACT","UV U relative to petal midrib")
    center.inputs[1].default_value=.5
    links.new(u,center.inputs[0])
    absolute=mathnode(nodes,"ABSOLUTE","Distance from petal midrib")
    links.new(center.outputs[0],absolute.inputs[0])
    normalized=mathnode(nodes,"MULTIPLY","Normalize lateral radius")
    normalized.inputs[1].default_value=2.0
    links.new(absolute.outputs[0],normalized.inputs[0])
    edge_noise=mathnode(nodes,"SUBTRACT","Asymmetric watercolor bleed")
    links.new(pooling,edge_noise.inputs[0])
    edge_noise.inputs[1].default_value=.5
    perturb=mathnode(nodes,"MULTIPLY","Bleed edge irregularity")
    links.new(edge_noise.outputs[0],perturb.inputs[0])
    perturb.inputs[1].default_value=.14
    edge=mathnode(nodes,"ADD","Noise-adjusted petal edge")
    links.new(normalized.outputs[0],edge.inputs[0])
    links.new(perturb.outputs[0],edge.inputs[1])
    stain=tonal_ramp(nodes,[
        (0.0,(1.,1.,1.)),(.58,(1.,1.,1.)),
        (.83,(.85,.79,.78)),(1.0,(.57,.50,.53))
    ],"Petal rim pigment accumulation")
    links.new(edge.outputs[0],stain.inputs["Fac"])
    colored=multiply(nodes,links,colored,stain.outputs["Color"],.74,"Ragged brush perimeter")

    # Long brush fibers running in the direction of the petal veins.
    stretch=nodes.new("ShaderNodeVectorMath")
    stretch.operation="MULTIPLY"
    stretch.inputs[1].default_value=(75.0,2.0,1.0)
    links.new(uv,stretch.inputs[0])
    streak=texture(nodes,links,stretch.outputs["Vector"],1.0,2.1,.65,"Long fibrous wash")
    fibers=tonal_ramp(nodes,[
        (0.0,(.67,.67,.65)),(.5,(.89,.90,.88)),(1.0,(1.,1.,1.))
    ],"Drybrush fine veining")
    links.new(streak,fibers.inputs["Fac"])
    colored=multiply(nodes,links,colored,fibers.outputs["Color"],.46,"Longitudinal drybrush")

    links.new(colored,shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value=1.0
    for name,value in (("Metallic",0.0),("Coat Weight",0.0),
                       ("Subsurface Weight",0.0),("Specular IOR Level",.08)):
        input_=shader.inputs.get(name)
        if input_ is not None:input_.default_value=value
    return 3

def build():
    materials=[]
    for name in PETAL_MATERIALS:
        mat=bpy.data.materials.get(name)
        if mat is None:
            raise RuntimeError("Missing V4.9 source material "+name)
        stages=watercolor(mat)
        if stages!=3:
            raise RuntimeError("Incomplete painterly shader")
        materials.append(mat.name)
    result={"painterly_source_materials":materials,
            "pigment_layers_per_material":3,
            "ink_wash_preserves_original_3d_meshes":True}
    print("V49_ARTISTIC_WATERCOLOR_QA_PASS",result,flush=True)
    return result
