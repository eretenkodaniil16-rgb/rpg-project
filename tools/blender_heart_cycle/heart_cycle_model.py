from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import bpy
    from mathutils import Vector
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Run this script with Blender's bundled Python, for example: "
        "blender.exe --background --python heart_cycle_model.py -- --output-root <dir>"
    ) from exc

from heart_cycle_data import FPS, PHASES, TOTAL_FRAMES, phase_ranges

MODEL_REVISION = "heart_cutaway_v01"
ROOT_NAME = "HEART_CYCLE"
CUT_PLANE_Y = 0.0


class HeartBuild:
    def __init__(self) -> None:
        self.collections: dict[str, bpy.types.Collection] = {}
        self.materials: dict[str, bpy.types.Material] = {}
        self.controls: dict[str, bpy.types.Object] = {}
        self.valve_leaflets: dict[str, list[bpy.types.Object]] = {}
        self.flow_groups: dict[str, list[bpy.types.Object]] = {}


def _arguments() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser(description="Build a cutaway animated heart model.")
    parser.add_argument("--output-root", default=str(SCRIPT_DIR / "output"))
    parser.add_argument("--blend-name", default=f"{MODEL_REVISION}.blend")
    parser.add_argument("--render-preview", action="store_true")
    parser.add_argument("--render-animation", action="store_true")
    parser.add_argument("--resolution", type=int, default=1080)
    return parser.parse_args(argv)


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def _collection(name: str, parent: bpy.types.Collection | None = None) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def _move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    roughness: float = 0.45,
    metallic: float = 0.0,
    subsurface: float = 0.0,
    emission: tuple[float, float, float, float] | None = None,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 1.8
    return material


def _smooth(obj: bpy.types.Object) -> None:
    if obj.type != "MESH":
        return
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def _apply_transform(obj: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def _uv_sphere(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    segments: int = 64,
    rings: int = 32,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    _apply_transform(obj)
    obj.data.materials.append(material)
    _smooth(obj)
    _move_to_collection(obj, collection)
    return obj


def _cylinder(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    vertices: int = 48,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    _smooth(obj)
    _move_to_collection(obj, collection)
    return obj


def _cone(
    name: str,
    location: tuple[float, float, float],
    radius1: float,
    radius2: float,
    depth: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cone_add(
        vertices=48,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    _smooth(obj)
    _move_to_collection(obj, collection)
    return obj


def _torus(
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    rotation: tuple[float, float, float] = (math.pi / 2.0, 0.0, 0.0),
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=64,
        minor_segments=16,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    _smooth(obj)
    _move_to_collection(obj, collection)
    return obj


def _curve_tube(
    name: str,
    points: Iterable[tuple[float, float, float]],
    radius: float,
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    *,
    cyclic: bool = False,
) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(name=f"{name}_curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 16
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 5
    spline = curve_data.splines.new("BEZIER")
    points = tuple(points)
    spline.bezier_points.add(len(points) - 1)
    for control, coordinate in zip(spline.bezier_points, points, strict=True):
        control.co = coordinate
        control.handle_left_type = "AUTO"
        control.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve_data)
    curve_data.materials.append(material)
    collection.objects.link(obj)
    return obj


def _boolean_apply(target: bpy.types.Object, cutter: bpy.types.Object, operation: str) -> None:
    modifier = target.modifiers.new(name=f"bool_{operation.lower()}", type="BOOLEAN")
    modifier.operation = operation
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = target
    target.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    finally:
        target.select_set(False)


def _make_cutaway_shell(
    name: str,
    location: tuple[float, float, float],
    outer_scale: tuple[float, float, float],
    inner_scale: tuple[float, float, float],
    outer_material: bpy.types.Material,
    cut_material: bpy.types.Material,
    collection: bpy.types.Collection,
    cutters: bpy.types.Collection,
) -> bpy.types.Object:
    outer = _uv_sphere(name, location, outer_scale, outer_material, collection)
    inner_location = (location[0], location[1] - 0.02, location[2] + 0.05)
    inner = _uv_sphere(
        f"{name}_inner_cutter",
        inner_location,
        inner_scale,
        cut_material,
        cutters,
        segments=48,
        rings=24,
    )
    _boolean_apply(outer, inner, "DIFFERENCE")

    bpy.ops.mesh.primitive_cube_add(location=(0.0, -5.05, 4.0), scale=(8.0, 5.0, 8.0))
    front_cutter = bpy.context.object
    front_cutter.name = f"{name}_front_cut"
    _move_to_collection(front_cutter, cutters)
    _boolean_apply(outer, front_cutter, "DIFFERENCE")

    if len(outer.data.materials) == 1:
        outer.data.materials.append(cut_material)
    bevel = outer.modifiers.new("cut_edge_bevel", "BEVEL")
    bevel.width = 0.035
    bevel.segments = 3
    return outer


def _leaflet(
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    rotation: tuple[float, float, float],
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    leaflet = _uv_sphere(name, location, scale, material, collection, segments=32, rings=16)
    leaflet.rotation_euler = rotation
    return leaflet


def _empty(name: str, collection: bpy.types.Collection, location=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.45
    obj.location = location
    collection.objects.link(obj)
    return obj


def _build_materials(build: HeartBuild) -> None:
    build.materials = {
        "myocardium": _material("M_Myocardium", (0.42, 0.055, 0.045, 1.0), roughness=0.5, subsurface=0.08),
        "myocardium_cut": _material("M_Myocardium_Cut", (0.72, 0.18, 0.14, 1.0), roughness=0.62, subsurface=0.12),
        "right_chamber": _material("M_Right_Chamber", (0.16, 0.19, 0.34, 1.0), roughness=0.62),
        "left_chamber": _material("M_Left_Chamber", (0.35, 0.07, 0.08, 1.0), roughness=0.62),
        "valve": _material("M_Valve", (0.86, 0.70, 0.55, 1.0), roughness=0.42, subsurface=0.05),
        "chordae": _material("M_Chordae", (0.93, 0.82, 0.67, 1.0), roughness=0.5),
        "artery": _material("M_Artery", (0.62, 0.055, 0.035, 1.0), roughness=0.38, subsurface=0.06),
        "vein": _material("M_Vein", (0.055, 0.16, 0.42, 1.0), roughness=0.38, subsurface=0.04),
        "flow_red": _material("M_Flow_Red", (0.9, 0.04, 0.02, 1.0), roughness=0.2, emission=(0.8, 0.0, 0.0, 1.0)),
        "flow_blue": _material("M_Flow_Blue", (0.03, 0.24, 0.92, 1.0), roughness=0.2, emission=(0.0, 0.16, 0.9, 1.0)),
    }


def _build_collections(build: HeartBuild) -> None:
    root = _collection(ROOT_NAME)
    build.collections["root"] = root
    for name in ("ANATOMY", "CHAMBERS", "VALVES", "VESSELS", "FLOW", "CONTROLS", "CUTTERS", "RENDER"):
        build.collections[name.lower()] = _collection(name, root)
    build.collections["cutters"].hide_render = True


def _build_ventricles(build: HeartBuild) -> None:
    chambers = build.collections["chambers"]
    cutters = build.collections["cutters"]
    controls = build.collections["controls"]

    left_control = _empty("CTRL_LeftVentricle", controls, (0.78, 0.0, 2.65))
    right_control = _empty("CTRL_RightVentricle", controls, (-0.78, 0.0, 2.7))
    build.controls["left_ventricle"] = left_control
    build.controls["right_ventricle"] = right_control

    left_wall = _make_cutaway_shell(
        "LeftVentricle_Wall",
        (0.78, 0.18, 2.55),
        (1.30, 0.95, 2.20),
        (0.78, 0.62, 1.62),
        build.materials["myocardium"],
        build.materials["myocardium_cut"],
        chambers,
        cutters,
    )
    right_wall = _make_cutaway_shell(
        "RightVentricle_Wall",
        (-0.78, 0.23, 2.65),
        (1.16, 0.82, 1.95),
        (0.80, 0.55, 1.47),
        build.materials["myocardium"],
        build.materials["myocardium_cut"],
        chambers,
        cutters,
    )
    left_wall.parent = left_control
    right_wall.parent = right_control

    left_cavity = _uv_sphere("LeftVentricle_Cavity", (0.78, 0.40, 2.64), (0.75, 0.12, 1.58), build.materials["left_chamber"], chambers)
    right_cavity = _uv_sphere("RightVentricle_Cavity", (-0.78, 0.40, 2.72), (0.77, 0.12, 1.42), build.materials["right_chamber"], chambers)
    left_cavity.parent = left_control
    right_cavity.parent = right_control

    septum = _uv_sphere("Interventricular_Septum", (0.0, 0.28, 2.62), (0.34, 0.32, 1.95), build.materials["myocardium_cut"], chambers)
    septum.rotation_euler[1] = math.radians(-4.0)

    for x, z in ((0.48, 2.2), (0.98, 2.0), (-0.48, 2.15), (-0.98, 2.05)):
        papillary = _cone(
            f"Papillary_{x:+.2f}_{z:.2f}",
            (x, -0.02, z),
            0.20,
            0.10,
            0.72,
            build.materials["myocardium_cut"],
            chambers,
            rotation=(math.radians(-9.0 if x > 0 else 9.0), 0.0, 0.0),
        )
        papillary.parent = left_control if x > 0 else right_control


def _build_atria(build: HeartBuild) -> None:
    chambers = build.collections["chambers"]
    cutters = build.collections["cutters"]
    controls = build.collections["controls"]

    left_control = _empty("CTRL_LeftAtrium", controls, (0.93, 0.0, 4.55))
    right_control = _empty("CTRL_RightAtrium", controls, (-0.93, 0.0, 4.55))
    build.controls["left_atrium"] = left_control
    build.controls["right_atrium"] = right_control

    left = _make_cutaway_shell(
        "LeftAtrium_Wall",
        (0.97, 0.20, 4.58),
        (1.00, 0.78, 0.92),
        (0.73, 0.53, 0.65),
        build.materials["myocardium"],
        build.materials["myocardium_cut"],
        chambers,
        cutters,
    )
    right = _make_cutaway_shell(
        "RightAtrium_Wall",
        (-0.97, 0.20, 4.58),
        (1.05, 0.78, 0.98),
        (0.78, 0.53, 0.70),
        build.materials["myocardium"],
        build.materials["myocardium_cut"],
        chambers,
        cutters,
    )
    left.parent = left_control
    right.parent = right_control

    left_cavity = _uv_sphere("LeftAtrium_Cavity", (0.97, 0.40, 4.58), (0.70, 0.10, 0.63), build.materials["left_chamber"], chambers)
    right_cavity = _uv_sphere("RightAtrium_Cavity", (-0.97, 0.40, 4.58), (0.75, 0.10, 0.68), build.materials["right_chamber"], chambers)
    left_cavity.parent = left_control
    right_cavity.parent = right_control


def _build_av_valve(
    build: HeartBuild,
    prefix: str,
    center: tuple[float, float, float],
    leaflet_count: int,
    parent: bpy.types.Object,
    papillary_points: tuple[tuple[float, float, float], ...],
) -> None:
    valves = build.collections["valves"]
    anatomy = build.collections["anatomy"]
    annulus = _torus(
        f"{prefix}_Annulus",
        center,
        0.49 if leaflet_count == 2 else 0.53,
        0.055,
        build.materials["valve"],
        valves,
    )
    annulus.parent = parent
    leaflets: list[bpy.types.Object] = []
    for index in range(leaflet_count):
        angle = (2.0 * math.pi * index / leaflet_count) + (math.pi / 2.0)
        x = center[0] + math.cos(angle) * 0.20
        z = center[2] + math.sin(angle) * 0.06
        leaflet = _leaflet(
            f"{prefix}_Leaflet_{index + 1}",
            (x, -0.10, z - 0.08),
            (0.32, 0.055, 0.38),
            (math.radians(18.0), 0.0, angle + math.pi / 2.0),
            build.materials["valve"],
            valves,
        )
        leaflet.parent = parent
        leaflet["valve_role"] = prefix
        leaflet["leaflet_index"] = index + 1
        leaflets.append(leaflet)

        for papillary_point in papillary_points:
            start = (x, -0.14, z - 0.30)
            _curve_tube(
                f"{prefix}_Chord_{index + 1}_{papillary_point[0]:+.2f}",
                (start, papillary_point),
                0.018,
                build.materials["chordae"],
                anatomy,
            ).parent = parent
    build.valve_leaflets[prefix] = leaflets


def _build_semilunar_valve(
    build: HeartBuild,
    prefix: str,
    center: tuple[float, float, float],
    parent: bpy.types.Object | None = None,
) -> None:
    valves = build.collections["valves"]
    annulus = _torus(prefix + "_Annulus", center, 0.34, 0.045, build.materials["valve"], valves)
    if parent:
        annulus.parent = parent
    leaflets: list[bpy.types.Object] = []
    for index in range(3):
        angle = 2.0 * math.pi * index / 3.0
        leaflet = _leaflet(
            f"{prefix}_Leaflet_{index + 1}",
            (
                center[0] + math.cos(angle) * 0.17,
                -0.08,
                center[2] + math.sin(angle) * 0.12,
            ),
            (0.22, 0.045, 0.22),
            (math.radians(22.0), 0.0, angle),
            build.materials["valve"],
            valves,
        )
        if parent:
            leaflet.parent = parent
        leaflet["valve_role"] = prefix
        leaflets.append(leaflet)
    build.valve_leaflets[prefix] = leaflets


def _build_valves(build: HeartBuild) -> None:
    _build_av_valve(
        build,
        "Mitral",
        (0.82, -0.02, 3.88),
        2,
        build.controls["left_ventricle"],
        ((0.48, -0.02, 2.22), (1.02, -0.02, 2.05)),
    )
    _build_av_valve(
        build,
        "Tricuspid",
        (-0.82, -0.02, 3.86),
        3,
        build.controls["right_ventricle"],
        ((-0.48, -0.02, 2.20), (-1.02, -0.02, 2.08)),
    )
    _build_semilunar_valve(build, "Aortic", (0.42, -0.02, 5.05))
    _build_semilunar_valve(build, "Pulmonary", (-0.42, -0.02, 5.05))


def _build_vessels(build: HeartBuild) -> None:
    vessels = build.collections["vessels"]
    artery = build.materials["artery"]
    vein = build.materials["vein"]

    _curve_tube(
        "Aorta",
        ((0.42, 0.16, 5.05), (0.58, 0.25, 5.75), (0.55, 0.35, 6.45), (0.0, 0.55, 6.85), (-0.65, 0.65, 6.55)),
        0.34,
        artery,
        vessels,
    )
    _curve_tube(
        "PulmonaryTrunk",
        ((-0.42, 0.16, 5.05), (-0.35, 0.14, 5.65), (-0.75, 0.25, 6.10), (-1.65, 0.30, 6.10)),
        0.31,
        vein,
        vessels,
    )
    _cylinder("SuperiorVenaCava", (-1.28, 0.45, 5.95), 0.30, 2.25, vein, vessels)
    _cylinder("InferiorVenaCava", (-1.18, 0.44, 3.45), 0.32, 2.15, vein, vessels)

    for index, z in enumerate((4.35, 4.80), start=1):
        _cylinder(
            f"RightPulmonaryVein_{index}",
            (1.92, 0.48, z),
            0.17,
            1.15,
            artery,
            vessels,
            rotation=(0.0, math.pi / 2.0, 0.0),
        )
        _cylinder(
            f"LeftPulmonaryVein_{index}",
            (0.55, 0.72, z + 0.10),
            0.15,
            0.90,
            artery,
            vessels,
            rotation=(0.0, math.pi / 2.0, 0.0),
        )

    for index, x in enumerate((-0.10, 0.35, 0.82), start=1):
        _cylinder(
            f"AorticBranch_{index}",
            (x, 0.55, 7.00 + (index % 2) * 0.10),
            0.13,
            0.78,
            artery,
            vessels,
        )


def _arrow(
    name: str,
    points: tuple[tuple[float, float, float], ...],
    material: bpy.types.Material,
    collection: bpy.types.Collection,
    radius: float = 0.055,
) -> list[bpy.types.Object]:
    shaft = _curve_tube(name + "_Shaft", points, radius, material, collection)
    end = Vector(points[-1])
    previous = Vector(points[-2])
    direction = (end - previous).normalized()
    cone = _cone(
        name + "_Head",
        tuple(end),
        radius * 2.7,
        0.0,
        radius * 5.5,
        material,
        collection,
    )
    cone.rotation_mode = "QUATERNION"
    cone.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction)
    return [shaft, cone]


def _register_flow(build: HeartBuild, key: str, objects: list[bpy.types.Object]) -> None:
    build.flow_groups.setdefault(key, []).extend(objects)
    for obj in objects:
        obj["flow_group"] = key
        obj.hide_viewport = True
        obj.hide_render = True


def _build_flow_paths(build: HeartBuild) -> None:
    flow = build.collections["flow"]
    red = build.materials["flow_red"]
    blue = build.materials["flow_blue"]

    _register_flow(build, "red_av", _arrow("Flow_Red_AV", ((0.96, -0.42, 4.62), (0.91, -0.45, 4.12), (0.80, -0.45, 3.35)), red, flow))
    _register_flow(build, "blue_av", _arrow("Flow_Blue_AV", ((-0.98, -0.42, 4.62), (-0.91, -0.45, 4.10), (-0.80, -0.45, 3.35)), blue, flow))
    _register_flow(build, "red_eject", _arrow("Flow_Red_Eject", ((0.78, -0.42, 3.05), (0.52, -0.40, 4.40), (0.42, -0.38, 5.35), (0.30, -0.35, 6.35)), red, flow, 0.075))
    _register_flow(build, "blue_eject", _arrow("Flow_Blue_Eject", ((-0.78, -0.42, 3.05), (-0.52, -0.40, 4.40), (-0.42, -0.38, 5.35), (-0.82, -0.35, 6.00)), blue, flow, 0.075))
    _register_flow(build, "red_reverse", _arrow("Flow_Red_Reverse", ((0.32, -0.42, 5.72), (0.39, -0.42, 5.30), (0.42, -0.42, 5.08)), red, flow, 0.045))
    _register_flow(build, "blue_reverse", _arrow("Flow_Blue_Reverse", ((-0.72, -0.42, 5.70), (-0.52, -0.42, 5.30), (-0.42, -0.42, 5.08)), blue, flow, 0.045))


def _set_visibility(objects: Iterable[bpy.types.Object], visible: bool, frame: int) -> None:
    for obj in objects:
        obj.hide_viewport = not visible
        obj.hide_render = not visible
        obj.keyframe_insert("hide_viewport", frame=frame)
        obj.keyframe_insert("hide_render", frame=frame)


def _valve_pose(leaflets: list[bpy.types.Object], state: str, frame: int, is_semilunar: bool) -> None:
    if state == "open":
        angle = math.radians(48.0 if is_semilunar else 34.0)
    elif state == "closing":
        angle = math.radians(18.0 if is_semilunar else 12.0)
    else:
        angle = 0.0
    for index, leaflet in enumerate(leaflets):
        sign = -1.0 if index % 2 else 1.0
        leaflet.rotation_euler[0] = math.radians(18.0) + sign * angle
        leaflet.keyframe_insert("rotation_euler", frame=frame)


def _control_scale(control: bpy.types.Object, contraction: float, frame: int, *, atrium: bool) -> None:
    if atrium:
        scale = (1.0 - 0.07 * contraction, 1.0 - 0.12 * contraction, 1.0 - 0.06 * contraction)
    else:
        scale = (1.0 - 0.09 * contraction, 1.0 - 0.16 * contraction, 1.0 - 0.11 * contraction)
    control.scale = scale
    control.keyframe_insert("scale", frame=frame)


def _flow_keys_for_phase(phase_slug: str) -> tuple[str, ...]:
    if phase_slug in {"atrial_systole", "rapid_filling", "slow_filling"}:
        return ("red_av", "blue_av")
    if phase_slug in {"rapid_ejection", "slow_ejection"}:
        return ("red_eject", "blue_eject")
    if phase_slug == "protodiastolic_period":
        return ("red_reverse", "blue_reverse")
    return ()


def _animate(build: HeartBuild) -> None:
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES
    scene.render.fps = FPS

    all_flow_objects = [obj for objects in build.flow_groups.values() for obj in objects]
    for phase, start, end in phase_ranges():
        for frame in (start, end):
            _control_scale(build.controls["left_atrium"], phase.atrial_contraction, frame, atrium=True)
            _control_scale(build.controls["right_atrium"], phase.atrial_contraction, frame, atrium=True)
            _control_scale(build.controls["left_ventricle"], phase.ventricular_contraction, frame, atrium=False)
            _control_scale(build.controls["right_ventricle"], phase.ventricular_contraction, frame, atrium=False)

            for valve_name in ("Mitral", "Tricuspid"):
                _valve_pose(build.valve_leaflets[valve_name], phase.av_valves, frame, False)
            for valve_name in ("Aortic", "Pulmonary"):
                _valve_pose(build.valve_leaflets[valve_name], phase.semilunar_valves, frame, True)

            _set_visibility(all_flow_objects, False, frame)
            for key in _flow_keys_for_phase(phase.slug):
                _set_visibility(build.flow_groups[key], True, frame)

        scene.timeline_markers.new(f"{phase.index:02d}_{phase.slug}", frame=start)


def _look_at(obj: bpy.types.Object, point: tuple[float, float, float]) -> None:
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _setup_render(build: HeartBuild, resolution: int) -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = int(resolution * 16 / 9)
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.world.color = (0.035, 0.035, 0.045)

    camera_data = bpy.data.cameras.new("HeartCamera")
    camera = bpy.data.objects.new("HeartCamera", camera_data)
    build.collections["render"].objects.link(camera)
    camera.location = (0.0, -17.5, 4.3)
    camera.data.lens = 58
    _look_at(camera, (0.0, 0.0, 3.8))
    scene.camera = camera

    key_data = bpy.data.lights.new("Key", type="AREA")
    key_data.energy = 1100
    key_data.shape = "DISK"
    key_data.size = 5.0
    key = bpy.data.objects.new("Key", key_data)
    key.location = (-4.5, -6.0, 9.0)
    _look_at(key, (0.0, 0.0, 3.8))
    build.collections["render"].objects.link(key)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 700
    fill_data.size = 4.0
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (5.0, -4.0, 6.0)
    _look_at(fill, (0.0, 0.0, 3.8))
    build.collections["render"].objects.link(fill)

    rim_data = bpy.data.lights.new("Rim", type="AREA")
    rim_data.energy = 900
    rim_data.size = 3.0
    rim = bpy.data.objects.new("Rim", rim_data)
    rim.location = (0.0, 3.5, 8.0)
    _look_at(rim, (0.0, 0.0, 4.2))
    build.collections["render"].objects.link(rim)

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0.0, 2.2, 0.20))
    backdrop = bpy.context.object
    backdrop.name = "Backdrop"
    backdrop.data.materials.append(_material("M_Backdrop", (0.025, 0.028, 0.04, 1.0), roughness=0.9))
    _move_to_collection(backdrop, build.collections["render"])


def _scene_metadata() -> None:
    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    scene["cycle_reference"] = "Pokrovsky cardiac-cycle phase structure"
    scene["phase_count"] = len(PHASES)
    scene["animation_seconds"] = TOTAL_FRAMES / FPS
    scene["cutaway_plane"] = "frontal; anterior half removed"
    scene["anatomy_scope"] = "educational procedural proxy; not diagnostic"


def _write_manifest(output_root: Path, blend_path: Path) -> Path:
    manifest = {
        "model_revision": MODEL_REVISION,
        "blend_path": str(blend_path),
        "fps": FPS,
        "total_frames": TOTAL_FRAMES,
        "animation_seconds": TOTAL_FRAMES / FPS,
        "phases": [
            {
                **asdict(phase),
                "start_frame": start,
                "end_frame": end,
            }
            for phase, start, end in phase_ranges()
        ],
    }
    path = output_root / "heart_cycle_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_model(resolution: int) -> HeartBuild:
    _clear_scene()
    build = HeartBuild()
    _build_collections(build)
    _build_materials(build)
    _build_ventricles(build)
    _build_atria(build)
    _build_valves(build)
    _build_vessels(build)
    _build_flow_paths(build)
    _animate(build)
    _setup_render(build, resolution)
    _scene_metadata()
    return build


def main() -> int:
    args = _arguments()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    build_model(args.resolution)
    blend_path = output_root / args.blend_name
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    manifest_path = _write_manifest(output_root, blend_path)

    scene = bpy.context.scene
    if args.render_preview:
        scene.frame_set(1)
        scene.render.filepath = str(output_root / "heart_cutaway_preview.png")
        bpy.ops.render.render(write_still=True)
    if args.render_animation:
        scene.render.filepath = str(output_root / "frames" / "heart_cycle_")
        (output_root / "frames").mkdir(exist_ok=True)
        bpy.ops.render.render(animation=True)

    print(f"HEART_CYCLE_BLEND={blend_path}")
    print(f"HEART_CYCLE_MANIFEST={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
