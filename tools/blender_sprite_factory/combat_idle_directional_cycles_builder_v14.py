from __future__ import annotations

import math

import blender_sprite_factory as factory
from combat_idle_directional_cycles_profile_v14 import (
    load_combat_idle_directional_cycles_profile_v14,
)
from combat_idle_directional_weapon_builder_v12 import (
    create_combat_idle_directional_weapon_v12,
)


def create_combat_idle_directional_cycles_v14(
    context: factory.BuildContext,
) -> None:
    create_combat_idle_directional_weapon_v12(context)
    profile = load_combat_idle_directional_cycles_profile_v14(
        context.config.character_id
    )

    for cycle in profile.cycles:
        action_name = f"{context.config.character_id}_{cycle.source_action_id}"
        action = factory.bpy.data.actions.get(action_name)
        if action is None:
            raise RuntimeError(
                f"combat idle directional cycles v14 cannot find action: {action_name}"
            )
        if action.get("profile_revision") != "v10":
            raise RuntimeError(
                f"combat idle directional cycles v14 requires v10 action: {action_name}"
            )
        if int(action.get("frame_count", 0)) != 4:
            raise RuntimeError(
                f"combat idle directional cycles v14 requires four frames: {action_name}"
            )
        if int(action.get("fps", 0)) != cycle.fps or not bool(action.get("loop", False)):
            raise RuntimeError(
                f"combat idle directional cycles v14 timing mismatch: {action_name}"
            )
        action["directional_cycle_revision"] = profile.revision
        action["directional_static_source_revision"] = profile.static_source_revision
        action["directional_render_animation_id"] = cycle.render_animation_id
        action["directional_directions"] = ",".join(profile.directions)
        action["artist_approved_directional_sources"] = True
        action["directional_action_reused_without_duplication"] = True
        action["mirroring_used"] = False
        action["negative_scale_used"] = False
        action.use_fake_user = True

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    context.rig.rotation_euler[2] = math.radians(context.config.directions["down"])
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_directional_cycles_revision"] = profile.revision
    scene["combat_idle_directional_cycles_static_source"] = (
        profile.static_source_revision
    )
    scene["combat_idle_directional_cycles_rejected_experiment"] = (
        profile.rejected_experiment_revision
    )
    scene["combat_idle_directional_cycles_count"] = len(profile.cycles)
    scene["combat_idle_directional_cycles_direction_count"] = len(profile.directions)
    scene["combat_idle_directional_cycles_frame_count"] = len(profile.frame_order)
    scene["combat_idle_directional_cycles_total_frames"] = (
        len(profile.cycles) * len(profile.directions) * len(profile.frame_order)
    )
    scene["combat_idle_directional_cycles_actions_reused"] = True
    scene["combat_idle_directional_cycles_weapon_geometry_rebuilt"] = False
    scene["combat_idle_directional_cycles_mirroring_used"] = False
    scene["combat_idle_directional_cycles_negative_scale_used"] = False
