from __future__ import annotations

import math

import blender_sprite_factory as factory
import combat_idle_down_animation_builder_v01 as base_builder
from combat_idle_down_weapon_variants_profile_v05 import (
    ONE_HAND_BLADE_LENGTH,
    ONE_HAND_GRIP_LENGTH,
    TWO_HAND_BLADE_LENGTH,
    TWO_HAND_GRIP_LENGTH,
    WeaponStanceVariantV05,
    load_weapon_stance_profile_v05,
)


ONE_HAND_LONG_OBJECT_NAMES = (
    "combat_onehand_long_blade",
    "combat_onehand_long_guard",
    "combat_onehand_long_grip",
    "combat_onehand_long_pommel",
)
TWO_HAND_LONG_OBJECT_NAMES = (
    "combat_twohand_long_blade",
    "combat_twohand_long_guard",
    "combat_twohand_long_grip",
    "combat_twohand_long_pommel",
)


def _create_action(
    context: factory.BuildContext,
    variant: WeaponStanceVariantV05,
) -> object:
    pose = variant.pose
    channels = {
        'pose.bones["pelvis"].location': {
            0: base_builder._value_pairs(pose.pelvis_x),
            2: base_builder._value_pairs(pose.pelvis_z),
        },
        'pose.bones["pelvis"].rotation_euler': {
            2: base_builder._degree_pairs(pose.pelvis_roll_z_degrees)
        },
        'pose.bones["spine"].rotation_euler': {
            0: base_builder._degree_pairs(pose.spine_pitch_x_degrees)
        },
        'pose.bones["chest"].rotation_euler': {
            2: base_builder._degree_pairs(pose.chest_yaw_z_degrees)
        },
        'pose.bones["head"].rotation_euler': {
            2: base_builder._degree_pairs(pose.head_yaw_z_degrees)
        },
        'pose.bones["thigh.L"].rotation_euler': {
            0: base_builder._degree_pairs(pose.thigh_left_x_degrees),
            2: base_builder._degree_pairs(pose.thigh_left_z_degrees),
        },
        'pose.bones["thigh.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.thigh_right_x_degrees),
            2: base_builder._degree_pairs(pose.thigh_right_z_degrees),
        },
        'pose.bones["shin.L"].rotation_euler': {
            0: base_builder._degree_pairs(pose.shin_left_x_degrees)
        },
        'pose.bones["shin.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.shin_right_x_degrees)
        },
        'pose.bones["foot.L"].rotation_euler': {
            0: base_builder._degree_pairs(pose.foot_left_x_degrees)
        },
        'pose.bones["foot.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.foot_right_x_degrees)
        },
        'pose.bones["upper_arm.L"].rotation_euler': {
            0: base_builder._degree_pairs(pose.upper_arm_left_x_degrees),
            2: base_builder._degree_pairs(pose.upper_arm_left_z_degrees),
        },
        'pose.bones["forearm.L"].rotation_euler': {
            0: base_builder._degree_pairs(pose.forearm_left_x_degrees),
            2: base_builder._degree_pairs(pose.forearm_left_z_degrees),
        },
        'pose.bones["hand.L"].rotation_euler': {
            0: base_builder._degree_pairs(variant.hand_left_x_degrees),
            2: base_builder._degree_pairs(variant.hand_left_z_degrees),
        },
        'pose.bones["upper_arm.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.upper_arm_right_x_degrees),
            2: base_builder._degree_pairs(pose.upper_arm_right_z_degrees),
        },
        'pose.bones["forearm.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.forearm_right_x_degrees),
            2: base_builder._degree_pairs(pose.forearm_right_z_degrees),
        },
        'pose.bones["hand.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.hand_right_x_degrees),
            2: base_builder._degree_pairs(pose.hand_right_z_degrees),
        },
        'pose.bones["cloth.L"].rotation_euler': {
            0: base_builder._degree_pairs(pose.cloth_left_x_degrees)
        },
        'pose.bones["cloth.C"].rotation_euler': {
            0: base_builder._degree_pairs(pose.cloth_center_x_degrees)
        },
        'pose.bones["cloth.R"].rotation_euler': {
            0: base_builder._degree_pairs(pose.cloth_right_x_degrees)
        },
    }
    action = factory._new_action(
        f"{context.config.character_id}_{variant.animation_id}",
        context.rig,
        channels,
        animation_id=variant.animation_id,
        fps=1,
    )
    action["profile_revision"] = "v05"
    action["variant_id"] = variant.variant_id
    action["display_name"] = variant.display_name
    action["grip_mode"] = variant.grip_mode
    action["weapon_id"] = variant.weapon_id
    action["blade_tip"] = variant.blade_tip
    action["direction"] = "down"
    action["appearance_revision"] = "v03"
    action["appearance_locked"] = True
    action["approved_walk_set_unchanged"] = True
    action["static_pose_only"] = True
    action["root_translation_used"] = False
    action["mirroring_used"] = False
    action["negative_scale_used"] = False
    action["neutral_pose_reset_before_assignment"] = True
    action.use_fake_user = True
    return action


def _register_weapon_part(
    context: factory.BuildContext,
    obj: object,
    *,
    weapon_id: str,
    weapon_part: str,
    physical_side: str,
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
    registered["combat_idle_weapon_variants_revision"] = "v05"
    registered.hide_render = True
    registered.hide_viewport = True
    return registered


def _assert_objects_absent(names: tuple[str, ...]) -> None:
    existing = [name for name in names if factory.bpy.data.objects.get(name) is not None]
    if existing:
        raise RuntimeError(f"combat idle v05 weapon objects already exist: {existing}")


def _build_one_hand_long_sword(context: factory.BuildContext) -> tuple[object, ...]:
    _assert_objects_absent(ONE_HAND_LONG_OBJECT_NAMES)
    hand = context.rig.pose.bones["hand.R"]
    anchor = context.rig.matrix_world @ ((hand.head + hand.tail) * 0.5)
    blade_direction = factory.Vector((0.34, -0.18, -1.0)).normalized()
    guard_lateral = factory.Vector((0.90, 0.40, 0.0)).normalized()

    grip_start = anchor - blade_direction * (ONE_HAND_GRIP_LENGTH * 0.46)
    grip_end = anchor + blade_direction * (ONE_HAND_GRIP_LENGTH * 0.54)
    pommel_center = grip_start - blade_direction * 0.13
    guard_center = grip_end + blade_direction * 0.08
    blade_start = guard_center + blade_direction * 0.12
    blade_end = blade_start + blade_direction * ONE_HAND_BLADE_LENGTH
    guard_extent = guard_lateral * 0.34

    grip = factory._cylinder_between(
        "combat_onehand_long_grip",
        tuple(grip_start),
        tuple(grip_end),
        0.082,
        8,
        context.materials["boots"],
    )
    guard = factory._cylinder_between(
        "combat_onehand_long_guard",
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.062,
        4,
        context.materials["silver"],
    )
    blade = factory._cylinder_between(
        "combat_onehand_long_blade",
        tuple(blade_start),
        tuple(blade_end),
        0.112,
        4,
        context.materials["silver"],
    )
    pommel = factory._ellipsoid(
        "combat_onehand_long_pommel",
        tuple(pommel_center),
        (0.13, 0.13, 0.15),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )
    return (
        _register_weapon_part(
            context,
            blade,
            weapon_id="sword_01_onehand_long",
            weapon_part="blade",
            physical_side="right",
        ),
        _register_weapon_part(
            context,
            guard,
            weapon_id="sword_01_onehand_long",
            weapon_part="guard",
            physical_side="right",
        ),
        _register_weapon_part(
            context,
            grip,
            weapon_id="sword_01_onehand_long",
            weapon_part="grip",
            physical_side="right",
        ),
        _register_weapon_part(
            context,
            pommel,
            weapon_id="sword_01_onehand_long",
            weapon_part="pommel",
            physical_side="right",
        ),
    )


def _build_two_hand_long_sword(context: factory.BuildContext) -> tuple[object, ...]:
    _assert_objects_absent(TWO_HAND_LONG_OBJECT_NAMES)
    hand_left = context.rig.pose.bones["hand.L"]
    hand_right = context.rig.pose.bones["hand.R"]
    left_anchor = context.rig.matrix_world @ ((hand_left.head + hand_left.tail) * 0.5)
    right_anchor = context.rig.matrix_world @ ((hand_right.head + hand_right.tail) * 0.5)
    midpoint = (left_anchor + right_anchor) * 0.5
    anchor = factory.Vector((0.0, midpoint.y - 0.04, midpoint.z))
    blade_direction = factory.Vector((0.0, -0.08, 1.0)).normalized()
    guard_lateral = factory.Vector((1.0, 0.0, 0.0))

    grip_start = anchor - blade_direction * (TWO_HAND_GRIP_LENGTH * 0.54)
    grip_end = anchor + blade_direction * (TWO_HAND_GRIP_LENGTH * 0.46)
    pommel_center = grip_start - blade_direction * 0.16
    guard_center = grip_end + blade_direction * 0.10
    blade_start = guard_center + blade_direction * 0.13
    blade_end = blade_start + blade_direction * TWO_HAND_BLADE_LENGTH
    guard_extent = guard_lateral * 0.40

    grip = factory._cylinder_between(
        "combat_twohand_long_grip",
        tuple(grip_start),
        tuple(grip_end),
        0.090,
        8,
        context.materials["boots"],
    )
    guard = factory._cylinder_between(
        "combat_twohand_long_guard",
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.067,
        4,
        context.materials["silver"],
    )
    blade = factory._cylinder_between(
        "combat_twohand_long_blade",
        tuple(blade_start),
        tuple(blade_end),
        0.125,
        4,
        context.materials["silver"],
    )
    pommel = factory._ellipsoid(
        "combat_twohand_long_pommel",
        tuple(pommel_center),
        (0.15, 0.15, 0.18),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )
    return (
        _register_weapon_part(
            context,
            blade,
            weapon_id="sword_02_twohand_long",
            weapon_part="blade",
            physical_side="center",
        ),
        _register_weapon_part(
            context,
            guard,
            weapon_id="sword_02_twohand_long",
            weapon_part="guard",
            physical_side="center",
        ),
        _register_weapon_part(
            context,
            grip,
            weapon_id="sword_02_twohand_long",
            weapon_part="grip",
            physical_side="center",
        ),
        _register_weapon_part(
            context,
            pommel,
            weapon_id="sword_02_twohand_long",
            weapon_part="pommel",
            physical_side="center",
        ),
    )


def create_weapon_stance_actions_v05(context: factory.BuildContext) -> None:
    base_builder.create_combat_idle_down_actions_v01(context)
    if "hand.L" not in context.rig.pose.bones:
        raise RuntimeError("combat idle v05 requires hand.L for the two-handed grip")
    profile = load_weapon_stance_profile_v05(context.config.character_id)

    actions: dict[str, object] = {}
    for variant in profile.variants:
        action_name = f"{context.config.character_id}_{variant.animation_id}"
        if factory.bpy.data.actions.get(action_name) is not None:
            raise RuntimeError(f"combat idle v05 action already exists: {action_name}")
        actions[variant.variant_id] = _create_action(context, variant)

    one_hand_variant = profile.variants[0]
    factory._assign_action(context.rig, actions[one_hand_variant.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    one_hand_parts = _build_one_hand_long_sword(context)

    two_hand_variant = profile.variants[2]
    factory._assign_action(context.rig, actions[two_hand_variant.variant_id])
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    two_hand_parts = _build_two_hand_long_sword(context)

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_weapon_variants_revision"] = profile.revision
    scene["combat_idle_weapon_variant_count"] = len(profile.variants)
    scene["combat_idle_weapon_variant_ids"] = ",".join(
        item.variant_id for item in profile.variants
    )
    scene["combat_idle_one_hand_blade_length"] = ONE_HAND_BLADE_LENGTH
    scene["combat_idle_two_hand_blade_length"] = TWO_HAND_BLADE_LENGTH
    scene["combat_idle_one_hand_object_count"] = len(one_hand_parts)
    scene["combat_idle_two_hand_object_count"] = len(two_hand_parts)
    scene["combat_idle_weapon_variants_mirroring_used"] = False
    scene["combat_idle_weapon_variants_approved_walk_set_unchanged"] = True
