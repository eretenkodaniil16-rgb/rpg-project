from __future__ import annotations

import math

import blender_sprite_factory as factory
import walk_animation_builder_v03 as appearance_contract
import walk_animation_builder_v04 as approved_walk_down_builder
from walk_left_profile_v01 import WalkLeftProfileV01, load_walk_left_profile_v01


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


def _pairs(profile: WalkLeftProfileV01, attribute: str) -> list[tuple[int, float]]:
    return [(pose.frame, float(getattr(pose, attribute))) for pose in profile.poses]


def _degree_pairs(profile: WalkLeftProfileV01, attribute: str) -> list[tuple[int, float]]:
    return [
        (pose.frame, math.radians(float(getattr(pose, attribute))))
        for pose in profile.poses
    ]


def _assert_rig_contract(context: factory.BuildContext) -> None:
    actual_bones = set(context.rig.pose.bones.keys())
    missing = sorted(_REQUIRED_BONES.difference(actual_bones))
    if missing:
        raise RuntimeError(f"walk_left v01 rig is missing required bones: {missing}")
    appearance_contract._assert_approved_appearance(context)


def _create_walk_left_action(
    context: factory.BuildContext,
    profile: WalkLeftProfileV01,
) -> object:
    config = context.config
    channels = {
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
        'pose.bones["forearm.L"].rotation_euler': {
            0: _degree_pairs(profile, "forearm_left_x_degrees")
        },
        'pose.bones["forearm.R"].rotation_euler': {
            0: _degree_pairs(profile, "forearm_right_x_degrees")
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
    action = factory._new_action(
        f"{config.character_id}_walk_left",
        context.rig,
        channels,
        animation_id=profile.animation_id,
        fps=profile.fps,
    )
    action["profile_revision"] = profile.revision
    action["animation_revision"] = profile.animation_revision
    action["direction"] = profile.direction
    action["phase_order"] = ",".join(pose.phase for pose in profile.poses)
    action["appearance_revision"] = "v03"
    action["appearance_locked"] = True
    action["approved_walk_down_revision"] = "v04"
    action["foreground_physical_side"] = "left"
    action["large_pauldron_foreground"] = True
    action["scabbard_foreground"] = True
    action["pouch_background"] = True
    action["physical_asymmetry_preserved"] = True
    action["forearm_articulation_enabled"] = True
    action["root_translation_used"] = False
    action["geometry_changed"] = False
    action["material_changed"] = False
    action["mirroring_used"] = False
    action.use_fake_user = True
    return action


def create_walk_left_actions_v01(context: factory.BuildContext) -> None:
    approved_walk_down_builder.create_walk_down_actions_v04(context)
    _assert_rig_contract(context)
    profile = load_walk_left_profile_v01(context.config.character_id)
    action = _create_walk_left_action(context, profile)

    scene = factory.bpy.context.scene
    scene["walk_down_artist_approved"] = True
    scene["walk_down_approved_revision"] = "v04"
    scene["walk_left_profile_revision"] = profile.revision
    scene["walk_left_animation_revision"] = profile.animation_revision
    scene["walk_left_direction"] = profile.direction
    scene["walk_left_phase_count"] = len(profile.poses)
    scene["walk_left_foreground_physical_side"] = "left"
    scene["walk_left_geometry_changed"] = False
    scene["walk_left_material_changed"] = False
    scene["walk_left_mirroring_used"] = False

    if action.name != f"{context.config.character_id}_walk_left":
        raise RuntimeError("walk_left v01 action name drifted")
