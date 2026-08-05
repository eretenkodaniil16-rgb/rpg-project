from __future__ import annotations

import blender_sprite_factory as factory
from combat_idle_directional_cycles_builder_v14 import (
    create_combat_idle_directional_cycles_v14,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
)
from death_down_keyposes_profile_v01 import (
    load_death_down_keyposes_profile_v01,
)
from hit_down_keyposes_builder_v01 import (
    _assert_rig_contract,
    _hit_channels,
)


def create_death_down_keypose_action_v01(context: factory.BuildContext) -> None:
    create_combat_idle_directional_cycles_v14(context)
    _assert_rig_contract(context)

    profile = load_death_down_keyposes_profile_v01(context.config.character_id)
    stance_profile = load_weapon_stance_profile_v09(context.config.character_id)
    stance_by_id = {item.variant_id: item for item in stance_profile.variants}
    stance = stance_by_id.get(profile.stance_variant_id)
    if stance is None:
        raise RuntimeError(
            f"death down v01 stance is missing: {profile.stance_variant_id}"
        )

    action_name = f"{context.config.character_id}_{profile.animation_id}"
    if factory.bpy.data.actions.get(action_name) is not None:
        raise RuntimeError(f"death down v01 action already exists: {action_name}")

    action = factory._new_action(
        action_name,
        context.rig,
        _hit_channels(profile.poses, stance),
        animation_id=profile.animation_id,
        fps=profile.fps,
    )
    action["profile_revision"] = profile.revision
    action["animation_revision"] = "keyposes_v01_pass01"
    action["animation_family"] = "death_01"
    action["direction"] = profile.direction
    action["grip_mode"] = stance.grip_mode
    action["stance_variant_id"] = profile.stance_variant_id
    action["stance_source_revision"] = profile.stance_source_revision
    action["weapon_cycle_id"] = profile.weapon_cycle_id
    action["fall_side"] = profile.fall_side
    action["frame_count"] = len(profile.poses)
    action["phase_order"] = ",".join(profile.phase_order)
    action["final_pose_persistent"] = profile.final_pose_persistent
    action["weapon_release_deferred"] = profile.weapon_release_deferred
    action["manual_keypose_review_required"] = True
    action["full_death_cycle_not_yet_approved"] = True
    action["directional_variants_not_started"] = True
    action["twohand_adaptation_not_started"] = True
    action["runtime_connected"] = False
    action["appearance_revision"] = profile.appearance_revision
    action["head_revision"] = profile.head_revision
    action["proxy_revision"] = profile.proxy_revision
    action["root_translation_used"] = False
    action["mirroring_used"] = False
    action["negative_scale_used"] = False
    action["geometry_changed"] = False
    action["material_changed"] = False
    action.use_fake_user = True

    scene = factory.bpy.context.scene
    scene["death_down_action_id"] = action.name
    scene["death_down_action_count"] = 1
    scene["death_down_direction"] = profile.direction
    scene["death_down_stance_variant_id"] = profile.stance_variant_id
    scene["death_down_fall_side"] = profile.fall_side
    scene["death_down_final_pose_persistent"] = profile.final_pose_persistent
    scene["death_down_weapon_release_deferred"] = profile.weapon_release_deferred
    scene["death_down_manual_keypose_review_required"] = True
    scene["death_down_full_cycle_not_yet_approved"] = True
    scene["death_down_runtime_connected"] = False
    scene["death_down_root_translation_used"] = False
    scene["death_down_mirroring_used"] = False
    scene["death_down_negative_scale_used"] = False
    scene["death_down_geometry_changed"] = False
    scene["death_down_material_changed"] = False
