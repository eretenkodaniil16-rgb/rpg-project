#!/usr/bin/env python3
"""V4.7 clean morph: a sparse and short ink stroke appears near each swallow.

This module edits the verified V4.6 scene without destroying original animated
objects. Grease Pencil v3 drawings follow each existing bird world trajectory.
All effects are authored at 24fps, with no post hoc smoothing or fake video.
"""
import math
import bpy

COLL="V47_15_INK_TRANSITION"

def smoothstep(x):
    t=max(0.0,min(1.0,x))
    return t*t*(3.0-2.0*t)

def lerp(a,b,t):
    return a+(b-a)*t

def build():
    scene=bpy.context.scene
    hidden={"large_brush":0,"old_gp":0,"fibers":0,"particles":0}
    # Keep legacy art and the 49 original Grease Pencil drawings editable,
    # but do not display the overgrown strokes in the film.
    for obj in bpy.data.objects:
        if obj.name.startswith("MORPH_BRUSH_STROKE_"):
            obj.hide_render=True
            hidden["large_brush"]+=1
        if obj.name=="GP43_Lotus_to_Swallow_Calligraphy":
            obj.hide_render=True
            hidden["old_gp"]+=1
        if obj.name.startswith("FIBER_"):
            obj.hide_render=True
            hidden["fibers"]+=1
        if obj.name.startswith("MORPH_PIGMENT_"):
            # Retain only a sparse third of the moving ink grains. This is
            # based on the original stable numerical ID, not iteration order.
            index=int(obj.name.rsplit("_",1)[1])
            if index%3!=0:
                obj.hide_render=True
                hidden["particles"]+=1
            else:
                # Replace the previous oversized particle scale curves.
                # All keyed values are world-space for the shared tiny mesh.
                for f,sz in (
                    (1,.0001),(125,.0001),(137,.010),
                    (150,.017),(163,.012),(176,.006),
                    (188,.0004),(205,.0001),(225,.0001),(288,.0001)
                ):
                    obj.scale=(sz,sz*.45,sz*1.1)
                    obj.keyframe_insert(data_path="scale",frame=f)
    if hidden["large_brush"]!=8 or hidden["old_gp"]!=1 or hidden["particles"]!=64:
        raise RuntimeError("Existing V4.6 morph hierarchy differs: "+str(hidden))
    collection=bpy.data.collections.get(COLL)
    if collection is None:
        collection=bpy.data.collections.new(COLL)
        scene.collection.children.link(collection)
    gp=bpy.data.grease_pencils.new("V47_Quiet_Ink_Calligraphy")
    mat=bpy.data.materials.new("V47_Charcoal_Stroke")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color=(.078,.084,.079,1)
    gp.materials.append(mat)
    layer=gp.layers.new("SEVEN_FLIGHT_STROKES")
    frames=[1,124]+list(range(126,200,2))+[200,288]
    POINTS=12
    BIRDS=7
    for f in frames:
        scene.frame_set(f)
        frame=layer.frames.new(f)
        if f in (1,124,200,288):
            # Explicit empty frames guarantee no residual marks at the ends.
            continue
        drawing=frame.drawing
        drawing.add_strokes([POINTS]*BIRDS)
        entered=smoothstep((f-130)/15)
        exit_fade=1-smoothstep((f-168)/20)
        opacity=entered*exit_fade
        advance=smoothstep((f-129)/47)
        for bird in range(BIRDS):
            rig=bpy.data.objects.get("BIRD_%02d_RIG"%bird)
            if rig is None:raise RuntimeError("Missing rig for stroke "+str(bird))
            # The rig inherits the existing cinematic path and V4.6 flock
            # offsets. Its actual world pose is sampled at this drawing frame.
            pos=rig.matrix_world.translation
            ang=bird*math.tau/BIRDS+.2
            source=(.19*math.cos(ang),-.3+pos.y*.90,.13+.19*math.sin(ang))
            target=(float(pos.x),float(pos.y)-.14,float(pos.z))
            center=(lerp(source[0],target[0],advance),
                    lerp(source[1],target[1],advance),
                    lerp(source[2],target[2],advance))
            vx=target[0]-source[0]
            vz=target[2]-source[2]
            length=math.hypot(vx,vz) or .001
            ux=vx/length;uz=vz/length
            arc_length=.18+.26*smoothstep((f-138)/20)
            stroke=drawing.strokes[bird]
            for j,p in enumerate(stroke.points):
                t=j/(POINTS-1)
                offset=(t-.82)*arc_length
                curl=.035*math.sin(t*math.pi)*math.sin((f-130)*.13+bird*1.71)
                p.position=(center[0]+ux*offset-uz*curl,
                            center[1]-.012*math.sin(math.pi*t),
                            center[2]+uz*offset+ux*curl)
                # Very narrow, tapering brush, not chunky black vectors.
                p.radius=.0067*(.19+.81*math.sin(math.pi*t)**.65)
                p.opacity=min(1.0,opacity*(.21+.22*math.sin(math.pi*t)))
    ob=bpy.data.objects.new("V47_Seven_Short_Handdrawn_Strokes",gp)
    collection.objects.link(ob)
    scene.frame_set(1)
    if ob.type!="GREASEPENCIL" or len(layer.frames)!=len(frames):
        raise RuntimeError("Grease Pencil temporal generation failed")
    if any(len(g.drawing.strokes)!=0 for g in layer.frames if g.frame_number in (1,124,200,288)):
        raise RuntimeError("Residual GP strokes at blank timeline endpoints")
    print("V47_MORPH_QA_PASS",hidden,"GP frames",len(frames),"7 swallows")
    return {"legacy_hidden":hidden,"grease_pencil_frames":len(frames),
            "visible_particles":32,"active_strokes":7}
