#!/usr/bin/env python3
"""V4.6: correct large/overdetailed birds in painterly landscape.

Preserves complete V4.5.2 hero rigs and 280 feather meshes in editable .blend,
but hides their geometry during main-film rendering. Replaces them with quiet,
simple dark-ink LOD birds and scales the inherited seven animated flight roots.
The size reduction is independent of 3D camera focal length and therefore
does not shrink the landscape or flower.
"""
import math
import bpy
import v45_birds as hero

# Relative to the previous V4.5 3D character size, chosen to keep bird wings
# ~20–40 screen pixels at 360×640 in the main mountain sequence.
SCALE_FACTORS=(.42,.35,.47,.38,.44,.32,.40)
GROUP="V46_14_PAINTERLY_SWALLOW_LOD"

def coll():
    c=bpy.data.collections.get(GROUP)
    if c is None:
        c=bpy.data.collections.new(GROUP)
        bpy.context.scene.collection.children.link(c)
    return c

def ob(name,verts,faces,material,parent):
    data=bpy.data.meshes.new(name+"_mesh")
    data.from_pydata(verts,[],faces);data.update()
    result=bpy.data.objects.new(name,data)
    coll().objects.link(result)
    result.parent=parent
    result.data.materials.append(material)
    for face in result.data.polygons:face.use_smooth=True
    return result

def black_ink():
    return hero.material("V46_Soft_Charcoal_Wash",(.079,.089,.086),rough=.94)

def silhouette_body(idx,rig,ink):
    # Narrow, tapering breast and small head; no white CG-looking chest
    # (the detailed V4.5.2 body stays available but hidden in final render).
    body=hero.ellipsoid("V46_BIRD_%02d_TORSO"%idx,rig,
                        (0,-.016,-.06),(.103,.074,.286),ink,16,12)
    for old in list(body.users_collection):old.objects.unlink(body)
    coll().objects.link(body)
    head=hero.ellipsoid("V46_BIRD_%02d_HEAD"%idx,rig,
                        (0,-.018,.235),(.072,.064,.087),ink,14,8)
    for old in list(head.users_collection):old.objects.unlink(head)
    coll().objects.link(head)
    # One solid forked tail at film scale; 2 tapered wings integrated into the
    # tail fan rather than thin isolated streamers that read like black wires.
    ob("V46_BIRD_%02d_FORKED_TAIL"%idx,
       [(-.050,.018,-.252),(.050,.018,-.252),(.23,.018,-.76),
        (.052,.018,-.51),(0,.018,-.43),(-.052,.018,-.51),
        (-.23,.018,-.76)],
       [(0,1,3,4,5),(1,2,3), (5,6,0)],ink,rig)
    return body

def silhouette_wings(idx,rig,ink):
    for side in (-1,1):
        code="L" if side==-1 else "R"
        joint=bpy.data.objects.get("BIRD_%02d_WING_%s"%(idx,code))
        if joint is None:raise RuntimeError("Missing original moving wing control")
        # A smoothly swept tapered silhouette instead of 20 individual
        # overlapping feather meshes. A discreet scallop near trailing edge.
        # Coordinates are in local wing-hinge space and inherit flap keyframes.
        outline=[
            (.00,.027),(.07,.095),(.18,.176),(.34,.242),
            (.57,.262),(.82,.209),(1.01,.108),
            (.81,.095),(.63,.055),(.52,-.022),
            (.43,-.077),(.36,-.115),(.30,-.090),
            (.20,-.139),(.13,-.095),(.06,-.033)]
        vertices=[(side*x,-.024+(.012*math.sin(i/15*math.pi)),z)
                  for i,(x,z) in enumerate(outline)]
        faces=[(0,i,i+1) for i in range(1,len(vertices)-1)]
        ob("V46_BIRD_%02d_WING_%s"%(idx,code),vertices,faces,ink,joint)
        # A short dark trailing line subtly breaks an otherwise perfectly
        # triangular vector shape, but no realistic micro-feather details.

def adapt_animation(idx,rig):
    factor=SCALE_FACTORS[idx]
    # Override the original key values at precisely the same keyframe times.
    # The root location/path remains unchanged, avoiding compression of the
    # whole flock around the world origin.
    base=[(1,.001),(112+idx*3,.001),(148+idx*3,.47),(210,.65),(288,.55)]
    for f,value in base:
        s=max(.0001,value*factor)
        rig.scale=(s,s,s)
        rig.keyframe_insert(data_path="scale",frame=f)
    # Small variation in flight position; offset parent is already present
    # from v42.spread_flock, so we do not rewrite root location F-curves.
    offset=bpy.data.objects.get("BIRD_%02d_COMPOSITION_OFFSET"%idx)
    if offset is not None:
        delta_x=(-.12,-.24,.09,.22,-.04,.18,-.15)[idx]
        delta_z=(.16,-.09,.30,-.18,.08,-.23,.25)[idx]
        offset.location.x+=delta_x
        offset.location.z+=delta_z
    return factor

def soften_transition():
    # Existing GP contours were authored for birds 2x larger. Progressively
    # taper calligraphy amplitude as the smaller flock emerges.
    gp=bpy.data.objects.get("GP43_Lotus_to_Swallow_Calligraphy")
    if gp is not None:
        for f,sc in ((1,1.0),(134,1.0),(153,.84),(174,.54),
                     (205,.32),(236,.32),(288,.32)):
            gp.scale=(sc,sc,sc)
            gp.keyframe_insert(data_path="scale",frame=f)

def build():
    original=bpy.data.collections.get(hero.GROUP)
    if original is None:
        raise RuntimeError("Original V45 hero bird library missing")
    # Keep all detailed 3D components and wing armatures in the scene. Hide
    # only V45 rendered meshes, never the BIRD_NN_RIG controllers or wing joints.
    old_meshes=0
    for item in original.objects:
        if item.type in ("MESH","CURVE"):
            item.hide_render=True
            old_meshes+=1
    if old_meshes<280:
        raise RuntimeError("Expected detailed bird model library to be present")
    ink=black_ink()
    factors=[]
    for idx in range(7):
        rig=bpy.data.objects.get("BIRD_%02d_RIG"%idx)
        if rig is None:raise RuntimeError("Flight root missing "+str(idx))
        silhouette_body(idx,rig,ink)
        silhouette_wings(idx,rig,ink)
        factors.append(adapt_animation(idx,rig))
    soften_transition()
    visible=[o for o in coll().objects if o.type=="MESH" and not o.hide_render]
    if len(visible)!=35:
        raise RuntimeError("Expected 35 visible painterly silhouette meshes; found "+str(len(visible)))
    print("V46_SMALL_FLOCK_QA",len(visible),"silhouette meshes",old_meshes,
          "hero meshes hidden; relative scales",factors)
    return {"bird_count":7,"silhouette_meshes":len(visible),
            "hero_meshes_hidden":old_meshes,"scale_factors":factors}
