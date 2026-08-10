from __future__ import annotations

import blender_sprite_factory as factory
from death_directional_cycles_profile_v01 import (
    load_death_directional_cycles_profile_v01,
)
from death_down_cycle_builder_v01 import create_death_down_cycle_actions_v01
from death_down_cycle_profile_v01 import load_death_down_cycle_profiles_v01


def _csv(values: tuple[object, ...]) -> str:
    return ",".join(str(value) for value in values)


def create_death_directional_cycle_actions_v01(
    context: factory.BuildContext,
) -> None:
    create_death_down_cycle_actions_v01(context)
    directional = load_death_directional_cycles_profile_v01(
        context.config.character_id
    )
    source_by_variant = {
        profile.death_variant_id: profile
        for profile in load_death_down_cycle_profiles_v01(
            context.config.character_id
        )
    }

    action_names: list[str] = []
    for variant in directional.variants:
        source = source_by_variant[variant.death_variant_id]
        action_name = f"{context.config.character_id}_{variant.animation_id}"
        action = factory.bpy.data.actions.get(action_name)
        if action is None:
            raise RuntimeError(
                f"death directional cycle action is missing: {action_name}"
            )
        if action.get("profile_revision") != source.revision:
            raise RuntimeError(
                f"death directional source action drifted: {action_name}"
            )
        action["animation_revision"] = "directional_full_cycle_v01"
        action["directional_profile_revision"] = directional.revision
        action["directional_directions"] = _csv(directional.directions)
        action["directional_direction_count"] = len(directional.directions)
        action["directional_frame_count"] = (
            len(directional.directions) * len(directional.frame_order)
        )
        action["manual_full_cycle_review_required"] = False
        action["full_death_cycle_not_yet_approved"] = False
        action["directional_variants_not_started"] = False
        action["directional_render_contract_ready"] = True
        action["directional_render_complete"] = False
        action["manual_directional_review_required"] = True
        action["directional_variants_not_yet_approved"] = True
        action["random_runtime_selection_not_started"] = True
        action["runtime_connected"] = False
        action_names.append(action_name)

    scene = factory.bpy.context.scene
    scene["death_directional_cycle_revision"] = "v01"
    scene["death_directional_profile_revision"] = directional.revision
    scene["death_directional_actions"] = ",".join(action_names)
    scene["death_directional_action_count"] = len(action_names)
    scene["death_directional_directions"] = _csv(directional.directions)
    scene["death_directional_review_directions"] = _csv(
        directional.review_directions
    )
    scene["death_directional_direction_count"] = len(directional.directions)
    scene["death_directional_frame_count"] = (
        len(directional.variants)
        * len(directional.directions)
        * len(directional.frame_order)
    )
    scene["death_down_manual_full_cycle_review_required"] = False
    scene["death_down_full_cycle_not_yet_approved"] = False
    scene["death_down_directional_variants_not_started"] = False
    scene["death_directional_render_contract_ready"] = True
    scene["death_directional_render_complete"] = False
    scene["death_directional_manual_review_required"] = True
    scene["death_directional_variants_not_yet_approved"] = True
    scene["death_directional_real_rig_rotation"] = True
    scene["death_directional_weapon_agnostic"] = True
    scene["death_directional_weapon_visible"] = False
    scene["death_directional_final_pose_persistent"] = True
    scene["death_directional_root_translation_used"] = False
    scene["death_directional_mirroring_used"] = False
    scene["death_directional_negative_scale_used"] = False
    scene["death_directional_geometry_changed"] = False
    scene["death_directional_material_changed"] = False
    scene["death_directional_random_runtime_selection_not_started"] = True
    scene["death_directional_runtime_connected"] = False
