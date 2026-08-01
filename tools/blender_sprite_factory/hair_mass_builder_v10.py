from __future__ import annotations

import math

import blender_sprite_factory as factory
import hair_mass_builder_v09 as previous_builder
from hair_lock_profile_v10 import HairLockGrooveV10, load_hair_lock_profile_v10
from hair_palette_v10 import HairPaletteV10, load_hair_palette_v10


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS

_LOCK_PROFILE = load_hair_lock_profile_v10()
_PALETTE = load_hair_palette_v10()
DARK_REFERENCE_HAIR_PALETTE = _PALETTE.all_colors
DARK_REFERENCE_HAIR_FACET_COLORS = {
    "shadow": _PALETTE.shadow,
    "base": _PALETTE.base,
    "mid": _PALETTE.mid,
    "highlight": _PALETTE.highlight,
    "separator": _PALETTE.separator,
}

_SOURCE_HAIR_MATERIAL_ROLES = {
    "hair_back_shell": "base",
    "hair_back_sweep_left": "mid",
    "hair_back_sweep_right": "mid",
    "hair_front_hairline_left": "base",
    "hair_front_hairline_right": "base",
    "hair_side_mass_left": "base",
    "hair_side_mass_right": "base",
    "hair_nape_left": "shadow",
    "hair_nape_center": "shadow",
    "hair_nape_right": "shadow",
}


def _hex_rgb_srgb(value: str) -> tuple[float, float, float]:
    raw = value.lstrip("#")
    return tuple(int(raw[index : index + 2], 16) / 255.0 for index in (0, 2, 4))


def _srgb_channel_to_linear(value: float) -> float:
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _hex_rgb_linear(value: str) -> tuple[float, float, float]:
    return tuple(_srgb_channel_to_linear(channel) for channel in _hex_rgb_srgb(value))


def _create_dark_emission_material(role: str, color_hex: str) -> object:
    material = factory.bpy.data.materials.new(f"MAT_hair_v10_{role}")
    material.use_nodes = True
    material["material_slot_id"] = "hair"
    material["hair_palette_revision"] = _PALETTE.revision
    material["hair_proxy_revision"] = _PALETTE.proxy_revision
    material["hair_palette_role"] = role
    material["hair_palette_hex"] = color_hex
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*_hex_rgb_linear(color_hex), 1.0)
    emission.inputs["Strength"].default_value = 1.0
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material.diffuse_color = (*_hex_rgb_srgb(color_hex), 1.0)
    material.use_backface_culling = False
    return material


def _create_dark_materials() -> dict[str, object]:
    return {
        role: _create_dark_emission_material(role, color_hex)
        for role, color_hex in DARK_REFERENCE_HAIR_FACET_COLORS.items()
    }


def _replace_profile_materials(obj: object, materials: dict[str, object]) -> None:
    previous_indices = [polygon.material_index for polygon in obj.data.polygons]
    obj.data.materials.clear()
    for role in ("shadow", "base", "mid", "highlight"):
        obj.data.materials.append(materials[role])
    for polygon, material_index in zip(obj.data.polygons, previous_indices):
        if not 0 <= material_index <= 3:
            raise RuntimeError(f"Unexpected profile material index on {obj.name}: {material_index}")
        polygon.material_index = material_index


def _apply_dark_palette_to_existing_hair(materials: dict[str, object]) -> None:
    crown = factory.bpy.data.objects.get("hair_reference_crown_mesh")
    forelock = factory.bpy.data.objects.get("hair_reference_forelock_mesh")
    if crown is None or forelock is None:
        raise RuntimeError("Proxy v13 requires the established crown and forelock meshes")
    _replace_profile_materials(crown, materials)
    _replace_profile_materials(forelock, materials)

    if set(_SOURCE_HAIR_MATERIAL_ROLES) != set(SOURCE_HAIR_PART_NAMES):
        raise RuntimeError("Every consolidated source hair part needs an explicit dark palette role")
    for name, role in _SOURCE_HAIR_MATERIAL_ROLES.items():
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Dark palette target was not built: {name}")
        factory._assign_material(obj, materials[role])
        obj[factory.MATERIAL_PROPERTY] = "hair"


def _point_tangent(points: tuple[tuple[float, float], ...], index: int) -> tuple[float, float]:
    previous = points[max(0, index - 1)]
    following = points[min(len(points) - 1, index + 1)]
    du = following[0] - previous[0]
    dv = following[1] - previous[1]
    length = math.hypot(du, dv)
    if length <= 0.000001:
        raise ValueError("Lock groove contains a zero-length tangent")
    return du / length, dv / length


def _ribbon_vertices(groove: HairLockGrooveV10) -> tuple[tuple[float, float, float], ...]:
    vertices: list[tuple[float, float, float]] = []
    for index, (u, v) in enumerate(groove.points_uv):
        tangent_u, tangent_v = _point_tangent(groove.points_uv, index)
        perpendicular_u = -tangent_v
        perpendicular_v = tangent_u
        for offset in (-groove.half_width, groove.half_width):
            shifted_u = u + perpendicular_u * offset
            shifted_v = v + perpendicular_v * offset
            if groove.plane == "XZ":
                vertices.append((shifted_u, groove.fixed_coordinate, shifted_v))
            else:
                vertices.append((groove.fixed_coordinate, shifted_u, shifted_v))
    return tuple(vertices)


def _replace_lock_separator_mesh(context: factory.BuildContext, separator_material: object) -> None:
    old = factory.bpy.data.objects.get(_LOCK_PROFILE.mesh_name)
    if old is None:
        raise RuntimeError("Proxy v13 expected the proxy v12 lock separator mesh")
    old_mesh = old.data
    factory.bpy.data.objects.remove(old, do_unlink=True)
    if old_mesh.users == 0:
        factory.bpy.data.meshes.remove(old_mesh)

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

    mesh = factory.bpy.data.meshes.new(f"{_LOCK_PROFILE.mesh_name}_mesh_v10")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)
    obj = factory.bpy.data.objects.new(_LOCK_PROFILE.mesh_name, mesh)
    obj["hair_shape_zone"] = "curved_large_lock_separators"
    obj["hair_lock_groove_count"] = len(_LOCK_PROFILE.grooves)
    obj["hair_lock_groove_ranges"] = str(groove_ranges)
    factory._flat_shade(obj)
    factory._assign_material(obj, separator_material)
    factory._register(context, obj, "hair", "head")


def _stamp_palette_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_palette_revision"] = _PALETTE.revision
        obj["hair_proxy_revision"] = _PALETTE.proxy_revision
        obj["hair_tone_strategy"] = "dark_reference_ramp_with_curved_large_lock_separators"
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after dark pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained an outdated material: {obj.name}")


def apply_dark_reference_hair_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.refine_reference_hair_locks(context)
    materials = _create_dark_materials()
    _apply_dark_palette_to_existing_hair(materials)
    _replace_lock_separator_mesh(context, materials["separator"])
    _stamp_palette_contract()

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v13 dark hair contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
