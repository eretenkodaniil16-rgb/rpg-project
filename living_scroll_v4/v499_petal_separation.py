#!/usr/bin/env python3
"""Living Scroll V4.9.9: independent physical trajectories for seven detached petals.

Problem confirmed on authentic 360x640 Blender frames of V4.9.8: the entire
flower contracts while the 7 copied exterior laminae remain visually close to
the center. Thus "flower -> swallow" resembles a disappearing flower with birds
appearing elsewhere rather than real individual petals separating in space.

The seven already animated 650-vertex carriers retain their evaluated original
world positions and materials at the exact frame 132/133 handoff and return to
the UNMODIFIED animation by 175. Add seven out-of-phase radial lift trajectories
only between frames 138 and 170, with very modest forward camera parallax.
Existing animated bird rigs and their world locations, rest of lotus, source
mesh vertices, material dissolves, camera, and 288f/24fps edit remain untouched.
"""
import math
import bpy
from mathutils import Vector

BIRDS=7
START=133
STOP=175
# Staggered pulse per bird, with 7 divergent directions dictated by the
# world-space originally sampled petal centroid; do NOT invent new tracks.
PULSE=[(133,0.0),(138,.025),(145,.16),(153,.29),(159,.22),
       (165,.075),(170,.014),(175,0.0)]
AMPLITUDES=(1.00,.90,1.12,1.02,.88,1.07,.94)

def horizontal_direction(point,origin,ordinal):
    vec=Vector((point.x-origin.x,0.,point.z-origin.z))
    if vec.length<.01:
        angle=(ordinal/7.)*math.tau
        vec=Vector((math.cos(angle),0.,math.sin(angle)))
    vec.normalize()
    return vec

def build():
    scene=bpy.context.scene
    root=bpy.data.objects.get("V44_HERO_LOTUS_ROOT")
    if root is None:
        raise RuntimeError("V499 cannot find source lotus transform")
    originals={}
    for frame in (132,133,138,145,153,159,165,170,175,182):
        scene.frame_set(frame)
        originals[frame]=[
            bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].location.copy()
            for i in range(BIRDS)
        ]
    scene.frame_set(132)
    root_origin=root.matrix_world.translation.copy()
    directions=[horizontal_direction(originals[132][i],root_origin,i)
                for i in range(BIRDS)]
    report=[]
    for i in range(BIRDS):
        obj=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
        if len(obj.data.vertices)!=650:
            raise RuntimeError("Original 650-vertex lamina topology changed")
        axis=directions[i]
        # Original frame 132,133 and 175,182 positions are reconstructed
        # exactly. Never move bird rigs, their parent offsets or wing joints.
        for frame in (132,133):
            obj.location=originals[frame][i]
            obj.keyframe_insert(data_path="location",frame=frame)
        for frame,amplitude in PULSE:
            if frame==133:
                continue
            baseline=originals[frame][i]
            radial=.85*AMPLITUDES[i]*amplitude
            # Slight forward separation while the petal keeps the paper-wash;
            # later the existing V4.9.7 dither releases the shadowy geometry.
            forward=-.065*amplitude*(1+.10*(i%3))
            new=baseline+axis*radial+Vector((0.,forward,0.))
            obj.location=new
            obj.keyframe_insert(data_path="location",frame=frame)
        for frame in (175,182):
            obj.location=originals[frame][i]
            obj.keyframe_insert(data_path="location",frame=frame)
        report.append({"ordinal":i,"radial_direction":[round(axis.x,4),round(axis.z,4)],
                       "max_added_radial_offset":round(.85*AMPLITUDES[i]*.29,4)})

    for frame in (132,133,175,182):
        scene.frame_set(frame)
        for i in range(BIRDS):
            obj=bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i]
            if (obj.location-originals[frame][i]).length>1e-6:
                raise RuntimeError("V499 changed fixed handoff/landing position on frame %d"%frame)
    scene.frame_set(153)
    spreads=[(bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].location-
              originals[153][i]).length for i in range(BIRDS)]
    if min(spreads)<.19 or max(spreads)>.34:
        raise RuntimeError("V499 detach amplitude outside safe range "+str(spreads))
    scene.frame_set(165)
    remain=[(bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].location-
             originals[165][i]).length for i in range(BIRDS)]
    if max(remain)>.075:
        raise RuntimeError("V499 deviated too far from true bird paths at 165")
    scene.frame_set(1)
    if (scene.frame_end,scene.render.fps)!=(288,24):
        raise RuntimeError("V499 master 12-second/24fps timing mismatch")
    result={"animated_3d_petal_flight_paths":BIRDS,
            "physical_detach_peak_frame":153,
            "retains_exact_worldspace_at_132_133_175_182":True,
            "min_detach_at_153":round(min(spreads),4),
            "max_detach_at_153":round(max(spreads),4),
            "max_residual_offset_at_165":round(max(remain),4),
            "original_bird_rigs_unchanged":BIRDS,
            "original_lamina_vertices":650,
            "film_frames":288,"fps":24,"tracks":report}
    print("V499_PETAL_SEPARATION_QA_PASS",result,flush=True)
    return result
