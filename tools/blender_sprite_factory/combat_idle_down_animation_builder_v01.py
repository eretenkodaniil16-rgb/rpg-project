from __future__ import annotations

import math

import blender_sprite_factory as factory
import walk_up_animation_builder_v02 as approved_walk_builder
from combat_idle_down_profile_v01 import (
    CombatIdleDownProfileV01,
    load_combat_idle_down_profile_v01,
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

COMBAT_WEAPON_OBJECT_NAMES = (
    "combat_sword_blade",
    "combat_sword_guard",
    "combat_sword_grip",
    "combat_sword_pommel",
)
SHEATHED_HILT_OBJECT_NAMES = ("sword_grip", "sword_guard")

_BASE_ASSIGN_ACTION = factory._assign_action
_NEUTRAL_ASSIGNMENT_INSTALLED = False


def reset_rig_pose_to_neutral(rig: object) -> None:
    for pose_bone in rig.pose.bones:
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    factory.bpy.context.view_layer.update()


def _assign_action_with_neutral_pose(rig: object, action: object) -> None:
    reset_rig_pose_to_neutral(rig)
    _BASE_ASSIGN_ACTION(rig, action)


def install_neutral_pose_action_assignment() -> None:
    global _NEUTRAL_ASSIGNMENT_INSTALLED
    if _NEUTRAL_ASSIGNMENT_INSTALLED:
        return
    factory._assign_action = _assign_action_with_neutral_pose
    _NEUTRAL_ASSIGNMENT_INSTALLED = True


def _value_pairs(value: float) -> list[tuple[int, float]]:
    return [(1, float(value))]


def _degree_pairs(value: float) -> list[tuple[int, float]]:
    return [(1, math.radians(float(value)))]


def _assert_rig_contract(context: factory.BuildContext) -> None:
    actual_bones = set(context.rig.pose.bones.keys())
    missing = sorted(_REQUIRED_BONES.difference(actual_bones))
    if missing:
        raise RuntimeError(
            f"combat_idle_down v01 rig is missing required bones: {missing}"
        )


def _create_combat_idle_action(
    context: factory.BuildContext,
    profile: CombatIdleDownProfileV01,
) -> object:
    pose = profile.pose
    channels = {
        'pose.bones["pelvis"].location': {
            0: _value_pairs(pose.pelvis_x),
            2: _value_pairs(pose.pelvis_z),
        },
        'pose.bones["pelvis"].rotation_euler': {
            2: _degree_pairs(pose.pelvis_roll_z_degrees)
        },
        'pose.bones["spine"].rotation_euler': {
            0: _degree_pairs(pose.spine_pitch_x_degrees)
        },
        'pose.bones["chest"].rotation_euler': {
            2: _degree_pairs(pose.chest_yaw_z_degrees)
        },
        'pose.bones["head"].rotation_euler': {
            2: _degree_pairs(pose.head_yaw_z_degrees)
        },
        'pose.bones["thigh.L"].rotation_euler': {
            0: _degree_pairs(pose.thigh_left_x_degrees),
            2: _degree_pairs(pose.thigh_left_z_degrees),
        },
        'pose.bones["thigh.R"].rotation_euler': {
            0: _degree_pairs(pose.thigh_right_x_degrees),
            2: _degree_pairs(pose.thigh_right_z_degrees),
        },
        'pose.bones["shin.L"].rotation_euler': {
            0: _degree_pairs(pose.shin_left_x_degrees)
        },
        'pose.bones["shin.R"].rotation_euler': {
            0: _degree_pairs(pose.shin_right_x_degrees)
        },
        'pose.bones["foot.L"].rotation_euler': {
            0: _degree_pairs(pose.foot_left_x_degrees)
        },
        'pose.bones["foot.R"].rotation_euler': {
            0: _degree_pairs(pose.foot_right_x_degrees)
        },
        'pose.bones["upper_arm.L"].rotation_euler': {
            0: _degree_pairs(pose.upper_arm_left_x_degrees),
            2: _degree_pairs(pose.upper_arm_left_z_degrees),
        },
        'pose.bones["forearm.L"].rotation_euler': {
            0: _degree_pairs(pose.forearm_left_x_degrees),
            2: _degree_pairs(pose.forearm_left_z_degrees),
        },
        'pose.bones["upper_arm.R"].rotation_euler': {
            0: _degree_pairs(pose.upper_arm_right_x_degrees),
            2: _degree_pairs(pose.upper_arm_right_z_degrees),
        },
        'pose.bones["forearm.R"].rotation_euler': {
            0: _degree_pairs(pose.forearm_right_x_degrees),
            2: _degree_pairs(pose.forearm_right_z_degrees),
        },
        'pose.bones["hand.R"].rotation_euler': {
            0: _degree_pairs(pose.hand_right_x_degrees),
            2: _degree_pairs(pose.hand_right_z_degrees),
        },
        'pose.bones["cloth.L"].rotation_euler': {
            0: _degree_pairs(pose.cloth_left_x_degrees)
        },
        'pose.bones["cloth.C"].rotation_euler': {
            0: _degree_pairs(pose.cloth_center_x_degrees)
        },
        'pose.bones["cloth.R"].rotation_euler': {
            0: _degree_pairs(pose.cloth_right_x_degrees)
        },
    }
    action = factory._new_action(
        f"{context.config.character_id}_combat_idle",
        context.rig,
        channels,
        animation_id=profile.animation_id,
        fps=profile.fps,
    )
    action["profile_revision"] = profile.revision
    action["pose_revision"] = profile.pose_revision
    action["direction"] = profile.direction
    action["phase"] = pose.phase
    action["weapon_id"] = profile.weapon_id
    action["weapon_hand"] = profile.weapon_hand
    action["appearance_revision"] = "v03"
    action["appearance_locked"] = True
    action["walk_down_approved_revision"] = "v04"
    action["walk_left_approved_revision"] = "v01"
    action["walk_right_approved_revision"] = "v01"
    action["walk_up_approved_revision"] = "v02"
    action["static_pose_only"] = True
    action["root_translation_used"] = False
    action["mirroring_used"] = False
    action["negative_scale_used"] = False
    action["neutral_pose_reset_before_assignment"] = True
    action.use_fake_user = True
    return action


def _ensure_combat_weapon_collection(context: factory.BuildContext) -> None:
    if "combat_weapon" in context.module_collections:
        return
    modules_root = factory.bpy.data.collections.get("MODULES")
    if modules_root is None:
        raise RuntimeError("combat_idle_down v01 cannot find MODULES collection")
    context.module_collections["combat_weapon"] = factory._new_collection(
        "MOD_combat_weapon",
        modules_root,
    )


def _register_weapon_part(
    context: factory.BuildContext,
    obj: object,
    weapon_part: str,
) -> object:
    registered = factory._register(
        context,
        obj,
        "combat_weapon",
        "hand.R",
        "right",
    )
    registered["weapon_id"] = "sword_01"
    registered["weapon_part"] = weapon_part
    registered["weapon_state"] = "drawn"
    registered["combat_idle_down_revision"] = "v01"
    registered.hide_render = True
    registered.hide_viewport = True
    return registered


def _build_drawn_sword(context: factory.BuildContext) -> tuple[object, ...]:
    existing = [
        name for name in COMBAT_WEAPON_OBJECT_NAMES if factory.bpy.data.objects.get(name)
    ]
    if existing:
        raise RuntimeError(
            f"combat_idle_down v01 weapon objects already exist: {existing}"
        )
    _ensure_combat_weapon_collection(context)

    hand_bone = context.rig.pose.bones["hand.R"]
    anchor = context.rig.matrix_world @ ((hand_bone.head + hand_bone.tail) * 0.5)
    blade_direction = factory.Vector((-0.23, -0.26, -1.0)).normalized()
    guard_lateral = factory.Vector((0.94, -0.34, 0.0)).normalized()

    pommel_center = anchor - blade_direction * 0.22
    grip_start = anchor - blade_direction * 0.14
    grip_end = anchor + blade_direction * 0.28
    guard_center = anchor + blade_direction * 0.32
    blade_start = anchor + blade_direction * 0.38
    blade_end = blade_start + blade_direction * 1.34
    guard_extent = guard_lateral * 0.27

    grip = factory._cylinder_between(
        "combat_sword_grip",
        tuple(grip_start),
        tuple(grip_end),
        0.075,
        8,
        context.materials["boots"],
    )
    guard = factory._cylinder_between(
        "combat_sword_guard",
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.055,
        4,
        context.materials["silver"],
    )
    blade = factory._cylinder_between(
        "combat_sword_blade",
        tuple(blade_start),
        tuple(blade_end),
        0.090,
        4,
        context.materials["silver"],
    )
    pommel = factory._ellipsoid(
        "combat_sword_pommel",
        tuple(pommel_center),
        (0.12, 0.12, 0.13),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )

    return (
        _register_weapon_part(context, blade, "blade"),
        _register_weapon_part(context, guard, "guard"),
        _register_weapon_part(context, grip, "grip"),
        _register_weapon_part(context, pommel, "pommel"),
    )


def create_combat_idle_down_actions_v01(context: factory.BuildContext) -> None:
    approved_walk_builder.create_walk_up_actions_v02(context)
    install_neutral_pose_action_assignment()
    _assert_rig_contract(context)
    profile = load_combat_idle_down_profile_v01(context.config.character_id)
    action = _create_combat_idle_action(context, profile)

    factory._assign_action(context.rig, action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(profile.pose.frame)
    factory.bpy.context.view_layer.update()
    weapon_parts = _build_drawn_sword(context)

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["walk_up_artist_approved"] = True
    scene["walk_up_approved_revision"] = "v02"
    scene["combat_idle_profile_revision"] = profile.revision
    scene["combat_idle_pose_revision"] = profile.pose_revision
    scene["combat_idle_direction"] = profile.direction
    scene["combat_idle_weapon_id"] = profile.weapon_id
    scene["combat_idle_weapon_hand"] = profile.weapon_hand
    scene["combat_idle_static_pose_only"] = True
    scene["combat_weapon_object_count"] = len(weapon_parts)
    scene["combat_idle_geometry_changed"] = False
    scene["combat_idle_material_changed"] = False
    scene["combat_idle_mirroring_used"] = False
    scene["neutral_pose_reset_before_action_assignment"] = True

    if action.name != f"{context.config.character_id}_combat_idle":
        raise RuntimeError("combat_idle_down v01 action name drifted")
