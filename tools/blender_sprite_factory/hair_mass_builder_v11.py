from __future__ import annotations

import math
from typing import Protocol

import blender_sprite_factory as factory
import hair_mass_builder_v10 as previous_builder
from hair_crown_profile_v11 import load_hair_crown_profile_v11
from hair_forelock_profile_v11 import load_hair_forelock_profile_v11
from hair_lock_profile_v11 import HairLockGrooveV11, load_hair_lock_profile_v11
from hair_palette_v10 import load_hair_palette_v10


class _SliceProfile(Protocol):
    mesh_name: str
    slices: tuple


SOURCE_HAIR_PART_NAMES = previous_builder.SOURCE_HAIR_PART_NAMES
ACTIVE_HAIR_PART_NAMES = previous_builder.ACTIVE_HAIR_PART_NAMES
HAIR_ROTATION_OVERRIDES_DEGREES = previous_builder.HAIR_ROTATION_OVERRIDES_DEGREES
HAIR_SCALE_MULTIPLIERS = previous_builder.HAIR_SCALE_MULTIPLIERS
HAIR_WORLD_OFFSETS = previous_builder.HAIR_WORLD_OFFSETS
DARK_REFERENCE_HAIR_PALETTE = previous_builder.DARK_REFERENCE_HAIR_PALETTE
DARK_REFERENCE_HAIR_FACET_COLORS = previous_builder.DARK_REFERENCE_HAIR_FACET_COLORS

_CROWN_PROFILE = load_hair_crown_profile_v11()
_FORELOCK_PROFILE = load_hair_forelock_profile_v11()
_LOCK_PROFILE = load_hair_lock_profile_v11()
_PALETTE = load_hair_palette_v10()


def _apply_profile_vertices(obj: object, profile: _SliceProfile) -> None:
    point_count = len(profile.slices[0].points_xz)
    profile_vertex_count = len(profile.slices) * point_count
    expected_vertex_count = profile_vertex_count + 2
    if len(obj.data.vertices) != expected_vertex_count:
        raise RuntimeError(
            f"Unexpected topology for {obj.name}: "
            f"{len(obj.data.vertices)} vertices instead of {expected_vertex_count}"
        )

    vertex_index = 0
    for profile_slice in profile.slices:
        for x, z in profile_slice.points_xz:
            obj.data.vertices[vertex_index].co = (x, profile_slice.y, z)
            vertex_index += 1

    front_slice = profile.slices[0]
    obj.data.vertices[profile_vertex_count].co = (
        sum(point[0] for point in front_slice.points_xz) / point_count,
        front_slice.y,
        sum(point[1] for point in front_slice.points_xz) / point_count,
    )
    back_slice = profile.slices[-1]
    obj.data.vertices[profile_vertex_count + 1].co = (
        sum(point[0] for point in back_slice.points_xz) / point_count,
        back_slice.y,
        sum(point[1] for point in back_slice.points_xz) / point_count,
    )
    obj.data.update()
    obj["hair_geometry_revision"] = "v11"
    obj["hair_proxy_revision"] = "v14"


def _retone_crown(crown: object) -> None:
    if len(crown.data.materials) != 4:
        raise RuntimeError("Physical crown requires the four-role dark palette from proxy v13")
    if len(crown.data.polygons) != 64:
        raise RuntimeError("Physical crown topology changed unexpectedly")

    for polygon in crown.data.polygons:
        polygon.material_index = 1

    for band_start in (0, 16):
        for local_index in (0, 1, 10, 11, 12, 14, 15):
            crown.data.polygons[band_start + local_index].material_index = 0
        for local_index in (2, 3, 4, 5, 6, 7, 8, 9):
            crown.data.polygons[band_start + local_index].material_index = 2

    for polygon_index in (5, 7, 21):
        crown.data.polygons[polygon_index].material_index = 3

    front_cap_start = 32
    back_cap_start = 48
    for local_index in range(2, 8):
        crown.data.polygons[front_cap_start + local_index].material_index = 2
    for local_index in range(3, 9):
        crown.data.polygons[back_cap_start + local_index].material_index = 2

    crown["hair_shape_zone"] = "physical_asymmetric_large_wave_crown"
    crown["hair_tone_strategy"] = "broad_contiguous_masses_without_radial_stripes"


def _retone_forelock(forelock: object) -> None:
    if len(forelock.data.materials) != 4:
        raise RuntimeError("Physical forelock requires the four-role dark palette from proxy v13")
    if len(forelock.data.polygons) != 28:
        raise RuntimeError("Physical forelock topology changed unexpectedly")

    for polygon in forelock.data.polygons:
        polygon.material_index = 1

    for polygon_index in (0, 1, 2, 7, 8, 14, 15, 16, 21, 22):
        forelock.data.polygons[polygon_index].material_index = 2
    for polygon_index in (4, 5, 6, 11, 12, 13, 18, 19, 20):
        forelock.data.polygons[polygon_index].material_index = 0
    for polygon_index in (1, 15):
        forelock.data.polygons[polygon_index].material_index = 3

    forelock["hair_shape_zone"] = "single_physical_left_forelock"
    forelock["hair_tone_strategy"] = "root_bend_tip_with_restrained_highlight"


def _point_tangent(
    points: tuple[tuple[float, float], ...],
    index: int,
) -> tuple[float, float]:
    previous = points[max(0, index - 1)]
    following = points[min(len(points) - 1, index + 1)]
    du = following[0] - previous[0]
    dv = following[1] - previous[1]
    length = math.hypot(du, dv)
    if length <= 0.000001:
        raise ValueError("Localized lock groove contains a zero-length tangent")
    return du / length, dv / length


def _ribbon_vertices(
    groove: HairLockGrooveV11,
) -> tuple[tuple[float, float, float], ...]:
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


def _replace_local_separator_mesh(context: factory.BuildContext) -> None:
    old = factory.bpy.data.objects.get(_LOCK_PROFILE.mesh_name)
    if old is None:
        raise RuntimeError("Proxy v14 expected the proxy v13 separator mesh")
    if not old.data.materials:
        raise RuntimeError("Proxy v13 separator mesh has no dark separator material")
    separator_material = old.data.materials[0]

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

    mesh = factory.bpy.data.meshes.new(f"{_LOCK_PROFILE.mesh_name}_mesh_v11")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)

    obj = factory.bpy.data.objects.new(_LOCK_PROFILE.mesh_name, mesh)
    obj["hair_shape_zone"] = "localized_interlock_depressions"
    obj["hair_lock_groove_count"] = len(_LOCK_PROFILE.grooves)
    obj["hair_lock_groove_ranges"] = str(groove_ranges)
    obj["hair_geometry_revision"] = "v11"
    obj["hair_proxy_revision"] = "v14"
    factory._flat_shade(obj)
    factory._assign_material(obj, separator_material)
    factory._register(context, obj, "hair", "head")


def _stamp_physical_shape_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v11"
        obj["hair_proxy_revision"] = "v14"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after physical shape pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_physical_lock_shape_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    applied_rotations = previous_builder.apply_dark_reference_hair_pass(context)

    crown = factory.bpy.data.objects.get(_CROWN_PROFILE.mesh_name)
    forelock = factory.bpy.data.objects.get(_FORELOCK_PROFILE.mesh_name)
    if crown is None or forelock is None:
        raise RuntimeError("Proxy v14 requires the established crown and forelock meshes")

    _apply_profile_vertices(crown, _CROWN_PROFILE)
    _apply_profile_vertices(forelock, _FORELOCK_PROFILE)
    _retone_crown(crown)
    _retone_forelock(forelock)
    _replace_local_separator_mesh(context)
    _stamp_physical_shape_contract()

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v14 physical hair contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )

    for name in actual_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return applied_rotations
