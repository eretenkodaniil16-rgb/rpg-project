from __future__ import annotations

import math

import blender_sprite_factory as factory
import combat_idle_down_weapon_variants_builder_v05 as action_builder
import combat_idle_down_weapon_variants_builder_v06 as weapon_builder
import combat_idle_down_weapon_variants_builder_v08 as previous_builder
from combat_idle_down_weapon_variants_profile_v06 import (
    ONE_HAND_BLADE_LENGTH,
    ONE_HAND_GRIP_LENGTH,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    ONE_HAND_BEHIND_Y,
    ONE_HAND_DOWN_Z,
    ONE_HAND_SIDE_X,
    load_weapon_stance_profile_v09,
)


ONE_HAND_LOW_V09_OBJECT_NAMES = (
    "combat_onehand_low_v09_blade",
    "combat_onehand_low_v09_highlight",
    "combat_onehand_low_v09_tip",
    "combat_onehand_low_v09_guard",
    "combat_onehand_low_v09_grip",
    "combat_onehand_low_v09_pommel",
)
ONE_HAND_READY_V09_OBJECT_NAMES = (
    "combat_onehand_ready_v09_blade",
    "combat_onehand_ready_v09_highlight",
    "combat_onehand_ready_v09_tip",
    "combat_onehand_ready_v09_guard",
    "combat_onehand_ready_v09_grip",
    "combat_onehand_ready_v09_pommel",
)


def _register_one_hand_part(
    context: factory.BuildContext,
    obj: object,
    *,
    weapon_part: str,
    variant_id: str,
) -> object:
    registered = factory._register(
        context,
        obj,
        "combat_weapon",
        "hand.R",
        "right",
    )
    registered["weapon_id"] = "sword_01_onehand_outward_back_v09"
    registered["weapon_part"] = weapon_part
    registered["weapon_state"] = "drawn"
    registered["weapon_variant_id"] = variant_id
    registered["combat_idle_weapon_variants_revision"] = "v09"
    registered["one_hand_trajectory"] = "physical_right_outward_and_partly_behind"
    registered.hide_render = True
    registered.hide_viewport = True
    return registered


def _build_one_hand_v09(
    context: factory.BuildContext,
    *,
    variant_id: str,
    prefix: str,
) -> tuple[object, ...]:
    hand = context.rig.pose.bones["hand.R"]
    anchor = context.rig.matrix_world @ ((hand.head + hand.tail) * 0.5)
    direction = factory.Vector(
        (ONE_HAND_SIDE_X, ONE_HAND_BEHIND_Y, ONE_HAND_DOWN_Z)
    ).normalized()
    guard_lateral = factory.Vector(
        (ONE_HAND_BEHIND_Y, -ONE_HAND_SIDE_X, 0.0)
    ).normalized()
    highlight_material = weapon_builder._ensure_highlight_material()

    grip_start = anchor - direction * (ONE_HAND_GRIP_LENGTH * 0.46)
    grip_end = anchor + direction * (ONE_HAND_GRIP_LENGTH * 0.54)
    pommel_center = grip_start - direction * 0.13
    guard_center = grip_end + direction * 0.08
    blade_start = guard_center + direction * 0.12
    blade_end = blade_start + direction * ONE_HAND_BLADE_LENGTH
    guard_extent = guard_lateral * 0.36
    highlight_offset = guard_lateral * 0.075 + factory.Vector((0.0, -0.018, 0.018))

    blade = factory._cylinder_between(
        f"{prefix}_blade",
        tuple(blade_start),
        tuple(blade_end),
        0.135,
        4,
        context.materials["silver"],
    )
    highlight = factory._cylinder_between(
        f"{prefix}_highlight",
        tuple(blade_start + highlight_offset),
        tuple(blade_end + highlight_offset),
        0.035,
        4,
        highlight_material,
    )
    tip = weapon_builder._pointed_tip(
        f"{prefix}_tip",
        blade_end,
        direction,
        0.135,
        context.materials["silver"],
    )
    guard = factory._cylinder_between(
        f"{prefix}_guard",
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.067,
        4,
        context.materials["silver"],
    )
    grip = factory._cylinder_between(
        f"{prefix}_grip",
        tuple(grip_start),
        tuple(grip_end),
        0.086,
        8,
        context.materials["boots"],
    )
    pommel = factory._ellipsoid(
        f"{prefix}_pommel",
        tuple(pommel_center),
        (0.14, 0.14, 0.16),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )
    parts = (blade, highlight, tip, guard, grip, pommel)
    part_names = ("blade", "highlight", "tip", "guard", "grip", "pommel")
    return tuple(
        _register_one_hand_part(
            context,
            obj,
            weapon_part=part_name,
            variant_id=variant_id,
        )
        for obj, part_name in zip(parts, part_names)
    )


def create_weapon_stance_actions_v09(context: factory.BuildContext) -> None:
    previous_builder.create_weapon_stance_actions_v08(context)
    profile = load_weapon_stance_profile_v09(context.config.character_id)

    actions: dict[str, object] = {}
    for variant in profile.variants[:2]:
        action_name = f"{context.config.character_id}_{variant.animation_id}"
        if factory.bpy.data.actions.get(action_name) is not None:
            raise RuntimeError(f"combat idle v09 action already exists: {action_name}")
        action = action_builder._create_action(context, variant)
        action["profile_revision"] = "v09"
        action["one_hand_blade_physical_right_outward_and_partly_behind"] = True
        action["body_pose_source_revision"] = "v06"
        action["two_hand_source_revision"] = "v06"
        action["supersedes_cross_torso_one_hand_revision"] = "v08"
        actions[variant.variant_id] = action

    one_hand_low = profile.variants[0]
    factory._assign_action(context.rig, actions[one_hand_low.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    low_parts = _build_one_hand_v09(
        context,
        variant_id=one_hand_low.variant_id,
        prefix="combat_onehand_low_v09",
    )

    one_hand_ready = profile.variants[1]
    factory._assign_action(context.rig, actions[one_hand_ready.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    ready_parts = _build_one_hand_v09(
        context,
        variant_id=one_hand_ready.variant_id,
        prefix="combat_onehand_ready_v09",
    )

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_weapon_variants_revision"] = "v09"
    scene["combat_idle_weapon_variant_count"] = len(profile.variants)
    scene["combat_idle_one_hand_low_v09_object_count"] = len(low_parts)
    scene["combat_idle_one_hand_ready_v09_object_count"] = len(ready_parts)
    scene["combat_idle_one_hand_separate_pose_fitted_modules"] = True
    scene["combat_idle_one_hand_physical_right_outward_and_partly_behind"] = True
    scene["combat_idle_one_hand_v08_rejected_for_cross_torso_projection"] = True
    scene["combat_idle_two_hand_source_revision"] = "v06"
    scene["combat_idle_two_hand_geometry_unchanged"] = True
    scene["combat_idle_appearance_revision"] = "v03"
    scene["combat_idle_approved_walk_set_unchanged"] = True
    scene["combat_idle_mirroring_used"] = False
    scene["combat_idle_negative_scale_used"] = False
