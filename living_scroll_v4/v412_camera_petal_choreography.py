#!/usr/bin/env python3
"""V4.12: make each authentic detached lotus petal legible in the rendered camera.

Previous attempts added world-space offsets without testing their projection.
Most of the seven petals still overlapped the flower when rendered at 360x640.
Here seven original 650-vertex carrier objects keep the same shape keys, real
3D positions at 132/133 and 175/182, and unmodified 3D bird flight rigs.
Their *intermediate* 3D trajectories are solved against the actual animated
Blender camera so the petal centres separate in screen space, not just world
space. Add a subtle rose-tint envelope to the source-pigment material input
while each petal detaches, ending before the dark-ink swallow stage.

No copied flat overlays, scene-wide fading or image-space compositing.
"""
import math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

N=7
FRAMES=(132,133,141,145,153,159,165,170,175,182)
# A fractional outward motion, softened on both sides of the legible frame.
ENVELOPE={132:0.,133:0.,141:0.,145:.38,153:1.,159:.52,
          165:.018,170:0.,175:0.,182:0.}
ROSE_KEYS=((1,0.),(132,0.),(133,0.),(141,0.),
           (145,.24),(153,.46),(159,.25),(165,0.),(288,0.))
PX_W,PX_H=360.,640.

def projected(scene,cam,point):
    xy=world_to_camera_view(scene,cam,point)
    return Vector((float(xy.x)*PX_W,float(xy.y)*PX_H))

def world_move_for_screen(scene,cam,point,dx,dy):
    """Solve the real perspective camera screen Jacobian in a fixed-depth
    camera-aligned 3D plane. Avoid guessing camera orientation or 3D units.
    """
    quat=cam.matrix_world.to_quaternion()
    right=quat@Vector((1.,0.,0.))
    up=quat@Vector((0.,1.,0.))
    p=projected(scene,cam,point)
    pr=projected(scene,cam,point+right)-p
    pu=projected(scene,cam,point+up)-p
    det=pr.x*pu.y-pu.x*pr.y
    if not math.isfinite(det) or abs(det)<1e-5:
        raise RuntimeError("V412 singular camera projection")
    a=(dx*pu.y-pu.x*dy)/det
    b=(pr.x*dy-dx*pr.y)/det
    return right*a+up*b

def color_detaching_petal(mat,i):
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    pigment=nodes.get("V49_Lotus_To_Ink_%02d"%i)
    if pigment is None or len(pigment.inputs[1].links)!=1:
        raise RuntimeError("V412 expected original per-petal watercolor source")
    original=pigment.inputs[1].links[0].from_socket
    tint=nodes.new("ShaderNodeMixRGB")
    tint.name="V412_Rose_While_Detached_%02d"%i
    tint.label="Rose pigment visible on flying petal"
    tint.blend_type="MIX"
    tint.use_clamp=True
    tint.inputs[2].default_value=(.90,.48,.57,1.)
    links.new(original,tint.inputs[1])
    links.new(tint.outputs[0],pigment.inputs[1])
    for frame,value in ROSE_KEYS:
        tint.inputs[0].default_value=value
        tint.inputs[0].keyframe_insert(data_path="default_value",frame=frame)
    return tint

def build():
    scene=bpy.context.scene
    cam=scene.camera
    root=bpy.data.objects.get("V44_HERO_LOTUS_ROOT")
    if cam is None or root is None:
        raise RuntimeError("V412 requires the real film camera and lotus origin")
    source_at={}
    center_at={}
    for f in FRAMES:
        scene.frame_set(f)
        source_at[f]=[
            bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].location.copy()
            for i in range(N)]
        center_at[f]=projected(scene,cam,root.matrix_world.translation)
    scene.frame_set(132)
    src_center=center_at[132]
    directions=[]
    for i in range(N):
        p=projected(scene,cam,source_at[132][i])
        axis=p-src_center
        if axis.length<10:
            a=(i+.5)*math.tau/N
            axis=Vector((math.cos(a),math.sin(a)))
        axis.normalize()
        # Small, ordinal-specific angular divergence reduces projected overlap
        # of opposite petals while preserving their actual radial orientation.
        angle=((i*5)%7-3)*.06
        axis=Vector((axis.x*math.cos(angle)-axis.y*math.sin(angle),
                     axis.x*math.sin(angle)+axis.y*math.cos(angle)))
        directions.append(axis)
    report=[]
    for i in range(N):
        ob=bpy.data.objects.get("V48_PETAL_TO_BIRD_%02d"%i)
        if ob is None or len(ob.data.vertices)!=650:
            raise RuntimeError("V412 carrier mesh topology regression")
        color_detaching_petal(ob.data.materials[0],i)
        displacement={}
        for f in FRAMES:
            scene.frame_set(f)
            baseline=source_at[f][i]
            t=ENVELOPE[f]
            if t>0:
                center=center_at[f]
                current=projected(scene,cam,baseline)
                axis=directions[i]
                along=(current-center).dot(axis)
                radius=120.+(i%3)*10.
                move=max(24.,radius-along)
                # Keep all objects safely within the 9:16 composition.
                goal=current+axis*move*t
                goal.x=max(16.,min(344.,goal.x))
                goal.y=max(100.,min(555.,goal.y))
                adjusted=world_move_for_screen(
                    scene,cam,baseline,goal.x-current.x,goal.y-current.y)
                proposed=baseline+adjusted
                px=(projected(scene,cam,proposed)-current).length
            else:
                proposed=baseline
                px=0.
            ob.location=proposed
            ob.keyframe_insert(data_path="location",frame=f)
            displacement[f]=px
        report.append({"ordinal":i,
                       "projected_offset_153_px":round(displacement[153],2),
                       "projected_offset_165_px":round(displacement[165],2)})
    for f in (132,133,175,182):
        scene.frame_set(f)
        for i in range(N):
            ob=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            if (ob.location-source_at[f][i]).length>1e-6:
                raise RuntimeError("V412 violated world-space anchor at frame %d"%f)
            tint=ob.data.materials[0].node_tree.nodes[
                "V412_Rose_While_Detached_%02d"%i]
            if f in (132,133) and abs(tint.inputs[0].default_value)>1e-6:
                raise RuntimeError("V412 pigment not source-matched at handoff")
    scene.frame_set(153)
    moved=sum(x["projected_offset_153_px"]>=20. for x in report)
    if moved<5:
        raise RuntimeError("Not enough petals visibly separate from the lotus")
    scene.frame_set(165)
    lingering=max(x["projected_offset_165_px"] for x in report)
    print("V412_PROJECTED_DETACH_REPORT",report,flush=True)
    if lingering>16.:
        raise RuntimeError("Too much screen-space detachment remains at bird emergence")
    scene.frame_set(1)
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("V412 original 12-second timing modified")
    result={"real_carrier_meshes":N,
            "screen_visible_petals_at_153":moved,
            "maximum_detachment_offset_at_165_px":lingering,
            "unchanged_handoff_positions":[132,133],
            "unchanged_end_positions":[175,182],
            "original_swallow_rigs_untouched":N,
            "original_vertices_each":650,"frames":288,"fps":24,
            "per_petal_camera_projection":report}
    print("V412_CAMERA_LEGIBLE_PETALS_QA_PASS",result,flush=True)
    return result
