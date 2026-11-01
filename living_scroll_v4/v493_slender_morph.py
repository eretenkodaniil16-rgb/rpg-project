#!/usr/bin/env python3
"""V4.9.3: slim swallow in-between and staggered scale handover.

Fixes visual QA of the actual seven-frame storyboard: broad, dark star-shaped
carriers at frame 165. The petal->carrier frame-132/133 world-space identity is
preserved exactly; the seven established bird rigs, flight paths, background,
and 288-frame timeline remain editable.

The 650-vertex lamina cannot become a fully rigged bird by itself. Instead it
becomes a narrow wingspan + fork-tail silhouette at reduced scale, then hands
off to the genuine articulated V4.6 small swallows.
"""
import math
import bpy

BIRDS=7

def ease(a,b,x):
    t=max(0.,min(1.,(x-a)/(b-a)))
    return t*t*(3.-2.*t)

def gaussian(x,mu,sigma):
    return math.exp(-((x-mu)/sigma)**2)

def slender_swallow_vertex(index,ordinal):
    """Continuous 25x13 by two-sheet topology: slim crescent wings and V tail."""
    band=index%325
    s=(band//13)/24.0
    u=2.0*(band%13)/12.0-1.0
    shell=index//325
    au=abs(u)
    chest=gaussian(s,.22,.20)
    wings=gaussian(s,.48,.090)
    tail=ease(.82,.99,s)
    # Wings are slender in the fore-aft direction: avoid the broad diamond.
    width=.037+.078*chest+.45*wings+.155*tail
    x=u*width
    swept=.17*(au**1.4)*wings
    notch=.28*(1-au)*tail
    z=.33-.85*s+swept+notch
    y=-.015-.016*(1.0-u*u)*chest-.009*(1-u*u)*wings
    y+=(.0035 if shell else -.0035)
    # Diversify flight attitudes without introducing an abrupt handoff.
    tilt=(ordinal-3)*.035
    return (x*math.cos(tilt)-z*math.sin(tilt),y,
            x*math.sin(tilt)+z*math.cos(tilt))

def animate_scale(obj):
    # All earlier frames retain an exact copy of the fully sized source petal.
    # Reduce the still-in-between carrier BEFORE its silhouette has become
    # charcoal, leaving the smaller V4.6 bird to complete the appearance.
    for f,scale in (
        (1,.001),(128,.001),(132,1.0),(133,1.0),
        (141,.91),(153,.66),(159,.44),(165,.29),
        (172,.14),(174,.105),(179,.023),(181,.001),
        (182,.001),(288,.001)
    ):
        obj.scale=(scale,)*3
        obj.keyframe_insert(data_path="scale",frame=f)
    # Prevent BEZIER auto-handle overshoot and unintended scale inversion.
    if obj.animation_data and obj.animation_data.action:
        try:
            action=obj.animation_data.action
            for fc in action.fcurves:
                if fc.data_path=="scale":
                    for p in fc.keyframe_points:
                        p.handle_left_type="AUTO_CLAMPED"
                        p.handle_right_type="AUTO_CLAMPED"
        except (AttributeError,TypeError):
            # Blender 5.2 layered Actions may not provide legacy fcurves.
            pass

def build():
    for ordinal in range(BIRDS):
        name="V48_PETAL_TO_BIRD_%02d"%ordinal
        obj=bpy.data.objects.get(name)
        if obj is None or len(obj.data.vertices)!=650:
            raise RuntimeError("V493 missing 650-vertex carrier "+name)
        shape=obj.data.shape_keys
        if not shape or "Ink_Wing" not in shape.key_blocks:
            raise RuntimeError("V493 missing animated destination "+name)
        key=shape.key_blocks["Ink_Wing"]
        values=[slender_swallow_vertex(i,ordinal) for i in range(650)]
        for i,coords in enumerate(values):
            key.data[i].co=coords
        if not all(math.isfinite(v) for vertex in values for v in vertex):
            raise RuntimeError("V493 nonfinite silhouette")
        xspan=max(p[0] for p in values)-min(p[0] for p in values)
        zspan=max(p[2] for p in values)-min(p[2] for p in values)
        if not (.80<xspan<1.40 and .65<zspan<1.40):
            raise RuntimeError("V493 invalid small bird silhouette extent "+str((xspan,zspan)))
        animate_scale(obj)
    scene=bpy.context.scene
    scene.frame_set(132)
    assert all(abs(bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].scale.x-1.)<1e-6 for i in range(BIRDS))
    scene.frame_set(165)
    assert all(.27<bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].scale.x<.31 for i in range(BIRDS))
    scene.frame_set(182)
    assert all(bpy.data.objects["V48_PETAL_TO_BIRD_%02d"%i].scale.x<=.002 for i in range(BIRDS))
    scene.frame_set(1)
    report={"narrow_bird_intermediate_count":BIRDS,
            "preserved_vertices_per_carrier":650,
            "carrier_scale_at_165":.29,
            "world_position_tracks_untouched":True,
            "real_swallow_rigs_untouched":True}
    print("V493_SLENDER_SWALLOW_TRANSITION_QA_PASS",report,flush=True)
    return report
