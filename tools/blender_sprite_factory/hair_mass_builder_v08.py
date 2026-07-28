from __future__ import annotations

import math

import blender_sprite_factory as factory
from head_profile_v08 import load_head_detail_profile_v08


ACTIVE_HAIR_PART_NAMES = frozenset(
    {
        "hair_cap",
        "hair_back_shell",
        "hair_front_rotation_bridge",
        "hair_front_crown_mass",
        "hair_front_hairline_left",
        "hair_front_hairline_right",
        "hair_forelock_characteristic",
        "hair_side_mass_left",
        "hair_side_mass_right",
        "hair_nape_left",
        "hair_nape_center",
        "hair_nape_right",
        "hair_forelock_root",
        "hair_forelock_tip",
    }
)

REFERENCE_HAIR_PALETTE = (
    "#0B0602",
    "#1A120A",
    "#26180B",
    "#582A15",
    "#7C4924",
)


def _apply_reference_palette(context: factory.BuildContext) -> None:
    material = context.materials["hair"]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    texture = next(node for node in nodes if node.type == "TEX_IMAGE")
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    for link in tuple(output.inputs["Surface"].links):
        links.remove(link)

    rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "hair_reference_palette"
    ramp.color_ramp.interpolation = "CONSTANT"
    elements = ramp.color_ramp.elements
    elements[0].position = 0.005
    elements[0].color = (0x0B / 255.0, 0x06 / 255.0, 0x02 / 255.0, 1.0)
    elements[1].position = 0.10
    elements[1].color = (0x7C / 255.0, 0x49 / 255.0, 0x24 / 255.0, 1.0)
    for position, color in (
        (0.010, (0x1A, 0x12, 0x0A)),
        (0.020, (0x26, 0x18, 0x0B)),
        (0.045, (0x58, 0x2A, 0x15)),
    ):
        element = elements.new(position)
        element.color = tuple(value / 255.0 for value in color) + (1.0,)

    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 0.82
    links.new(texture.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(rgb_to_bw.outputs["Val"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material.use_backface_culling = False


def _remove_inactive_hair_parts() -> None:
    for obj in tuple(factory.bpy.data.objects):
        if obj.get(factory.MODULE_PROPERTY) != "hair":
            continue
        if obj.name not in ACTIVE_HAIR_PART_NAMES:
            factory.bpy.data.objects.remove(obj, do_unlink=True)


def _apply_reference_rotations(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    detail = load_head_detail_profile_v08(context.config.character_id)
    applied: dict[str, tuple[float, float, float]] = {}
    for name, degrees in detail.hair_rotations_degrees:
        if name not in ACTIVE_HAIR_PART_NAMES:
            continue
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Active reference hair part was not built: {name}")
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(math.radians(value) for value in degrees)
        applied[name] = degrees
    return applied


def consolidate_reference_hair_masses(
    context: factory.BuildContext,
) -> dict[str, tuple[float, float, float]]:
    _remove_inactive_hair_parts()
    _apply_reference_palette(context)
    applied_rotations = _apply_reference_rotations(context)

    actual_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    missing = sorted(ACTIVE_HAIR_PART_NAMES.difference(actual_names))
    unexpected = sorted(actual_names.difference(ACTIVE_HAIR_PART_NAMES))
    if missing or unexpected:
        raise RuntimeError(
            "Consolidated hair mass contract failed: "
            f"missing={missing}, unexpected={unexpected}"
        )

    factory.bpy.context.view_layer.update()
    return applied_rotations
