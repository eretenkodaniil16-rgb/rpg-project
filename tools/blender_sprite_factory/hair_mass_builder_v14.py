from __future__ import annotations

import math

import blender_sprite_factory as factory
import hair_mass_builder_v13 as previous_builder
from hair_major_lock_profile_v14 import HairMajorLockV14, load_hair_major_lock_profile_v14
from hair_palette_v10 import load_hair_palette_v10


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS

_MAJOR_LOCK_PROFILE = load_hair_major_lock_profile_v14()
_PALETTE = load_hair_palette_v10()
MAJOR_LOCK_NAMES = frozenset(lock.name for lock in _MAJOR_LOCK_PROFILE.locks)


def _build_major_lock_geometry(
    lock: HairMajorLockV14,
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[int, ...], ...],
]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    sides = lock.ring_sides
    extent_x, extent_y, extent_z = lock.half_extent
    angle_offset = math.pi / sides

    for ring in lock.rings:
        for side_index in range(sides):
            angle = angle_offset + (math.tau * side_index / sides)
            x = (
                ring.center_x_ratio
                + math.cos(angle) * ring.radius_x_ratio
            ) * extent_x
            y = (
                ring.center_y_ratio
                + math.sin(angle) * ring.radius_y_ratio
            ) * extent_y
            z = ring.z_ratio * extent_z
            vertices.append((x, y, z))

    for ring_index in range(len(lock.rings) - 1):
        upper = ring_index * sides
        lower = (ring_index + 1) * sides
        for side_index in range(sides):
            next_index = (side_index + 1) % sides
            faces.append(
                (
                    upper + side_index,
                    upper + next_index,
                    lower + next_index,
                    lower + side_index,
                )
            )

    top_ring = lock.rings[0]
    top_center = len(vertices)
    vertices.append(
        (
            top_ring.center_x_ratio * extent_x,
            top_ring.center_y_ratio * extent_y,
            top_ring.z_ratio * extent_z,
        )
    )
    for side_index in range(sides):
        next_index = (side_index + 1) % sides
        faces.append((top_center, side_index, next_index))

    bottom_ring = lock.rings[-1]
    bottom_start = (len(lock.rings) - 1) * sides
    bottom_center = len(vertices)
    vertices.append(
        (
            bottom_ring.center_x_ratio * extent_x,
            bottom_ring.center_y_ratio * extent_y,
            bottom_ring.z_ratio * extent_z,
        )
    )
    for side_index in range(sides):
        next_index = (side_index + 1) % sides
        faces.append(
            (
                bottom_center,
                bottom_start + next_index,
                bottom_start + side_index,
            )
        )

    return tuple(vertices), tuple(faces)


def _replace_ellipsoid_with_major_lock(lock: HairMajorLockV14) -> dict[str, int]:
    obj = factory.bpy.data.objects.get(lock.name)
    if obj is None:
        raise RuntimeError(f"Proxy v17 lock target was not built: {lock.name}")
    if obj.get(factory.MODULE_PROPERTY) != "hair":
        raise RuntimeError(f"Proxy v17 lock target is not a hair module: {lock.name}")
    if obj.get("hair_physical_side") != lock.physical_side:
        raise RuntimeError(f"Physical side drift before lock replacement: {lock.name}")

    previous_materials = tuple(obj.data.materials)
    if len(previous_materials) != 1:
        raise RuntimeError(f"Major lock expects one established material: {lock.name}")
    material_role = previous_materials[0].get("hair_palette_role")
    if material_role != lock.material_role:
        raise RuntimeError(
            f"Major lock material role drift on {lock.name}: "
            f"{material_role!r} instead of {lock.material_role!r}"
        )

    vertices, faces = _build_major_lock_geometry(lock)
    mesh = factory.bpy.data.meshes.new(f"{lock.name}_profile_mesh_v14")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)
    for material in previous_materials:
        mesh.materials.append(material)

    previous_mesh = obj.data
    obj.data = mesh
    if previous_mesh.users == 0:
        factory.bpy.data.meshes.remove(previous_mesh)

    factory._flat_shade(obj)
    obj[factory.MATERIAL_PROPERTY] = "hair"
    obj["hair_shape_zone"] = f"profile_major_{lock.zone}_lock"
    obj["hair_physical_side"] = lock.physical_side
    obj["hair_material_role"] = lock.material_role
    obj["hair_geometry_revision"] = "v14"
    obj["hair_proxy_revision"] = "v17"
    obj["hair_mesh_strategy"] = "six_ring_pointed_profile_replacing_uv_ellipsoid"
    obj["hair_profile_ring_count"] = len(lock.rings)
    obj["hair_profile_ring_sides"] = lock.ring_sides
    obj["hair_profile_half_extent"] = str(lock.half_extent)

    return {
        "vertices": len(vertices),
        "faces": len(faces),
        "rings": len(lock.rings),
        "ring_sides": lock.ring_sides,
    }


def _replace_major_lock_meshes() -> dict[str, dict[str, int]]:
    return {
        lock.name: _replace_ellipsoid_with_major_lock(lock)
        for lock in _MAJOR_LOCK_PROFILE.locks
    }


def _stamp_major_lock_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v14"
        obj["hair_proxy_revision"] = "v17"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after major lock pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_major_profile_lock_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_side_back_silhouette_pass(context)
    replacement_stats = _replace_major_lock_meshes()
    _stamp_major_lock_contract()

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v17 major lock contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if set(replacement_stats) != set(MAJOR_LOCK_NAMES):
        raise RuntimeError("Proxy v17 did not replace every required major lock mesh")

    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")
    for name in MAJOR_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Unexpected major lock topology after replacement: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
