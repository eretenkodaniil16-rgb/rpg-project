#!/usr/bin/env python3
"""Living Scroll V4.3: Grease Pencil v3 calligraphy and actual petal mesh deformation.

Compatibility: pinned Blender 5.2.0. Reuses tested V4.2.1 geometry/art.
This is code-generated animation, not text-to-video synthesis.
Usage: blender -b --python-exit-code 1 --python living_scroll_v4/v43.py -- --smoke
"""
from pathlib import Path
import argparse
import math
import sys
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import v42

OUT=HERE/"renders_v43"
OUT.mkdir(parents=True,exist_ok=True)
FPS=24
LAST=288

def smootherstep(x):
    t=max(0.0,min(1.0,x))
    return t*t*t*(t*(t*6-15)+10)

def ink_washed_petals():
    """Variation in shader pigment density, rather than a flat CG plastic surface."""
    changed=0
    for name,lo,hi in [
        ("LOTUS_Paper_Ivory",(.77,.68,.56,1),(.96,.88,.75,1)),
        ("LOTUS_Pearl",(.84,.76,.63,1),(.995,.95,.83,1))
    ]:
        mat=bpy.data.materials.get(name)
        if mat is None or not mat.use_nodes:
            raise RuntimeError("Missing shaded petal material: "+name)
        nodes=mat.node_tree.nodes
        principled=nodes.get("Principled BSDF")
        if principled is None:
            raise RuntimeError("Missing Principled shader for "+name)
        noise=nodes.new("ShaderNodeTexNoise")
        noise.name="V43_Handmade_Grain"
        noise.inputs["Scale"].default_value=7.6
        noise.inputs["Detail"].default_value=3.5
        noise.inputs["Roughness"].default_value=.71
        ramp=nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position=.22
        ramp.color_ramp.elements[0].color=lo
        ramp.color_ramp.elements[1].position=.78
        ramp.color_ramp.elements[1].color=hi
        mat.node_tree.links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
        mat.node_tree.links.new(ramp.outputs["Color"],principled.inputs["Base Color"])
        changed+=1
    return changed

def shape_key_petals():
    """Deform mesh vertices of all 20 actual 3D petals (not a transparency fade)."""
    count=0
    for ob in list(bpy.data.objects):
        if ob.type!="MESH" or not ob.name.startswith("LOTUS_R") or not ob.name.endswith("_MESH"):
            continue
        if ob.data.shape_keys is not None:
            continue
        basis=ob.shape_key_add(name="V43_Original_Petal",from_mix=False)
        fold=ob.shape_key_add(name="V43_Into_Ink_Feather",from_mix=False)
        coords=[(float(v.co.x),float(v.co.y),float(v.co.z)) for v in ob.data.vertices]
        length=max(max(z for _,_,z in coords),.001)
        index=count
        for i,(x,y,z) in enumerate(coords):
            s=max(0.0,z/length)
            phase=(index%5-2)*.13
            # Fold and stretch the petal tip as it follows the departing ink.
            fold.data[i].co=(
                x*(1-.28*s)+.13*math.sin(math.pi*s+phase)*s,
                y-.18*s*s+.025*math.sin(4*s+phase),
                z*(1+.13*s)+.19*math.sin(math.pi*s)*s
            )
        for f,value in [(1,0),(118,0),(137,.16),(151,.56),(170,1.0),(190,1.0)]:
            fold.value=value
            fold.keyframe_insert(data_path="value",frame=f)
        count+=1
    if count!=20:
        raise RuntimeError("V4.3 requires 20 3D petals, got %d"%count)
    return count

def stroke_point(i,j,n,frame):
    """Continuous geometric interpolation of calligraphy between lotus and bird wing.
    Each of fourteen strokes contains the same ordered vertices across keyframes.
    """
    t=j/(n-1)
    a=2*math.pi*(i+.27)/14.0
    radius=.23+1.17*t
    original_x=math.cos(a)*radius+.080*math.sin(t*math.pi*2+i)*t
    original_z=.17+math.sin(a)*radius*.90
    # Seven birds, two calligraphy strokes per bird (left and right wing).
    bird=i%7
    wing= -1 if i<7 else 1
    cx=-1.49+(bird%4)*.56 + (bird%4-1.5)*.22
    cz=.22+(bird//4)*.42
    target_x=cx+wing*(.08+1.05*t)
    target_z=cz+.10+.29*math.sin(math.pi*t)-.12*t + .038*math.sin(5*t+bird)
    blend=smootherstep((frame-132)/44)
    x=(1-blend)*original_x+blend*target_x
    z=(1-blend)*original_z+blend*target_z
    x+=.040*math.sin(frame*.12+i)*math.sin(math.pi*t)*blend
    y=-3.36-.04*math.sin(t*math.pi)
    return x,y,z

def make_grease_pencil():
    """Actual Grease Pencil v3 strokes through the supported Blender 5.2 data API."""
    if bpy.app.version < (5,0,0):
        raise RuntimeError("This build requires Blender 5.x Grease Pencil v3.")
    gp=bpy.data.grease_pencils.new("LivingScroll_GP43_Calligraphy")
    mat=bpy.data.materials.new("GP43_Carbon_Ink")
    bpy.data.materials.create_gpencil_data(mat)
    mat.grease_pencil.color=(.055,.063,.059,1.0)
    gp.materials.append(mat)
    layer=gp.layers.new("LOTUS_TO_WINGS")
    frames=[1]+list(range(118,209,2))+[210,288]
    sample_points=18
    for f in frames:
        frame=layer.frames.new(f)
        drawing=frame.drawing
        if f in (1,288):continue
        drawing.add_strokes([sample_points]*14)
        emergence=smootherstep((f-118)/18)
        departure=1.0-smootherstep((f-179)/28)
        alpha=emergence*departure
        for i in range(14):
            stroke=drawing.strokes[i]
            for j,p in enumerate(stroke.points):
                t=j/(sample_points-1)
                p.position=stroke_point(i,j,sample_points,f)
                # tapered brush tips; discreet initial lines, strongest at 150-170
                p.radius=.0085*(.27+.90*math.sin(math.pi*t)**.58)*(1+.16*math.sin(i*4.7))
                p.opacity=min(1.0,alpha*(.42+.32*math.sin(math.pi*t)))
    ob=bpy.data.objects.new("GP43_Lotus_to_Swallow_Calligraphy",gp)
    collection=bpy.data.collections.get("V43_11_GREASE_PENCIL")
    if collection is None:
        collection=bpy.data.collections.new("V43_11_GREASE_PENCIL")
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(ob)
    return ob,len(frames)

def subtle_bird_feathering():
    """Slightly stretch and soften the animated 3D wing silhouettes.
    Mesh remains editable and rigged; the GP strokes carry painterly variation.
    """
    changed=0
    for ob in bpy.data.objects:
        if ob.type=="MESH" and "WING_SURFACE" in ob.name and ob.name.startswith("BIRD_"):
            for v in ob.data.vertices:
                if abs(v.co.x)>.18:
                    v.co.z+=.075*math.sin(3.2*abs(v.co.x)+changed*.9)
                    v.co.y+=.03*math.sin(4.4*abs(v.co.x)+changed*.7)
            changed+=1
    if changed!=14:
        raise RuntimeError("Bird wing regression: expected 14 wings, got %d"%changed)
    return changed

def validate(petals,wing_count,gp_obj,n):
    if gp_obj.type!="GREASEPENCIL" or len(gp_obj.data.layers)!=1:
        raise RuntimeError("Grease Pencil v3 datablock mismatch")
    if len(gp_obj.data.layers[0].frames)!=n:
        raise RuntimeError("Missing Grease Pencil temporal strokes")
    if petals!=20 or wing_count!=14:
        raise RuntimeError("Morph shape contract invalid")
    for f in (120,142,158,176,196):
        if not any(g.frame_number<=f for g in gp_obj.data.layers[0].frames):
            raise RuntimeError("Missing calligraphy keyframe at "+str(f))
    print("V43_QA_PASS",petals,"petal mesh shape keys;",wing_count,
          "wings;",n,"Grease Pencil v3 drawings")

def main(smoke=False,full=False,probe=False):
    if probe and (smoke or full):
        raise RuntimeError("Probe cannot render")
    v42.v4.build(False,False)
    v42.spread_flock()
    v42.scatter_to_birds()
    v42.add_sky_ink_particles()
    mats=ink_washed_petals()
    petals=shape_key_petals()
    wings=subtle_bird_feathering()
    gp,n=make_grease_pencil()
    validate(petals,wings,gp,n)
    scene=bpy.context.scene
    scene.frame_set(1)
    scene.render.resolution_x=360 if smoke else 720
    scene.render.resolution_y=640 if smoke else 1280
    bpy.ops.file.pack_all()
    path=HERE/"living_scroll_v43.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    if probe:
        print("V43_PROBE_OK",path)
        return
    frames=[88,139,155,175,216,275] if smoke else range(1,LAST+1)
    if smoke or full:
        for f in frames:
            scene.frame_set(f)
            scene.render.filepath=str(OUT/(("smoke_%03d"%f) if smoke else ("frame_%04d"%f)))
            bpy.ops.render.render(write_still=True)
    print("V43_RENDER_COMPLETE",len(frames),path)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--probe",action="store_true")
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--full",action="store_true")
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opts=p.parse_args(args)
    if sum((opts.smoke,opts.full,opts.probe))!=1:
        p.error("Choose exactly one of --probe, --smoke or --full")
    main(opts.smoke,opts.full,opts.probe)
