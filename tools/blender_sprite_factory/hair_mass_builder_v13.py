from __future__ import annotations

import math

import blender_sprite_factory as factory
import hair_mass_builder_v12 as previous_builder
from hair_crown_profile_v13 import load_hair_crown_profile_v13
from hair_palette_v10 import load_hair_palette_v10
from hair_side_back_profile_v13 import load_hair_side_back_profile_v13


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS

_CROWN_PROFILE = load_hair_crown_profile_v13()
_SIDE_BACK_PROFILE = load_hair_side_back_profile_v13()
_PALETTE = load_hair_palette_v10()


def _apply_crown_side_back_vertices(crown: object) -> None:
    point_count = len(_CROWN_PROFILE.slices[0].points_xz)
    profile_vertex_count = len(_CROWN_PROFILE.slices) * point_count
    expected_vertex_count = profile_vertex_count + 2
    if len(crown.data.vertices) != expected_vertex_count:
        raise RuntimeError(
            f"Unexpected crown topology: {len(crown.data.vertices)} vertices "
            f"instead of {expected_vertex_count}"
        )

    vertex_index = 0
    for profile_slice in _CROWN_PROFILE.slices:
        for x, z in profile_slice.points_xz:
            crown.data.vertices[vertex_index].co = (x, profile_slice.y, z)
            vertex_index += 1

    front_slice = _CROWN_PROFILE.slices[0]
    crown.data.vertices[profile_vertex_count].co = (
        sum(point[0] for point in front_slice.points_xz) / point_count,
        front_slice.y,
        sum(point[1] for point in front_slice.points_xz) / point_count,
    )
    back_slice = _CROWN_PROFILE.slices[-1]
    crown.data.vertices[profile_vertex_count + 1].co = (
        sum(point[0] for point in back_slice.points_xz) / point_count,
        back_slice.y,
        sum(point[1] for point in back_slice.points_xz) / point_count,
    )
    crown.data.update()

    crown["hair_shape_zone"] = "physical_crown_with_wavy_side_and_rear_silhouette"
    crown["hair_geometry_revision"] = "v13"
    crown["hair_proxy_revision"] = "v16"
    crown["hair_side_back_strategy"] = (
        "preserve_front_and_scalp_coverage_while_reshaping_middle_and_rear_edges"
    )


def _apply_existing_mass_transforms() -> dict[str, dict[str, tuple[float, float, float]]]:
    applied: dict[str, dict[str, tuple[float, float, float]]] = {}
    for transform in _SIDE_BACK_PROFILE.transforms:
        obj = factory.bpy.data.objects.get(transform.name)
        if obj is None:
            raise RuntimeError(f"Proxy v16 transform target was not built: {transform.name}")
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            raise RuntimeError(f"Proxy v16 transform target is not a hair module: {transform.name}")

        obj.scale = tuple(
            float(obj.scale[index]) * transform.scale_multiplier[index]
            for index in range(3)
        )
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(
            float(obj.rotation_euler[index])
            + math.radians(transform.rotation_delta_degrees[index])
            for index in range(3)
        )
        world_matrix = obj.matrix_world.copy()
        world_matrix.translation += factory.Vector(transform.world_offset)
        obj.matrix_world = world_matrix

        obj["hair_shape_zone"] = f"physical_{transform.zone}_mass"
        obj["hair_physical_side"] = transform.physical_side
        obj["hair_geometry_revision"] = "v13"
        obj["hair_proxy_revision"] = "v16"
        obj["hair_scale_multiplier_v13"] = str(transform.scale_multiplier)
        obj["hair_world_offset_v13"] = str(transform.world_offset)
        obj["hair_rotation_delta_degrees_v13"] = str(
            transform.rotation_delta_degrees
        )
        applied[transform.name] = {
            "scale_multiplier": transform.scale_multiplier,
            "world_offset": transform.world_offset,
            "rotation_delta_degrees": transform.rotation_delta_degrees,
        }
    return applied


def _stamp_side_back_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v13"
        obj["hair_proxy_revision"] = "v16"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(
                f"Hair object has no material after side/back silhouette pass: {obj.name}"
            )
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(
                    f"Hair object retained a non-v10 palette material: {obj.name}"
                )


def apply_side_back_silhouette_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_scalp_coverage_pass(context)

    crown = factory.bpy.data.objects.get(_CROWN_PROFILE.mesh_name)
    if crown is None:
        raise RuntimeError("Proxy v16 requires the established crown mesh")

    _apply_crown_side_back_vertices(crown)
    _apply_existing_mass_transforms()
    _stamp_side_back_contract()

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v16 side/back silhouette contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )

    transformed_names = {item.name for item in _SIDE_BACK_PROFILE.transforms}
    if not transformed_names.issubset(actual_names):
        raise RuntimeError("Proxy v16 lost one or more existing side/back hair masses")

    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
