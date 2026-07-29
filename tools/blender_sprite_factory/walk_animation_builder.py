from __future__ import annotations

import math

import blender_sprite_factory as factory
from walk_down_profile_v01 import WalkDownProfileV01, load_walk_down_profile_v01


_REQUIRED_BONES = frozenset(
    {
        "pelvis",
        "spine",
        "chest",
        "head",
        "upper_arm.L",
        "upper_arm.R",
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


def _pairs(profile: WalkDownProfileV01, attribute: str) -> list[tuple[int, float]]:
    return [(pose.frame, float(getattr(pose, attribute))) for pose in profile.poses]


def _degree_pairs(profile: WalkDownProfileV01, attribute: str) -> list[tuple[int, float]]:
    return [
        (pose.frame, math.radians(float(getattr(pose, attribute))))
        for pose in profile.poses
    ]


def _assert_rig_contract(context: factory.BuildContext) -> None:
    actual_bones = set(context.rig.pose.bones.keys())
    missing = sorted(_REQUIRED_BONES.difference(actual_bones))
    if missing:
        raise RuntimeError(f"walk_down v02 rig is missing required bones: {missing}")
    if context.proxy_revision != "v24":
        raise RuntimeError("walk_down v02 must build on head v21 / proxy v24")


def _create_idle_action(context: factory.BuildContext) -> object:
    config = context.config
    idle_channels = {
        'pose.bones["pelvis"].location': {
            0: [(1, 0.0)],
            2: [(1, 0.0)],
        },
        'pose.bones["pelvis"].rotation_euler': {2: [(1, 0.0)]},
        'pose.bones["spine"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["chest"].rotation_euler': {2: [(1, 0.0)]},
        'pose.bones["head"].rotation_euler': {2: [(1, 0.0)]},
        'pose.bones["thigh.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["thigh.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["shin.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["shin.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["foot.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["foot.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["upper_arm.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["upper_arm.R"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["cloth.L"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["cloth.C"].rotation_euler': {0: [(1, 0.0)]},
        'pose.bones["cloth.R"].rotation_euler': {0: [(1, 0.0)]},
    }
    idle_action = factory._new_action(
        f"{config.character_id}_idle",
        context.rig,
        idle_channels,
        animation_id="idle",
        fps=int(config.animations["idle"]["fps"]),
    )
    idle_action["animation_revision"] = "locked_idle_proxy_v24"
    idle_action["geometry_changed"] = False
    idle_action.use_fake_user = True
    return idle_action


def _create_walk_action(
    context: factory.BuildContext,
    profile: WalkDownProfileV01,
) -> object:
    config = context.config
    walk_channels = {
        'pose.bones["pelvis"].location': {
            0: _pairs(profile, "pelvis_x"),
            2: _pairs(profile, "pelvis_z"),
        },
        'pose.bones["pelvis"].rotation_euler': {
            2: _degree_pairs(profile, "pelvis_roll_z_degrees")
        },
        'pose.bones["spine"].rotation_euler': {
            0: _degree_pairs(profile, "spine_pitch_x_degrees")
        },
        'pose.bones["chest"].rotation_euler': {
            2: _degree_pairs(profile, "chest_yaw_z_degrees")
        },
        'pose.bones["head"].rotation_euler': {
            2: _degree_pairs(profile, "head_yaw_z_degrees")
        },
        'pose.bones["thigh.L"].rotation_euler': {
            0: _degree_pairs(profile, "thigh_left_x_degrees")
        },
        'pose.bones["thigh.R"].rotation_euler': {
            0: _degree_pairs(profile, "thigh_right_x_degrees")
        },
        'pose.bones["shin.L"].rotation_euler': {
            0: _degree_pairs(profile, "shin_left_x_degrees")
        },
        'pose.bones["shin.R"].rotation_euler': {
            0: _degree_pairs(profile, "shin_right_x_degrees")
        },
        'pose.bones["foot.L"].rotation_euler': {
            0: _degree_pairs(profile, "foot_left_x_degrees")
        },
        'pose.bones["foot.R"].rotation_euler': {
            0: _degree_pairs(profile, "foot_right_x_degrees")
        },
        'pose.bones["upper_arm.L"].rotation_euler': {
            0: _degree_pairs(profile, "upper_arm_left_x_degrees")
        },
        'pose.bones["upper_arm.R"].rotation_euler': {
            0: _degree_pairs(profile, "upper_arm_right_x_degrees")
        },
        'pose.bones["cloth.L"].rotation_euler': {
            0: _degree_pairs(profile, "cloth_left_x_degrees")
        },
        'pose.bones["cloth.C"].rotation_euler': {
            0: _degree_pairs(profile, "cloth_center_x_degrees")
        },
        'pose.bones["cloth.R"].rotation_euler': {
            0: _degree_pairs(profile, "cloth_right_x_degrees")
        },
    }
    walk_action = factory._new_action(
        f"{config.character_id}_walk_down",
        context.rig,
        walk_channels,
        animation_id=profile.animation_id,
        fps=profile.fps,
    )
    walk_action["profile_revision"] = profile.revision
    walk_action["animation_revision"] = profile.animation_revision
    walk_action["phase_order"] = ",".join(pose.phase for pose in profile.poses)
    walk_action["root_translation_used"] = False
    walk_action["geometry_changed"] = False
    walk_action["physical_asymmetry_preserved"] = True
    walk_action["head_stabilization_enabled"] = True
    walk_action["foot_articulation_enabled"] = True
    walk_action.use_fake_user = True
    return walk_action


def create_walk_down_actions_v02(context: factory.BuildContext) -> None:
    _assert_rig_contract(context)
    profile = load_walk_down_profile_v01(context.config.character_id)

    if tuple(int(value) for value in context.config.animations["walk_down"]["frames"]) != (
        1,
        2,
        3,
        4,
        5,
        6,
    ):
        raise RuntimeError("walk_down v02 requires the configured six-frame sequence")
    if int(context.config.animations["walk_down"]["fps"]) != profile.fps:
        raise RuntimeError("walk_down v02 FPS must match the structured profile")

    idle_action = _create_idle_action(context)
    _create_walk_action(context, profile)
    factory._assign_action(context.rig, idle_action)

    scene = factory.bpy.context.scene
    scene["walk_down_profile_revision"] = profile.revision
    scene["walk_down_animation_revision"] = profile.animation_revision
    scene["walk_down_phase_count"] = len(profile.poses)
    scene["walk_down_geometry_changed"] = False
