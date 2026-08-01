from __future__ import annotations

import attack_sword_down_keyposes_builder_v17 as keypose_builder
import blender_sprite_factory as factory
from attack_sword_down_cycle_profile_v20 import (
    SOURCE_KEYPOSE_REVISION,
    load_attack_sword_down_cycle_profile_v20,
)


BASE_PROFILE_LOADER = keypose_builder.load_attack_sword_down_keyposes_profile_v17


def create_attack_sword_down_cycle_actions_v20(
    context: factory.BuildContext,
) -> None:
    keypose_builder.load_attack_sword_down_keyposes_profile_v17 = (
        load_attack_sword_down_cycle_profile_v20
    )
    try:
        keypose_builder.create_attack_sword_down_keypose_actions_v17(context)
    finally:
        keypose_builder.load_attack_sword_down_keyposes_profile_v17 = (
            BASE_PROFILE_LOADER
        )

    profile = load_attack_sword_down_cycle_profile_v20(context.config.character_id)
    action_names: list[str] = []
    for grip in profile.grips:
        action_name = f"{context.config.character_id}_{grip.action_id}"
        action = factory.bpy.data.actions.get(action_name)
        if action is None:
            raise RuntimeError(f"attack sword down v20 action is missing: {action_name}")
        action["profile_revision"] = profile.revision
        action["animation_revision"] = "full_cycle_v20"
        action["animation_family"] = "attack_sword_01"
        action["direction"] = "down"
        action["frame_count"] = len(profile.frame_order)
        action["phase_order"] = ",".join(profile.phase_order)
        action["source_keypose_revision"] = SOURCE_KEYPOSE_REVISION
        action["approved_anchor_frames"] = "1,3,4,5,7,8"
        action["interpolated_frames"] = "2,6"
        action["manual_full_cycle_review_required"] = True
        action["full_attack_cycle_not_yet_approved"] = True
        action["runtime_connected"] = False
        action_names.append(action_name)

    scene = factory.bpy.context.scene
    scene["attack_sword_down_cycle_revision"] = profile.revision
    scene["attack_sword_down_cycle_action_count"] = len(action_names)
    scene["attack_sword_down_cycle_frame_count"] = sum(
        len(grip.poses) for grip in profile.grips
    )
    scene["attack_sword_down_cycle_actions"] = ",".join(action_names)
    scene["attack_sword_down_cycle_source_keyposes"] = SOURCE_KEYPOSE_REVISION
    scene["attack_sword_down_cycle_manual_review_required"] = True
    scene["attack_sword_down_cycle_runtime_connected"] = False
    scene["attack_sword_down_cycle_root_translation_used"] = False
    scene["attack_sword_down_cycle_mirroring_used"] = False
    scene["attack_sword_down_cycle_negative_scale_used"] = False
    scene["attack_sword_down_cycle_geometry_changed"] = False
    scene["attack_sword_down_cycle_material_changed"] = False
