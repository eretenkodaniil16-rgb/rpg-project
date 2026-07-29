from __future__ import annotations

import blender_sprite_factory as factory
import walk_animation_builder as base_builder
import walk_animation_builder_v03 as previous_builder
from walk_down_profile_v03 import WalkDownProfileV03, load_walk_down_profile_v03


_APPROVED_APPEARANCE_REVISION = "v03"


def _stamp_action_contract(
    context: factory.BuildContext,
    profile: WalkDownProfileV03,
    idle_action: object,
    walk_action: object,
) -> None:
    idle_action["appearance_revision"] = _APPROVED_APPEARANCE_REVISION
    idle_action["appearance_locked"] = True

    walk_action["profile_revision"] = profile.revision
    walk_action["animation_revision"] = profile.animation_revision
    walk_action["appearance_revision"] = _APPROVED_APPEARANCE_REVISION
    walk_action["appearance_locked"] = True
    walk_action["vertical_amplitude_reduced"] = True
    walk_action["phase_height_balanced"] = True
    walk_action["left_recoil_straightened"] = True
    walk_action["right_contact_compressed"] = True
    walk_action["support_foot_contact_refined"] = True
    walk_action["loop_wrap_refined"] = True
    walk_action["head_motion_restrained"] = True
    walk_action["geometry_changed"] = False
    walk_action["material_changed"] = False

    scene = factory.bpy.context.scene
    scene["walk_down_profile_revision"] = profile.revision
    scene["walk_down_animation_revision"] = profile.animation_revision
    scene["walk_down_phase_count"] = len(profile.poses)
    scene["walk_down_geometry_changed"] = False
    scene["walk_down_material_changed"] = False
    scene["walk_down_appearance_revision"] = _APPROVED_APPEARANCE_REVISION
    scene["walk_down_vertical_amplitude_reduced"] = True
    scene["walk_down_phase_height_balanced"] = True
    scene["walk_down_left_recoil_straightened"] = True
    scene["walk_down_right_contact_compressed"] = True
    scene["walk_down_loop_wrap_refined"] = True


def create_walk_down_actions_v04(context: factory.BuildContext) -> None:
    base_builder._assert_rig_contract(context)
    previous_builder._assert_approved_appearance(context)
    profile = load_walk_down_profile_v03(context.config.character_id)

    configured_frames = tuple(
        int(value) for value in context.config.animations["walk_down"]["frames"]
    )
    if configured_frames != (1, 2, 3, 4, 5, 6):
        raise RuntimeError("walk_down v04 requires the configured six-frame sequence")
    if int(context.config.animations["walk_down"]["fps"]) != profile.fps:
        raise RuntimeError("walk_down v04 FPS must match the structured profile")

    idle_action = base_builder._create_idle_action(context)
    walk_action = base_builder._create_walk_action(context, profile)
    _stamp_action_contract(context, profile, idle_action, walk_action)
    factory._assign_action(context.rig, idle_action)
