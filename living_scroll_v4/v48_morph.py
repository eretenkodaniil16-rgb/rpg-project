#!/usr/bin/env python3
"""Living Scroll V4.8: seven evaluated 3D lotus petals detach, deform into
ink-shaped wing strips, and travel into the seven existing small bird paths.

Retains source meshes, full V4.7 clean transition, and V4.6 low-detail flock.
Artistic morph only: constant mesh topology for each carrier, not conversion
of the whole flower into biologically accurate birds.
"""
import math
import bpy
from mathutils import Vector

GROUP="V48_16_PETAL_TO_FLIGHT"
INDICES=(0,2,4,6,8,10,12)
START_FRAME=132
END_FRAME=182

def smoothstep(t):
    t=max(0.,min(1.,t))
    return t*t*(3.-2.*t)

def col():
    collection=bpy.data.collections.get(GROUP)
    if collection is None:
        collection=bpy.data.collections.new(GROUP)
        bpy.context.scene.collection.children.link(collection)
    return collection

def transform_material():
    mat=bpy.data.materials.new("V48_Petal_Into_Charcoal")
    mat.use_nodes=True
    p=mat.node_tree.nodes.get("Principled BSDF")
    p.inputs["Roughness"].default_value=.87
    p.inputs["Metallic"].default_value=0.
    info=mat.node_tree.nodes.new("ShaderNodeObjectInfo")
    mat.node_tree.links.new(info.outputs["Color"],p.inputs["Base Color"])
    return mat

def evaluate_lamina(obj,frame):
    scene=bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps)
    temp=evaluated.to_mesh()
    try:
        transform=evaluated.matrix_world.copy()
        verts=[transform @ vertex.co for vertex in temp.vertices]
        polys=[tuple(p.vertices) for p in temp.polygons]
    finally:
        evaluated.to_mesh_clear()
    if len(verts)!=650 or len(polys)<500:
        raise RuntimeError("V4.4 petal topology unexpected: "+obj.name)
    return verts,polys

def get_positions():
    scene=bpy.context.scene
    result=[]
    for i in range(7):
        rig=bpy.data.objects.get("BIRD_%02d_RIG"%i)
        if rig is None:
            raise RuntimeError("V4.6 swallow missing "+str(i))
        positions={}
        for f in (136,148,160,172,182):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            positions[f]=rig.matrix_world.translation.copy()
        result.append(positions)
    return result

def target_shape(index,ordinal,total):
    """Same 650-vertex ordering as the source (two 25x13 surfaces).
    A tapered and cambered flight feather/wing, not a uniform triangle.
    """
    block=325
    j=(index%block)//13
    k=(index%block)%13
    shell=index//block
    s=j/24.
    u=2*k/12.-1.
    side=-1 if ordinal%2==0 else 1
    wing_angle=(ordinal-3)*.12
    taper=.5*math.sin(math.pi*s)**.55 + .13*(1-s)
    x=side*(.13+.54*s) + u*taper*.16*math.sin(wing_angle)
    z=.10+.22*s+.05*math.sin(math.pi*s) + u*taper*.19
    y=-.03-.025*s*s + (.003 if shell else -.003)
    return (x,y,z)

def animate(source,ordinal,positions,material):
    start_verts,polys=evaluate_lamina(source,START_FRAME)
    centroid=sum(start_verts,Vector((0.,0.,0.)))/len(start_verts)
    base=[tuple(v-centroid) for v in start_verts]
    datablock=bpy.data.meshes.new("V48_CARRIER_%02d_MESH"%ordinal)
    datablock.from_pydata(base,[],polys)
    datablock.update()
    obj=bpy.data.objects.new("V48_PETAL_TO_BIRD_%02d"%ordinal,datablock)
    col().objects.link(obj)
    datablock.materials.append(material)
    for poly in datablock.polygons:
        poly.use_smooth=True
    obj.shape_key_add(name="Lotus_Lamina",from_mix=False)
    wing=obj.shape_key_add(name="Ink_Wing",from_mix=False)
    for idx in range(len(base)):
        wing.data[idx].co=target_shape(idx,ordinal,len(base))
    for f,v in ((1,0.),(132,0.),(143,.16),(153,.64),(165,1.),(288,1.)):
        wing.value=v
        wing.keyframe_insert(data_path="value",frame=f)
    # Move from the actual evaluated V4.4 petal into the corresponding
    # sampled V4.6 bird flight path. 3D world-space, no teleport.
    end=positions[172]
    start=centroid
    middle=positions[160]
    via=Vector((
       .46*start.x+.54*middle.x,
       -.09+(.46*start.y+.54*middle.y),
       .46*start.z+.54*middle.z+.13
    ))
    landing=Vector((end.x,end.y-.015,end.z))
    for f,point in (
        (1,start),(128,start),(132,start),
        (146,via),(163,(via+landing)*.5),
        (175,landing),(182,positions[182])
    ):
        obj.location=point
        obj.keyframe_insert(data_path="location",frame=f)
    for f,s in ((1,.001),(128,.001),(132,1.0),(141,1.0),
                (153,.82),(165,.48),(174,.18),(182,.001),(288,.001)):
        obj.scale=(s,s,s)
        obj.keyframe_insert(data_path="scale",frame=f)
    # Object Info Color becomes the physically rendered pigment per object.
    for f,color in (
        (1,(.92,.82,.74,1)),(132,(.92,.82,.74,1)),
        (147,(.63,.47,.43,1)),(158,(.25,.24,.23,1)),
        (170,(.078,.091,.087,1)),(288,(.078,.091,.087,1))
    ):
        obj.color=color
        obj.keyframe_insert(data_path="color",frame=f)
    # Crossfade source lamina smoothly via its actual object scale, while
    # cloned geometry assumes the same position and shape at frame 132.
    for f,s in ((1,1.),(128,1.),(132,1.),(140,.68),
                (150,.11),(158,.001),(288,.001)):
        source.scale=(s,s,s)
        source.keyframe_insert(data_path="scale",frame=f)
    return obj

def assert_continuity(objects):
    scene=bpy.context.scene
    for f in (132,140,153,165,175,182):
        scene.frame_set(f)
        for obj in objects:
            if not all(math.isfinite(value) for value in (*obj.location,*obj.scale)):
                raise RuntimeError("Invalid morph transform")
    scene.frame_set(132)
    for i,obj in enumerate(objects):
        if max(obj.scale)<.8 or obj.data.shape_keys is None:
            raise RuntimeError("Petal continuity not established for "+str(i))
    scene.frame_set(182)
    for i,obj in enumerate(objects):
        if max(obj.scale)>.01:
            raise RuntimeError("Carrier leaked into final flock for "+str(i))
    scene.frame_set(1)

def build():
    scene=bpy.context.scene
    material=transform_material()
    targets=get_positions()
    objects=[]
    for i,petal in enumerate(INDICES):
        source=bpy.data.objects.get("V44_LOTUS_R0_P%02d"%petal)
        if source is None:
            raise RuntimeError("V4.4 detailed lotus source absent: "+str(petal))
        objects.append(animate(source,i,targets[i],material))
    assert_continuity(objects)
    metrics={"source_petals":len(INDICES),
             "carriers":len(objects),
             "topology_vertices_each":len(objects[0].data.vertices),
             "carrier_start":START_FRAME,"carrier_end":END_FRAME}
    print("V48_PETAL_FLIGHT_QA_PASS",metrics,flush=True)
    return metrics
