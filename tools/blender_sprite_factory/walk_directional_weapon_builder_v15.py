from __future__ import annotations

import math

import blender_sprite_factory as factory
from combat_idle_directional_cycles_builder_v14 import (
    create_combat_idle_directional_cycles_v14,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
)
from walk_directional_weapon_profile_v15 import (
    ArmedWalkDirectionV15,
    ArmedWalkGripV15,
    load_walk_directional_weapon_profile_v15,
)
from walk_down_profile_v03 import load_walk_down_profile_v03
from walk_left_profile_v01 import load_walk_left_profile_v01
from walk_right_profile_v01 import load_walk_right_profile_v01
from walk_up_profile_v02 import load_walk_up_profile_v02


SPINE_STANCE_BLEND = 0.45
CHEST_STANCE_BLEND = 0.50
HEAD_STANCE_BLEND = 0.50
FREE_FOREARM_SWING_SCALE = 0.18
WEAPON_FOREARM_COUNTER_SCALE = -0.50

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


def _source_profile(character_id: str, direction: str) -> object:
    loaders = {
        "down": load_walk_down_profile_v03,
        "left": load_walk_left_profile_v01,
        "right": load_walk_right_profile_v01,
        "up": load_walk_up_profile_v02,
    }
    try:
        return loaders[direction](character_id)
    except KeyError as exc:
        raise KeyError(f"Unknown armed walk direction: {direction}") from exc


def _pairs(profile: object, attribute: str) -> list[tuple[int, float]]:
    return [
        (int(pose.frame), float(getattr(pose, attribute)))
        for pose in profile.poses
    ]


def _degree_pairs(profile: object, attribute: str) -> list[tuple[int, float]]:
    return [
        (int(pose.frame), math.radians(float(getattr(pose, attribute))))
        for pose in profile.poses
    ]


def _constant_degree_pairs(
    frames: tuple[int, ...],
    value_degrees: float,
) -> list[tuple[int, float]]:
    value = math.radians(float(value_degrees))
    return [(frame, value) for frame in frames]


def _combined_degree_pairs(
    profile: object,
    source_attribute: str,
    *,
    base_degrees: float,
    source_scale: float,
) -> list[tuple[int, float]]:
    return [
        (
            int(pose.frame),
            math.radians(
                float(base_degrees)
                + float(getattr(pose, source_attribute)) * float(source_scale)
            ),
        )
        for pose in profile.poses
    ]


def _offset_degree_pairs(
    frames: tuple[int, ...],
    *,
    base_degrees: float,
    offsets_degrees: tuple[float, ...],
    offset_scale: float = 1.0,
) -> list[tuple[int, float]]:
    return [
        (
            frame,
            math.radians(
                float(base_degrees)
                + float(offset) * float(offset_scale)
            ),
        )
        for frame, offset in zip(frames, offsets_degrees)
    ]


def _optional_source_attribute(
    profile: object,
    primary_attribute: str,
    fallback_attribute: str,
) -> str:
    first_pose = profile.poses[0]
    if hasattr(first_pose, primary_attribute):
        return primary_attribute
    if hasattr(first_pose, fallback_attribute):
        return fallback_attribute
    raise AttributeError(
        f"Armed walk source lacks {primary_attribute} and {fallback_attribute}"
    )


def _assert_rig_contract(context: factory.BuildContext) -> None:
    actual = set(context.rig.pose.bones.keys())
    missing = sorted(_REQUIRED_BONES.difference(actual))
    if missing:
        raise RuntimeError(f"armed walk v15 rig is missing bones: {missing}")
    if context.head.revision != "v22" or context.proxy_revision != "v25":
        raise RuntimeError(
            "armed walk v15 requires the approved head v22 / proxy v25 geometry"
        )


def _base_walk_channels(profile: object, stance: object) -> dict[str, dict[int, list[tuple[int, float]]]]:
    return {
        'pose.bones["pelvis"].location': {
            0: _pairs(profile, "pelvis_x"),
            2: _pairs(profile, "pelvis_z"),
        },
        'pose.bones["pelvis"].rotation_euler': {
            2: _degree_pairs(profile, "pelvis_roll_z_degrees")
        },
        'pose.bones["spine"].rotation_euler': {
            0: _combined_degree_pairs(
                profile,
                "spine_pitch_x_degrees",
                base_degrees=stance.pose.spine_pitch_x_degrees * SPINE_STANCE_BLEND,
                source_scale=1.0,
            )
        },
        'pose.bones["chest"].rotation_euler': {
            2: _combined_degree_pairs(
                profile,
                "chest_yaw_z_degrees",
                base_degrees=stance.pose.chest_yaw_z_degrees * CHEST_STANCE_BLEND,
                source_scale=1.0,
            )
        },
        'pose.bones["head"].rotation_euler': {
            2: _combined_degree_pairs(
                profile,
                "head_yaw_z_degrees",
                base_degrees=stance.pose.head_yaw_z_degrees * HEAD_STANCE_BLEND,
                source_scale=1.0,
            )
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


def _onehand_channels(
    profile: object,
    grip: ArmedWalkGripV15,
    stance: object,
    frames: tuple[int, ...],
) -> dict[str, dict[int, list[tuple[int, float]]]]:
    channels = _base_walk_channels(profile, stance)
    free_forearm_source = _optional_source_attribute(
        profile,
        "forearm_left_x_degrees",
        "upper_arm_left_x_degrees",
    )
    channels.update(
        {
            'pose.bones["upper_arm.L"].rotation_euler': {
                0: _combined_degree_pairs(
                    profile,
                    "upper_arm_left_x_degrees",
                    base_degrees=stance.pose.upper_arm_left_x_degrees,
                    source_scale=grip.free_arm_swing_scale,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.upper_arm_left_z_degrees,
                ),
            },
            'pose.bones["forearm.L"].rotation_euler': {
                0: _combined_degree_pairs(
                    profile,
                    free_forearm_source,
                    base_degrees=stance.pose.forearm_left_x_degrees,
                    source_scale=FREE_FOREARM_SWING_SCALE,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.forearm_left_z_degrees,
                ),
            },
            'pose.bones["hand.L"].rotation_euler': {
                0: _constant_degree_pairs(frames, stance.hand_left_x_degrees),
                2: _constant_degree_pairs(frames, stance.hand_left_z_degrees),
            },
            'pose.bones["upper_arm.R"].rotation_euler': {
                0: _offset_degree_pairs(
                    frames,
                    base_degrees=stance.pose.upper_arm_right_x_degrees,
                    offsets_degrees=grip.weapon_arm_step_offsets_degrees,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.upper_arm_right_z_degrees,
                ),
            },
            'pose.bones["forearm.R"].rotation_euler': {
                0: _offset_degree_pairs(
                    frames,
                    base_degrees=stance.pose.forearm_right_x_degrees,
                    offsets_degrees=grip.weapon_arm_step_offsets_degrees,
                    offset_scale=WEAPON_FOREARM_COUNTER_SCALE,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.forearm_right_z_degrees,
                ),
            },
            'pose.bones["hand.R"].rotation_euler': {
                0: _constant_degree_pairs(
                    frames,
                    stance.pose.hand_right_x_degrees,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.hand_right_z_degrees,
                ),
            },
        }
    )
    return channels


def _twohand_channels(
    profile: object,
    grip: ArmedWalkGripV15,
    stance: object,
    frames: tuple[int, ...],
) -> dict[str, dict[int, list[tuple[int, float]]]]:
    channels = _base_walk_channels(profile, stance)
    channels.update(
        {
            'pose.bones["upper_arm.L"].rotation_euler': {
                0: _offset_degree_pairs(
                    frames,
                    base_degrees=stance.pose.upper_arm_left_x_degrees,
                    offsets_degrees=grip.weapon_arm_step_offsets_degrees,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.upper_arm_left_z_degrees,
                ),
            },
            'pose.bones["upper_arm.R"].rotation_euler': {
                0: _offset_degree_pairs(
                    frames,
                    base_degrees=stance.pose.upper_arm_right_x_degrees,
                    offsets_degrees=grip.weapon_arm_step_offsets_degrees,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.upper_arm_right_z_degrees,
                ),
            },
            'pose.bones["forearm.L"].rotation_euler': {
                0: _offset_degree_pairs(
                    frames,
                    base_degrees=stance.pose.forearm_left_x_degrees,
                    offsets_degrees=grip.weapon_arm_step_offsets_degrees,
                    offset_scale=WEAPON_FOREARM_COUNTER_SCALE,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.forearm_left_z_degrees,
                ),
            },
            'pose.bones["forearm.R"].rotation_euler': {
                0: _offset_degree_pairs(
                    frames,
                    base_degrees=stance.pose.forearm_right_x_degrees,
                    offsets_degrees=grip.weapon_arm_step_offsets_degrees,
                    offset_scale=WEAPON_FOREARM_COUNTER_SCALE,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.forearm_right_z_degrees,
                ),
            },
            'pose.bones["hand.L"].rotation_euler': {
                0: _constant_degree_pairs(frames, stance.hand_left_x_degrees),
                2: _constant_degree_pairs(frames, stance.hand_left_z_degrees),
            },
            'pose.bones["hand.R"].rotation_euler': {
                0: _constant_degree_pairs(
                    frames,
                    stance.pose.hand_right_x_degrees,
                ),
                2: _constant_degree_pairs(
                    frames,
                    stance.pose.hand_right_z_degrees,
                ),
            },
        }
    )
    return channels


def _action_id(grip: ArmedWalkGripV15, direction: str) -> str:
    return f"{grip.action_prefix}_{direction}_v15"


def _create_armed_walk_action(
    context: factory.BuildContext,
    direction: ArmedWalkDirectionV15,
    grip: ArmedWalkGripV15,
    stance: object,
) -> object:
    source_profile = _source_profile(context.config.character_id, direction.direction)
    frames = tuple(int(pose.frame) for pose in source_profile.poses)
    if grip.grip_id == "onehand_ready":
        channels = _onehand_channels(source_profile, grip, stance, frames)
    elif grip.grip_id == "twohand_center_high":
        channels = _twohand_channels(source_profile, grip, stance, frames)
    else:
        raise KeyError(f"Unknown armed walk grip: {grip.grip_id}")

    animation_id = _action_id(grip, direction.direction)
    action = factory._new_action(
        f"{context.config.character_id}_{animation_id}",
        context.rig,
        channels,
        animation_id=animation_id,
        fps=source_profile.fps,
    )
    action["profile_revision"] = "v15"
    action["animation_revision"] = "v01"
    action["direction"] = direction.direction
    action["frame_count"] = len(frames)
    action["source_walk_action_id"] = direction.source_action_id
    action["source_walk_profile_revision"] = direction.source_profile_revision
    action["source_walk_animation_revision"] = direction.source_animation_revision
    action["source_stance_variant_id"] = grip.stance_variant_id
    action["source_stance_revision"] = grip.stance_source_revision
    action["weapon_cycle_id"] = grip.weapon_cycle_id
    action["grip_mode"] = stance.grip_mode
    action["approved_lower_body_preserved"] = True
    action["armed_upper_body_override"] = True
    action["weapon_hand_stabilized"] = True
    action["physical_asymmetry_preserved"] = True
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


def create_walk_directional_weapon_actions_v15(
    context: factory.BuildContext,
) -> None:
    create_combat_idle_directional_cycles_v14(context)
    _assert_rig_contract(context)
    profile = load_walk_directional_weapon_profile_v15(
        context.config.character_id
    )
    stance_profile = load_weapon_stance_profile_v09(context.config.character_id)
    stance_by_id = {
        item.variant_id: item
        for item in stance_profile.variants
    }

    created_actions: list[str] = []
    for grip in profile.grips:
        stance = stance_by_id[grip.stance_variant_id]
        for direction in profile.directions:
            source_action_name = (
                f"{context.config.character_id}_{direction.source_action_id}"
            )
            source_action = factory.bpy.data.actions.get(source_action_name)
            if source_action is None:
                raise RuntimeError(
                    f"armed walk v15 source action is missing: {source_action_name}"
                )
            if source_action.get("profile_revision") != (
                direction.source_profile_revision
            ):
                raise RuntimeError(
                    f"armed walk v15 source profile mismatch: {source_action_name}"
                )
            if source_action.get("animation_revision") != (
                direction.source_animation_revision
            ):
                raise RuntimeError(
                    f"armed walk v15 source animation mismatch: {source_action_name}"
                )
            action = _create_armed_walk_action(
                context,
                direction,
                grip,
                stance,
            )
            created_actions.append(action.name)

    if len(created_actions) != 8 or len(set(created_actions)) != 8:
        raise RuntimeError(
            f"armed walk v15 requires eight unique actions, got {created_actions}"
        )

    idle = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle)
    context.rig.rotation_euler[2] = math.radians(
        context.config.directions["down"]
    )
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["walk_directional_weapon_revision"] = profile.revision
    scene["walk_directional_weapon_animation_revision"] = (
        profile.animation_revision
    )
    scene["walk_directional_weapon_action_count"] = len(created_actions)
    scene["walk_directional_weapon_total_frame_count"] = (
        len(created_actions) * len(profile.frame_order)
    )
    scene["walk_directional_weapon_source_walks"] = (
        "walk_down_v04,walk_left_v01,walk_right_v01,walk_up_v02"
    )
    scene["walk_directional_weapon_source_stances"] = (
        "onehand_ready_v09,twohand_center_high_v06"
    )
    scene["walk_directional_weapon_static_source"] = (
        profile.static_weapon_source_revision
    )
    scene["walk_directional_weapon_combat_idle_source"] = (
        profile.combat_idle_source_revision
    )
    scene["walk_directional_weapon_lower_body_preserved"] = True
    scene["walk_directional_weapon_geometry_changed"] = False
    scene["walk_directional_weapon_material_changed"] = False
    scene["walk_directional_weapon_root_translation_used"] = False
    scene["walk_directional_weapon_mirroring_used"] = False
    scene["walk_directional_weapon_negative_scale_used"] = False
