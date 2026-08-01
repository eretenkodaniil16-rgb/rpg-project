from __future__ import annotations

import blender_sprite_factory as factory
import hair_mass_builder_v11 as previous_builder
from hair_crown_profile_v12 import load_hair_crown_profile_v12
from hair_palette_v10 import load_hair_palette_v10


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS

_CROWN_PROFILE = load_hair_crown_profile_v12()
_PALETTE = load_hair_palette_v10()


def _apply_crown_coverage_vertices(crown: object) -> None:
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

    crown["hair_shape_zone"] = "physical_large_wave_crown_with_scalp_coverage"
    crown["hair_geometry_revision"] = "v12"
    crown["hair_proxy_revision"] = "v15"
    crown["hair_coverage_strategy"] = "raise_internal_wave_valleys_without_changing_outer_silhouette"
    crown["hair_coverage_adjusted_indices"] = str((4, 6, 8))


def _stamp_scalp_coverage_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v12"
        obj["hair_proxy_revision"] = "v15"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after scalp coverage pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_scalp_coverage_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_physical_lock_shape_pass(context)

    crown = factory.bpy.data.objects.get(_CROWN_PROFILE.mesh_name)
    if crown is None:
        raise RuntimeError("Proxy v15 requires the established crown mesh")

    _apply_crown_coverage_vertices(crown)
    _stamp_scalp_coverage_contract()

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v15 scalp coverage contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )

    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
