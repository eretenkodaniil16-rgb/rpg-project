from __future__ import annotations

import math

import blender_sprite_factory as factory
import combat_idle_down_animation_builder_v01 as base_builder
import combat_idle_down_weapon_variants_builder_v09 as previous_builder
from combat_idle_down_cycles_profile_v10 import (
    CombatIdleCycleV10,
    CombatIdleCyclesProfileV10,
    load_combat_idle_cycles_profile_v10,
)


_REQUIRED_BONES = frozenset(
    {
        "pelvis",
        "spine",
        "chest",
        "head",
        "upper_arm.L",
        "upper_arm.R",
        "forearm.L",
        "forearm.R",
        "hand.L",
        "hand.R",
        "thigh.L",
        "thigh.R",
        "shin.L",
        "shin.R",
        "foot.L",
        "foot.R",
        "cloth.L",
        "cloth.C",
        "cloth.R",
    }
)


def _pose_pairs(cycle: CombatIdleCycleV10, attribute: str) -> list[tuple[int, float]]:
    return [
        (frame.pose.frame, float(getattr(frame.pose, attribute)))
        for frame in cycle.frames
    ]


def _degree_pose_pairs(
    cycle: CombatIdleCycleV10,
    attribute: str,
) -> list[tuple[int, float]]:
    return [
        (frame.pose.frame, math.radians(float(getattr(frame.pose, attribute))))
        for frame in cycle.frames
    ]


def _frame_pairs(cycle: CombatIdleCycleV10, attribute: str) -> list[tuple[int, float]]:
    return [
        (frame.pose.frame, float(getattr(frame, attribute))) for frame in cycle.frames
    ]


def _degree_frame_pairs(
    cycle: CombatIdleCycleV10,
    attribute: str,
) -> list[tuple[int, float]]:
    return [
        (frame.pose.frame, math.radians(float(getattr(frame, attribute))))
        for frame in cycle.frames
    ]


def _assert_rig_contract(context: factory.BuildContext) -> None:
    actual_bones = set(context.rig.pose.bones.keys())
    missing = sorted(_REQUIRED_BONES.difference(actual_bones))
    if missing:
        raise RuntimeError(f"combat idle cycles v10 rig is missing bones: {missing}")


def _create_cycle_action(
    context: factory.BuildContext,
    profile: CombatIdleCyclesProfileV10,
    cycle: CombatIdleCycleV10,
) -> object:
    channels = {
        'pose.bones["pelvis"].location': {
            0: _pose_pairs(cycle, "pelvis_x"),
            2: _pose_pairs(cycle, "pelvis_z"),
        },
        'pose.bones["pelvis"].rotation_euler': {
            2: _degree_pose_pairs(cycle, "pelvis_roll_z_degrees")
        },
        'pose.bones["spine"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "spine_pitch_x_degrees")
        },
        'pose.bones["chest"].location': {2: _frame_pairs(cycle, "chest_lift_z")},
        'pose.bones["chest"].rotation_euler': {
            2: _degree_pose_pairs(cycle, "chest_yaw_z_degrees")
        },
        'pose.bones["head"].rotation_euler': {
            2: _degree_pose_pairs(cycle, "head_yaw_z_degrees")
        },
        'pose.bones["thigh.L"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "thigh_left_x_degrees"),
            2: _degree_pose_pairs(cycle, "thigh_left_z_degrees"),
        },
        'pose.bones["thigh.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "thigh_right_x_degrees"),
            2: _degree_pose_pairs(cycle, "thigh_right_z_degrees"),
        },
        'pose.bones["shin.L"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "shin_left_x_degrees")
        },
        'pose.bones["shin.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "shin_right_x_degrees")
        },
        'pose.bones["foot.L"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "foot_left_x_degrees")
        },
        'pose.bones["foot.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "foot_right_x_degrees")
        },
        'pose.bones["upper_arm.L"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "upper_arm_left_x_degrees"),
            2: _degree_pose_pairs(cycle, "upper_arm_left_z_degrees"),
        },
        'pose.bones["forearm.L"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "forearm_left_x_degrees"),
            2: _degree_pose_pairs(cycle, "forearm_left_z_degrees"),
        },
        'pose.bones["hand.L"].rotation_euler': {
            0: _degree_frame_pairs(cycle, "hand_left_x_degrees"),
            2: _degree_frame_pairs(cycle, "hand_left_z_degrees"),
        },
        'pose.bones["upper_arm.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "upper_arm_right_x_degrees"),
            2: _degree_pose_pairs(cycle, "upper_arm_right_z_degrees"),
        },
        'pose.bones["forearm.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "forearm_right_x_degrees"),
            2: _degree_pose_pairs(cycle, "forearm_right_z_degrees"),
        },
        'pose.bones["hand.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "hand_right_x_degrees"),
            2: _degree_pose_pairs(cycle, "hand_right_z_degrees"),
        },
        'pose.bones["cloth.L"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "cloth_left_x_degrees")
        },
        'pose.bones["cloth.C"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "cloth_center_x_degrees")
        },
        'pose.bones["cloth.R"].rotation_euler': {
            0: _degree_pose_pairs(cycle, "cloth_right_x_degrees")
        },
    }
    action = factory._new_action(
        f"{context.config.character_id}_{cycle.animation_id}",
        context.rig,
        channels,
        animation_id=cycle.animation_id,
        fps=cycle.fps,
    )
    action["profile_revision"] = profile.revision
    action["cycle_id"] = cycle.cycle_id
    action["display_name"] = cycle.display_name
    action["grip_mode"] = cycle.grip_mode
    action["weapon_variant_id"] = cycle.weapon_variant_id
    action["weapon_id"] = cycle.weapon_id
    action["source_animation_id"] = cycle.source_animation_id
    action["source_revision"] = cycle.source_revision
    action["direction"] = profile.direction
    action["phase_order"] = ",".join(frame.pose.phase for frame in cycle.frames)
    action["frame_count"] = len(cycle.frames)
    action["loop"] = cycle.loop
    action["selected_best_candidate"] = True
    action["appearance_revision"] = "v03"
    action["appearance_locked"] = True
    action["planted_lower_body"] = True
    action["restrained_breathing"] = True
    action["weapon_geometry_rebuilt"] = False
    action["root_translation_used"] = False
    action["mirroring_used"] = False
    action["negative_scale_used"] = False
    action["neutral_pose_reset_before_assignment"] = True
    action.use_fake_user = True
    return action


def create_combat_idle_cycles_v10(context: factory.BuildContext) -> None:
    previous_builder.create_weapon_stance_actions_v09(context)
    base_builder.install_neutral_pose_action_assignment()
    _assert_rig_contract(context)
    profile = load_combat_idle_cycles_profile_v10(context.config.character_id)

    actions: list[object] = []
    for cycle in profile.cycles:
        action_name = f"{context.config.character_id}_{cycle.animation_id}"
        if factory.bpy.data.actions.get(action_name) is not None:
            raise RuntimeError(f"combat idle cycle v10 action already exists: {action_name}")
        actions.append(_create_cycle_action(context, profile, cycle))

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_cycles_revision"] = profile.revision
    scene["combat_idle_cycles_direction"] = profile.direction
    scene["combat_idle_cycles_count"] = len(profile.cycles)
    scene["combat_idle_cycles_ids"] = ",".join(cycle.cycle_id for cycle in profile.cycles)
    scene["combat_idle_cycles_frame_count"] = 4
    scene["combat_idle_cycles_fps"] = profile.cycles[0].fps
    scene["combat_idle_cycles_loop"] = True
    scene["combat_idle_one_hand_selected_source"] = "onehand_ready_v09"
    scene["combat_idle_two_hand_selected_source"] = "twohand_center_high_v06"
    scene["combat_idle_low_stances_retained_as_alternatives"] = True
    scene["combat_idle_cycle_weapon_geometry_rebuilt"] = False
    scene["combat_idle_cycle_appearance_revision"] = "v03"
    scene["combat_idle_cycle_approved_walk_set_unchanged"] = True
    scene["combat_idle_cycle_mirroring_used"] = False
    scene["combat_idle_cycle_negative_scale_used"] = False
