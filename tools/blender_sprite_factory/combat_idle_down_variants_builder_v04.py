from __future__ import annotations

import blender_sprite_factory as factory
import combat_idle_down_animation_builder_v01 as base_builder
import combat_idle_down_variants_builder_v02 as shared_builder
from combat_idle_down_variants_profile_v04 import (
    load_combat_idle_down_variants_profile_v04,
)


def create_combat_idle_down_variant_actions_v04(
    context: factory.BuildContext,
) -> None:
    base_builder.create_combat_idle_down_actions_v01(context)
    profile = load_combat_idle_down_variants_profile_v04(context.config.character_id)

    created_names: list[str] = []
    for variant in profile.variants:
        action_name = f"{context.config.character_id}_{variant.animation_id}"
        if factory.bpy.data.actions.get(action_name) is not None:
            raise RuntimeError(
                f"combat_idle_down variants v04 action already exists: {action_name}"
            )
        action = shared_builder._create_variant_action(context, variant)
        action["profile_revision"] = "v04"
        action["wide_side_guard"] = True
        action["arms_move_away_from_torso_center"] = True
        action["blade_remains_outside_torso_center"] = True
        action["supersedes_centered_revision"] = "v03"
        action["approved_walk_set_unchanged"] = True
        created_names.append(action.name)

    idle_action = factory.bpy.data.actions[f"{context.config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    factory.bpy.context.scene.frame_set(1)
    factory.bpy.context.view_layer.update()

    scene = factory.bpy.context.scene
    scene["combat_idle_variants_revision"] = profile.revision
    scene["combat_idle_variant_count"] = len(profile.variants)
    scene["combat_idle_variant_ids"] = ",".join(
        item.variant_id for item in profile.variants
    )
    scene["combat_idle_variant_actions"] = ",".join(created_names)
    scene["combat_idle_variants_weapon_hand"] = profile.weapon_hand
    scene["combat_idle_variants_wide_side_guard"] = True
    scene["combat_idle_variants_centered_revision_rejected"] = "v03"
    scene["combat_idle_variants_mirroring_used"] = False
    scene["combat_idle_variants_approved_walk_set_unchanged"] = True
