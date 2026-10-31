#!/usr/bin/env python3
"""V4.4 Hero Lotus: anatomically informed Nelumbo-inspired, painterly PBR geometry.

Targets Blender 5.2.0. Creates 28 unique, thick, double-sided petals in three
staggered whorls, receptacle with seed cavities, 84 stamens, stem and sepals.
Animation: BudFold, WindFlex, InkDeparture shape keys per petal, with per-petal
time offsets. Not a scan or precise botanical reconstruction.
"""
import math
import random
import bpy

SEED=44041
RNG=random.Random(SEED)
COLLECTION="V44_12_HERO_LOTUS"

def collection():
    c=bpy.data.collections.get(COLLECTION)
    if c is None:
        c=bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(c)
    return c

def register(obj):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collection().objects.link(obj)
    return obj

def empty(name,parent=None):
    o=bpy.data.objects.new(name,None)
    collection().objects.link(o)
    o.parent=parent
    return o

def surface_material(name,base,tip):
    m=bpy.data.materials.new(name)
    m.use_nodes=True
    t=m.node_tree
    n=t.nodes
    p=n.get("Principled BSDF")
    p.inputs["Roughness"].default_value=.81
    p.inputs["Metallic"].default_value=0
    sub=p.inputs.get("Subsurface Weight")
    if sub is not None:sub.default_value=.23
    uv=n.new("ShaderNodeTexCoord")
    sep=n.new("ShaderNodeSeparateXYZ")
    t.links.new(uv.outputs["UV"],sep.inputs["Vector"])
    ramp=n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position=.18
    ramp.color_ramp.elements[0].color=(*base,1)
    ramp.color_ramp.elements[1].position=.90
    ramp.color_ramp.elements[1].color=(*tip,1)
    noise=n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=69
    noise.inputs["Detail"].default_value=3.8
    noise.inputs["Roughness"].default_value=.7
    texmix=n.new("ShaderNodeMixRGB")
    texmix.blend_type="MULTIPLY"
    texmix.inputs[0].default_value=.14
    t.links.new(sep.outputs["Y"],ramp.inputs["Fac"])
    t.links.new(ramp.outputs["Color"],texmix.inputs[1])
    t.links.new(noise.outputs["Color"],texmix.inputs[2])
    t.links.new(texmix.outputs[0],p.inputs["Base Color"])
    bump=n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.075
    bump.inputs["Distance"].default_value=.012
    t.links.new(noise.outputs["Fac"],bump.inputs["Height"])
    t.links.new(bump.outputs["Normal"],p.inputs["Normal"])
    m.diffuse_color=(*base,1)
    return m

def opaque(name,color,metal=0,rough=.7):
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    p=mat.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough
    p.inputs["Metallic"].default_value=metal
    mat.diffuse_color=(*color,1)
    return mat

def mesh(name,verts,faces,mat,parent=None,uvs=None):
    m=bpy.data.meshes.new(name+"_mesh")
    m.from_pydata(verts,[],faces)
    m.update()
    ob=bpy.data.objects.new(name,m)
    collection().objects.link(ob)
    ob.parent=parent
    m.materials.append(mat)
    if uvs:
        layer=m.uv_layers.new(name="PETAL_UV")
        for poly in m.polygons:
            for li in poly.loop_indices:
                index=m.loops[li].vertex_index
                layer.data[li].uv=uvs[index]
    for p in m.polygons:p.use_smooth=True
    return ob

def curve(name,points,mat,width,parent=None):
    cu=bpy.data.curves.new(name+"_path","CURVE")
    cu.dimensions="3D"
    cu.bevel_resolution=2
    cu.bevel_depth=width
    sp=cu.splines.new("POLY")
    sp.points.add(len(points)-1)
    for p,xyz in zip(sp.points,points):p.co=(*xyz,1)
    ob=bpy.data.objects.new(name,cu)
    collection().objects.link(ob)
    ob.parent=parent
    cu.materials.append(mat)
    return ob

def petal_shape(ring,index,theta,L,W,radius,jitter,parent,mat,ink):
    along=(math.cos(theta),math.sin(theta))
    tangent=(-along[1],along[0])
    nx=25
    ny=13
    verts=[]
    uvs=[]
    loops=[]
    # Shared coordinates for front/back of a curved lamina.
    twist=jitter[0]
    asym=jitter[1]
    edge_wave=jitter[2]
    camber=jitter[3]
    for shell in (0,1):
        for j in range(nx):
            s=j/(nx-1)
            r=radius+L*s
            spread=max(.001,math.sin(math.pi*s)**.63)*(1+.15*s)
            for k in range(ny):
                t=2*k/(ny-1)-1
                half=W*spread*(1+.10*math.sin(3*math.pi*s+jitter[4]))
                # Anatomically inspired paddle-shaped blade, subtly undulating edge.
                lateral=(half*t)+asym*s*s+twist*math.sin(math.pi*s)*t
                lateral+=edge_wave*math.sin((5+ring)*math.pi*s+.3*index)*abs(t)**4*s
                x=along[0]*r+tangent[0]*lateral
                z=.12+along[1]*r+tangent[1]*lateral
                # Outer whorls fall further back; center of lamina gently cups toward camera.
                y=(-.035*ring-.16*math.sin(math.pi*s)*(1-t*t)
                   -.19*s*s+camber*math.sin(2*math.pi*s)*t)
                thickness=(.020*(1-s)**.6+.004)*(.8+.2*(1-t*t))
                y+=(thickness if shell else -thickness)*.5
                verts.append((x,y,z))
                uvs.append(((t+1)*.5,s))
    block=nx*ny
    for shell in (0,1):
        base=shell*block
        for j in range(nx-1):
            for k in range(ny-1):
                a=base+j*ny+k
                b=a+ny
                face=(a,a+1,b+1,b)
                loops.append(face if shell==0 else face[::-1])
    # Seal all edges of the lamina.
    for k in range(ny-1):
        for j in (0,nx-1):
            a=j*ny+k; b=a+1
            loops.append((a,b,b+block,a+block))
    for j in range(nx-1):
        for k in (0,ny-1):
            a=j*ny+k; b=a+ny
            loops.append((a,b,b+block,a+block))
    ob=mesh("V44_LOTUS_R%d_P%02d"%(ring,index),verts,loops,mat,parent,uvs+uvs)
    # Keep actual geometry for detailed close-up and per-petal pose editing.
    base=ob.shape_key_add(name="Original_Sculpt",from_mix=False)
    folded=ob.shape_key_add(name="BudFold",from_mix=False)
    wind=ob.shape_key_add(name="WindFlex",from_mix=False)
    depart=ob.shape_key_add(name="InkDeparture",from_mix=False)
    for i,v in enumerate(verts):
        x,y,z=v
        s=uvs[i%block][1]
        u=uvs[i%block][0]*2-1
        # Bud: narrow/raise petals without collapsing their topology.
        folded.data[i].co=(x*(.39+.53*s),y+.30*s,
                           .12+(z-.12)*(.42+.45*s)+.18*s)
        wind.data[i].co=(x+.075*s*s*math.sin(3*s+theta),
                         y-.085*s*s*(1-u*u),
                         z+.10*s*s*math.cos(theta+4*s))
        depart.data[i].co=(x+.42*s*s*math.cos(theta+.72),
                           y-.23*s,
                           z+.42*s*s*math.sin(theta+.72))
    delay=(index*5+ring*8)%17
    for f,v in ((1,1),(32+delay,1),(67+delay,.75),(88+delay,.22),
                (111+delay,0),(288,0)):
        folded.value=v;folded.keyframe_insert(data_path="value",frame=f)
    for f,v in ((1,0),(99,0),(120,.36),(138,0),
                (150,.53),(167,0),(288,0)):
        wind.value=v;wind.keyframe_insert(data_path="value",frame=f)
    for f,v in ((1,0),(125,0),(141,.14),(158,.71),(173,1),(288,1)):
        depart.value=v;depart.keyframe_insert(data_path="value",frame=f)
    # Edge ink tracing and primary veins follow shape via static curves only:
    # avoid crisp cartoon outlines along each and every edge.
    if (ring+index)%3==0:
        along_len=[verts[j*ny+(ny//2)] for j in range(1,nx-1,2)]
        linepoints=[(x,y-.008,z) for x,y,z in along_len]
        line=curve("V44_LOTUS_MIDVEIN_R%d_%02d"%(ring,index),linepoints,ink,.0038,parent)
        line.scale=(.93,1,.93)
    return ob

def seed_receptacle(root,green,dark,anther):
    # Convex receptacle of Nelumbo-like blossom with central seed pits.
    vertices=[]
    faces=[]
    N=40;M=9
    for j in range(M):
        t=j/(M-1)
        r=.035+.26*t
        y=-.35+.12*t*t
        for i in range(N):
            a=2*math.pi*i/N
            vertices.append((r*math.cos(a),y,.12+r*math.sin(a)))
    for j in range(M-1):
        for i in range(N):
            a=j*N+i
            b=j*N+(i+1)%N
            faces.append((a,b,b+N,a+N))
    cup=mesh("V44_SEED_RECEPTACLE",vertices,faces,green,root)
    # Receptacle seed wells: small dark depressed ovals; deliberately nonuniform.
    for i in range(23):
        ang=2*math.pi*i/23+RNG.uniform(-.10,.10)
        rad=(.02+.18*math.sqrt((i+.5)/23))
        x=rad*math.cos(ang);z=.12+rad*math.sin(ang)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=10,ring_count=6,radius=1)
        dot=register(bpy.context.object)
        dot.name="V44_SEED_PIT_%02d"%i
        dot.parent=root
        dot.location=(x,-.363+rad*.32,z)
        dot.scale=(.012, .0045,.011)
        dot.data.materials.append(dark)
    return cup

def stamens(root,filament,anther):
    for i in range(84):
        a=(2*math.pi*i/84)+RNG.uniform(-.055,.055)
        radius=.23+RNG.uniform(.0,.06)
        length=.38+RNG.uniform(-.07,.13)
        x0=radius*.57*math.cos(a)
        z0=.12+radius*.57*math.sin(a)
        x1=(radius+length*.48)*math.cos(a)
        z1=.12+(radius+length*.45)*math.sin(a)
        points=[(x0,-.27,z0),((x0+x1)*.5,-.38,z0*.54+z1*.46),(x1,-.29,z1)]
        curve("V44_STAMEN_%03d"%i,points,filament,.0032,root)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=6,radius=1)
        tip=register(bpy.context.object)
        tip.name="V44_ANTHER_%03d"%i
        tip.parent=root
        tip.location=(x1,-.295,z1)
        tip.scale=(.020,.009,.031)
        tip.rotation_euler[1]=a
        tip.data.materials.append(anther)

def build(parent):
    materials=[
        surface_material("V44_Petal_Ivory_Outer",(.90,.86,.76),(.88,.47,.48)),
        surface_material("V44_Petal_Blush_Middle",(.95,.88,.79),(.88,.57,.59)),
        surface_material("V44_Petal_Cream_Inner",(.95,.90,.82),(.94,.72,.69))]
    ink=opaque("V44_Muted_Vein",(.35,.25,.24))
    pollen=opaque("V44_Stamen_Gold",(.70,.51,.21),rough=.88)
    anther=opaque("V44_Anther_Amber",(.73,.37,.19),rough=.78)
    green=opaque("V44_Olive_Receptacle",(.50,.54,.27),rough=.94)
    dark=opaque("V44_Seed_Depression",(.19,.21,.14),rough=.92)
    root=empty("V44_HERO_LOTUS_ROOT",parent)
    root.location=(0,-.08,.01)
    # Entire geometry is explicitly editable and built deterministically.
    counts=(13,9,6)
    sizes=((1.68,.41,.24),(1.20,.36,.18),(.77,.27,.11))
    for ring,count in enumerate(counts):
        L,W,radius=sizes[ring]
        for i in range(count):
            a=2*math.pi*(i+.20*ring)/count+RNG.uniform(-.12,.12)
            jitter=(RNG.uniform(-.14,.14), RNG.uniform(-.055,.055),
                    RNG.uniform(-.09,.09),RNG.uniform(-.06,.06),RNG.uniform(-2,2))
            petal_shape(ring,i,a,L*RNG.uniform(.91,1.08),
                        W*RNG.uniform(.83,1.12),radius,jitter,root,materials[ring],ink)
    seed_receptacle(root,green,dark,anther)
    stamens(root,pollen,anther)
    # Individual small sepals at the flower's base.
    for i in range(6):
        a=i*math.pi/3+.18
        points=[]
        for j in range(9):
            s=j/8
            r=.18+.39*s
            w=.12*math.sin(math.pi*s)
            points.extend([(r*math.cos(a)-w*math.sin(a),.015,.12+r*math.sin(a)+w*math.cos(a))])
        curve("V44_GREEN_SEPAL_%02d"%i,points,green,.012,root)
    return {"petals":sum(counts),"stamens":84,"seed_pits":23,"root":root.name}
