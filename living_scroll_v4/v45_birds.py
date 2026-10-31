#!/usr/bin/env python3
"""V4.5 Barn-swallow-inspired HERO models, designed for the real V4.4 scene.

Not a scan or a full avian musculoskeletal simulation. Seven individually
rigged stylized 3D birds with volumetric bodies, 2-segment animated wings,
12 primary and 8 secondary feather meshes per wing, forked tail streamers.
The silhouettes are grounded in Hirundo rustica reference anatomy.
"""
import math
import random
import bpy

SEED=455060
R=random.Random(SEED)
GROUP="V45_13_HERO_SWALLOWS"

def collection():
    obj=bpy.data.collections.get(GROUP)
    if obj is None:
        obj=bpy.data.collections.new(GROUP)
        bpy.context.scene.collection.children.link(obj)
    return obj

def add_object(name,mesh=None,parent=None):
    ob=bpy.data.objects.new(name,mesh)
    collection().objects.link(ob)
    if parent is not None:ob.parent=parent
    return ob

def material(name,color,rough=.78,metal=.0):
    m=bpy.data.materials.get(name)
    if m is None:
        m=bpy.data.materials.new(name)
        m.use_nodes=True
        p=m.node_tree.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value=(*color,1)
        p.inputs["Roughness"].default_value=rough
        p.inputs["Metallic"].default_value=metal
        p.inputs["Coat Weight"].default_value=.07
        m.diffuse_color=(*color,1)
    return m

def mesh(name,vertices,faces,material,root,face_materials=None,extra=None):
    data=bpy.data.meshes.new(name+"_mesh")
    data.from_pydata(vertices,[],faces)
    data.update()
    ob=add_object(name,data,root)
    data.materials.append(material)
    if extra:
        for mat in extra:data.materials.append(mat)
    if face_materials:
        for poly,index in zip(data.polygons,face_materials):poly.material_index=index
    for polygon in data.polygons:polygon.use_smooth=True
    return ob

def ellipsoid(name,parent,center,dimensions,mat,segments=16,rings=10):
    verts=[];faces=[]
    for j in range(rings+1):
        theta=math.pi*j/rings
        for i in range(segments):
            phi=2*math.pi*i/segments
            x=center[0]+dimensions[0]*math.sin(theta)*math.cos(phi)
            y=center[1]+dimensions[1]*math.sin(theta)*math.sin(phi)
            z=center[2]+dimensions[2]*math.cos(theta)
            verts.append((x,y,z))
    for j in range(rings):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments
            faces.append((a,b,b+segments,a+segments))
    return mesh(name,verts,faces,mat,parent)

def torso(name,root,dark,belly):
    """Tapered body with different material regions on ventral/dorsal surface."""
    rings=18;seg=24
    verts=[];faces=[];assignment=[]
    for j in range(rings+1):
        t=j/rings
        z=.22-.61*t
        shape=max(.02,math.sin(math.pi*(.08+.84*t)))**.68
        rx=.116*shape*(1-.15*t)
        ry=.104*shape*(1-.20*t)
        for k in range(seg):
            a=k*math.tau/seg
            verts.append((rx*math.cos(a),ry*math.sin(a)+.008,z))
    for j in range(rings):
        for k in range(seg):
            a=j*seg+k;b=j*seg+(k+1)%seg
            faces.append((a,b,b+seg,a+seg))
            phi=((k+.5)%seg)*math.tau/seg
            # camera faces negative y, pale ventral plumage
            assignment.append(1 if math.sin(phi)<-.36 and j>2 else 0)
    ob=mesh(name,verts,faces,dark,root,assignment,[belly])
    return ob

def feather(name,root,p0,p1,width,mat,curvature=.04):
    """Six-station tapered, cambered feather lamina, with a finite 3D profile."""
    verts=[];faces=[]
    longitudinal=8
    transversal=5
    dx=p1[0]-p0[0]
    dz=p1[2]-p0[2]
    norm=math.hypot(dx,dz) or 1
    perpendicular=(-dz/norm, dx/norm)
    for j in range(longitudinal):
        s=j/(longitudinal-1)
        w=width*(max(.003,1-s)**.66)*math.sin(math.pi*(s*.93+.035))**.52
        for k in range(transversal):
            u=2*k/(transversal-1)-1
            verts.append((
               p0[0]+dx*s+perpendicular[0]*u*w,
               p0[1]+(p1[1]-p0[1])*s+curvature*s*(1-s)*(1-u*u),
               p0[2]+dz*s+perpendicular[1]*u*w
            ))
    for j in range(longitudinal-1):
        for k in range(transversal-1):
            a=j*transversal+k
            faces.append((a,a+1,a+1+transversal,a+transversal))
    ob=mesh(name,verts,faces,mat,root)
    return ob

def make_bird(idx,mats):
    name="V45_BIRD_%02d"%idx
    root=bpy.data.objects.get("BIRD_%02d_RIG"%idx)
    if root is None:raise RuntimeError("V4.4 bird rig missing "+str(idx))
    dark,belly,wing,secondaries,throat,eye,beak=mats
    torso(name+"_TORSO",root,dark,belly)
    head=ellipsoid(name+"_HEAD",root,(0,-.002,.235),(.090,.082,.100),dark)
    # White upper breast, cinnamon throat, dark head and thin charcoal beak.
    patch=ellipsoid(name+"_VENTRAL_CHEST",root,(0,-.069,.085),(.066,.016,.120),belly,12,8)
    rufous=ellipsoid(name+"_CINNAMON_THROAT",root,(0,-.077,.193),(.058,.012,.052),throat,12,8)
    for side in (-1,1):
        eyeob=ellipsoid(name+"_EYE_%+d"%side,root,(side*.071,-.054,.259),(.012,.009,.013),eye,10,6)
        eyeob.rotation_euler[2]=side*.20
    mesh(name+"_TAPERED_BEAK",
         [(-.022,-.061,.31),(.022,-.061,.31),(0,-.089,.396), (0,-.051,.312)],
         [(0,1,2),(0,2,3),(1,3,2)],beak,root)
    # Tail: compact central fan + very long asymmetric tapered outer retrices.
    for side in (-1,1):
        for i in range(5):
            x=(i-2)*.041
            feather(name+"_TAIL_FAN_%+d_%d"%(side,i),root,
                    (x,-.008,-.26), (x+side*.020,-.015,-.54-R.uniform(0,.055)),
                    .038,dark,.013)
        streamer=feather(name+"_FORK_STREAMER_%+d"%side,root,
                    (side*.047,-.005,-.33),
                    (side*(.30+R.uniform(-.06,.05)),-.01,-.88-R.uniform(-.03,.14)),
                    .019,wing,.036)
    for side in (-1,1):
        code="L" if side<0 else "R"
        wingroot=bpy.data.objects.get("BIRD_%02d_WING_%s"%(idx,code))
        if wingroot is None:raise RuntimeError("Missing wing hinge "+name+code)
        # Preserve the proven V4 wing hinge animation; replace old mesh below it.
        shoulder=(side*.07,0,.08)
        mesh(name+"_PROXIMAL_%s"%code,
            [(0,-.028,.07),(side*.22,-.037,.165),(side*.57,-.016,.125),
             (side*.51,.031,-.085),(side*.22,.050,-.12)],
            [(0,1,4),(1,2,3,4)],dark,wingroot)
        hand=add_object(name+"_CARPOMETACARPAL_%s"%code,None,wingroot)
        hand.location=(side*.49,-.002,.075)
        # Secondary articulation, subtle flaps & sweep. Avoid 100% synchronous wings.
        for f in range(1,289,5):
            phase=idx*.73 + (0.24 if side>0 else 0.0)
            hand.rotation_euler[1]=side*(.07+.15*math.sin(f*.27+phase))
            hand.rotation_euler[0]=.05*math.cos(f*.20+phase)
            hand.keyframe_insert("rotation_euler",frame=f)
        for n in range(12):
            t=n/11
            origin=(side*(.025+t*.41),-.022,.018-.13*t)
            end=(side*(.19+t*(.59+.04*math.sin(idx*.7+n*.75))),-.035,
                 .205-.18*t + .055*math.sin(n*.92+idx*.64))
            width=.041*(1-.36*t)*(1+.13*math.sin(n*1.8+idx*.35))
            feather(name+"_PRIMARY_%s_%02d"%(code,n),hand,
                    origin,end,width,wing,.028+R.uniform(-.01,.02))
        for n in range(8):
            t=n/7
            origin=(side*(.07+.33*t),.008,-.015-.055*t)
            end=(side*(.15+.43*t),.035,-.205-.08*t + .015*math.sin(idx*.51+n))
            feather(name+"_SECONDARY_%s_%02d"%(code,n),wingroot,
                    origin,end,.039,secondaries,.016)
        # Narrow ink-sheened leading edge, visible at 360px and bird closeups.
        feather(name+"_LEADING_EDGE_%s"%code,wingroot,
             (side*.075,-.041,.075),(side*.57,-.029,.145),.048,dark,.025)
    # Subtle independent bank and pitch across flock.
    for frame in (1,118+idx*2,160+idx*2,198+idx*2,249,288):
        angle=.15*math.sin(frame*.039+idx*.91)+.065*((idx%3)-1)
        root.rotation_euler[1]=angle
        root.rotation_euler[0]=.13*math.sin(frame*.028+idx*.72)
        root.rotation_euler[2]=.13*math.sin(frame*.031+idx*.81)
        root.keyframe_insert("rotation_euler",frame=frame)
    return root

def build():
    # Hide only legacy bird geometry. Keep flight roots and keyed wing joints.
    legacy=bpy.data.collections.get("V4_06_BIRDS")
    if legacy is None:raise RuntimeError("Legacy bird collection missing")
    hidden=0
    for o in legacy.objects:
        if o.type in ("MESH","CURVE"):
            o.hide_render=True
            hidden+=1
    if hidden<28:raise RuntimeError("Unexpectedly few legacy bird meshes: "+str(hidden))
    mats=(
       material("V45_Iridescent_Indigo_Ink",(.036,.065,.076),.53,.13),
       material("V45_Buff_Ventral",(.66,.61,.51),.86,.0),
       material("V45_Flight_Feathers",(.059,.082,.090),.85,.020),
       material("V45_Secondary_Feathers",(.13,.15,.14),.91,.008),
       material("V45_Rufous_Throat",(.36,.15,.090),.89,0),
       material("V45_Glassy_Eye",(.013,.016,.021),.13,.0),
       material("V45_Fine_Beak",(.10,.070,.054),.82,0))
    rigs=[make_bird(i,mats) for i in range(7)]
    feathers=[o for o in collection().objects if o.name.startswith("V45_BIRD_") and
              ("PRIMARY" in o.name or "SECONDARY" in o.name)]
    if len(feathers)!=7*2*(12+8):
        raise RuntimeError("Hero swallow feather contract broken: "+str(len(feathers)))
    print("V45_HERO_SWALLOWS_QA",len(rigs),"rigs",len(feathers),
          "primary and secondary feather meshes; hidden old",hidden)
    return {"birds":len(rigs),"flight_feathers":len(feathers),"legacy_hidden":hidden}
