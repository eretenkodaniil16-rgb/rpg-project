from __future__ import annotations

import blender_sprite_factory as factory
import combat_idle_down_animation_builder_v01 as base_builder
from combat_idle_down_variants_profile_v02 import (
    CombatIdleDownVariantV02,
    load_combat_idle_down_variants_profile_v02,
)


def _create_variant_action(
    context: factory.BuildContext,
    variant: CombatIdleDownVariantV02,
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
    action["profile_revision"] = "v02"
    action["variant_id"] = variant.variant_id
    action["display_name"] = variant.display_name
    action["direction"] = "down"
    action["phase"] = pose.phase
    action["weapon_id"] = "sword_01"
    action["weapon_hand"] = "right"
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


def create_combat_idle_down_variant_actions_v02(
    context: factory.BuildContext,
) -> None:
    base_builder.create_combat_idle_down_actions_v01(context)
    profile = load_combat_idle_down_variants_profile_v02(context.config.character_id)

    created_names: list[str] = []
    for variant in profile.variants:
        action_name = f"{context.config.character_id}_{variant.animation_id}"
        if factory.bpy.data.actions.get(action_name) is not None:
            raise RuntimeError(f"combat_idle_down variants v02 action already exists: {action_name}")
        action = _create_variant_action(context, variant)
        created_names.append(action.name)

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_variants_revision"] = profile.revision
    scene["combat_idle_variant_count"] = len(profile.variants)
    scene["combat_idle_variant_ids"] = ",".join(
        item.variant_id for item in profile.variants
    )
    scene["combat_idle_variant_actions"] = ",".join(created_names)
    scene["combat_idle_variants_weapon_hand"] = profile.weapon_hand
    scene["combat_idle_variants_mirroring_used"] = False
    scene["combat_idle_variants_approved_walk_set_unchanged"] = True
