from __future__ import annotations

import blender_sprite_factory as factory
import hair_mass_builder_v17 as previous_builder
from hair_organic_tone_profile_v18 import (
    HairOrganicToneProfileV18,
    load_hair_organic_tone_profile_v18,
)
from hair_palette_v10 import load_hair_palette_v10


_PROFILE = load_hair_organic_tone_profile_v18()
_PALETTE = load_hair_palette_v10()

REMOVED_BACK_OVERLAY_NAMES = previous_builder.REMOVED_BACK_OVERLAY_NAMES
RETAINED_PROFILE_LOCK_NAMES = previous_builder.RETAINED_PROFILE_LOCK_NAMES
SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
MAJOR_LOCK_NAMES = previous_builder.MAJOR_LOCK_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS

_EXPECTED_MATERIAL_ROLES = ("shadow", "base", "mid", "highlight")


def _material_index_for_position(
    profile: HairOrganicToneProfileV18,
    x: float,
    y: float,
    z: float,
) -> int:
    lower_boundary = (
        profile.lower_shadow_base_z
        + profile.lower_shadow_x_slope * x
        + profile.lower_shadow_y_slope * y
    )
    if z < lower_boundary:
        return 0

    rear_boundary = profile.rear_shadow_base_z + profile.rear_shadow_x_slope * x
    if y > profile.rear_shadow_min_y and z < rear_boundary:
        return 0

    if profile.highlight_region.contains(x, y, z):
        return 3
    if profile.main_mid_region.contains(x, y, z):
        return 2
    if profile.rear_mid_region.contains(x, y, z):
        return 2
    return 1


def _polygon_centroid(obj: object, polygon: object) -> tuple[float, float, float]:
    count = float(len(polygon.vertices))
    return tuple(
        sum(float(obj.data.vertices[index].co[axis]) for index in polygon.vertices) / count
        for axis in range(3)
    )


def _assert_previous_organic_state() -> tuple[object, set[str]]:
    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v21 expected one completed proxy v20 scene before tone refinement: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if REMOVED_BACK_OVERLAY_NAMES.intersection(actual_names):
        raise RuntimeError("Proxy v21 restored a redundant back overlay")
    if not RETAINED_PROFILE_LOCK_NAMES.issubset(actual_names):
        raise RuntimeError("Proxy v21 lost one or more side/nape profile locks")

    crown = factory.bpy.data.objects.get("hair_reference_crown_mesh")
    if crown is None:
        raise RuntimeError("Proxy v21 cannot find the proxy v20 organic crown")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v21 must preserve the proxy v20 organic topology")
    material_roles = tuple(
        material.get("hair_palette_role") for material in crown.data.materials
    )
    if material_roles != _EXPECTED_MATERIAL_ROLES:
        raise RuntimeError(
            "Proxy v21 requires the established v10 crown material order: "
            f"{material_roles!r}"
        )
    for name in RETAINED_PROFILE_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v21 found invalid retained profile lock: {name}")
    return crown, actual_names


def _apply_localized_tones(crown: object) -> dict[str, int]:
    counts = {role: 0 for role in _EXPECTED_MATERIAL_ROLES}
    for polygon in crown.data.polygons:
        x, y, z = _polygon_centroid(crown, polygon)
        material_index = _material_index_for_position(_PROFILE, x, y, z)
        polygon.material_index = material_index
        counts[_EXPECTED_MATERIAL_ROLES[material_index]] += 1

    if any(count <= 0 for count in counts.values()):
        raise RuntimeError(f"Localized organic tone pass must use every hair tone: {counts}")
    if counts["base"] <= counts["mid"]:
        raise RuntimeError(f"Base tone must remain the dominant hair mass: {counts}")
    if not 4 <= counts["highlight"] <= 24:
        raise RuntimeError(f"Highlight must remain a small local patch: {counts}")

    crown["hair_geometry_revision"] = "v18"
    crown["hair_proxy_revision"] = "v21"
    crown["hair_tone_strategy"] = (
        "localized_ellipsoid_highlight_with_broad_base_and_mid_support"
    )
    crown["hair_highlight_intent"] = (
        "small_natural_glint_not_a_large_flat_or_angular_cap"
    )
    crown["hair_material_face_counts"] = str(counts)
    crown.data.update()
    return counts


def _stamp_tone_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v18"
        obj["hair_proxy_revision"] = "v21"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after tone pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_localized_organic_tone_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    crown, previous_names = _assert_previous_organic_state()
    tone_counts = _apply_localized_tones(crown)
    _stamp_tone_contract()

    current_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    if current_names != previous_names:
        raise RuntimeError("Proxy v21 must change tones without changing hair identities")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v21 changed the proxy v20 crown topology")
    if sum(tone_counts.values()) != len(crown.data.polygons):
        raise RuntimeError("Proxy v21 did not assign a tone to every crown polygon")
    for name in current_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return dict(HAIR_ROTATION_OVERRIDES_DEGREES)
