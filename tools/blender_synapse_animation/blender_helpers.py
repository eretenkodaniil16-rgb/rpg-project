from __future__ import annotations

from mathutils import Vector
import bpy


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def _set_socket(node, names, value) -> None:
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def material(name: str, color, roughness=0.42, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    _set_socket(bsdf, ["Base Color"], color)
    _set_socket(bsdf, ["Roughness"], roughness)
    _set_socket(bsdf, ["Metallic"], metallic)
    if emission is not None:
        _set_socket(bsdf, ["Emission Color", "Emission"], emission)
        _set_socket(bsdf, ["Emission Strength"], emission_strength)
    return mat


def assign(obj, mat) -> None:
    if getattr(obj.data, "materials", None) is not None:
        obj.data.materials.append(mat)


def smooth(obj) -> None:
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def uv_sphere(name, location, scale, mat, segments=40, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    smooth(obj)
    return obj


def cube(name, location, scale, mat, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel:
        modifier = obj.modifiers.new("Soft bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 4
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), vertices=28):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    smooth(obj)
    return obj


def torus(name, location, major_radius, minor_radius, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=40,
        minor_segments=10,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    smooth(obj)
    return obj


def text(name, body, location, size, mat, align="CENTER"):
    curve = bpy.data.curves.new(name + "_curve", "FONT")
    curve.body = body
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size
    curve.bevel_depth = 0.003
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    assign(obj, mat)
    return obj


def polyline(name, points, bevel_depth, mat):
    data = bpy.data.curves.new(name + "_curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = bevel_depth
    data.bevel_resolution = 3
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, xyz in zip(spline.points, points):
        point.co = (*xyz, 1.0)
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    assign(obj, mat)
    return obj


def look_at(obj, target=(0, 0, 0)) -> None:
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def key_location(obj, frame, location) -> None:
    obj.location = location
    obj.keyframe_insert(data_path="location", frame=frame)


def key_scale(obj, frame, scale) -> None:
    obj.scale = scale
    obj.keyframe_insert(data_path="scale", frame=frame)


def key_rotation(obj, frame, rotation) -> None:
    obj.rotation_euler = rotation
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_visible(obj, frame, visible) -> None:
    obj.hide_render = not visible
    obj.hide_viewport = not visible
    obj.keyframe_insert(data_path="hide_render", frame=frame)
    obj.keyframe_insert(data_path="hide_viewport", frame=frame)


def visibility_window(obj, start, end, total_frames) -> None:
    set_visible(obj, max(1, start - 1), False)
    set_visible(obj, start, True)
    set_visible(obj, end, True)
    if end < total_frames:
        set_visible(obj, end + 1, False)


def ease(obj) -> None:
    if obj.animation_data and obj.animation_data.action:
        for curve in obj.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "BEZIER"
                key.easing = "EASE_IN_OUT"
