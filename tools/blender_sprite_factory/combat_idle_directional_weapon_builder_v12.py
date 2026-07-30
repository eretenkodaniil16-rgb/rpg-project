from __future__ import annotations

import math

import blender_sprite_factory as factory
import combat_idle_down_weapon_variants_builder_v06 as weapon_builder
from combat_idle_directional_weapon_profile_v12 import (
    OneHandDirectionVectorV12,
    load_combat_idle_directional_weapon_profile_v12,
)
from combat_idle_down_cycles_builder_v10 import create_combat_idle_cycles_v10
from combat_idle_down_weapon_variants_profile_v06 import (
    ONE_HAND_BLADE_LENGTH,
    ONE_HAND_GRIP_LENGTH,
)


ONE_HAND_LEFT_V12_OBJECT_NAMES = (
    "combat_onehand_left_v12_blade",
    "combat_onehand_left_v12_highlight",
    "combat_onehand_left_v12_tip",
    "combat_onehand_left_v12_guard",
    "combat_onehand_left_v12_grip",
    "combat_onehand_left_v12_pommel",
)
ONE_HAND_RIGHT_V12_OBJECT_NAMES = (
    "combat_onehand_right_v12_blade",
    "combat_onehand_right_v12_highlight",
    "combat_onehand_right_v12_tip",
    "combat_onehand_right_v12_guard",
    "combat_onehand_right_v12_grip",
    "combat_onehand_right_v12_pommel",
)
ONE_HAND_UP_V12_OBJECT_NAMES = (
    "combat_onehand_up_v12_blade",
    "combat_onehand_up_v12_highlight",
    "combat_onehand_up_v12_tip",
    "combat_onehand_up_v12_guard",
    "combat_onehand_up_v12_grip",
    "combat_onehand_up_v12_pommel",
)
ONE_HAND_V12_OBJECTS_BY_DIRECTION = {
    "left": ONE_HAND_LEFT_V12_OBJECT_NAMES,
    "right": ONE_HAND_RIGHT_V12_OBJECT_NAMES,
    "up": ONE_HAND_UP_V12_OBJECT_NAMES,
}


def _register_part(
    context: factory.BuildContext,
    obj: object,
    *,
    weapon_part: str,
    direction: str,
) -> object:
    registered = factory._register(
        context,
        obj,
        "combat_weapon",
        "hand.R",
        "right",
    )
    registered["weapon_id"] = f"sword_01_onehand_directional_v12_{direction}"
    registered["weapon_part"] = weapon_part
    registered["weapon_state"] = "drawn"
    registered["weapon_variant_id"] = "onehand_ready"
    registered["combat_idle_directional_weapon_revision"] = "v12"
    registered["combat_idle_direction"] = direction
    registered["pose_fitted_directional_module"] = True
    registered.hide_render = True
    registered.hide_viewport = True
    return registered


def _build_directional_onehand(
    context: factory.BuildContext,
    vector_profile: OneHandDirectionVectorV12,
) -> tuple[object, ...]:
    direction_id = vector_profile.direction
    names = ONE_HAND_V12_OBJECTS_BY_DIRECTION[direction_id]
    existing = [name for name in names if factory.bpy.data.objects.get(name) is not None]
    if existing:
        raise RuntimeError(
            f"combat idle directional weapon v12 objects already exist: {existing}"
        )

    hand = context.rig.pose.bones["hand.R"]
    anchor = context.rig.matrix_world @ ((hand.head + hand.tail) * 0.5)
    direction = factory.Vector(vector_profile.as_tuple()).normalized()
    guard_lateral = factory.Vector((direction.y, -direction.x, 0.0)).normalized()
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
        names[0],
        tuple(blade_start),
        tuple(blade_end),
        0.135,
        4,
        context.materials["silver"],
    )
    highlight = factory._cylinder_between(
        names[1],
        tuple(blade_start + highlight_offset),
        tuple(blade_end + highlight_offset),
        0.035,
        4,
        highlight_material,
    )
    tip = weapon_builder._pointed_tip(
        names[2],
        blade_end,
        direction,
        0.135,
        context.materials["silver"],
    )
    guard = factory._cylinder_between(
        names[3],
        tuple(guard_center - guard_extent),
        tuple(guard_center + guard_extent),
        0.067,
        4,
        context.materials["silver"],
    )
    grip = factory._cylinder_between(
        names[4],
        tuple(grip_start),
        tuple(grip_end),
        0.086,
        8,
        context.materials["boots"],
    )
    pommel = factory._ellipsoid(
        names[5],
        tuple(pommel_center),
        (0.14, 0.14, 0.16),
        context.materials["dark_steel"],
        segments=8,
        rings=5,
    )
    parts = (blade, highlight, tip, guard, grip, pommel)
    part_names = ("blade", "highlight", "tip", "guard", "grip", "pommel")
    return tuple(
        _register_part(
            context,
            obj,
            weapon_part=part_name,
            direction=direction_id,
        )
        for obj, part_name in zip(parts, part_names)
    )


def create_combat_idle_directional_weapon_v12(
    context: factory.BuildContext,
) -> None:
    create_combat_idle_cycles_v10(context)
    profile = load_combat_idle_directional_weapon_profile_v12(
        context.config.character_id
    )
    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_combat_idle_onehand_ready_cycle_v10"
    )
    if action is None or action.get("profile_revision") != "v10":
        raise RuntimeError("combat idle directional weapon v12 requires one-hand cycle v10")

    built_counts: dict[str, int] = {}
    for vector_profile in profile.corrected_onehand_directions:
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            context.config.directions[vector_profile.direction]
        )
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
        parts = _build_directional_onehand(context, vector_profile)
        built_counts[vector_profile.direction] = len(parts)

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_directional_weapon_revision"] = profile.revision
    scene["combat_idle_directional_weapon_corrected_directions"] = "left,right,up"
    scene["combat_idle_directional_weapon_object_count"] = sum(built_counts.values())
    scene["combat_idle_directional_weapon_onehand_down_preserved"] = True
    scene["combat_idle_directional_weapon_twohand_v11_preserved"] = True
    scene["combat_idle_directional_weapon_body_actions_unchanged"] = True
    scene["combat_idle_directional_weapon_appearance_revision"] = "v03"
    scene["combat_idle_directional_weapon_mirroring_used"] = False
    scene["combat_idle_directional_weapon_negative_scale_used"] = False
