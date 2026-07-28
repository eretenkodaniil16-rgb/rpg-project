from __future__ import annotations

import blender_sprite_factory as factory
import hair_mass_builder_v16 as previous_builder
from hair_organic_crown_back_profile_v17 import (
    HairOrganicCrownBackProfileV17,
    load_hair_organic_crown_back_profile_v17,
)
from hair_palette_v10 import load_hair_palette_v10


_PROFILE = load_hair_organic_crown_back_profile_v17()
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
_EXPECTED_TOPOLOGY = {
    "vertices": 226,
    "faces": 256,
    "slices": 7,
    "control_points_per_slice": 16,
    "sampled_points_per_slice": 32,
}


def _organic_material_index(x: float, y: float, z: float) -> int:
    lower_boundary = 4.27 + 0.10 * x - 0.05 * y
    if z < lower_boundary:
        return 0

    rear_shadow_boundary = 4.47 - 0.10 * x
    if y > 0.28 and z < rear_shadow_boundary:
        return 0

    highlight_boundary = 4.76 - 0.18 * x + 0.08 * y
    if -0.28 < x < 0.26 and y < 0.28 and z > highlight_boundary:
        return 3

    diagonal_field = z + 0.38 * x - 0.24 * y
    if diagonal_field > 4.58:
        return 2
    return 1


def _centroid(
    vertices: list[tuple[float, float, float]],
    indices: tuple[int, ...],
) -> tuple[float, float, float]:
    count = float(len(indices))
    return tuple(
        sum(vertices[index][axis] for index in indices) / count
        for axis in range(3)
    )


def _append_face(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    material_indices: list[int],
    indices: tuple[int, ...],
) -> None:
    faces.append(indices)
    x, y, z = _centroid(vertices, indices)
    material_indices.append(_organic_material_index(x, y, z))


def _build_organic_geometry(
    profile: HairOrganicCrownBackProfileV17,
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
            _append_face(
                vertices,
                faces,
                material_indices,
                (
                    previous + point_index,
                    previous + next_index,
                    current + next_index,
                    current + point_index,
                ),
            )

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
        _append_face(
            vertices,
            faces,
            material_indices,
            (front_center, next_index, point_index),
        )

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
    for point_index in range(point_count):
        next_index = (point_index + 1) % point_count
        _append_face(
            vertices,
            faces,
            material_indices,
            (rear_center, rear_start + point_index, rear_start + next_index),
        )

    return tuple(vertices), tuple(faces), tuple(material_indices)


def _replace_integrated_mesh_with_organic_form() -> dict[str, object]:
    crown = factory.bpy.data.objects.get(_PROFILE.mesh_name)
    if crown is None:
        raise RuntimeError("Proxy v20 requires the established integrated crown object")
    if crown.get(factory.MODULE_PROPERTY) != "hair":
        raise RuntimeError("Proxy v20 crown object is not registered as hair")

    previous_materials = tuple(crown.data.materials)
    material_roles = tuple(material.get("hair_palette_role") for material in previous_materials)
    if material_roles != _EXPECTED_MATERIAL_ROLES:
        raise RuntimeError(
            "Organic crown/back mesh requires the established v10 material order: "
            f"{material_roles!r}"
        )

    vertices, faces, material_indices = _build_organic_geometry(_PROFILE)
    material_counts = {
        role: material_indices.count(index)
        for index, role in enumerate(_EXPECTED_MATERIAL_ROLES)
    }
    if any(count <= 0 for count in material_counts.values()):
        raise RuntimeError(
            "Organic diagonal tone assignment must use every established hair tone: "
            f"{material_counts}"
        )

    mesh = factory.bpy.data.meshes.new("hair_reference_crown_back_mesh_v17_organic")
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
    crown["hair_shape_zone"] = "organic_integrated_crown_back_with_broad_waves"
    crown["hair_geometry_revision"] = "v17"
    crown["hair_proxy_revision"] = "v20"
    crown["hair_mesh_strategy"] = (
        "seven_gradual_slices_with_chaikin_smoothed_broad_control_contours"
    )
    crown["hair_surface_intent"] = (
        "natural_mass_first_without_deliberately_forcing_angular_pixel_shapes"
    )
    crown["hair_tone_strategy"] = "large_organic_diagonal_regions_without_depth_bands"
    crown["hair_profile_slice_count"] = len(_PROFILE.slices)
    crown["hair_control_point_count"] = len(_PROFILE.slices[0].control_points_xz)
    crown["hair_sampled_point_count"] = len(_PROFILE.slices[0].points_xz)
    crown["hair_material_face_counts"] = str(material_counts)
    crown["hair_rear_tip_count"] = 3

    return {
        "vertices": len(vertices),
        "faces": len(faces),
        "slices": len(_PROFILE.slices),
        "control_points_per_slice": len(_PROFILE.slices[0].control_points_xz),
        "sampled_points_per_slice": len(_PROFILE.slices[0].points_xz),
        "material_counts": material_counts,
    }


def _stamp_organic_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v17"
        obj["hair_proxy_revision"] = "v20"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after organic pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_organic_crown_back_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_integrated_crown_back_pass(context)
    crown_stats = _replace_integrated_mesh_with_organic_form()
    _stamp_organic_contract()

    for key, expected in _EXPECTED_TOPOLOGY.items():
        if crown_stats[key] != expected:
            raise RuntimeError(f"Unexpected organic crown/back topology: {crown_stats}")

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v20 organic crown/back contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if REMOVED_BACK_OVERLAY_NAMES.intersection(actual_names):
        raise RuntimeError("Proxy v20 restored a redundant back overlay")
    if not RETAINED_PROFILE_LOCK_NAMES.issubset(actual_names):
        raise RuntimeError("Proxy v20 lost one or more side/nape profile locks")

    crown = factory.bpy.data.objects[_PROFILE.mesh_name]
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Organic crown/back topology drifted after construction")
    for name in RETAINED_PROFILE_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v20 changed retained profile lock topology: {name}")
    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
