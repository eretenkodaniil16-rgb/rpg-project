#!/usr/bin/env python3
"""The Living Scroll V4: editable Blender 5.2 model pass.
Reuses the V3 2.5D backdrop; replaces flat hero objects with actual animated meshes.
Usage: blender -b --python-exit-code 1 --python living_scroll_v4/scene.py -- --smoke
"""
import argparse
import math
import random
import sys
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/"living_scroll_v3"))
import blender_scene as v3

FPS=24
END=288
RAND=random.Random(4401)
OUT=HERE/"renders"
OUT.mkdir(parents=True,exist_ok=True)

def coll(name):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def move(obj,name):
    c=coll(name)
    for old in list(obj.users_collection):old.objects.unlink(obj)
    c.objects.link(obj)
    return obj

def new_empty(name,collection,loc=(0,0,0)):
    obj=bpy.data.objects.new(name,None)
    coll(collection).objects.link(obj)
    obj.location=loc
    return obj

def em(name,color):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    n=m.node_tree.nodes
    n.clear()
    o=n.new("ShaderNodeOutputMaterial")
    e=n.new("ShaderNodeEmission")
    e.inputs["Color"].default_value=(*color,1)
    e.inputs["Strength"].default_value=1
    m.node_tree.links.new(e.outputs[0],o.inputs["Surface"])
    m.diffuse_color=(*color,1)
    return m

def principled(name,color,metal=0,rough=.75):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    p=mat.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Metallic"].default_value=metal
    p.inputs["Roughness"].default_value=rough
    return mat

def mesh_object(name,verts,faces,mat,group,parent=None):
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    coll(group).objects.link(ob)
    if parent:ob.parent=parent
    ob.data.materials.append(mat)
    return ob

def line(name,coords,mat,bevel,group,parent=None):
    cu=bpy.data.curves.new(name+"_curve","CURVE")
    cu.dimensions="3D"
    cu.bevel_depth=bevel
    cu.bevel_resolution=2
    cu.resolution_u=16
    poly=cu.splines.new("POLY")
    poly.points.add(len(coords)-1)
    for a,p in zip(poly.points,coords):a.co=(p[0],p[1],p[2],1)
    ob=bpy.data.objects.new(name,cu)
    coll(group).objects.link(ob)
    ob.data.materials.append(mat)
    if parent:ob.parent=parent
    return ob

def smooth_scale(obj,keys):
    for f,s in keys:
        obj.scale=(s,)*3
        obj.keyframe_insert("scale",frame=f)
    if obj.animation_data and obj.animation_data.action:
        pass

def lockeys(obj,keys):
    for f,p in keys:
        obj.location=p
        obj.keyframe_insert("location",frame=f)

def hide_v3_hero():
    old=bpy.data.objects.get("Lotus_Bloom")
    if old:old.hide_render=True
    for ob in list(bpy.data.objects):
        if ob.name.startswith("Swallow_") or ob.name in ("Left_Scroll_Roller","Right_Scroll_Roller"):
            bpy.data.objects.remove(ob,do_unlink=True)

def petals():
    group="V4_03_LOTUS"
    ivory=principled("LOTUS_Paper_Ivory",(.88,.78,.65),0,.91)
    white=principled("LOTUS_Pearl",(.97,.91,.79),0,.92)
    rose=em("LOTUS_Cinnabar_Tips",(.68,.20,.13))
    outline=em("LOTUS_Ink_Outline",(.14,.16,.16))
    vein=em("LOTUS_Delicate_Veins",(.44,.34,.28))
    core=em("LOTUS_Golden_Pollen",(.62,.39,.16))
    flower=new_empty("LOTUS_HERO_CTRL",group,(0,-2.45,.15))
    smooth_scale(flower,[(1,.001),(22,.001),(48,.51),(78,.95),(104,1.12),(138,1.04),(157,.94),(176,.02),(194,.001)])
    # Each petal is a curved 3D mesh with 17x9 vertices, outline and ink veins.
    for ring,(num,L,W,delay) in enumerate([(12,1.64,.55,0),(8,1.19,.47,12)]):
        for i in range(num):
            d=(2*math.pi*(i+.2+ring*.45)/num)+RAND.uniform(-.12,.12)
            if d>math.pi:d-=2*math.pi
            parent=new_empty("LOTUS_R%02d_P%02d_CTRL"%(ring,i),group)
            parent.parent=flower
            parent.location=(.11*math.cos(d),-.016*ring,.09*math.sin(d))
            verts=[]
            nseg,nwidth=17,9
            asym=RAND.uniform(-.29,.29)
            for j in range(nseg):
                s=j/(nseg-1)
                half=W*math.sin(math.pi*s)**.68*(.92+.09*s)
                for k in range(nwidth):
                    t=2*k/(nwidth-1)-1
                    x=half*t+.16*math.sin(4*s+asym)*s
                    y=-.13*math.sin(math.pi*s)*(1-t*t)-.17*s*s+.022*t*t
                    z=L*s+.10*math.sin(math.pi*s)*(t*t)
                    verts.append((x,y,z))
            faces=[]
            for j in range(nseg-1):
                for k in range(nwidth-1):
                    q=j*nwidth+k
                    faces.append((q,q+1,q+1+nwidth,q+nwidth))
            ob=mesh_object("LOTUS_R%02d_P%02d_MESH"%(ring,i),verts,faces,
                           white if ring==0 else ivory,group,parent)
            # Slight individual curvature; no identical-looking petals.
            ob.scale=(RAND.uniform(.83,1.17),1,RAND.uniform(.88,1.12))
            # Red nib on last 10% (small cut-out surface)
            tip=mesh_object("LOTUS_R%02d_P%02d_RED_TIP"%(ring,i),
                  [(-.075,-.19,L*.90),(.075,-.19,L*.90),(0,-.20,L*.995)],
                  [(0,1,2)],rose,group,parent)
            # Ink contour follows the outer edges of the curved surface.
            for sign in (-1,1):
                pts=[]
                for j in range(1,nseg):
                    s=j/(nseg-1)
                    x=sign*W*math.sin(math.pi*s)**.68+.08*math.sin(4*s+asym)*s
                    pts.append((x,-.14-.17*s*s,L*s+.10*math.sin(math.pi*s)))
                line("LOTUS_R%d_P%d_EDGE_%+d"%(ring,i,sign),pts,outline,.006,group,parent)
            line("LOTUS_R%d_P%d_VEIN"%(ring,i),
                 [(0,-.15,L*s/15) for s in range(1,15)],vein,.006,group,parent)
            for f,q in [(1,.08),(32+delay,.12),(60+delay,.42),(98+delay,1.0)]:
                parent.rotation_euler[1]=d*q
                parent.rotation_euler[0]=-.10*math.sin(f/24)+RAND.uniform(-.015,.015)
                parent.keyframe_insert("rotation_euler",frame=f)
    # pollen core and stamens
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28,ring_count=14,radius=.30)
    center=bpy.context.object
    move(center,group)
    center.name="LOTUS_Centre_Seedpod"
    center.parent=flower
    center.location=(0,-.10,0)
    center.scale=(1,.35,.85)
    center.data.materials.append(core)
    for i in range(26):
        a=2*math.pi*i/26
        x=.16*math.cos(a);z=.16*math.sin(a)
        r=.38+RAND.uniform(-.06,.07)
        line("LOTUS_STAMEN_%02d"%i,[(x,-.19,z),(r*math.cos(a),-.22,r*math.sin(a))],
             core,.007,group,flower)
    return flower

def cylinder(name,center,radius,depth,material,group,align="Z",parent=None,vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=center)
    ob=bpy.context.object
    move(ob,group)
    ob.name=name
    ob.data.materials.append(material)
    if align=="X":ob.rotation_euler[1]=math.pi/2
    if align=="Y":ob.rotation_euler[0]=math.pi/2
    if parent:
        # parent inverse for proper local coordinates
        loc=ob.location.copy()
        ob.parent=parent
        ob.location=loc-parent.location
    return ob

def pavilion(tag,origin,scale=1.0):
    """Front-visible layered Chinese pavilion instead of edge-on planar roof."""
    group="V4_05_ARCHITECTURE"
    timber=em("Pavilion_Ebony_Timber",(.070,.087,.082))
    roofing=em("Pavilion_Lacquered_Roof",(.090,.125,.120))
    under=em("Pavilion_Roof_Soffit",(.19,.17,.14))
    highlights=em("Pavilion_Bronze_Rim",(.45,.30,.18))
    root=new_empty("PAVILION_"+tag+"_CTRL",group,origin)
    def cube(name,location,dims,mat):
        bpy.ops.mesh.primitive_cube_add(size=1)
        o=bpy.context.object
        move(o,group)
        o.name=tag+"_"+name
        o.parent=root
        o.location=location
        o.scale=dims
        o.data.materials.append(mat)
        return o
    cube("Stone_Terrace",(0,0,-.07),(1.18,.55,.13),timber)
    for sx in (-.43,.43):
        for sy in (-.26,.22):
            cube("Pillar_%+d_%+d"%(int(sx*100),int(sy*100)),
                 (sx,sy,.40),(.066,.069,.84),timber)
    cube("Crossbeam",(0,-.24,.80),(1.08,.09,.12),under)
    for tier in (0,1):
        zz=.88+tier*.59
        w=1.48-tier*.21
        # Front fascia: broad shaded geometry facing -Y camera, not edge-on sheets.
        X=[-w*.54,-w*.46,-w*.20,0,w*.20,w*.46,w*.54]
        Z=[zz+.18,zz+.08,zz+.28,zz+.37,zz+.28,zz+.08,zz+.18]
        yf=-.40
        vertices=[]
        for x,z in zip(X,Z):
            vertices.extend([(x,yf,z-.15),(x,yf,z)])
        faces=[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(X)-1)]
        fascia=mesh_object(tag+"_Roof_Front_%d"%tier,vertices,faces,roofing,group,root)
        # Solid roof planes with overhanging eaves and raised central ridge.
        back=[(x,.34,z-.09) for x,z in zip(X,Z)]
        roof_verts=[(x,yf,z) for x,z in zip(X,Z)]+back
        roof_faces=[(j,j+1,j+1+len(X),j+len(X)) for j in range(len(X)-1)]
        mesh_object(tag+"_Roof_Slopes_%d"%tier,roof_verts,roof_faces,under,group,root)
        line(tag+"_Roof_Eaves_%d"%tier,
             [(x,yf-.015,z-.15) for x,z in zip(X,Z)],highlights,.015,group,root)
        if tier==0:
            cube("Upper_Story",(0,0,1.18),(.61,.39,.51),timber)
            for px in (-.28,.28):
                cube("Upper_Column_%s"%px,(px,-.24,1.16),(.05,.05,.42),highlights)
        else:
            line(tag+"_Roof_Ornament",[(0,-.43,zz+.37),(0,-.43,zz+.49)],
                 highlights,.016,group,root)
    root.scale=(scale,)*3
    smooth_scale(root,[(1,.001),(130,.001),(160,scale*.36),(185,scale),(288,scale)])
    return root

def birds():
    group="V4_06_BIRDS"
    ink=em("BIRD_Deep_Ink",(.025,.037,.041))
    ember=em("BIRD_Cinnabar_Head",(.60,.16,.10))
    for i in range(7):
        root=new_empty("BIRD_%02d_RIG"%i,group)
        body=mesh_object("BIRD_%02d_BODY"%i,
            [(-.18,0,0),(0,-.065,.095),(.22,0,0),(0,-.02,-.09)],
            [(0,1,3),(1,2,3)],ink,group,root)
        for side in (-1,1):
            wroot=new_empty("BIRD_%02d_WING_%s"%(i,"L" if side<0 else "R"),group)
            wroot.parent=root
            wing=mesh_object("BIRD_%02d_WING_SURFACE_%s"%(i,side),
              [(0,0,0),(.20*side,-.03,.12),(.70*side,-.03,.22),
               (.95*side,0,.06),(.40*side,.035,-.12)],
              [(0,1,4),(1,2,3,4)],ink,group,wroot)
            for f in range(1,289,6):
                wroot.rotation_euler[1]=side*(.16+.44*math.sin(f*.30+i*.95))
                wroot.keyframe_insert("rotation_euler",frame=f)
        mesh_object("BIRD_%02d_FORKED_TAIL"%i,
            [(-.06,.018,-.04),(-.32,.018,-.39),(0,.018,-.22),
             (.28,.018,-.42),(.06,.018,-.04)],
            [(0,1,2),(2,3,4)],ink,group,root)
        # Red mark gives birds an original consistent visual accent.
        mesh_object("BIRD_%02d_RED_CROWN"%i,
            [(-.03,-.08,.06),(.03,-.08,.06),(0,-.09,.12)],[(0,1,2)],
            ember,group,root)
        y=-2.75-.09*(i%3)
        dx=(i%4)*.57;dz=(i//4)*.35
        lockeys(root,[(1,(-1.8,-3.0,-.65)),(116+i*2,(-1.5+dx,y,-.9+dz)),
              (170+i*3,(-1.45+dx,y,.30+dz)),
              (221+i*2,(-.1+dx,y,1.25+dz)),
              (288,(2.45+dx,y,2.55+dz))])
        smooth_scale(root,[(1,.001),(112+i*3,.001),(148+i*3,.47),(210,.65),(288,.55)])

def scroll():
    group="V4_07_SCROLL"
    bronze=principled("Scroll_Aged_Brass",(.40,.24,.10),.73,.35)
    lacquer=principled("Scroll_Charcoal_Wood",(.08,.053,.035),.12,.23)
    vermilion=em("Scroll_Vermilion_Lining",(.57,.145,.09))
    reveal=new_empty("SCROLL_REVEAL_CTRL",group)
    smooth_scale(reveal,[(1,.001),(223,.001),(248,.30),(273,1),(288,1)])
    for z in (-4.82,4.82):
        cylinder("SCROLL_%s_ROLLER"%("TOP" if z>0 else "BOTTOM"),
                 (0,-2.08,z),.16,6.15,lacquer,group,"X",reveal,48)
        for sign in (-1,1):
            cylinder("SCROLL_CAP_%+d_%+d"%(int(z),sign),
                (sign*3.16,-2.08,z),.205,.15,bronze,group,"X",reveal,32)
            cylinder("SCROLL_INLAY_%+d_%+d"%(int(z),sign),
                (sign*2.76,-2.08,z),.169,.09,bronze,group,"X",reveal,32)
    # Thin dark fabric frame bands, avoid hiding image between them.
    for sign in (-1,1):
        # vertical vermilion piping
        mesh_object("SCROLL_SIDE_BORDER_%+d"%sign,
          [(sign*2.86,-2.02,-4.7),(sign*2.92,-2.02,-4.7),
           (sign*2.92,-2.02,4.7),(sign*2.86,-2.02,4.7)],
           [(0,1,2,3)],vermilion,group,reveal)
    # tassel ties: thin and slightly uneven
    for x in (-2.6,2.6):
        line("SCROLL_TASSELS_%+d"%int(x),
             [(x,-2.1,-4.83),(x+.06,-2.12,-5.14),(x-.03,-2.11,-5.49)],
             bronze,.025,group,reveal)

def mist():
    """Soft-edged spatial ink haze: fading in BOTH UV directions."""
    group="V4_04_ATMOSPHERE"
    for i,(y,z,opacity) in enumerate([(-1.75,-2.9,.22),(-2.08,-1.7,.14),(-2.40,1.3,.08)]):
        mat=bpy.data.materials.new("Mist_Tonal_Veil_%d"%i)
        mat.use_nodes=True
        nodes=mat.node_tree.nodes
        nodes.clear()
        out=nodes.new("ShaderNodeOutputMaterial")
        trans=nodes.new("ShaderNodeBsdfTransparent")
        white=nodes.new("ShaderNodeEmission")
        white.inputs["Color"].default_value=(.88,.86,.79,1)
        uv=nodes.new("ShaderNodeTexCoord")
        split=nodes.new("ShaderNodeSeparateXYZ")
        noise=nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=2.2
        noise.inputs["Detail"].default_value=2.0
        links=mat.node_tree.links
        links.new(uv.outputs["UV"],split.inputs["Vector"])
        links.new(uv.outputs["UV"],noise.inputs["Vector"])
        masks=[]
        for axis in ("X","Y"):
            sub=nodes.new("ShaderNodeMath");sub.operation="SUBTRACT";sub.inputs[1].default_value=.5
            ab=nodes.new("ShaderNodeMath");ab.operation="ABSOLUTE"
            mul2=nodes.new("ShaderNodeMath");mul2.operation="MULTIPLY";mul2.inputs[1].default_value=2
            ramp=nodes.new("ShaderNodeMapRange")
            ramp.clamp=True
            ramp.inputs["From Min"].default_value=.22 if axis=="X" else .10
            ramp.inputs["From Max"].default_value=1.0
            ramp.inputs["To Min"].default_value=1.0
            ramp.inputs["To Max"].default_value=0.0
            links.new(split.outputs[axis],sub.inputs[0])
            links.new(sub.outputs[0],ab.inputs[0])
            links.new(ab.outputs[0],mul2.inputs[0])
            links.new(mul2.outputs[0],ramp.inputs["Value"])
            masks.append(ramp.outputs["Result"])
        m1=nodes.new("ShaderNodeMath");m1.operation="MULTIPLY"
        m2=nodes.new("ShaderNodeMath");m2.operation="MULTIPLY"
        m3=nodes.new("ShaderNodeMath");m3.operation="MULTIPLY";m3.inputs[1].default_value=opacity
        mix=nodes.new("ShaderNodeMixShader")
        links.new(masks[0],m1.inputs[0]);links.new(masks[1],m1.inputs[1])
        links.new(m1.outputs[0],m2.inputs[0]);links.new(noise.outputs["Fac"],m2.inputs[1])
        links.new(m2.outputs[0],m3.inputs[0])
        links.new(m3.outputs[0],mix.inputs[0])
        links.new(trans.outputs[0],mix.inputs[1])
        links.new(white.outputs[0],mix.inputs[2])
        links.new(mix.outputs[0],out.inputs["Surface"])
        if hasattr(mat,"surface_render_method"):
            mat.surface_render_method="DITHERED"
        bpy.ops.mesh.primitive_plane_add(size=2,location=(0,y,z))
        o=bpy.context.object
        move(o,group)
        o.name="MIST_CARD_%02d"%i
        o.rotation_euler[0]=math.pi/2
        o.scale=(3.1,1.06,1)
        o.data.materials.append(mat)
        lockeys(o,[(1,(-.15,y,z)),(135,(.22,y,z+.08)),(288,(-.13,y,z))])

def configure(smoke=False):
    scene=bpy.context.scene
    # Dramatic push-in and a slower reveal, keyframed independent of sprite layers.
    cam=scene.camera
    cam.data.ortho_scale=8.85;cam.data.keyframe_insert("ortho_scale",frame=1)
    for f,v in [(65,8.85),(125,8.5),(180,9.45),(226,10.2),(265,11.9),(288,12.3)]:
        cam.data.ortho_scale=v;cam.data.keyframe_insert("ortho_scale",frame=f)
    # Add large soft light to physically modeled wood and metal.
    bpy.ops.object.light_add(type="AREA",location=(-3,-6,5))
    key=bpy.context.object;move(key,"V4_00_MASTER")
    key.name="KEY_Softbox"
    key.data.energy=930
    key.data.shape="DISK"
    key.data.size=10
    bpy.ops.object.light_add(type="AREA",location=(3,-4,0))
    fill=bpy.context.object;move(fill,"V4_00_MASTER")
    fill.data.energy=360;fill.data.size=7
    scene.render.resolution_x=360 if smoke else 720
    scene.render.resolution_y=640 if smoke else 1280
    scene.render.resolution_percentage=100
    scene.view_settings.view_transform="Standard"
    scene.render.film_transparent=False
    # Stable color management for comparison against V3.
    scene.display.shading.light="STUDIO" if hasattr(scene.display.shading,"light") else "STUDIO"

def validate():
    must=["LOTUS_HERO_CTRL","PAVILION_FOREGROUND_CTRL",
          "BIRD_00_RIG","SCROLL_REVEAL_CTRL","MIST_CARD_00"]
    missing=[x for x in must if bpy.data.objects.get(x) is None]
    if missing:raise RuntimeError("Missing V4 models: "+",".join(missing))
    lotus_meshes=[o for o in bpy.data.objects if o.name.startswith("LOTUS_R") and o.type=="MESH"]
    if len(lotus_meshes)<20:raise RuntimeError("3D lotus mesh regression")
    scene=bpy.context.scene
    if scene.render.fps!=24 or scene.frame_end!=288:raise RuntimeError("Timeline contract changed")
    print("V4_QA_OK",len(lotus_meshes),"lotus meshes; bird rigs=7; scene collections=",len(bpy.data.collections))

def build(smoke=False,full=False):
    v3.build(False,False)
    hide_v3_hero()
    petals()
    pavilion("FOREGROUND",(-1.66,-3.05,-2.70),.98)
    pavilion("MID",(1.51,-2.95,-1.49),.65)
    pavilion("FAR",(-1.25,-2.75,-.25),.36)
    birds()
    scroll()
    mist()
    configure(smoke)
    validate()
    scene=bpy.context.scene
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    save=HERE/"living_scroll_v4.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(save))
    frames=[1,48,88,115,146,175,216,275] if smoke else range(1,END+1)
    if smoke or full:
        for f in frames:
            scene.frame_set(f)
            scene.render.filepath=str(OUT/(("smoke_%03d"%f) if smoke else ("frame_%04d"%f)))
            bpy.ops.render.render(write_still=True)
    print("V4_BUILD_COMPLETE",save,len(frames) if smoke or full else 0)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--full",action="store_true")
    a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opt=p.parse_args(a)
    if opt.smoke and opt.full:p.error("Specify one render mode")
    build(opt.smoke,opt.full)
