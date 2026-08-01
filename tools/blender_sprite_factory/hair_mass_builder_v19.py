from __future__ import annotations

import blender_sprite_factory as factory
import hair_mass_builder_v18 as previous_builder
from hair_mass_builder_v17 import _build_organic_geometry, _centroid
from hair_organic_tone_profile_v18 import load_hair_organic_tone_profile_v18
from hair_palette_v10 import load_hair_palette_v10
from hair_volume_crown_back_profile_v19 import (
    HairVolumeCrownBackProfileV19,
    load_hair_volume_crown_back_profile_v19,
)


_PROFILE = load_hair_volume_crown_back_profile_v19()
_TONE_PROFILE = load_hair_organic_tone_profile_v18()
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


def _assert_previous_tone_state() -> tuple[object, set[str]]:
    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Proxy v22 expected one completed proxy v21 scene before volume refinement: "
            f"missing={missing}, unexpected={unexpected}"
        )
    if REMOVED_BACK_OVERLAY_NAMES.intersection(actual_names):
        raise RuntimeError("Proxy v22 restored a redundant back overlay")
    if not RETAINED_PROFILE_LOCK_NAMES.issubset(actual_names):
        raise RuntimeError("Proxy v22 lost one or more side/nape profile locks")

    crown = factory.bpy.data.objects.get(_PROFILE.mesh_name)
    if crown is None:
        raise RuntimeError("Proxy v22 cannot find the proxy v21 organic crown")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v22 must refine the established proxy v21 topology")
    if crown.get("hair_proxy_revision") != "v21":
        raise RuntimeError("Proxy v22 requires the completed proxy v21 tone state")

    material_roles = tuple(
        material.get("hair_palette_role") for material in crown.data.materials
    )
    if material_roles != _EXPECTED_MATERIAL_ROLES:
        raise RuntimeError(
            "Proxy v22 requires the established v10 crown material order: "
            f"{material_roles!r}"
        )
    for name in RETAINED_PROFILE_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v22 found invalid retained profile lock: {name}")
    return crown, actual_names


def _localized_material_indices(
    vertices: tuple[tuple[float, float, float], ...],
    faces: tuple[tuple[int, ...], ...],
) -> tuple[int, ...]:
    indices: list[int] = []
    for face in faces:
        x, y, z = _centroid(vertices, face)
        indices.append(
            previous_builder._material_index_for_position(
                _TONE_PROFILE,
                x,
                y,
                z,
            )
        )
    return tuple(indices)


def _replace_crown_with_tapered_volume(
    profile: HairVolumeCrownBackProfileV19,
    crown: object,
) -> dict[str, object]:
    previous_materials = tuple(crown.data.materials)
    material_roles = tuple(
        material.get("hair_palette_role") for material in previous_materials
    )
    if material_roles != _EXPECTED_MATERIAL_ROLES:
        raise RuntimeError(
            "Tapered volume mesh requires the established v10 material order: "
            f"{material_roles!r}"
        )

    vertices, faces, _ = _build_organic_geometry(profile)
    material_indices = _localized_material_indices(vertices, faces)
    material_counts = {
        role: material_indices.count(index)
        for index, role in enumerate(_EXPECTED_MATERIAL_ROLES)
    }
    if any(count <= 0 for count in material_counts.values()):
        raise RuntimeError(
            "Tapered volume pass must preserve every established hair tone: "
            f"{material_counts}"
        )
    if material_counts["base"] <= material_counts["mid"]:
        raise RuntimeError(f"Base tone must remain the dominant hair mass: {material_counts}")
    if not 4 <= material_counts["highlight"] <= 24:
        raise RuntimeError(f"Highlight must remain a small local patch: {material_counts}")

    mesh = factory.bpy.data.meshes.new("hair_reference_crown_back_mesh_v19_volume")
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
    crown["hair_shape_zone"] = "organic_integrated_crown_back_with_centered_volume_taper"
    crown["hair_geometry_revision"] = "v19"
    crown["hair_proxy_revision"] = "v22"
    crown["hair_tone_revision"] = _TONE_PROFILE.revision
    crown["hair_mesh_strategy"] = (
        "seven_gradual_slices_with_broad_center_rise_and_smooth_rear_taper"
    )
    crown["hair_surface_intent"] = (
        "natural_mass_first_without_forced_angularity_or_monolithic_cap"
    )
    crown["hair_tone_strategy"] = (
        "reuse_v18_localized_dark_tones_on_refined_v19_geometry"
    )
    crown["hair_profile_slice_count"] = len(profile.slices)
    crown["hair_control_point_count"] = len(profile.slices[0].control_points_xz)
    crown["hair_sampled_point_count"] = len(profile.slices[0].points_xz)
    crown["hair_material_face_counts"] = str(material_counts)
    crown["hair_rear_tip_count"] = 3

    return {
        "vertices": len(vertices),
        "faces": len(faces),
        "slices": len(profile.slices),
        "control_points_per_slice": len(profile.slices[0].control_points_xz),
        "sampled_points_per_slice": len(profile.slices[0].points_xz),
        "material_counts": material_counts,
    }


def _stamp_volume_contract() -> None:
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        obj["hair_geometry_revision"] = "v19"
        obj["hair_proxy_revision"] = "v22"
        obj["hair_palette_source_revision"] = _PALETTE.revision
        obj["hair_palette_source_proxy_revision"] = _PALETTE.proxy_revision
        if not obj.data.materials:
            raise RuntimeError(f"Hair object has no material after volume pass: {obj.name}")
        for material in obj.data.materials:
            if material.get("hair_palette_revision") != _PALETTE.revision:
                raise RuntimeError(f"Hair object retained a non-v10 palette material: {obj.name}")


def apply_centered_volume_taper_pass(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    crown, previous_names = _assert_previous_tone_state()
    crown_stats = _replace_crown_with_tapered_volume(_PROFILE, crown)
    _stamp_volume_contract()

    for key, expected in _EXPECTED_TOPOLOGY.items():
        if crown_stats[key] != expected:
            raise RuntimeError(f"Unexpected tapered crown/back topology: {crown_stats}")

    current_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    if current_names != previous_names:
        raise RuntimeError("Proxy v22 must refine volume without changing hair object identities")
    if REMOVED_BACK_OVERLAY_NAMES.intersection(current_names):
        raise RuntimeError("Proxy v22 restored a redundant back overlay")
    if not RETAINED_PROFILE_LOCK_NAMES.issubset(current_names):
        raise RuntimeError("Proxy v22 lost one or more side/nape profile locks")

    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v22 crown topology drifted after construction")
    if sum(crown_stats["material_counts"].values()) != len(crown.data.polygons):
        raise RuntimeError("Proxy v22 did not assign a tone to every crown polygon")
    for name in RETAINED_PROFILE_LOCK_NAMES:
        obj = factory.bpy.data.objects[name]
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Proxy v22 changed retained profile lock topology: {name}")
    for name in current_names:
        obj = factory.bpy.data.objects[name]
        if any(value <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Hair object has non-positive scale: {name}")

    factory.bpy.context.view_layer.update()
    return dict(HAIR_ROTATION_OVERRIDES_DEGREES)
