from __future__ import annotations

import math

import blender_sprite_factory as factory
import combat_idle_down_weapon_variants_builder_v05 as previous_builder
from combat_idle_down_weapon_variants_profile_v06 import (
    BLADE_TIP_LENGTH,
    ONE_HAND_BLADE_LENGTH,
    ONE_HAND_GRIP_LENGTH,
    TWO_HAND_AWAY_Y,
    TWO_HAND_BLADE_LENGTH,
    TWO_HAND_CENTER_X_OFFSET,
    TWO_HAND_GRIP_LENGTH,
    load_weapon_stance_profile_v06,
)


ONE_HAND_V06_OBJECT_NAMES = (
    "combat_onehand_v06_blade",
    "combat_onehand_v06_highlight",
    "combat_onehand_v06_tip",
    "combat_onehand_v06_guard",
    "combat_onehand_v06_grip",
    "combat_onehand_v06_pommel",
)
TWO_HAND_LOW_V06_OBJECT_NAMES = (
    "combat_twohand_low_v06_blade",
    "combat_twohand_low_v06_highlight",
    "combat_twohand_low_v06_tip",
    "combat_twohand_low_v06_guard",
    "combat_twohand_low_v06_grip",
    "combat_twohand_low_v06_pommel",
)
TWO_HAND_HIGH_V06_OBJECT_NAMES = (
    "combat_twohand_high_v06_blade",
    "combat_twohand_high_v06_highlight",
    "combat_twohand_high_v06_tip",
    "combat_twohand_high_v06_guard",
    "combat_twohand_high_v06_grip",
    "combat_twohand_high_v06_pommel",
)


def _ensure_highlight_material() -> object:
    name = "MAT_combat_sword_highlight_v06"
    existing = factory.bpy.data.materials.get(name)
    if existing is not None:
        return existing
    material = factory.bpy.data.materials.new(name)
    color = factory._hex_to_linear_rgb("#B09B9D")
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    material["material_slot_id"] = "combat_sword_highlight_v06"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = 0.78
    shader.inputs["Roughness"].default_value = 0.26
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return material


def _register_part(
    context: factory.BuildContext,
    obj: object,
    *,
    weapon_id: str,
    weapon_part: str,
    physical_side: str,
    variant_id: str,
) -> object:
    registered = factory._register(
        context,
        obj,
        "combat_weapon",
        "hand.R",
        physical_side,
    )
    registered["weapon_id"] = weapon_id
    registered["weapon_part"] = weapon_part
    registered["weapon_state"] = "drawn"
    registered["weapon_variant_id"] = variant_id
    registered["combat_idle_weapon_variants_revision"] = "v06"
    registered.hide_render = True
    registered.hide_viewport = True
    return registered


def _pointed_tip(
    name: str,
    blade_end: factory.Vector,
    direction: factory.Vector,
    radius: float,
    material: object,
) -> object:
    center = blade_end + direction * (BLADE_TIP_LENGTH * 0.5)
    rotation = direction.to_track_quat("Z", "Y").to_euler()
    return factory._frustum(
        name,
        tuple(center),
        radius,
        0.0,
        BLADE_TIP_LENGTH,
        4,
        material,
        rotation=tuple(rotation),
    )


def _build_one_hand_v06(context: factory.BuildContext) -> tuple[object, ...]:
    hand = context.rig.pose.bones["hand.R"]
    anchor = context.rig.matrix_world @ ((hand.head + hand.tail) * 0.5)
    direction = factory.Vector((0.37, -0.16, -1.0)).normalized()
    guard_lateral = factory.Vector((0.90, 0.40, 0.0)).normalized()
    highlight_material = _ensure_highlight_material()

    grip_start = anchor - direction * (ONE_HAND_GRIP_LENGTH * 0.46)
    grip_end = anchor + direction * (ONE_HAND_GRIP_LENGTH * 0.54)
    pommel_center = grip_start - direction * 0.13
    guard_center = grip_end + direction * 0.08
    blade_start = guard_center + direction * 0.12
    blade_end = blade_start + direction * ONE_HAND_BLADE_LENGTH
    guard_extent = guard_lateral * 0.36
    highlight_offset = guard_lateral * 0.075 + factory.Vector((0.0, -0.025, 0.0))

    blade = factory._cylinder_between(
        "combat_onehand_v06_blade",
        tuple(blade_start),
        tuple(blade_end),
        0.135,
        4,
        context.materials["silver"],
    )
    highlight = factory._cylinder_between(
        "combat_onehand_v06_highlight",
        tuple(blade_start + highlight_offset),
        tuple(blade_end + highlight_offset),
        0.035,
        4,
        highlight_material,
    )
    tip = _pointed_tip(
        "combat_onehand_v06_tip",
        blade_end,
        direction,
        0.135,
        context.materials["silver"],
    )
    guard = factory._cylinder_between(
        "combat_onehand_v06_guard",
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.067,
        4,
        context.materials["silver"],
    )
    grip = factory._cylinder_between(
        "combat_onehand_v06_grip",
        tuple(grip_start),
        tuple(grip_end),
        0.086,
        8,
        context.materials["boots"],
    )
    pommel = factory._ellipsoid(
        "combat_onehand_v06_pommel",
        tuple(pommel_center),
        (0.14, 0.14, 0.16),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )
    parts = (blade, highlight, tip, guard, grip, pommel)
    part_names = ("blade", "highlight", "tip", "guard", "grip", "pommel")
    return tuple(
        _register_part(
            context,
            obj,
            weapon_id="sword_01_onehand_long_v06",
            weapon_part=part_name,
            physical_side="right",
            variant_id="onehand_shared",
        )
        for obj, part_name in zip(parts, part_names)
    )


def _build_two_hand_v06(
    context: factory.BuildContext,
    *,
    variant_id: str,
    prefix: str,
) -> tuple[object, ...]:
    hand_left = context.rig.pose.bones["hand.L"]
    hand_right = context.rig.pose.bones["hand.R"]
    left_anchor = context.rig.matrix_world @ ((hand_left.head + hand_left.tail) * 0.5)
    right_anchor = context.rig.matrix_world @ ((hand_right.head + hand_right.tail) * 0.5)
    midpoint = (left_anchor + right_anchor) * 0.5
    anchor = factory.Vector(
        (
            TWO_HAND_CENTER_X_OFFSET,
            midpoint.y - 0.02,
            midpoint.z,
        )
    )
    direction = factory.Vector((0.045, TWO_HAND_AWAY_Y, 1.0)).normalized()
    guard_lateral = factory.Vector((1.0, 0.0, 0.0))
    highlight_material = _ensure_highlight_material()

    grip_start = anchor - direction * (TWO_HAND_GRIP_LENGTH * 0.54)
    grip_end = anchor + direction * (TWO_HAND_GRIP_LENGTH * 0.46)
    pommel_center = grip_start - direction * 0.16
    guard_center = grip_end + direction * 0.10
    blade_start = guard_center + direction * 0.13
    blade_end = blade_start + direction * TWO_HAND_BLADE_LENGTH
    guard_extent = guard_lateral * 0.42
    highlight_offset = factory.Vector((0.072, -0.018, 0.0))

    blade = factory._cylinder_between(
        f"{prefix}_blade",
        tuple(blade_start),
        tuple(blade_end),
        0.145,
        4,
        context.materials["silver"],
    )
    highlight = factory._cylinder_between(
        f"{prefix}_highlight",
        tuple(blade_start + highlight_offset),
        tuple(blade_end + highlight_offset),
        0.038,
        4,
        highlight_material,
    )
    tip = _pointed_tip(
        f"{prefix}_tip",
        blade_end,
        direction,
        0.145,
        context.materials["silver"],
    )
    guard = factory._cylinder_between(
        f"{prefix}_guard",
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.070,
        4,
        context.materials["silver"],
    )
    grip = factory._cylinder_between(
        f"{prefix}_grip",
        tuple(grip_start),
        tuple(grip_end),
        0.094,
        8,
        context.materials["boots"],
    )
    pommel = factory._ellipsoid(
        f"{prefix}_pommel",
        tuple(pommel_center),
        (0.16, 0.16, 0.19),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )
    parts = (blade, highlight, tip, guard, grip, pommel)
    part_names = ("blade", "highlight", "tip", "guard", "grip", "pommel")
    return tuple(
        _register_part(
            context,
            obj,
            weapon_id="sword_02_twohand_long_v06",
            weapon_part=part_name,
            physical_side="center",
            variant_id=variant_id,
        )
        for obj, part_name in zip(parts, part_names)
    )


def create_weapon_stance_actions_v06(context: factory.BuildContext) -> None:
    previous_builder.create_weapon_stance_actions_v05(context)
    profile = load_weapon_stance_profile_v06(context.config.character_id)

    actions: dict[str, object] = {}
    for variant in profile.variants:
        action_name = f"{context.config.character_id}_{variant.animation_id}"
        if factory.bpy.data.actions.get(action_name) is not None:
            raise RuntimeError(f"combat idle v06 action already exists: {action_name}")
        action = previous_builder._create_action(context, variant)
        action["profile_revision"] = "v06"
        action["visible_pointed_blade_revision"] = True
        action["supersedes_visual_candidate_revision"] = "v05"
        actions[variant.variant_id] = action

    one_hand = profile.variants[0]
    factory._assign_action(context.rig, actions[one_hand.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    one_hand_parts = _build_one_hand_v06(context)

    two_hand_low = profile.variants[2]
    factory._assign_action(context.rig, actions[two_hand_low.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    two_hand_low_parts = _build_two_hand_v06(
        context,
        variant_id=two_hand_low.variant_id,
        prefix="combat_twohand_low_v06",
    )

    two_hand_high = profile.variants[3]
    factory._assign_action(context.rig, actions[two_hand_high.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    two_hand_high_parts = _build_two_hand_v06(
        context,
        variant_id=two_hand_high.variant_id,
        prefix="combat_twohand_high_v06",
    )

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_weapon_variants_revision"] = "v06"
    scene["combat_idle_weapon_variant_count"] = len(profile.variants)
    scene["combat_idle_weapon_variant_ids"] = ",".join(
        item.variant_id for item in profile.variants
    )
    scene["combat_idle_one_hand_v06_object_count"] = len(one_hand_parts)
    scene["combat_idle_two_hand_low_v06_object_count"] = len(two_hand_low_parts)
    scene["combat_idle_two_hand_high_v06_object_count"] = len(two_hand_high_parts)
    scene["combat_idle_two_hand_separate_pose_fitted_modules"] = True
    scene["combat_idle_pointed_blades"] = True
    scene["combat_idle_weapon_variants_mirroring_used"] = False
    scene["combat_idle_weapon_variants_approved_walk_set_unchanged"] = True
