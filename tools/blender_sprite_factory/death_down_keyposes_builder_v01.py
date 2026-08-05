from __future__ import annotations

import blender_sprite_factory as factory
from combat_idle_directional_cycles_builder_v14 import (
    create_combat_idle_directional_cycles_v14,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    load_weapon_stance_profile_v09,
)
from death_down_keyposes_profile_v01 import (
    load_death_down_keyposes_profiles_v01,
)
from hit_down_keyposes_builder_v01 import (
    _assert_rig_contract,
    _hit_channels,
)


_GORE_ORIGINAL_FOREARM = "arm_forearm_L"
_GORE_ORIGINAL_HAND = "arm_hand_L"
_GORE_DETACHED_FOREARM = "death03_detached_forearm_L"
_GORE_DETACHED_HAND = "death03_detached_hand_L"
_GORE_STUMP_CAP = "death03_left_elbow_stump"
_GORE_DETACHED_CAP = "death03_detached_elbow_cap"


def _set_hidden(obj: factory.bpy.types.Object, hidden: bool) -> None:
    obj.hide_render = hidden
    obj.hide_viewport = hidden


def _duplicate_detached_object(
    context: factory.BuildContext,
    source_name: str,
    duplicate_name: str,
) -> factory.bpy.types.Object:
    source = factory.bpy.data.objects.get(source_name)
    if source is None:
        raise RuntimeError(f"death_03 gore source object is missing: {source_name}")
    duplicate = source.copy()
    duplicate.name = duplicate_name
    context.module_collections["arms"].objects.link(duplicate)
    world_matrix = source.matrix_world.copy()
    duplicate.parent = None
    duplicate.parent_type = "OBJECT"
    duplicate.matrix_world = world_matrix
    duplicate["death_gore_module"] = True
    duplicate["detached_part_id"] = "left_forearm_and_hand"
    _set_hidden(duplicate, True)
    return duplicate


def _create_gore_modules_v01(context: factory.BuildContext) -> None:
    required_names = (
        _GORE_DETACHED_FOREARM,
        _GORE_DETACHED_HAND,
        _GORE_STUMP_CAP,
        _GORE_DETACHED_CAP,
    )
    if any(factory.bpy.data.objects.get(name) is not None for name in required_names):
        raise RuntimeError("death_03 gore modules already exist")

    _duplicate_detached_object(
        context,
        _GORE_ORIGINAL_FOREARM,
        _GORE_DETACHED_FOREARM,
    )
    _duplicate_detached_object(
        context,
        _GORE_ORIGINAL_HAND,
        _GORE_DETACHED_HAND,
    )

    _, elbow, _, _, _ = context.silhouette.arm_points("L")
    stump = factory._ellipsoid(
        _GORE_STUMP_CAP,
        elbow,
        (0.115, 0.095, 0.115),
        context.materials["scarf"],
        segments=8,
        rings=5,
    )
    factory._register(context, stump, "arms", "upper_arm.L", "left")
    stump["death_gore_module"] = True
    stump["gore_role"] = "body_stump"
    _set_hidden(stump, True)

    detached_cap = factory._ellipsoid(
        _GORE_DETACHED_CAP,
        elbow,
        (0.105, 0.085, 0.105),
        context.materials["scarf"],
        segments=8,
        rings=5,
    )
    factory._register(context, detached_cap, "arms", "forearm.L", "left")
    world_matrix = detached_cap.matrix_world.copy()
    detached_cap.parent = None
    detached_cap.parent_type = "OBJECT"
    detached_cap.matrix_world = world_matrix
    detached_cap["death_gore_module"] = True
    detached_cap["gore_role"] = "detached_cut_cap"
    _set_hidden(detached_cap, True)


def create_death_down_keypose_actions_v01(context: factory.BuildContext) -> None:
    create_combat_idle_directional_cycles_v14(context)
    _assert_rig_contract(context)
    _create_gore_modules_v01(context)

    profiles = load_death_down_keyposes_profiles_v01(context.config.character_id)
    stance_profile = load_weapon_stance_profile_v09(context.config.character_id)
    stance_by_id = {item.variant_id: item for item in stance_profile.variants}
    actions: list[factory.Action] = []

    for profile in profiles:
        stance = stance_by_id.get(profile.source_stance_variant_id)
        if stance is None:
            raise RuntimeError(
                "death down v01 source stance is missing: "
                f"{profile.source_stance_variant_id}"
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
        action["animation_revision"] = "base_keyposes_v01"
        action["animation_family"] = "death"
        action["death_variant_id"] = profile.death_variant_id
        action["direction"] = profile.direction
        action["grip_mode"] = "base"
        action["source_stance_variant_id"] = profile.source_stance_variant_id
        action["source_stance_revision"] = profile.source_stance_revision
        action["weapon_visible"] = profile.weapon_visible
        action["weapon_agnostic"] = True
        action["fall_side"] = profile.fall_side
        action["frame_count"] = len(profile.poses)
        action["phase_order"] = ",".join(profile.phase_order)
        action["final_pose_persistent"] = profile.final_pose_persistent
        action["gore_mode"] = profile.gore_mode
        action["detached_part_id"] = profile.detached_part_id or ""
        action["detachment_frame"] = profile.detachment_frame or 0
        action["manual_keypose_review_required"] = True
        action["full_death_cycle_not_yet_approved"] = True
        action["directional_variants_not_started"] = True
        action["random_runtime_selection_not_started"] = True
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
        actions.append(action)

    scene = factory.bpy.context.scene
    scene["death_down_action_ids"] = ",".join(action.name for action in actions)
    scene["death_down_action_count"] = len(actions)
    scene["death_down_variant_ids"] = ",".join(
        profile.death_variant_id for profile in profiles
    )
    scene["death_down_direction"] = "down"
    scene["death_down_weapon_agnostic"] = True
    scene["death_down_weapon_visible"] = False
    scene["death_down_gore_variant_count"] = sum(
        profile.gore_mode != "none" for profile in profiles
    )
    scene["death_down_detachment_variant_count"] = sum(
        profile.detached_part_id is not None for profile in profiles
    )
    scene["death_down_final_pose_persistent"] = True
    scene["death_down_manual_keypose_review_required"] = True
    scene["death_down_full_cycle_not_yet_approved"] = True
    scene["death_down_random_runtime_selection_not_started"] = True
    scene["death_down_runtime_connected"] = False
    scene["death_down_root_translation_used"] = False
    scene["death_down_mirroring_used"] = False
    scene["death_down_negative_scale_used"] = False
    scene["death_down_geometry_changed"] = False
    scene["death_down_material_changed"] = False
