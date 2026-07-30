from __future__ import annotations

import math

import blender_sprite_factory as factory
import combat_idle_down_weapon_variants_builder_v06 as weapon_builder
from combat_idle_directional_weapon_builder_v12 import (
    create_combat_idle_directional_weapon_v12,
)
from combat_idle_directional_weapon_profile_v13 import (
    OneHandSideCorrectionV13,
    load_combat_idle_directional_weapon_profile_v13,
)
from combat_idle_down_weapon_variants_profile_v06 import (
    ONE_HAND_BLADE_LENGTH,
    ONE_HAND_GRIP_LENGTH,
)


ONE_HAND_LEFT_V13_OBJECT_NAMES = tuple(
    f"combat_onehand_left_v13_{part}"
    for part in ("blade", "highlight", "tip", "guard", "grip", "pommel")
)
ONE_HAND_RIGHT_V13_OBJECT_NAMES = tuple(
    f"combat_onehand_right_v13_{part}"
    for part in ("blade", "highlight", "tip", "guard", "grip", "pommel")
)
ONE_HAND_V13_OBJECTS_BY_DIRECTION = {
    "left": ONE_HAND_LEFT_V13_OBJECT_NAMES,
    "right": ONE_HAND_RIGHT_V13_OBJECT_NAMES,
}


def _register_part(
    context: factory.BuildContext,
    obj: object,
    *,
    part: str,
    direction: str,
) -> object:
    registered = factory._register(context, obj, "combat_weapon", "hand.R", "right")
    registered["weapon_id"] = f"sword_01_onehand_side_v13_{direction}"
    registered["weapon_part"] = part
    registered["weapon_state"] = "drawn"
    registered["weapon_variant_id"] = "onehand_ready"
    registered["combat_idle_directional_weapon_revision"] = "v13"
    registered["combat_idle_direction"] = direction
    registered["pose_fitted_directional_module"] = True
    registered["anchor_offset_applied"] = True
    registered.hide_render = True
    registered.hide_viewport = True
    return registered


def _build_side_module(
    context: factory.BuildContext,
    correction: OneHandSideCorrectionV13,
) -> tuple[object, ...]:
    names = ONE_HAND_V13_OBJECTS_BY_DIRECTION[correction.direction]
    existing = [name for name in names if factory.bpy.data.objects.get(name) is not None]
    if existing:
        raise RuntimeError(f"combat idle directional weapon v13 objects exist: {existing}")

    hand = context.rig.pose.bones["hand.R"]
    anchor = context.rig.matrix_world @ ((hand.head + hand.tail) * 0.5)
    anchor += factory.Vector(correction.anchor_offset)
    direction = factory.Vector(correction.blade_vector).normalized()
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

    objects = (
        factory._cylinder_between(names[0], tuple(blade_start), tuple(blade_end), 0.135, 4, context.materials["silver"]),
        factory._cylinder_between(names[1], tuple(blade_start + highlight_offset), tuple(blade_end + highlight_offset), 0.035, 4, highlight_material),
        weapon_builder._pointed_tip(names[2], blade_end, direction, 0.135, context.materials["silver"]),
        factory._cylinder_between(names[3], tuple(guard_center - guard_extent), tuple(guard_center + guard_extent), 0.067, 4, context.materials["silver"]),
        factory._cylinder_between(names[4], tuple(grip_start), tuple(grip_end), 0.086, 8, context.materials["boots"]),
        factory._ellipsoid(names[5], tuple(pommel_center), (0.14, 0.14, 0.16), context.materials["dark_steel"], segments=8, rings=5),
    )
    parts = ("blade", "highlight", "tip", "guard", "grip", "pommel")
    return tuple(
        _register_part(context, obj, part=part, direction=correction.direction)
        for obj, part in zip(objects, parts)
    )


def create_combat_idle_directional_weapon_v13(context: factory.BuildContext) -> None:
    create_combat_idle_directional_weapon_v12(context)
    profile = load_combat_idle_directional_weapon_profile_v13(context.config.character_id)
    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_combat_idle_onehand_ready_cycle_v10"
    )
    if action is None or action.get("profile_revision") != "v10":
        raise RuntimeError("combat idle directional weapon v13 requires v10 action")

    count = 0
    for correction in profile.corrected_sides:
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            context.config.directions[correction.direction]
        )
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
        count += len(_build_side_module(context, correction))

    idle = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_directional_weapon_revision"] = "v13"
    scene["combat_idle_directional_weapon_v13_object_count"] = count
    scene["combat_idle_directional_weapon_v13_corrected_sides"] = "left,right"
    scene["combat_idle_directional_weapon_v13_down_up_locked"] = True
    scene["combat_idle_directional_weapon_v13_twohand_locked"] = True
    scene["combat_idle_directional_weapon_v13_actions_unchanged"] = True
    scene["combat_idle_directional_weapon_v13_mirroring_used"] = False
