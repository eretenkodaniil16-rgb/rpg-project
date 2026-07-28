from __future__ import annotations

import math

import blender_sprite_factory as factory
import hair_mass_builder_v08 as previous_builder
from hair_lock_profile_v09 import HairLockGroove, load_hair_lock_profile_v09


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
REFERENCE_HAIR_PALETTE = previous_builder.REFERENCE_HAIR_PALETTE
REFERENCE_HAIR_FACET_COLORS = previous_builder.REFERENCE_HAIR_FACET_COLORS
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS

_LOCK_PROFILE = load_hair_lock_profile_v09()
ACTIVE_HAIR_PART_NAMES = frozenset(
    {*previous_builder.ACTIVE_HAIR_PART_NAMES, _LOCK_PROFILE.mesh_name}
)


def _hex_rgb(value: str) -> tuple[float, float, float]:
    raw = value.lstrip("#")
    return (
        int(raw[0:2], 16) / 255.0,
        int(raw[2:4], 16) / 255.0,
        int(raw[4:6], 16) / 255.0,
    )


def _retone_profile_meshes() -> None:
    crown = factory.bpy.data.objects.get("hair_reference_crown_mesh")
    forelock = factory.bpy.data.objects.get("hair_reference_forelock_mesh")
    if crown is None or forelock is None:
        raise RuntimeError("Proxy v12 requires the crown and forelock meshes from proxy v11")

    crown_points = 16
    crown_side_faces = crown_points * 2
    crown_front_cap_start = crown_side_faces
    crown_back_cap_start = crown_front_cap_start + crown_points
    for polygon_index, polygon in enumerate(crown.data.polygons):
        if polygon_index < crown_points:
            polygon.material_index = 2  # broad front/middle mass
        elif polygon_index < crown_side_faces:
            polygon.material_index = 1  # quieter rear transition
        elif polygon_index < crown_back_cap_start:
            polygon.material_index = 2  # readable front cap
        else:
            polygon.material_index = 2  # readable rear cap

    for local_index in (3, 5, 7):
        crown.data.polygons[local_index].material_index = 3
        crown.data.polygons[crown_front_cap_start + local_index].material_index = 3
        crown.data.polygons[crown_back_cap_start + local_index].material_index = 3

    forelock_points = 7
    forelock_side_faces = forelock_points * 2
    forelock_front_cap_start = forelock_side_faces
    for polygon_index, polygon in enumerate(forelock.data.polygons):
        polygon.material_index = 2
        if forelock_points <= polygon_index < forelock_side_faces:
            polygon.material_index = 1
    for local_index in (1, 2, 3):
        forelock.data.polygons[local_index].material_index = 3
        forelock.data.polygons[forelock_front_cap_start + local_index].material_index = 3

    crown["hair_lock_tone_strategy"] = "broad_masses_with_dark_separators"
    forelock["hair_lock_tone_strategy"] = "single_readable_forelock"


def _create_separator_material() -> object:
    material = factory.bpy.data.materials.new("MAT_hair_lock_separator_shadow")
    material.use_nodes = True
    material["material_slot_id"] = "hair"
    material["hair_lock_role"] = _LOCK_PROFILE.material_role
    color = _hex_rgb(REFERENCE_HAIR_PALETTE[0])
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1.0)
    emission.inputs["Strength"].default_value = 0.82
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material.diffuse_color = (*color, 1.0)
    material.use_backface_culling = False
    return material


def _point_tangent(points: tuple[tuple[float, float], ...], index: int) -> tuple[float, float]:
    previous = points[max(0, index - 1)]
    following = points[min(len(points) - 1, index + 1)]
    du = following[0] - previous[0]
    dv = following[1] - previous[1]
    length = math.hypot(du, dv)
    if length <= 0.000001:
        raise ValueError("Lock groove contains a zero-length tangent")
    return du / length, dv / length


def _ribbon_vertices(groove: HairLockGroove) -> tuple[tuple[float, float, float], ...]:
    vertices: list[tuple[float, float, float]] = []
    for index, (u, v) in enumerate(groove.points_uv):
        tangent_u, tangent_v = _point_tangent(groove.points_uv, index)
        perpendicular_u = -tangent_v
        perpendicular_v = tangent_u
        offsets = (-groove.half_width, groove.half_width)
        for offset in offsets:
            shifted_u = u + perpendicular_u * offset
            shifted_v = v + perpendicular_v * offset
            if groove.plane == "XZ":
                vertices.append((shifted_u, groove.fixed_coordinate, shifted_v))
            else:
                vertices.append((groove.fixed_coordinate, shifted_u, shifted_v))
    return tuple(vertices)


def _build_lock_separator_mesh(context: factory.BuildContext) -> None:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int, int]] = []
    groove_ranges: dict[str, tuple[int, int]] = {}

    for groove in _LOCK_PROFILE.grooves:
        start = len(vertices)
        ribbon = _ribbon_vertices(groove)
        vertices.extend(ribbon)
        for segment_index in range(len(groove.points_uv) - 1):
            base = start + segment_index * 2
            faces.append((base, base + 2, base + 3, base + 1))
        groove_ranges[groove.name] = (start, len(vertices))

    mesh = factory.bpy.data.meshes.new(f"{_LOCK_PROFILE.mesh_name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)
    obj = factory.bpy.data.objects.new(_LOCK_PROFILE.mesh_name, mesh)
    obj["hair_shape_zone"] = "large_lock_separators"
    obj["hair_lock_groove_count"] = len(_LOCK_PROFILE.grooves)
    obj["hair_lock_groove_ranges"] = str(groove_ranges)
    factory._flat_shade(obj)
    factory._assign_material(obj, _create_separator_material())
    factory._register(context, obj, "hair", "head")


def refine_reference_hair_locks(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.consolidate_reference_hair_masses(context)
    _retone_profile_meshes()
    _build_lock_separator_mesh(context)

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v12 hair lock contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
