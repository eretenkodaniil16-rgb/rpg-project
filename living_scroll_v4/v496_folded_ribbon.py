#!/usr/bin/env python3
"""V4.9.6 experimental physical bridge: folded lotus petal -> ink ribbon -> swallow.

A direct 650-vertex blend from the wide, pink 3D lamina to the forked swallow
made an unnatural five-pointed black silhouette at frames 150-165. Keep the
EXACT source shape and pigment until the 132/133 handoff, but animate an
additional 650-vertex folded-petal *relative shape key* before the existing
swallow silhouette takes over. Apply a small alternating bank after detachment
to avoid seven rigid, identical billboard-shaped intermediates.

The scene, 21 independently dissolving petals, seven original bird paths,
material networks, source-to-carrier world identity, 650-vertex mesh topology,
and 288-frame/24fps timeline remain unchanged. Designed for independent
Blender image + 24fps moving-image verification before any merge.
"""
import math
import bpy
from mathutils import Vector
from v495_staggered_swallows import OFFSET, SHAPE_EVENTS

BIRDS=7

def folded_ribbon(carrier,index):
    """Narrow the petal around its OWN actual sampled midvein, not an axis-
    aligned proxy. The two 25 x 13 lamina shells remain fully contiguous.
    """
    basis=carrier.data.shape_keys.key_blocks["Lotus_Lamina"]
    j=(index%325)//13
    k=(index%325)%13
    shell=index//325
    t=j/24.0
    u=2.0*k/12.0-1.0
    center=(Vector(basis.data[j*13+6].co)+
            Vector(basis.data[325+j*13+6].co))*.5
    source=Vector(basis.data[index].co)
    # Keep physical petal length and curved midvein; fold inward only width.
    width=.51-.16*t
    p=center+width*(source-center)
    # Ink on folded paper has a subtle 3D curl and negative camber.
    p.y-=.055*math.sin(math.pi*t)*(u*u)
    p.y+=.026*math.sin(2.0*math.pi*t)*u
    p.z+=.036*math.sin(math.pi*t)*(1.0-abs(u))
    p.y+=(.0015 if shell else -.0015)
    return tuple(p)

def retime_wing(carrier,ordinal):
    key=carrier.data.shape_keys.key_blocks["Ink_Wing"]
    delta=OFFSET[ordinal]
    # These 3 keys are the only offsets added by V4.9.5. Keep its 133
    # anchor and the original 1/132/288 keys to guarantee exact continuity.
    for frame,_ in SHAPE_EVENTS:
        if not key.keyframe_delete(data_path="value",frame=frame+delta):
            raise RuntimeError("V496 missing V495 wing animation at %d"% (frame+delta))
    events=((133,0.),(139,0.),(147+delta,0.),
            (153+delta,.085),(159+delta,.44),
            (168+delta,1.),(181,1.),(288,1.))
    last=-1
    for f,v in events:
        if f<=last:
            raise RuntimeError("Unsorted V496 wing keyframes")
        key.value=v
        if not key.keyframe_insert(data_path="value",frame=f):
            raise RuntimeError("Failed V496 wing frame %d"%f)
        last=f

def add_folded_bridge(carrier,ordinal):
    if "V496_Folded_Ribbon" in carrier.data.shape_keys.key_blocks:
        raise RuntimeError("Duplicate V496 folded shape key")
    ribbon=carrier.shape_key_add(name="V496_Folded_Ribbon",from_mix=False)
    verts=[folded_ribbon(carrier,i) for i in range(650)]
    for i,coords in enumerate(verts):
        ribbon.data[i].co=coords
    for j in range(25):
        left=Vector(carrier.data.shape_keys.key_blocks["Lotus_Lamina"].data[j*13].co)
        right=Vector(carrier.data.shape_keys.key_blocks["Lotus_Lamina"].data[j*13+12].co)
        width=(left-right).length
        folded=(Vector(ribbon.data[j*13].co)-
                Vector(ribbon.data[j*13+12].co)).length
        if width>.03 and not (.30<folded/width<.65):
            raise RuntimeError("V496 petal folds in invalid direction on row "+str(j))
    delta=OFFSET[ordinal]
    # Its zero-weight basis at frames 132/133 is the original world sampled
    # lotus petal; the envelope rises during flight, then vanishes BEFORE the
    # true small articulated bird renders prominently.
    for f,v in ((1,0.),(132,0.),(133,0.),(139,0.),
                (145+delta,.56),(151+delta,1.),
                (159+delta,.58),(168+delta,0.),
                (181,0.),(288,0.)):
        ribbon.value=v
        ribbon.keyframe_insert(data_path="value",frame=f)
    return ribbon

def bank_detaching_carrier(carrier,ordinal):
    # Small bank around the viewing axis. This is 3D object rotation, not
    # sprite rotation; start 0 degrees through the source/clone handoff.
    sign=-1 if ordinal%2 else 1
    magnitude=(.085,.115,.140,.090,.135,.105,.100)[ordinal]
    for f,r in ((1,0.),(132,0.),(133,0.),(139,0.),
                (148,.46),(156,1.),(164,-.44),
                (174,.15),(182,0.),(288,0.)):
        angle=magnitude*r*sign
        carrier.rotation_euler=(.40*angle,.22*angle,angle)
        carrier.keyframe_insert(data_path="rotation_euler",frame=f)

def build():
    scene=bpy.context.scene
    report=[]
    for i in range(BIRDS):
        carrier=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%i)
        if carrier is None or len(carrier.data.vertices)!=650:
            raise RuntimeError("Missing intact 650-vertex morph carrier "+str(i))
        if carrier.data.shape_keys is None or "Ink_Wing" not in carrier.data.shape_keys.key_blocks:
            raise RuntimeError("Missing preexisting V4.9.5 swallow shape")
        ribbon=add_folded_bridge(carrier,i)
        retime_wing(carrier,i)
        bank_detaching_carrier(carrier,i)
        report.append({"carrier":i,"ribbon_key":ribbon.name,
                       "deformation_offset_frames":OFFSET[i]})
    for f in (132,133):
        scene.frame_set(f)
        for i in range(BIRDS):
            ob=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            if abs(ob.data.shape_keys.key_blocks["V496_Folded_Ribbon"].value)>1e-6:
                raise RuntimeError("Folded in-between leaked into handoff")
            if abs(ob.data.shape_keys.key_blocks["Ink_Wing"].value)>1e-6:
                raise RuntimeError("Ink silhouette leaked into handoff")
            if any(abs(a)>1e-6 for a in ob.rotation_euler):
                raise RuntimeError("New carrier bank rotated the original petal")
    scene.frame_set(153)
    bridge=[bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            .data.shape_keys.key_blocks["V496_Folded_Ribbon"].value for i in range(BIRDS)]
    if sum(bridge)/7.<.40 or max(bridge)-min(bridge)<.10:
        raise RuntimeError("Seven independently staggered ribbons failed to form")
    scene.frame_set(175)
    if any(bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
           .data.shape_keys.key_blocks["V496_Folded_Ribbon"].value>.001 for i in range(BIRDS)):
        raise RuntimeError("Folded petals persist into the real swallow flock")
    scene.frame_set(1)
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("Original 12s/24fps edit changed")
    result={"folded_ribbon_carriers":7,
            "original_vertices_per_mesh":650,
            "mean_fold_weight_153":round(sum(bridge)/7,4),
            "untouched_real_swallow_paths":7,
            "untouched_other_ink_dissolve_petals":21,
            "timeline_frames":288,"fps":24,"individual_carriers":report}
    print("V496_FOLDED_PETAL_TO_SWALLOW_QA_PASS",result,flush=True)
    return result
