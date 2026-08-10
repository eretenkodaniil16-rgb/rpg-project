from __future__ import annotations

import blender_sprite_factory as factory
import death_down_keyposes_builder_v01 as keypose_builder
from death_down_cycle_profile_v01 import (
    APPROVED_ANCHOR_FRAMES,
    CORPSE_HOLD_FRAME,
    INTERPOLATED_FRAMES,
    SOURCE_KEYPOSE_REVISIONS,
    load_death_down_cycle_profiles_v01,
)


BASE_PROFILE_LOADER = keypose_builder.load_death_down_keyposes_profiles_v01


def _frame_list(values: tuple[int, ...]) -> str:
    return ",".join(str(value) for value in values)


def create_death_down_cycle_actions_v01(context: factory.BuildContext) -> None:
    keypose_builder.load_death_down_keyposes_profiles_v01 = (
        load_death_down_cycle_profiles_v01
    )
    try:
        keypose_builder.create_death_down_keypose_actions_v01(context)
    finally:
        keypose_builder.load_death_down_keyposes_profiles_v01 = BASE_PROFILE_LOADER

    profiles = load_death_down_cycle_profiles_v01(context.config.character_id)
    action_names: list[str] = []
    for profile in profiles:
        action_name = f"{context.config.character_id}_{profile.animation_id}"
        action = factory.bpy.data.actions.get(action_name)
        if action is None:
            raise RuntimeError(f"death down cycle v01 action is missing: {action_name}")
        action["profile_revision"] = profile.revision
        action["animation_revision"] = "full_cycle_v01"
        action["animation_family"] = "death"
        action["source_keypose_revision"] = SOURCE_KEYPOSE_REVISIONS[
            profile.death_variant_id
        ]
        action["approved_anchor_frames"] = _frame_list(APPROVED_ANCHOR_FRAMES)
        action["interpolated_frames"] = _frame_list(INTERPOLATED_FRAMES)
        action["corpse_hold_frame"] = CORPSE_HOLD_FRAME
        action["manual_keypose_review_required"] = False
        action["manual_full_cycle_review_required"] = True
        action["full_death_cycle_not_yet_approved"] = True
        action["directional_variants_not_started"] = True
        action["random_runtime_selection_not_started"] = True
        action["runtime_connected"] = False
        action_names.append(action_name)

    scene = factory.bpy.context.scene
    scene["death_down_cycle_revision"] = "v01"
    scene["death_down_cycle_action_count"] = len(action_names)
    scene["death_down_cycle_frame_count"] = sum(
        len(profile.frame_order) for profile in profiles
    )
    scene["death_down_cycle_actions"] = ",".join(action_names)
    scene["death_down_cycle_source_keyposes"] = ",".join(
        SOURCE_KEYPOSE_REVISIONS[profile.death_variant_id]
        for profile in profiles
    )
    scene["death_down_cycle_approved_anchor_frames"] = _frame_list(
        APPROVED_ANCHOR_FRAMES
    )
    scene["death_down_cycle_interpolated_frames"] = _frame_list(
        INTERPOLATED_FRAMES
    )
    scene["death_down_cycle_corpse_hold_frame"] = CORPSE_HOLD_FRAME
    scene["death_down_manual_keypose_review_required"] = False
    scene["death_down_manual_full_cycle_review_required"] = True
    scene["death_down_full_cycle_not_yet_approved"] = True
    scene["death_down_directional_variants_not_started"] = True
    scene["death_down_random_runtime_selection_not_started"] = True
    scene["death_down_runtime_connected"] = False
    scene["death_down_root_translation_used"] = False
    scene["death_down_mirroring_used"] = False
    scene["death_down_negative_scale_used"] = False
    scene["death_down_geometry_changed"] = False
    scene["death_down_material_changed"] = False
