from __future__ import annotations

import math

import blender_sprite_factory as factory
import hair_mass_builder_v20 as previous_builder
from hair_palette_v10 import load_hair_palette_v10
from hair_side_nape_volume_profile_v21 import (
    HairSideNapeVolumeProfileV21,
    load_hair_side_nape_volume_profile_v21,
)


_PROFILE = load_hair_side_nape_volume_profile_v21()
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

_TARGET_NAMES = frozenset(item.name for item in _PROFILE.transforms)
_CROWN_NAME = "hair_reference_crown_mesh"


def _coordinates(obj: object) -> tuple[tuple[float, float, float], ...]:
    return tuple(tuple(float(value) for value in vertex.co) for vertex in obj.data.vertices)


def _assert_proxy_v23_state() -> tuple[object, set[str], dict[str, tuple[float, float, float]]]:
    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v24 expected one completed proxy v23 scene before side/nape refinement: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if REMOVED_BACK_OVERLAY_NAMES.intersection(actual_names):
        raise RuntimeError("Proxy v24 restored a redundant back overlay")
    if not RETAINED_PROFILE_LOCK_NAMES.issubset(actual_names):
        raise RuntimeError("Proxy v24 lost one or more retained side/nape masses")
    if _TARGET_NAMES != RETAINED_PROFILE_LOCK_NAMES:
        raise RuntimeError("Proxy v24 profile must target all and only retained side/nape masses")

    crown = factory.bpy.data.objects.get(_CROWN_NAME)
    if crown is None:
        raise RuntimeError("Proxy v24 cannot find the completed proxy v23 crown")
    if crown.get("hair_proxy_revision") != "v23":
        raise RuntimeError("Proxy v24 requires the completed proxy v23 dense crown state")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v24 must preserve proxy v23 crown topology")

    previous_scales: dict[str, tuple[float, float, float]] = {}
    for name in sorted(_TARGET_NAMES):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Proxy v24 cannot find retained hair mass: {name}")
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            raise RuntimeError(f"Proxy v24 target is not a hair module: {name}")
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v24 found invalid retained mass topology: {name}")
        if obj.get("hair_proxy_revision") != "v23":
            raise RuntimeError(f"Proxy v24 requires proxy v23 target state: {name}")
        previous_scales[name] = tuple(float(value) for value in obj.scale)

    return crown, actual_names, previous_scales


def _apply_side_nape_transforms(
    profile: HairSideNapeVolumeProfileV21,
) -> dict[str, dict[str, tuple[float, float, float]]]:
    applied: dict[str, dict[str, tuple[float, float, float]]] = {}
    for transform in profile.transforms:
        obj = factory.bpy.data.objects[transform.name]

        before_scale = tuple(float(value) for value in obj.scale)
        obj.scale = tuple(
            before_scale[index] * transform.scale_multiplier[index]
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

        after_scale = tuple(float(value) for value in obj.scale)
        if any(after < before for after, before in zip(after_scale, before_scale)):
            raise RuntimeError(
                f"Proxy v24 reduced a retained hair mass instead of adding volume: {transform.name}"
            )

        obj["hair_shape_zone"] = f"dense_transition_{transform.zone}_mass"
        obj["hair_physical_side"] = transform.physical_side
        obj["hair_geometry_revision"] = "v21"
        obj["hair_proxy_revision"] = "v24"
        obj["hair_transition_strategy"] = "temple_to_side_to_nape_without_density_loss"
        obj["hair_scale_multiplier_v21"] = str(transform.scale_multiplier)
        obj["hair_world_offset_v21"] = str(transform.world_offset)
        obj["hair_rotation_delta_degrees_v21"] = str(
            transform.rotation_delta_degrees
        )
        applied[transform.name] = {
            "scale_before": before_scale,
            "scale_after": after_scale,
            "scale_multiplier": transform.scale_multiplier,
            "world_offset": transform.world_offset,
            "rotation_delta_degrees": transform.rotation_delta_degrees,
        }
    return applied


def _stamp_side_nape_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_pass_revision"] = "v21"
        obj["hair_proxy_revision"] = "v24"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after proxy v24 pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_side_nape_volume_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    crown, previous_names, previous_scales = _assert_proxy_v23_state()
    crown_coordinates_before = _coordinates(crown)

    applied = _apply_side_nape_transforms(_PROFILE)
    _stamp_side_nape_contract()
    factory.bpy.context.view_layer.update()

    current_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    if current_names != previous_names:
        raise RuntimeError("Proxy v24 must not change hair object identities")
    if _coordinates(crown) != crown_coordinates_before:
        raise RuntimeError("Proxy v24 must not modify the accepted proxy v23 crown mesh")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v24 changed crown topology")

    for name in sorted(_TARGET_NAMES):
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v24 changed retained mass topology: {name}")
        after_scale = tuple(float(value) for value in obj.scale)
        if any(after < before for after, before in zip(after_scale, previous_scales[name])):
            raise RuntimeError(f"Proxy v24 reduced visible side/nape volume: {name}")
        if name not in applied:
            raise RuntimeError(f"Proxy v24 did not transform retained mass: {name}")

    for name in current_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    return dict(HAIR_ROTATION_OVERRIDES_DEGREES)
