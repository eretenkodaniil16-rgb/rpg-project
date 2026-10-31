#!/usr/bin/env python3
"""V4.9 shape correction: petal lamina becomes a swallow-like intermediate.

V4.8 ended in a tapered feather strip without head, paired wings, or a tail.
Here the same seven 650-vertex carrier meshes retain their lotus basis but their
Ink_Wing shape keys become a low-detail bird-like outline with a forked tail.
It is an artistic in-between, not a biologically exact swallow reconstruction.
"""
import math
import bpy

BIRDS=7

def smooth(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3.-2.*t)

def destination(index,ordinal):
    block=325
    longitudinal=(index%block)//13
    transversal=(index%block)%13
    shell=index//block
    s=longitudinal/24.
    u=2.*transversal/12.-1.
    # A compact head -> neck -> breast -> full wing span -> forked tail.
    # Two lobes in the wings are controlled by the same original lamina grid.
    shoulder=math.exp(-((s-.43)/.17)**2)
    chest=math.exp(-((s-.17)/.15)**2)
    fork=math.exp(-((s-.95)/.11)**2)
    halfwidth=.032+.097*chest+.68*shoulder+.18*fork
    x=u*halfwidth
    wing_sweep=.075*(abs(u)**1.4)*shoulder
    # Fork center returns forward; tail edges project backward in flight.
    notch=.34*(1.-abs(u))*(smooth(.76,.99,s))
    z=.34-.94*s+wing_sweep+notch
    # Subtle camber/ink-shell thickness, not two intersecting planar faces.
    y=-.018-.025*chest*(1-u*u)-.018*shoulder*(1-u*u)
    y+=(.004 if shell else -.004)
    angle=(ordinal-3)*.045
    return (x*math.cos(angle)-z*math.sin(angle), y,
            x*math.sin(angle)+z*math.cos(angle))

def retime_flock():
    """Delay separate visible birds until their petal carriers are nearly ink.

    Keep all animated 3D flight paths and individual scale factors from V4.6;
    re-key only the scale channel. Each bird becomes prominent near the end
    of its own physical petal trajectory, rather than flying early in parallel.
    """
    from v46_birds import SCALE_FACTORS
    scene=bpy.context.scene
    for i in range(BIRDS):
        rig=bpy.data.objects.get("BIRD_%02d_RIG"%i)
        if rig is None:
            raise RuntimeError("Missing original flight rig "+str(i))
        factor=SCALE_FACTORS[i]
        for f,normalized in (
                (1,.001),(112+3*i,.001),(148+3*i,.001),
                (159+i,.001),(168+i,.24),(178+i//2,.47),
                (210,.65),(288,.55)):
            scale=max(.0001,normalized*factor)
            rig.scale=(scale,scale,scale)
            rig.keyframe_insert(data_path="scale",frame=f)
    scene.frame_set(155)
    if any(max(bpy.data.objects["BIRD_%02d_RIG"%i].scale)>.025 for i in range(BIRDS)):
        raise RuntimeError("Independent birds appear too early")
    scene.frame_set(185)
    if any(max(bpy.data.objects["BIRD_%02d_RIG"%i].scale)<.10 for i in range(BIRDS)):
        raise RuntimeError("Retimed flock did not emerge")
    scene.frame_set(1)
    return {'flight_paths_preserved':BIRDS,'retimed_bird_scale_tracks':BIRDS}

def build():
    collection=[]
    for i in range(BIRDS):
        carrier=bpy.data.objects.get('V48_PETAL_TO_BIRD_%02d'%i)
        if carrier is None or len(carrier.data.vertices)!=650:
            raise RuntimeError('Missing source 650-vertex morph carrier '+str(i))
        keys=carrier.data.shape_keys
        if keys is None or 'Ink_Wing' not in keys.key_blocks:
            raise RuntimeError('Missing destination shape key '+str(i))
        wing=keys.key_blocks['Ink_Wing']
        points=[destination(idx,i) for idx in range(650)]
        for idx,point in enumerate(points):
            wing.data[idx].co=point
        xs=[v[0] for v in points]
        zs=[v[2] for v in points]
        if max(xs)-min(xs)<1.0 or max(zs)-min(zs)<.55:
            raise RuntimeError('Intermediate bird silhouette collapsed')
        if not all(math.isfinite(v) for point in points for v in point):
            raise RuntimeError('Invalid final vertex coordinate')
        collection.append(carrier.name)
    timing=retime_flock()
    scene=bpy.context.scene
    scene.frame_set(165)
    if any(bpy.data.objects[n].data.shape_keys.key_blocks['Ink_Wing'].value<.99 for n in collection):
        raise RuntimeError('V4.8 timeline no longer finishes intermediate silhouette by 165')
    scene.frame_set(1)
    print('V49_FORKED_SWALLOW_INBETWEEN_QA_PASS',len(collection),flush=True)
    return {'new_full_span_forked_silhouettes':len(collection),
            'retained_carrier_vertices_per_bird':650, **timing}
