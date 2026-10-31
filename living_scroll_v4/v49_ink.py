#!/usr/bin/env python3
"""V4.9 matte ink-wash petals and single-frame, z-fight-free petal handoff.

Non-destructive: original V4.8 shape keys, bird rigs, topology and timeline stay.
Runs after v48.build('probe') inside Blender 5.2.
"""
import math
import bpy

PALETTES = {
    "V44_Petal_Ivory_Outer": ((.79, .77, .69), (.70, .44, .46)),
    "V44_Petal_Blush_Middle": ((.83, .79, .72), (.73, .52, .53)),
    "V44_Petal_Cream_Inner": ((.85, .81, .71), (.81, .62, .60)),
}

def ramp(nodes, stops, name):
    item = nodes.new('ShaderNodeValToRGB')
    item.label = name
    colors = item.color_ramp
    colors.elements.remove(colors.elements[1])
    colors.elements[0].position = stops[0][0]
    colors.elements[0].color = (*stops[0][1], 1.0)
    for pos, value in stops[1:]:
        point = colors.elements.new(pos)
        point.color = (*value, 1.0)
    colors.interpolation = 'EASE'
    return item

def wash_petals(mat, base, tip):
    """UV-local watercolor pigment, not glossy plastic or toon outlines."""
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = .98
    bsdf.inputs['Metallic'].default_value = 0.
    if bsdf.inputs.get('Subsurface Weight'):
        bsdf.inputs['Subsurface Weight'].default_value = 0.
    if bsdf.inputs.get('Coat Weight'):
        bsdf.inputs['Coat Weight'].default_value = 0.
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    coord = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    links.new(coord.outputs['UV'], sep.inputs['Vector'])
    gradient = ramp(nodes, [(0., base), (.54, base), (1., tip)], 'Muted petal-edge pigment')
    links.new(sep.outputs['Y'], gradient.inputs['Fac'])
    blotch = nodes.new('ShaderNodeTexNoise')
    blotch.inputs['Scale'].default_value = 8.5
    blotch.inputs['Detail'].default_value = 4.
    blotch.inputs['Roughness'].default_value = .72
    links.new(coord.outputs['UV'], blotch.inputs['Vector'])
    pigment = ramp(nodes, [
        (0., (.52, .44, .43)), (.37, (.76, .72, .69)),
        (.62, (1., .97, .94)), (1., (1., 1., .99))
    ], 'Irregular watercolor density')
    links.new(blotch.outputs['Fac'], pigment.inputs['Fac'])
    multiply = nodes.new('ShaderNodeMixRGB')
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = .52
    links.new(gradient.outputs['Color'], multiply.inputs[1])
    links.new(pigment.outputs['Color'], multiply.inputs[2])
    links.new(multiply.outputs[0], bsdf.inputs['Base Color'])
    paper = nodes.new('ShaderNodeTexNoise')
    paper.inputs['Scale'].default_value = 92.
    paper.inputs['Detail'].default_value = 2.
    links.new(coord.outputs['UV'], paper.inputs['Vector'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .038
    bump.inputs['Distance'].default_value = .008
    links.new(paper.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    mat.diffuse_color = (*base, 1.)

def ink_carrier_material():
    name = 'V49_Matte_Wing_Pigment'
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    links = mat.node_tree.links
    output = nodes.new('ShaderNodeOutputMaterial')
    shader = nodes.new('ShaderNodeBsdfPrincipled')
    shader.inputs['Roughness'].default_value = 1.
    shader.inputs['Metallic'].default_value = 0.
    links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    obj = nodes.new('ShaderNodeObjectInfo')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 16.
    noise.inputs['Detail'].default_value = 3.
    coords = nodes.new('ShaderNodeTexCoord')
    links.new(coords.outputs['UV'], noise.inputs['Vector'])
    wash = ramp(nodes, [(0., (.48, .46, .43)), (.52, (.83, .80, .77)), (1., (1., 1., 1.))], 'Soot granulation')
    links.new(noise.outputs['Fac'], wash.inputs['Fac'])
    pigment = nodes.new('ShaderNodeMixRGB')
    pigment.blend_type = 'MULTIPLY'
    pigment.inputs[0].default_value = .38
    links.new(obj.outputs['Color'], pigment.inputs[1])
    links.new(wash.outputs['Color'], pigment.inputs[2])
    links.new(pigment.outputs[0], shader.inputs['Base Color'])
    return mat

def set_swap_visibility(obj, keyframes):
    for f, hidden in keyframes:
        obj.hide_render = hidden
        obj.keyframe_insert(data_path='hide_render', frame=f)

def build():
    scene = bpy.context.scene
    for name, (base, tip) in PALETTES.items():
        mat = bpy.data.materials.get(name)
        if mat is None:
            raise RuntimeError('Expected V4.4 watercolor-ready material: ' + name)
        wash_petals(mat, base, tip)
    material = ink_carrier_material()
    for i, petal_id in enumerate((0, 2, 4, 6, 8, 10, 12)):
        source = bpy.data.objects.get('V44_LOTUS_R0_P%02d' % petal_id)
        carrier = bpy.data.objects.get('V48_PETAL_TO_BIRD_%02d' % i)
        if source is None or carrier is None:
            raise RuntimeError('Missing source/carrier pair ' + str(i))
        if len(carrier.data.vertices) != 650 or carrier.data.shape_keys is None:
            raise RuntimeError('Original V4.8 morph topology was modified')
        carrier.data.materials.clear()
        carrier.data.materials.append(material)
        uv = carrier.data.uv_layers.get('V49_PETAL_UV') or carrier.data.uv_layers.new(name='V49_PETAL_UV')
        for polygon in carrier.data.polygons:
            for loop_id in polygon.loop_indices:
                vertex_id = carrier.data.loops[loop_id].vertex_index % 325
                uv.data[loop_id].uv = ((vertex_id % 13) / 12., (vertex_id // 13) / 24.)
        # Source is visible on frame 132; its evaluated clone takes over on 133.
        # No two coplanar copies are ever rendered in the same frame.
        set_swap_visibility(source, [(1, False), (132, False), (133, True), (288, True)])
        set_swap_visibility(carrier, [(1, True), (132, True), (133, False), (181, False), (182, True), (288, True)])
        for f, rgba in ((133, (.79, .77, .69, 1.)),
                        (145, (.64, .55, .50, 1.)),
                        (158, (.29, .28, .27, 1.)),
                        (171, (.078, .091, .087, 1.))):
            carrier.color = rgba
            carrier.keyframe_insert(data_path='color', frame=f)
    for frame in (132, 133, 153, 175, 182):
        scene.frame_set(frame)
        for i, p in enumerate((0, 2, 4, 6, 8, 10, 12)):
            src = bpy.data.objects['V44_LOTUS_R0_P%02d' % p]
            dst = bpy.data.objects['V48_PETAL_TO_BIRD_%02d' % i]
            if src.hide_render != (frame >= 133):
                raise RuntimeError('Source visibility QA failed for frame %d' % frame)
            if dst.hide_render != (frame == 132 or frame >= 182):
                raise RuntimeError('Carrier visibility QA failed for frame %d' % frame)
            if any(not math.isfinite(v) for v in (*dst.location, *dst.scale)):
                raise RuntimeError('Non-finite geometry at frame %d' % frame)
    scene.frame_set(1)
    result = {'wash_materials': len(PALETTES), 'topology_preserved': 7,
              'handoff_frame': 133, 'carriers': 7, 'frames': 288}
    print('V49_INK_WASH_AND_HANDOFF_QA_PASS', result, flush=True)
    return result
