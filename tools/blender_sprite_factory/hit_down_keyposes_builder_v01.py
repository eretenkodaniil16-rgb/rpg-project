from __future__ import annotations

import math

import blender_sprite_factory as factory
from combat_idle_directional_cycles_builder_v14 import (
    create_combat_idle_directional_cycles_v14,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
)
from hit_down_cycle_profile_v01 import load_hit_down_cycle_profile_v01
from hit_down_keyposes_profile_v01 import (
    HitDownPoseDeltaV01,
    load_hit_down_keyposes_profile_v01,
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
        raise RuntimeError(f"hit down v01 rig is missing bones: {missing}")
    if context.head.revision != "v22" or context.proxy_revision != "v25":
        raise RuntimeError("hit down v01 requires approved head v22 / proxy v25")


def _value_pairs(
    poses: tuple[HitDownPoseDeltaV01, ...],
    attribute: str,
    *,
    base_value: float,
) -> list[tuple[int, float]]:
    return [
        (int(pose.frame), float(base_value) + float(getattr(pose, attribute, 0.0)))
        for pose in poses
    ]


def _degree_pairs(
    poses: tuple[HitDownPoseDeltaV01, ...],
    attribute: str,
    *,
    base_degrees: float,
) -> list[tuple[int, float]]:
    return [
        (
            int(pose.frame),
            math.radians(float(base_degrees) + float(getattr(pose, attribute, 0.0))),
        )
        for pose in poses
    ]


def _constant_degree_pairs(
    poses: tuple[HitDownPoseDeltaV01, ...],
    value_degrees: float,
) -> list[tuple[int, float]]:
    value = math.radians(float(value_degrees))
    return [(int(pose.frame), value) for pose in poses]


def _hit_channels(
    poses: tuple[HitDownPoseDeltaV01, ...],
    stance: object,
) -> dict[str, dict[int, list[tuple[int, float]]]]:
    base = stance.pose
    return {
        'pose.bones["pelvis"].location': {
            0: _value_pairs(poses, "pelvis_x", base_value=base.pelvis_x),
            1: _value_pairs(poses, "pelvis_y", base_value=0.0),
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
            0: _degree_pairs(poses, "head_pitch_x_degrees", base_degrees=0.0),
            2: _degree_pairs(
                poses,
                "head_yaw_z_degrees",
                base_degrees=base.head_yaw_z_degrees,
            ),
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
            1: _degree_pairs(poses, "upper_arm_left_y_degrees", base_degrees=0.0),
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
            1: _degree_pairs(poses, "forearm_left_y_degrees", base_degrees=0.0),
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
            1: _degree_pairs(poses, "hand_left_y_degrees", base_degrees=0.0),
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
            1: _degree_pairs(poses, "upper_arm_right_y_degrees", base_degrees=0.0),
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
            1: _degree_pairs(poses, "forearm_right_y_degrees", base_degrees=0.0),
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
            1: _degree_pairs(poses, "hand_right_y_degrees", base_degrees=0.0),
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


def _create_hit_action(
    context: factory.BuildContext,
    profile: object,
    *,
    animation_revision: str,
    manual_keypose_review_required: bool,
    manual_cycle_review_required: bool,
) -> None:
    create_combat_idle_directional_cycles_v14(context)
    _assert_rig_contract(context)
    stance_profile = load_weapon_stance_profile_v09(context.config.character_id)
    stance_by_id = {item.variant_id: item for item in stance_profile.variants}
    stance = stance_by_id[profile.stance_variant_id]

    action_name = f"{context.config.character_id}_{profile.animation_id}"
    if factory.bpy.data.actions.get(action_name) is not None:
        raise RuntimeError(f"hit down v01 action already exists: {action_name}")
    action = factory._new_action(
        action_name,
        context.rig,
        _hit_channels(profile.poses, stance),
        animation_id=profile.animation_id,
        fps=profile.fps,
    )
    action["profile_revision"] = profile.revision
    action["animation_revision"] = animation_revision
    action["animation_family"] = "hit_01"
    action["direction"] = profile.direction
    action["stance_variant_id"] = profile.stance_variant_id
    action["stance_source_revision"] = profile.stance_source_revision
    action["weapon_cycle_id"] = profile.weapon_cycle_id
    action["incoming_direction"] = profile.incoming_direction
    action["frame_count"] = len(profile.poses)
    action["phase_order"] = ",".join(profile.phase_order)
    action["approved_keyposes_preserved_exactly"] = True
    action["shared_reaction_motion"] = True
    action["manual_keypose_review_required"] = manual_keypose_review_required
    action["manual_cycle_review_required"] = manual_cycle_review_required
    action["full_hit_cycle_candidate"] = manual_cycle_review_required
    action["full_hit_cycle_not_yet_approved"] = True
    action["runtime_connected"] = False
    action["appearance_revision"] = profile.appearance_revision
    action["head_revision"] = profile.head_revision
    action["proxy_revision"] = profile.proxy_revision
    action["root_translation_used"] = False
    action["mirroring_used"] = False
    action["negative_scale_used"] = False
    action["geometry_changed"] = False
    action["material_changed"] = False
    action.use_fake_user = True

    scene = factory.bpy.context.scene
    scene["hit_down_profile_revision"] = profile.revision
    scene["hit_down_action"] = action.name
    scene["hit_down_frame_count"] = len(profile.poses)
    scene["hit_down_direction"] = profile.direction
    scene["hit_down_incoming_direction"] = profile.incoming_direction
    scene["hit_down_manual_keypose_review_required"] = manual_keypose_review_required
    scene["hit_down_manual_cycle_review_required"] = manual_cycle_review_required
    scene["hit_down_full_cycle_not_yet_approved"] = True
    scene["hit_down_runtime_connected"] = False
    scene["hit_down_root_translation_used"] = False
    scene["hit_down_mirroring_used"] = False
    scene["hit_down_negative_scale_used"] = False
    scene["hit_down_geometry_changed"] = False
    scene["hit_down_material_changed"] = False


def create_hit_down_keypose_actions_v01(context: factory.BuildContext) -> None:
    profile = load_hit_down_keyposes_profile_v01(context.config.character_id)
    _create_hit_action(
        context,
        profile,
        animation_revision="keyposes_v01_pass02",
        manual_keypose_review_required=True,
        manual_cycle_review_required=False,
    )


def create_hit_down_cycle_actions_v01(context: factory.BuildContext) -> None:
    profile = load_hit_down_cycle_profile_v01(context.config.character_id)
    _create_hit_action(
        context,
        profile,
        animation_revision="cycle_v01",
        manual_keypose_review_required=False,
        manual_cycle_review_required=True,
    )
