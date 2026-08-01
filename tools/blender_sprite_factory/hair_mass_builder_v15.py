from __future__ import annotations

import math

import blender_sprite_factory as factory
import hair_mass_builder_v14 as previous_builder
from hair_lock_exposure_profile_v15 import load_hair_lock_exposure_profile_v15
from hair_palette_v10 import load_hair_palette_v10


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS
MAJOR_LOCK_NAMES = previous_builder.MAJOR_LOCK_NAMES

_EXPOSURE_PROFILE = load_hair_lock_exposure_profile_v15()
_PALETTE = load_hair_palette_v10()


def _apply_lock_exposure_transforms() -> dict[str, dict[str, tuple[float, float, float]]]:
    applied: dict[str, dict[str, tuple[float, float, float]]] = {}
    for transform in _EXPOSURE_PROFILE.transforms:
        obj = factory.bpy.data.objects.get(transform.name)
        if obj is None:
            raise RuntimeError(f"Proxy v18 exposure target was not built: {transform.name}")
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            raise RuntimeError(f"Proxy v18 exposure target is not hair: {transform.name}")
        if obj.get("hair_physical_side") != transform.physical_side:
            raise RuntimeError(f"Physical side drift before exposure pass: {transform.name}")
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v18 expected the proxy v17 profile mesh: {transform.name}")

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

        obj["hair_shape_zone"] = f"exposed_profile_{transform.zone}_lock"
        obj["hair_geometry_revision"] = "v15"
        obj["hair_proxy_revision"] = "v18"
        obj["hair_exposure_strategy"] = (
            "shrink_central_overlap_and_separate_existing_profile_lock_tips"
        )
        obj["hair_exposure_scale_multiplier"] = str(transform.scale_multiplier)
        obj["hair_exposure_world_offset"] = str(transform.world_offset)
        obj["hair_exposure_rotation_delta_degrees"] = str(
            transform.rotation_delta_degrees
        )
        applied[transform.name] = {
            "scale_multiplier": transform.scale_multiplier,
            "world_offset": transform.world_offset,
            "rotation_delta_degrees": transform.rotation_delta_degrees,
        }
    return applied


def _stamp_exposure_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v15"
        obj["hair_proxy_revision"] = "v18"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after exposure pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_major_lock_exposure_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_major_profile_lock_pass(context)
    applied_exposure = _apply_lock_exposure_transforms()
    _stamp_exposure_contract()

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v18 exposure contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if set(applied_exposure) != set(MAJOR_LOCK_NAMES):
        raise RuntimeError("Proxy v18 did not expose every required profile lock")

    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")
    for name in MAJOR_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Exposure pass changed major lock topology: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
