from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import blender_sprite_factory as factory
import blender_sprite_factory_head_v21 as head_adapter
from appearance_readability_profile_v01 import (
    AppearanceReadabilityProfileV01,
    load_appearance_readability_profile_v01,
)
from factory_config import FactoryConfig, MaterialSlot


BASE_LOAD_FACTORY_CONFIG = factory.load_factory_config
BASE_CREATE_MATERIAL = factory._create_material
BASE_BUILD_ARMOR = factory._build_armor
BASE_BUILD_ARMS = factory._build_arms
BASE_BUILD_LEGS = factory._build_legs
BASE_BUILD_ACCESSORIES = factory._build_accessories

_PROFILE = load_appearance_readability_profile_v01("human_warrior_m01")
_EXPECTED_PREVIOUS_HAIR_COUNT = 10
_EXPECTED_FINAL_HAIR_COUNT = 12
_CROWN_NAME = "hair_reference_crown_mesh"


def _rgb(hex_color: str) -> tuple[float, float, float]:
    return factory._hex_rgb_normalized(hex_color)


def load_factory_config_appearance_v01(
    manifest_path: Path,
    repo_root: Path,
) -> FactoryConfig:
    config = BASE_LOAD_FACTORY_CONFIG(manifest_path, repo_root)
    profile = load_appearance_readability_profile_v01(config.character_id)
    palette = tuple(dict.fromkeys((*config.quantization_palette, *profile.quantization_additions)))
    if len(palette) != len(config.quantization_palette) + len(profile.quantization_additions):
        raise RuntimeError("Appearance v01 quantization additions collided with the base palette")
    return replace(config, quantization_palette=palette)


def create_material_appearance_v01(slot: MaterialSlot) -> object:
    material = BASE_CREATE_MATERIAL(slot)
    color = _PROFILE.material_override_map().get(slot.slot_id)
    if color is None:
        return material

    shader = next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"),
        None,
    )
    if shader is None:
        raise RuntimeError(f"Appearance v01 cannot find Principled shader: {slot.slot_id}")
    base_input = shader.inputs.get("Base Color")
    if base_input is None:
        raise RuntimeError(f"Appearance v01 cannot find Base Color input: {slot.slot_id}")
    for link in tuple(base_input.links):
        material.node_tree.links.remove(link)
    base_input.default_value = (*_rgb(color), 1.0)
    material.diffuse_color = (*_rgb(color), 1.0)
    material["appearance_revision"] = _PROFILE.revision
    material["appearance_override_hex"] = color
    material["appearance_texture_link_disabled"] = True
    return material


def _constant_material(
    name: str,
    hex_color: str,
    roughness: float,
    metallic: float = 0.0,
) -> object:
    existing = factory.bpy.data.materials.get(name)
    if existing is not None:
        return existing
    material = factory.bpy.data.materials.new(name)
    material.diffuse_color = (*_rgb(hex_color), 1.0)
    material.use_nodes = True
    material["appearance_revision"] = _PROFILE.revision
    material["appearance_override_hex"] = hex_color
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*_rgb(hex_color), 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _coordinates(obj: object) -> tuple[tuple[float, float, float], ...]:
    return tuple(tuple(float(value) for value in vertex.co) for vertex in obj.data.vertices)


def _hair_names() -> set[str]:
    return {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }


def _base_hair_material(crown: object) -> object:
    for material in crown.data.materials:
        if material.get("hair_palette_role") == "base":
            return material
    side = factory.bpy.data.objects.get("hair_side_mass_left")
    if side is None or not side.data.materials:
        raise RuntimeError("Appearance v01 cannot resolve a base hair material")
    return side.data.materials[0]


def _apply_existing_hair_volume(profile: AppearanceReadabilityProfileV01) -> None:
    for transform in profile.hair_transforms:
        obj = factory.bpy.data.objects.get(transform.name)
        if obj is None:
            raise RuntimeError(f"Appearance v01 cannot find hair target: {transform.name}")
        if len(obj.data.vertices) != 38 or len(obj.data.polygons) != 42:
            raise RuntimeError(f"Appearance v01 found changed side/nape topology: {transform.name}")
        before = tuple(float(value) for value in obj.scale)
        obj.scale = tuple(
            before[index] * transform.scale_multiplier[index]
            for index in range(3)
        )
        after = tuple(float(value) for value in obj.scale)
        if any(current < previous for current, previous in zip(after, before)):
            raise RuntimeError(f"Appearance v01 reduced hair volume: {transform.name}")
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(
            float(obj.rotation_euler[index])
            + math.radians(transform.rotation_delta_degrees[index])
            for index in range(3)
        )
        matrix = obj.matrix_world.copy()
        matrix.translation += factory.Vector(transform.world_offset)
        obj.matrix_world = matrix
        obj["hair_coverage_revision"] = "v22"
        obj["hair_coverage_strategy"] = "increase_side_and_nape_mass_without_crown_reduction"
        obj["hair_fill_scale_multiplier"] = str(transform.scale_multiplier)
        obj["hair_fill_world_offset"] = str(transform.world_offset)
        obj["hair_fill_rotation_delta_degrees"] = str(transform.rotation_delta_degrees)


def _create_temple_fills(
    context: factory.BuildContext,
    profile: AppearanceReadabilityProfileV01,
    crown: object,
) -> None:
    material = _base_hair_material(crown)
    for spec in profile.temple_fills:
        if factory.bpy.data.objects.get(spec.name) is not None:
            raise RuntimeError(f"Appearance v01 temple fill already exists: {spec.name}")
        obj = factory._ellipsoid(
            spec.name,
            spec.location,
            spec.scale,
            material,
            segments=10,
            rings=6,
        )
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(math.radians(value) for value in spec.rotation_degrees)
        factory._register(context, obj, "hair", "head", spec.physical_side)
        obj["hair_shape_zone"] = "temple_coverage_fill"
        obj["hair_physical_side"] = spec.physical_side
        obj["hair_geometry_revision"] = "v22"
        obj["hair_proxy_revision"] = "v25"
        obj["hair_coverage_revision"] = "v22"
        obj["hair_fill_strategy"] = "close_visible_temple_skin_gap_without_mirroring"


def build_head_and_hair_appearance_v01(context: factory.BuildContext) -> None:
    if context.head.revision != "v22" or context.proxy_revision != "v25":
        raise RuntimeError("Appearance v01 requires head v22 / proxy v25")
    head_adapter._build_head_and_hair_v21(context)

    previous_names = _hair_names()
    if len(previous_names) != _EXPECTED_PREVIOUS_HAIR_COUNT:
        raise RuntimeError(
            f"Appearance v01 expected {_EXPECTED_PREVIOUS_HAIR_COUNT} hair objects, "
            f"found {len(previous_names)}"
        )
    crown = factory.bpy.data.objects.get(_CROWN_NAME)
    if crown is None:
        raise RuntimeError("Appearance v01 cannot find the accepted dense crown")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Appearance v01 must preserve crown topology 226/256")
    crown_coordinates = _coordinates(crown)

    _apply_existing_hair_volume(_PROFILE)
    _create_temple_fills(context, _PROFILE, crown)

    final_names = _hair_names()
    expected_fills = {item.name for item in _PROFILE.temple_fills}
    if final_names != previous_names.union(expected_fills):
        raise RuntimeError("Appearance v01 changed unexpected hair object identities")
    if len(final_names) != _EXPECTED_FINAL_HAIR_COUNT:
        raise RuntimeError("Appearance v01 must finish with twelve hair objects")
    if _coordinates(crown) != crown_coordinates:
        raise RuntimeError("Appearance v01 must not modify crown vertex coordinates")

    for name in final_names:
        obj = factory.bpy.data.objects[name]
        if any(float(value) <= 0.0 for value in obj.scale):
            raise RuntimeError(f"Appearance v01 found non-positive hair scale: {name}")
        obj["hair_proxy_revision"] = "v25"
        obj["appearance_revision"] = _PROFILE.revision
    crown["hair_coverage_revision"] = "v22"
    crown["hair_coverage_strategy"] = "keep_dense_proxy_v24_crown_and_fill_temples"
    factory.bpy.context.view_layer.update()


def _apply_object_transforms(profile: AppearanceReadabilityProfileV01) -> None:
    for transform in profile.object_transforms:
        obj = factory.bpy.data.objects.get(transform.name)
        if obj is None:
            raise RuntimeError(f"Appearance v01 cannot find clothing object: {transform.name}")
        before = tuple(float(value) for value in obj.scale)
        obj.scale = tuple(
            before[index] * transform.scale_multiplier[index]
            for index in range(3)
        )
        matrix = obj.matrix_world.copy()
        matrix.translation += factory.Vector(transform.world_offset)
        obj.matrix_world = matrix
        obj["appearance_revision"] = profile.revision
        obj["readability_scale_multiplier"] = str(transform.scale_multiplier)
        obj["readability_world_offset"] = str(transform.world_offset)


def _assign_scarf_highlight(obj: object, material: object) -> int:
    material_index = len(obj.data.materials)
    obj.data.materials.append(material)
    assigned = 0
    normal_matrix = obj.matrix_world.to_3x3()
    for polygon in obj.data.polygons:
        world_normal = normal_matrix @ polygon.normal
        should_highlight = (
            world_normal.y < -0.32
            or (world_normal.z > 0.46 and world_normal.y < 0.25)
        )
        if should_highlight:
            polygon.material_index = material_index
            assigned += 1
    if assigned <= 0:
        raise RuntimeError(f"Appearance v01 could not assign scarf highlight: {obj.name}")
    obj["scarf_highlight_face_count"] = assigned
    return assigned


def _build_clothing_details(
    context: factory.BuildContext,
    profile: AppearanceReadabilityProfileV01,
) -> None:
    for spec in profile.clothing_details:
        if factory.bpy.data.objects.get(spec.name) is not None:
            raise RuntimeError(f"Appearance clothing detail already exists: {spec.name}")
        material = context.materials.get(spec.material_slot_id)
        if material is None:
            raise RuntimeError(f"Appearance detail material is missing: {spec.material_slot_id}")
        detail = factory._box(
            spec.name,
            spec.location,
            spec.dimensions,
            material,
            spec.bevel,
        )
        factory._register(context, detail, spec.module_id, spec.bone_name)
        detail["appearance_revision"] = profile.revision
        detail["clothing_readability_role"] = spec.name


def build_armor_appearance_v01(context: factory.BuildContext) -> None:
    BASE_BUILD_ARMOR(context)
    _apply_object_transforms(_PROFILE)
    highlight = _constant_material(
        "MAT_scarf_highlight_v01",
        _PROFILE.scarf_highlight_hex,
        roughness=0.88,
    )
    _assign_scarf_highlight(factory.bpy.data.objects["scarf_wrap"], highlight)
    _assign_scarf_highlight(factory.bpy.data.objects["scarf_front"], highlight)
    _build_clothing_details(context, _PROFILE)
    factory.bpy.context.view_layer.update()


def build_arms_appearance_v01(context: factory.BuildContext) -> None:
    BASE_BUILD_ARMS(context)
    for name in (
        "arm_forearm_L",
        "arm_forearm_R",
        "pauldron_left_outer",
        "pauldron_left_inner",
    ):
        obj = factory.bpy.data.objects.get(name)
        if obj is not None:
            obj["appearance_revision"] = _PROFILE.revision


def build_legs_appearance_v01(context: factory.BuildContext) -> None:
    BASE_BUILD_LEGS(context)
    for name in ("leg_knee_L", "leg_knee_R", "leg_shin_L", "leg_shin_R"):
        obj = factory.bpy.data.objects.get(name)
        if obj is not None:
            obj["appearance_revision"] = _PROFILE.revision


def build_accessories_appearance_v01(context: factory.BuildContext) -> None:
    BASE_BUILD_ACCESSORIES(context)
    for obj in factory.bpy.data.objects:
        if obj.get(factory.MODULE_PROPERTY) in {"back_cloth", "pouch", "sword_scabbard"}:
            obj["appearance_revision"] = _PROFILE.revision
    factory.bpy.context.view_layer.update()
