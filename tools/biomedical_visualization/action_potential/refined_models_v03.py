# Blender 4.x/5.x standalone model builder for action-potential animation
# Creates refined membrane, Na+/K+-ATPase, voltage-gated Na+ and K+ channels,
# and Na+/K+/Cl- ions. Run with Blender's Scripting workspace or:
# blender --background --python refined_models_v03.py

import bpy
import math
from mathutils import Vector

OUT_BLEND = "//action_potential_models_v03.blend"


def clean():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def mat(name, rgb, rough=.28, emission=0.0, transmission=0.0, subsurface=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb, 1.0)
    bs.inputs['Roughness'].default_value = rough
    if 'Transmission Weight' in bs.inputs:
        bs.inputs['Transmission Weight'].default_value = transmission
    elif 'Transmission' in bs.inputs:
        bs.inputs['Transmission'].default_value = transmission
    if 'Subsurface Weight' in bs.inputs:
        bs.inputs['Subsurface Weight'].default_value = subsurface
    elif 'Subsurface' in bs.inputs:
        bs.inputs['Subsurface'].default_value = subsurface
    if emission:
        if 'Emission Color' in bs.inputs:
            bs.inputs['Emission Color'].default_value = (*rgb, 1.0)
            bs.inputs['Emission Strength'].default_value = emission
        elif 'Emission' in bs.inputs:
            bs.inputs['Emission'].default_value = (*rgb, 1.0)
            bs.inputs['Emission Strength'].default_value = emission
    return m


M = {
    'head': mat('M_LipidHead', (0.95, 0.62, 0.20), .25, subsurface=.06),
    'tail': mat('M_LipidTail', (0.58, 0.32, 0.12), .40),
    'core': mat('M_MembraneCore', (0.08, 0.12, 0.20), .18, transmission=.18),
    'pump': mat('M_ATPase', (0.04, 0.44, 0.28), .25, transmission=.05, subsurface=.08),
    'pump_hi': mat('M_ATPaseHighlight', (0.10, 0.68, 0.44), .20, emission=.15),
    'na_ch': mat('M_NaChannel', (0.05, 0.40, 0.85), .22, transmission=.05),
    'na_hi': mat('M_NaGlow', (0.05, 0.72, 1.00), .16, emission=1.0),
    'k_ch': mat('M_KChannel', (0.46, 0.10, 0.72), .23, transmission=.05),
    'k_hi': mat('M_KGlow', (0.75, 0.22, 1.00), .16, emission=.8),
    'na': mat('M_NaIon', (0.04, 0.46, 1.00), .16, emission=.28),
    'k': mat('M_KIon', (0.64, 0.10, 0.96), .17, emission=.24),
    'cl': mat('M_ClIon', (0.18, 0.70, 0.22), .18, emission=.12),
    'red': mat('M_InactivationGate', (0.88, 0.08, 0.10), .20, emission=.30),
    'white': mat('M_White', (0.92, 0.96, 1.00), .35),
}


def smooth(o):
    if o.type == 'MESH':
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def sphere(name, loc, scale, material, seg=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    return smooth(o)


def cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(material)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = 5
    return o


def torus(name, loc, major, minor, material):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                    major_segments=64, minor_segments=18,
                                    location=loc, rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    return smooth(o)


def tube(name, coords, radius, material):
    c = bpy.data.curves.new(name + '_Curve', 'CURVE')
    c.dimensions = '3D'
    c.resolution_u = 4
    c.bevel_depth = radius
    c.bevel_resolution = 4
    s = c.splines.new('BEZIER')
    s.bezier_points.add(len(coords) - 1)
    for bp, co in zip(s.bezier_points, coords):
        bp.co = co
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'
    o = bpy.data.objects.new(name, c)
    bpy.context.collection.objects.link(o)
    o.data.materials.append(material)
    return o


def text(name, body, loc, size=.28, material=None):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(90), 0, 0))
    o = bpy.context.object
    o.name = name
    o.data.body = body
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    o.data.size = size
    o.data.extrude = .006
    o.data.bevel_depth = .002
    o.data.materials.append(material or M['white'])
    return o


def build_membrane():
    root = bpy.data.objects.new('Membrane_Root', None)
    bpy.context.collection.objects.link(root)
    cube('Membrane_Core', (0, .10, 0), (7.8, .07, .43), M['core'], .10).parent = root
    for i in range(48):
        x = -7.75 + i * .33
        wave = .025 * math.sin(i * .65)
        for side in (-1, 1):
            z = side * (.43 + wave)
            sphere(f'LipidHead_{i}_{side}', (x, 0, z), (.12, .10, .12), M['head'], 28, 16).parent = root
            inward = -1 if side > 0 else 1
            z1, z2 = z + inward*.17, z + inward*.35
            tube(f'LipidTailA_{i}_{side}', [(x-.035,0,z1),(x-.055,0,(z1+z2)/2),(x-.025,0,z2)], .018, M['tail']).parent = root
            tube(f'LipidTailB_{i}_{side}', [(x+.035,0,z1),(x+.055,0,(z1+z2)/2),(x+.025,0,z2)], .018, M['tail']).parent = root
    return root


def protein_lobe(name, loc, scale, material):
    o = sphere(name, loc, scale, material, 56, 32)
    s = o.modifiers.new('Subdivision', 'SUBSURF')
    s.levels = 1
    s.render_levels = 1
    return o


def build_atpase(x=-3.2):
    root = bpy.data.objects.new('NaK_ATPase_Root', None)
    bpy.context.collection.objects.link(root)
    lobes = [
        ('ATPase_Cytosolic_A', (x-.15,0,-.54), (.60,.34,.58), M['pump']),
        ('ATPase_Cytosolic_B', (x+.35,0,-.34), (.50,.31,.46), M['pump']),
        ('ATPase_Neck', (x+.02,0,.03), (.48,.29,.52), M['pump']),
        ('ATPase_OuterCap', (x-.03,0,.58), (.56,.32,.43), M['pump_hi']),
        ('ATPase_OuterSide', (x+.42,0,.38), (.38,.27,.43), M['pump']),
    ]
    for n, loc, scale, material in lobes:
        protein_lobe(n, loc, scale, material).parent = root
    sphere('ATPase_Cavity', (x+.08,-.23,.06), (.28,.08,.45), M['core']).parent = root
    for i, z in enumerate((-.46,-.24,-.02)):
        torus(f'ATPase_NaPocket_{i}', (x-.18+i*.18,-.27,z), .095,.022,M['na_hi']).parent = root
    for i, xx in enumerate((-.12,.16)):
        torus(f'ATPase_KPocket_{i}', (x+xx,-.27,.47), .105,.024,M['k_hi']).parent = root
    text('ATPase_Label', 'Na⁺/K⁺-АТФаза', (x+.08,-.65,-1.25), .30).parent = root
    text('ATPase_Stoich', '3 Na⁺ наружу • 2 K⁺ внутрь', (x+.08,-.65,-1.58), .21, M['pump_hi']).parent = root
    # Slow conformational rocking demonstrates continuous activity, not inactivation.
    for frame, angle, sx in [(1,-5,1.0),(35,7,1.04),(70,-4,.98),(105,5,1.02),(140,-5,1.0)]:
        root.rotation_euler[1] = math.radians(angle)
        root.scale.x = sx
        root.keyframe_insert('rotation_euler', frame=frame)
        root.keyframe_insert('scale', frame=frame)
    if root.animation_data and root.animation_data.action:
        for fc in root.animation_data.action.fcurves:
            try: fc.modifiers.new('CYCLES')
            except Exception: pass
    return root


def channel_shell(prefix, x, base, glow):
    root = bpy.data.objects.new(prefix + '_Root', None)
    bpy.context.collection.objects.link(root)
    left = [(x-.42,0,-.80),(x-.50,0,-.30),(x-.44,0,.26),(x-.31,0,.80)]
    right = [(2*x-a,b,c) for a,b,c in left]
    tube(prefix+'_LeftWall', left, .23, base).parent = root
    tube(prefix+'_RightWall', right, .23, base).parent = root
    for z in (-.48,.46): torus(prefix+f'_Filter_{z:+.2f}', (x,-.03,z), .23,.045,glow).parent = root
    sphere(prefix+'_TopCap', (x,.02,.73), (.40,.25,.22), base).parent = root
    sphere(prefix+'_BottomCap', (x,.02,-.73), (.40,.25,.22), base).parent = root
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=.085, depth=1.34, location=(x,.02,0))
    pore = bpy.context.object; pore.name=prefix+'_PoreGlow'; pore.data.materials.append(glow); pore.parent=root; smooth(pore)
    return root, pore


def build_na_channel(x=.35):
    root, pore = channel_shell('NaChannel', x, M['na_ch'], M['na_hi'])
    gl = sphere('Na_ActivationGate_L', (x-.12,-.18,-.49), (.14,.10,.10), M['na_hi']); gl.parent=root
    gr = sphere('Na_ActivationGate_R', (x+.12,-.18,-.49), (.14,.10,.10), M['na_hi']); gr.parent=root
    ball = sphere('Na_InactivationBall', (x,-.22,-.28), (.14,.11,.14), M['red']); ball.parent=root
    tether = tube('Na_InactivationTether', [(x,-.22,-.68),(x+.12,-.22,-.50),(x,-.22,-.34)], .025, M['red']); tether.parent=root
    text('Na_ChannelLabel', 'Na⁺-канал', (x,-.66,1.48), .29, M['na_hi']).parent=root
    # Demo keyframes: closed -> open -> inactivated -> recovered closed.
    states = [(1,.12,0.001),(60,.32,0.001),(120,.12,1.0),(180,.12,0.001)]
    for f, off, inact in states:
        gl.location.x=x-off; gr.location.x=x+off
        gl.keyframe_insert('location',frame=f); gr.keyframe_insert('location',frame=f)
        ball.scale=(.14,.11,.14) if inact>0.5 else (.0001,.0001,.0001)
        tether.scale=(1,1,1) if inact>0.5 else (.0001,.0001,.0001)
        ball.keyframe_insert('scale',frame=f); tether.keyframe_insert('scale',frame=f)
    return root


def build_k_channel(x=2.75):
    root, pore = channel_shell('KChannel', x, M['k_ch'], M['k_hi'])
    gl = sphere('K_Gate_L', (x-.13,-.18,-.45), (.15,.10,.11), M['k_hi']); gl.parent=root
    gr = sphere('K_Gate_R', (x+.13,-.18,-.45), (.15,.10,.11), M['k_hi']); gr.parent=root
    text('K_ChannelLabel', 'K⁺-канал', (x,-.66,1.48), .29, M['k_hi']).parent=root
    # Delayed demo: closed while Na opens, then open during repolarization/hyperpolarization.
    for f, off in [(1,.13),(60,.13),(120,.34),(180,.13)]:
        gl.location.x=x-off; gr.location.x=x+off
        gl.keyframe_insert('location',frame=f); gr.keyframe_insert('location',frame=f)
    return root


def build_ion(name, kind, loc, r):
    material={'Na':M['na'],'K':M['k'],'Cl':M['cl']}[kind]
    label={'Na':'Na⁺','K':'K⁺','Cl':'Cl⁻'}[kind]
    o=sphere(name,loc,(r,r,r),material,32,18)
    t=text(name+'_Label',label,(0,-.14,0),r*1.15); t.parent=o
    return o


def build_sample_ions():
    # Larger ions, deliberately sparse to avoid text/model overlap.
    for i,(x,z) in enumerate([(-6.5,1.35),(-5.6,1.72),(-4.8,1.25),(-2.0,1.65),(-.8,1.25),(1.5,1.65),(4.4,1.35),(5.6,1.70)]):
        build_ion(f'Na_Out_{i}','Na',(x,.28,z),.108)
    for i,(x,z) in enumerate([(-6.2,-1.35),(-5.2,-1.72),(-4.2,-1.28),(-2.0,-1.67),(-.8,-1.28),(1.4,-1.65),(4.0,-1.30),(5.2,-1.68)]):
        build_ion(f'K_In_{i}','K',(x,.28,z),.114)
    for i,(x,z) in enumerate([(-5.8,1.02),(-2.8,1.85),(3.4,1.83),(5.9,-1.82)]):
        build_ion(f'Cl_{i}','Cl',(x,.30,z),.110)


def lights_camera():
    bpy.ops.object.camera_add(location=(0,-22.5,2.8))
    cam=bpy.context.object; cam.data.lens=55; bpy.context.scene.camera=cam
    d=Vector((0,0,0))-cam.location; cam.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    for name,loc,energy,size,color in [
        ('Key',(-4,-7,7),1100,5,(.68,.82,1)),('Fill',(6,-5,3),700,4,(.46,.34,1)),
        ('Warm',(-1,-3,.3),420,3,(1,.55,.24)),('Rim',(0,2.5,7),950,3.5,(.16,.75,1))]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        L=bpy.context.object; L.name=name; L.data.energy=energy; L.data.size=size; L.data.color=color
        d=Vector((0,0,0))-L.location; L.rotation_euler=d.to_track_quat('-Z','Y').to_euler()


def build():
    clean()
    build_membrane()
    build_atpase(-3.2)
    build_na_channel(.35)
    build_k_channel(2.75)
    build_sample_ions()
    lights_camera()
    scene=bpy.context.scene
    scene.frame_start=1; scene.frame_end=180; scene.render.fps=30
    scene.world.color=(.004,.010,.028)
    try: scene.render.engine='BLENDER_EEVEE_NEXT'
    except Exception: pass
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print('Saved refined action-potential model pack:', OUT_BLEND)


build()
