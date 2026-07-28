from __future__ import annotations

import math
from typing import Protocol

import blender_sprite_factory as factory
from hair_crown_profile_v08 import load_hair_crown_profile_v08
from hair_forelock_profile_v08 import load_hair_forelock_profile_v08
from head_profile_v08 import load_head_detail_profile_v08


class _SliceProfile(Protocol):
    mesh_name: str
    slices: tuple


SOURCE_HAIR_PART_NAMES = frozenset(
    {
        "hair_back_shell",
        "hair_back_sweep_left",
        "hair_back_sweep_right",
        "hair_front_hairline_left",
        "hair_front_hairline_right",
        "hair_side_mass_left",
        "hair_side_mass_right",
        "hair_nape_left",
        "hair_nape_center",
        "hair_nape_right",
    }
)

ACTIVE_HAIR_PART_NAMES = frozenset(
    {
        *SOURCE_HAIR_PART_NAMES,
        "hair_reference_crown_mesh",
        "hair_reference_forelock_mesh",
    }
)

REFERENCE_HAIR_PALETTE = (
    "#0B0602",
    "#1A120A",
    "#26180B",
    "#582A15",
    "#7C4924",
)

REFERENCE_HAIR_FACET_COLORS = {
    "shadow": "#1A120A",
    "base": "#26180B",
    "mid": "#582A15",
    "highlight": "#7C4924",
}

CROWN_FRONT_FACET_PATTERN = (
    0,
    0,
    2,
    3,
    0,
    3,
    1,
    2,
    0,
    2,
    1,
    0,
    1,
    2,
    0,
    1,
)
CROWN_BACK_FACET_PATTERN = (
    0,
    0,
    1,
    2,
    0,
    3,
    1,
    2,
    0,
    2,
    1,
    0,
    0,
    1,
    0,
    0,
)
FORELOCK_FRONT_FACET_PATTERN = (0, 1, 2, 1, 0, 0, 1)
FORELOCK_BACK_FACET_PATTERN = (0, 0, 1, 1, 0, 0, 0)

HAIR_ROTATION_OVERRIDES_DEGREES: dict[str, tuple[float, float, float]] = {
    "hair_back_sweep_left": (18.0, 0.0, -8.0),
    "hair_back_sweep_right": (20.0, 0.0, 4.0),
}

HAIR_SCALE_MULTIPLIERS: dict[str, tuple[float, float, float]] = {
    "hair_back_sweep_left": (1.00, 0.95, 1.08),
    "hair_back_sweep_right": (0.95, 1.00, 1.02),
    "hair_side_mass_left": (0.95, 0.95, 1.05),
    "hair_side_mass_right": (0.95, 0.95, 1.03),
}

HAIR_WORLD_OFFSETS: dict[str, tuple[float, float, float]] = {
    "hair_back_sweep_left": (0.010, -0.010, 0.000),
    "hair_back_sweep_right": (-0.015, 0.005, -0.005),
}


def _assert_positive_transform_contract() -> None:
    for name, multiplier in HAIR_SCALE_MULTIPLIERS.items():
        if name not in SOURCE_HAIR_PART_NAMES:
            raise ValueError(f"Scale override targets inactive hair part: {name}")
        if any(value <= 0.0 for value in multiplier):
            raise ValueError(f"Hair scale override must stay positive: {name}")
    for name in HAIR_WORLD_OFFSETS:
        if name not in SOURCE_HAIR_PART_NAMES:
            raise ValueError(f"World offset targets inactive hair part: {name}")
    for name in HAIR_ROTATION_OVERRIDES_DEGREES:
        if name not in SOURCE_HAIR_PART_NAMES:
            raise ValueError(f"Rotation override targets inactive hair part: {name}")
    if len(CROWN_FRONT_FACET_PATTERN) != 16 or len(CROWN_BACK_FACET_PATTERN) != 16:
        raise ValueError("Crown facet patterns must match the sixteen-point contour")
    if len(FORELOCK_FRONT_FACET_PATTERN) != 7 or len(FORELOCK_BACK_FACET_PATTERN) != 7:
        raise ValueError("Forelock facet patterns must match the seven-point contour")
    for pattern in (
        CROWN_FRONT_FACET_PATTERN,
        CROWN_BACK_FACET_PATTERN,
        FORELOCK_FRONT_FACET_PATTERN,
        FORELOCK_BACK_FACET_PATTERN,
    ):
        if min(pattern) < 0 or max(pattern) >= len(REFERENCE_HAIR_FACET_COLORS):
            raise ValueError("Hair facet pattern references an unknown material")


def _apply_reference_palette(context: factory.BuildContext) -> None:
    material = context.materials["hair"]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    texture = next(node for node in nodes if node.type == "TEX_IMAGE")
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    for link in tuple(output.inputs["Surface"].links):
        links.remove(link)

    rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "hair_reference_palette"
    ramp.color_ramp.interpolation = "CONSTANT"
    elements = ramp.color_ramp.elements
    elements[0].position = 0.005
    elements[0].color = (0x0B / 255.0, 0x06 / 255.0, 0x02 / 255.0, 1.0)
    elements[1].position = 0.10
    elements[1].color = (0x7C / 255.0, 0x49 / 255.0, 0x24 / 255.0, 1.0)
    for position, color in (
        (0.010, (0x1A, 0x12, 0x0A)),
        (0.020, (0x26, 0x18, 0x0B)),
        (0.045, (0x58, 0x2A, 0x15)),
    ):
        element = elements.new(position)
        element.color = tuple(value / 255.0 for value in color) + (1.0,)

    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 0.82
    links.new(texture.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(rgb_to_bw.outputs["Val"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material.use_backface_culling = False


def _hex_rgb(value: str) -> tuple[float, float, float]:
    raw = value.lstrip("#")
    return (
        int(raw[0:2], 16) / 255.0,
        int(raw[2:4], 16) / 255.0,
        int(raw[4:6], 16) / 255.0,
    )


def _create_facet_materials() -> tuple[object, ...]:
    materials: list[object] = []
    for facet_name, color_hex in REFERENCE_HAIR_FACET_COLORS.items():
        material = factory.bpy.data.materials.new(f"MAT_hair_facet_{facet_name}")
        material.use_nodes = True
        material["material_slot_id"] = "hair"
        material["hair_facet_role"] = facet_name
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        output = nodes.new("ShaderNodeOutputMaterial")
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (*_hex_rgb(color_hex), 1.0)
        emission.inputs["Strength"].default_value = 0.82
        links.new(emission.outputs["Emission"], output.inputs["Surface"])
        material.diffuse_color = (*_hex_rgb(color_hex), 1.0)
        material.use_backface_culling = False
        materials.append(material)
    return tuple(materials)


def _remove_inactive_hair_parts() -> None:
    for obj in tuple(factory.bpy.data.objects):
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        if obj.name not in SOURCE_HAIR_PART_NAMES:
            factory.bpy.data.objects.remove(obj, do_unlink=True)


def _build_slice_profile_mesh(
    context: factory.BuildContext,
    profile: _SliceProfile,
    shape_zone: str,
    facet_materials: tuple[object, ...],
    front_pattern: tuple[int, ...],
    back_pattern: tuple[int, ...],
) -> None:
    point_count = len(profile.slices[0].points_xz)
    if len(front_pattern) != point_count or len(back_pattern) != point_count:
        raise ValueError(f"Facet pattern does not match profile {profile.mesh_name}")

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []

    for profile_slice in profile.slices:
        vertices.extend((x, profile_slice.y, z) for x, z in profile_slice.points_xz)

    for slice_index in range(1, len(profile.slices)):
        previous = (slice_index - 1) * point_count
        current = slice_index * point_count
        for point_index in range(point_count):
            next_index = (point_index + 1) % point_count
            faces.append(
                (
                    previous + point_index,
                    previous + next_index,
                    current + next_index,
                    current + point_index,
                )
            )
            material_indices.append(front_pattern[point_index] if slice_index == 1 else back_pattern[point_index])

    front_slice = profile.slices[0]
    front_center_index = len(vertices)
    vertices.append(
        (
            sum(point[0] for point in front_slice.points_xz) / point_count,
            front_slice.y,
            sum(point[1] for point in front_slice.points_xz) / point_count,
        )
    )
    for point_index in range(point_count):
        next_index = (point_index + 1) % point_count
        faces.append((front_center_index, next_index, point_index))
        material_indices.append(front_pattern[point_index])

    back_slice = profile.slices[-1]
    back_start = (len(profile.slices) - 1) * point_count
    back_center_index = len(vertices)
    vertices.append(
        (
            sum(point[0] for point in back_slice.points_xz) / point_count,
            back_slice.y,
            sum(point[1] for point in back_slice.points_xz) / point_count,
        )
    )
    for point_index in range(point_count):
        next_index = (point_index + 1) % point_count
        faces.append(
            (
                back_center_index,
                back_start + point_index,
                back_start + next_index,
            )
        )
        material_indices.append(back_pattern[point_index])

    mesh = factory.bpy.data.meshes.new(f"{profile.mesh_name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)
    obj = factory.bpy.data.objects.new(profile.mesh_name, mesh)
    obj["hair_shape_zone"] = shape_zone
    obj["hair_facet_material_count"] = len(facet_materials)
    factory._flat_shade(obj)
    for material in facet_materials:
        obj.data.materials.append(material)
    for polygon, material_index in zip(obj.data.polygons, material_indices):
        polygon.material_index = material_index
    factory._register(context, obj, "hair", "head")


def _build_reference_profile_meshes(context: factory.BuildContext) -> None:
    facet_materials = _create_facet_materials()
    _build_slice_profile_mesh(
        context,
        load_hair_crown_profile_v08(),
        "top_crown",
        facet_materials,
        CROWN_FRONT_FACET_PATTERN,
        CROWN_BACK_FACET_PATTERN,
    )
    _build_slice_profile_mesh(
        context,
        load_hair_forelock_profile_v08(),
        "front_forelock",
        facet_materials,
        FORELOCK_FRONT_FACET_PATTERN,
        FORELOCK_BACK_FACET_PATTERN,
    )


def _apply_shape_overrides() -> None:
    for name, multiplier in HAIR_SCALE_MULTIPLIERS.items():
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Hair scale target was not built: {name}")
        obj.scale = multiplier

    for name, offset in HAIR_WORLD_OFFSETS.items():
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Hair offset target was not built: {name}")
        world_matrix = obj.matrix_world.copy()
        world_matrix.translation += factory.Vector(offset)
        obj.matrix_world = world_matrix


def _apply_reference_rotations(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    detail = load_head_detail_profile_v08(context.config.character_id)
    applied: dict[str, tuple[float, float, float]] = {}
    profile_rotations = dict(detail.hair_rotations_degrees)
    for name in sorted(SOURCE_HAIR_PART_NAMES):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Active reference hair part was not built: {name}")
        degrees = HAIR_ROTATION_OVERRIDES_DEGREES.get(name, profile_rotations.get(name))
        if degrees is None:
            continue
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(math.radians(value) for value in degrees)
        applied[name] = degrees
    return applied


def consolidate_reference_hair_masses(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    _assert_positive_transform_contract()
    _remove_inactive_hair_parts()
    _apply_reference_palette(context)
    _build_reference_profile_meshes(context)
    _apply_shape_overrides()
    applied_rotations = _apply_reference_rotations(context)

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Consolidated hair mass contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )

    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
