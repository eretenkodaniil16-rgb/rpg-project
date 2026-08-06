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


_GORE_UPPER_CUT_CAP = "death03_upper_waist_cut_cap"
_GORE_LOWER_CUT_CAP = "death03_lower_waist_cut_cap"
_GORE_UPPER_BODY_BONES = frozenset(
    {
        "spine",
        "chest",
        "neck",
        "head",
        "upper_arm.L",
        "upper_arm.R",
        "forearm.L",
        "forearm.R",
        "hand.L",
        "hand.R",
    }
)


def _set_hidden(obj: factory.bpy.types.Object, hidden: bool) -> None:
    obj.hide_render = hidden
    obj.hide_viewport = hidden


def _create_gore_modules_v01(context: factory.BuildContext) -> None:
    required_names = (_GORE_UPPER_CUT_CAP, _GORE_LOWER_CUT_CAP)
    if any(factory.bpy.data.objects.get(name) is not None for name in required_names):
        raise RuntimeError("death_03 waist gore modules already exist")

    upper_cap = factory._ellipsoid(
        _GORE_UPPER_CUT_CAP,
        (0.0, -0.01, 2.38),
        (0.20, 0.15, 0.070),
        context.materials["scarf"],
        segments=10,
        rings=5,
    )
    factory._register(context, upper_cap, "torso_armor", "spine")
    upper_cap["death_gore_module"] = True
    upper_cap["gore_role"] = "upper_torso_cut_surface"
    upper_cap["detached_part_id"] = "upper_torso_and_lower_body"
    _set_hidden(upper_cap, True)

    lower_cap = factory._ellipsoid(
        _GORE_LOWER_CUT_CAP,
        (0.0, -0.01, 2.31),
        (0.22, 0.16, 0.075),
        context.materials["scarf"],
        segments=10,
        rings=5,
    )
    factory._register(context, lower_cap, "torso_armor", "pelvis")
    lower_cap["death_gore_module"] = True
    lower_cap["gore_role"] = "lower_body_cut_surface"
    lower_cap["detached_part_id"] = "upper_torso_and_lower_body"
    _set_hidden(lower_cap, True)



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
