from __future__ import annotations

import math

import blender_sprite_factory as factory
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownGripV17,
    AttackSwordDownPoseDeltaV17,
    load_attack_sword_down_keyposes_profile_v17,
)
from combat_idle_directional_cycles_builder_v14 import (
    create_combat_idle_directional_cycles_v14,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
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


def _assert_rig_contract(context: factory.BuildContext) -> None:
    actual = set(context.rig.pose.bones.keys())
    missing = sorted(_REQUIRED_BONES.difference(actual))
    if missing:
        raise RuntimeError(f"attack sword down v17 rig is missing bones: {missing}")
    if context.head.revision != "v22" or context.proxy_revision != "v25":
        raise RuntimeError(
            "attack sword down v17 requires approved head v22 / proxy v25 geometry"
        )


def _value_pairs(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
    attribute: str,
    *,
    base_value: float,
) -> list[tuple[int, float]]:
    return [
        (int(pose.frame), float(base_value) + float(getattr(pose, attribute)))
        for pose in poses
    ]


def _degree_pairs(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
    attribute: str,
    *,
    base_degrees: float,
) -> list[tuple[int, float]]:
    return [
        (
            int(pose.frame),
            math.radians(float(base_degrees) + float(getattr(pose, attribute))),
        )
        for pose in poses
    ]


def _constant_degree_pairs(
    poses: tuple[AttackSwordDownPoseDeltaV17, ...],
    value_degrees: float,
) -> list[tuple[int, float]]:
    value = math.radians(float(value_degrees))
    return [(int(pose.frame), value) for pose in poses]


def _attack_channels(
    grip: AttackSwordDownGripV17,
    stance: object,
) -> dict[str, dict[int, list[tuple[int, float]]]]:
    poses = grip.poses
    base = stance.pose
    return {
        'pose.bones["pelvis"].location': {
            0: _value_pairs(poses, "pelvis_x", base_value=base.pelvis_x),
            2: _value_pairs(poses, "pelvis_z", base_value=base.pelvis_z),
        },
        'pose.bones["pelvis"].rotation_euler': {
            2: _degree_pairs(
                poses,
                "pelvis_roll_z_degrees",
                base_degrees=base.pelvis_roll_z_degrees,
            )
        },
        'pose.bones["spine"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "spine_pitch_x_degrees",
                base_degrees=base.spine_pitch_x_degrees,
            )
        },
        'pose.bones["chest"].rotation_euler': {
            2: _degree_pairs(
                poses,
                "chest_yaw_z_degrees",
                base_degrees=base.chest_yaw_z_degrees,
            )
        },
        'pose.bones["head"].rotation_euler': {
            2: _degree_pairs(
                poses,
                "head_yaw_z_degrees",
                base_degrees=base.head_yaw_z_degrees,
            )
        },
        'pose.bones["thigh.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "thigh_left_x_degrees",
                base_degrees=base.thigh_left_x_degrees,
            ),
            2: _constant_degree_pairs(poses, base.thigh_left_z_degrees),
        },
        'pose.bones["thigh.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "thigh_right_x_degrees",
                base_degrees=base.thigh_right_x_degrees,
            ),
            2: _constant_degree_pairs(poses, base.thigh_right_z_degrees),
        },
        'pose.bones["shin.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "shin_left_x_degrees",
                base_degrees=base.shin_left_x_degrees,
            )
        },
        'pose.bones["shin.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "shin_right_x_degrees",
                base_degrees=base.shin_right_x_degrees,
            )
        },
        'pose.bones["foot.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "foot_left_x_degrees",
                base_degrees=base.foot_left_x_degrees,
            )
        },
        'pose.bones["foot.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "foot_right_x_degrees",
                base_degrees=base.foot_right_x_degrees,
            )
        },
        'pose.bones["upper_arm.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "upper_arm_left_x_degrees",
                base_degrees=base.upper_arm_left_x_degrees,
            ),
            2: _degree_pairs(
                poses,
                "upper_arm_left_z_degrees",
                base_degrees=base.upper_arm_left_z_degrees,
            ),
        },
        'pose.bones["forearm.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "forearm_left_x_degrees",
                base_degrees=base.forearm_left_x_degrees,
            ),
            2: _degree_pairs(
                poses,
                "forearm_left_z_degrees",
                base_degrees=base.forearm_left_z_degrees,
            ),
        },
        'pose.bones["hand.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "hand_left_x_degrees",
                base_degrees=stance.hand_left_x_degrees,
            ),
            2: _degree_pairs(
                poses,
                "hand_left_z_degrees",
                base_degrees=stance.hand_left_z_degrees,
            ),
        },
        'pose.bones["upper_arm.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "upper_arm_right_x_degrees",
                base_degrees=base.upper_arm_right_x_degrees,
            ),
            2: _degree_pairs(
                poses,
                "upper_arm_right_z_degrees",
                base_degrees=base.upper_arm_right_z_degrees,
            ),
        },
        'pose.bones["forearm.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "forearm_right_x_degrees",
                base_degrees=base.forearm_right_x_degrees,
            ),
            2: _degree_pairs(
                poses,
                "forearm_right_z_degrees",
                base_degrees=base.forearm_right_z_degrees,
            ),
        },
        'pose.bones["hand.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "hand_right_x_degrees",
                base_degrees=base.hand_right_x_degrees,
            ),
            2: _degree_pairs(
                poses,
                "hand_right_z_degrees",
                base_degrees=base.hand_right_z_degrees,
            ),
        },
        'pose.bones["cloth.L"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "cloth_left_x_degrees",
                base_degrees=base.cloth_left_x_degrees,
            )
        },
        'pose.bones["cloth.C"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "cloth_center_x_degrees",
                base_degrees=base.cloth_center_x_degrees,
            )
        },
        'pose.bones["cloth.R"].rotation_euler': {
            0: _degree_pairs(
                poses,
                "cloth_right_x_degrees",
                base_degrees=base.cloth_right_x_degrees,
            )
        },
    }


def _create_attack_action(
    context: factory.BuildContext,
    grip: AttackSwordDownGripV17,
    stance: object,
    *,
    fps: int,
) -> object:
    action_name = f"{context.config.character_id}_{grip.action_id}"
    if factory.bpy.data.actions.get(action_name) is not None:
        raise RuntimeError(f"attack sword down v17 action already exists: {action_name}")
    action = factory._new_action(
        action_name,
        context.rig,
        _attack_channels(grip, stance),
        animation_id=grip.action_id,
        fps=fps,
    )
    action["profile_revision"] = "v17"
    action["animation_revision"] = "keyposes_v01"
    action["animation_family"] = "attack_sword_01"
    action["direction"] = "down"
    action["grip_id"] = grip.grip_id
    action["grip_mode"] = stance.grip_mode
    action["frame_count"] = len(grip.poses)
    action["phase_order"] = ",".join(pose.phase for pose in grip.poses)
    action["trajectory_id"] = grip.trajectory_id
    action["source_stance_variant_id"] = grip.stance_variant_id
    action["source_stance_revision"] = grip.stance_source_revision
    action["source_weapon_cycle_id"] = grip.weapon_cycle_id
    action["guard_exactly_matches_approved_source"] = True
    action["manual_keypose_review_required"] = True
    action["full_attack_cycle_not_yet_approved"] = True
    action["appearance_revision"] = "v03"
    action["head_revision"] = "v22"
    action["proxy_revision"] = "v25"
    action["root_translation_used"] = False
    action["mirroring_used"] = False
    action["negative_scale_used"] = False
    action["geometry_changed"] = False
    action["material_changed"] = False
    action.use_fake_user = True
    return action


def create_attack_sword_down_keypose_actions_v17(
    context: factory.BuildContext,
) -> None:
    create_combat_idle_directional_cycles_v14(context)
    _assert_rig_contract(context)
    profile = load_attack_sword_down_keyposes_profile_v17(
        context.config.character_id
    )
    stance_profile = load_weapon_stance_profile_v09(context.config.character_id)
    stance_by_id = {item.variant_id: item for item in stance_profile.variants}

    created_actions: list[str] = []
    for grip in profile.grips:
        stance = stance_by_id[grip.stance_variant_id]
        action = _create_attack_action(
            context,
            grip,
            stance,
            fps=profile.fps,
        )
        created_actions.append(action.name)

    scene = factory.bpy.context.scene
    scene["attack_sword_down_keyposes_revision"] = profile.revision
    scene["attack_sword_down_keypose_action_count"] = len(created_actions)
    scene["attack_sword_down_keypose_frame_count"] = sum(
        len(grip.poses) for grip in profile.grips
    )
    scene["attack_sword_down_keypose_actions"] = ",".join(created_actions)
    scene["attack_sword_down_direction"] = profile.direction
    scene["attack_sword_down_manual_review_required"] = True
    scene["attack_sword_down_full_cycle_not_yet_approved"] = True
    scene["attack_sword_down_source_combat_idle_revision"] = (
        profile.combat_idle_source_revision
    )
    scene["attack_sword_down_source_directional_weapon_revision"] = (
        profile.directional_weapon_source_revision
    )
    scene["attack_sword_down_appearance_revision"] = profile.appearance_revision
    scene["attack_sword_down_head_revision"] = profile.head_revision
    scene["attack_sword_down_proxy_revision"] = profile.proxy_revision
    scene["attack_sword_down_root_translation_used"] = False
    scene["attack_sword_down_mirroring_used"] = False
    scene["attack_sword_down_negative_scale_used"] = False
    scene["attack_sword_down_geometry_changed"] = False
    scene["attack_sword_down_material_changed"] = False
