from __future__ import annotations

import blender_sprite_factory as factory
import hair_mass_builder_v15 as previous_builder
from hair_integrated_crown_back_profile_v16 import (
    HairIntegratedCrownBackProfileV16,
    load_hair_integrated_crown_back_profile_v16,
)
from hair_palette_v10 import load_hair_palette_v10


_PROFILE = load_hair_integrated_crown_back_profile_v16()
_PALETTE = load_hair_palette_v10()

REMOVED_BACK_OVERLAY_NAMES = frozenset(_PROFILE.removed_overlay_names)
RETAINED_PROFILE_LOCK_NAMES = frozenset(_PROFILE.retained_profile_lock_names)
SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES.difference(
    REMOVED_BACK_OVERLAY_NAMES
)
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES.difference(
    REMOVED_BACK_OVERLAY_NAMES
)
MAJOR_LOCK_NAMES = previous_builder.MAJOR_LOCK_NAMES.difference(
    REMOVED_BACK_OVERLAY_NAMES
)
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS

_EXPECTED_MATERIAL_ROLES = ("shadow", "base", "mid", "highlight")
_BOTTOM_INDICES = frozenset({0, 11, 12, 13, 14, 15})
_TOP_HIGHLIGHT_INDICES = frozenset({3, 5, 7})
_TOP_MID_INDICES = frozenset({2, 4, 6, 8, 9})


def _panel_material_index(depth_segment: int, point_index: int) -> int:
    if point_index in _BOTTOM_INDICES:
        return 0 if depth_segment >= 1 else 1
    if point_index in _TOP_HIGHLIGHT_INDICES:
        return 3 if depth_segment <= 1 else 2
    if point_index in _TOP_MID_INDICES:
        return 2
    return 1


def _build_integrated_geometry(
    profile: HairIntegratedCrownBackProfileV16,
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, ...], ...],
    tuple[int, ...],
]:
    point_count = len(profile.slices[0].points_xz)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    material_indices: list[int] = []

    for profile_slice in profile.slices:
        vertices.extend((x, profile_slice.y, z) for x, z in profile_slice.points_xz)

    for slice_index in range(len(profile.slices) - 1):
        previous = slice_index * point_count
        current = (slice_index + 1) * point_count
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
            material_indices.append(_panel_material_index(slice_index, point_index))

    front = profile.slices[0]
    front_center = len(vertices)
    vertices.append(
        (
            sum(point[0] for point in front.points_xz) / point_count,
            front.y,
            sum(point[1] for point in front.points_xz) / point_count,
        )
    )
    for point_index in range(point_count):
        next_index = (point_index + 1) % point_count
        faces.append((front_center, next_index, point_index))
        material_indices.append(_panel_material_index(0, point_index))

    rear = profile.slices[-1]
    rear_start = (len(profile.slices) - 1) * point_count
    rear_center = len(vertices)
    vertices.append(
        (
            sum(point[0] for point in rear.points_xz) / point_count,
            rear.y,
            sum(point[1] for point in rear.points_xz) / point_count,
        )
    )
    rear_segment = len(profile.slices) - 2
    for point_index in range(point_count):
        next_index = (point_index + 1) % point_count
        faces.append(
            (
                rear_center,
                rear_start + point_index,
                rear_start + next_index,
            )
        )
        material_indices.append(_panel_material_index(rear_segment, point_index))

    return tuple(vertices), tuple(faces), tuple(material_indices)


def _replace_crown_with_integrated_mesh() -> dict[str, int]:
    crown = factory.bpy.data.objects.get(_PROFILE.mesh_name)
    if crown is None:
        raise RuntimeError("Proxy v19 requires the established crown object")
    if crown.get(factory.MODULE_PROPERTY) != "hair":
        raise RuntimeError("Proxy v19 crown object is not registered as hair")

    previous_materials = tuple(crown.data.materials)
    material_roles = tuple(material.get("hair_palette_role") for material in previous_materials)
    if material_roles != _EXPECTED_MATERIAL_ROLES:
        raise RuntimeError(
            "Integrated crown/back mesh requires the established v10 material order: "
            f"{material_roles!r}"
        )

    vertices, faces, material_indices = _build_integrated_geometry(_PROFILE)
    mesh = factory.bpy.data.meshes.new("hair_reference_crown_back_mesh_v16")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)
    for material in previous_materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index

    previous_mesh = crown.data
    crown.data = mesh
    if previous_mesh.users == 0:
        factory.bpy.data.meshes.remove(previous_mesh)

    factory._flat_shade(crown)
    crown[factory.MATERIAL_PROPERTY] = "hair"
    crown["hair_shape_zone"] = "integrated_crown_back_with_three_broad_rear_tips"
    crown["hair_geometry_revision"] = "v16"
    crown["hair_proxy_revision"] = "v19"
    crown["hair_mesh_strategy"] = "five_slice_integrated_crown_back_replacing_overlapping_shells"
    crown["hair_profile_slice_count"] = len(_PROFILE.slices)
    crown["hair_profile_point_count"] = len(_PROFILE.slices[0].points_xz)
    crown["hair_removed_back_overlays"] = str(tuple(sorted(REMOVED_BACK_OVERLAY_NAMES)))
    crown["hair_rear_tip_count"] = 3

    return {
        "vertices": len(vertices),
        "faces": len(faces),
        "slices": len(_PROFILE.slices),
        "points_per_slice": len(_PROFILE.slices[0].points_xz),
    }


def _remove_redundant_back_overlays() -> tuple[str, ...]:
    removed: list[str] = []
    for name in sorted(REMOVED_BACK_OVERLAY_NAMES):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Proxy v19 redundant back overlay was not built: {name}")
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            raise RuntimeError(f"Proxy v19 removal target is not hair: {name}")
        previous_mesh = obj.data
        factory.bpy.data.objects.remove(obj, do_unlink=True)
        if previous_mesh.users == 0:
            factory.bpy.data.meshes.remove(previous_mesh)
        removed.append(name)
    return tuple(removed)


def _stamp_integrated_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v16"
        obj["hair_proxy_revision"] = "v19"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after integrated pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_integrated_crown_back_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_major_lock_exposure_pass(context)
    crown_stats = _replace_crown_with_integrated_mesh()
    removed_names = _remove_redundant_back_overlays()
    _stamp_integrated_contract()

    if set(removed_names) != set(REMOVED_BACK_OVERLAY_NAMES):
        raise RuntimeError("Proxy v19 did not remove every redundant back overlay")
    if crown_stats != {
        "vertices": 82,
        "faces": 96,
        "slices": 5,
        "points_per_slice": 16,
    }:
        raise RuntimeError(f"Unexpected integrated crown/back topology: {crown_stats}")

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v19 integrated crown/back contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if REMOVED_BACK_OVERLAY_NAMES.intersection(actual_names):
        raise RuntimeError("Proxy v19 retained a redundant back overlay")
    if not RETAINED_PROFILE_LOCK_NAMES.issubset(actual_names):
        raise RuntimeError("Proxy v19 lost one or more side/nape profile locks")

    crown = factory.bpy.data.objects[_PROFILE.mesh_name]
    if len(crown.data.vertices) != 82 or len(crown.data.polygons) != 96:
        raise RuntimeError("Integrated crown/back topology drifted after construction")
    for name in RETAINED_PROFILE_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v19 changed retained profile lock topology: {name}")
    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
