from __future__ import annotations

import blender_sprite_factory as factory
import walk_animation_builder as previous_builder
from walk_down_profile_v02 import WalkDownProfileV02, load_walk_down_profile_v02


_APPROVED_GEOMETRY_STATE = ("v22", "v25")
_APPROVED_APPEARANCE_REVISION = "v03"


def _assert_approved_appearance(context: factory.BuildContext) -> None:
    geometry_state = (context.head.revision, context.proxy_revision)
    if geometry_state != _APPROVED_GEOMETRY_STATE:
        raise RuntimeError(
            "walk_down v03 requires approved head v22 / proxy v25: "
            f"actual={geometry_state}"
        )

    for name in ("scarf_wrap", "scarf_front"):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"walk_down v03 cannot find approved appearance object: {name}")
        if obj.get("appearance_correction_revision") != _APPROVED_APPEARANCE_REVISION:
            raise RuntimeError(f"walk_down v03 requires appearance v03 on object: {name}")
        if not bool(obj.get("scarf_full_base_assignment")):
            raise RuntimeError(f"walk_down v03 requires the approved red scarf assignment: {name}")

    hair_names = {
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    }
    if len(hair_names) != 12:
        raise RuntimeError(
            f"walk_down v03 requires the approved twelve-object hair state: {sorted(hair_names)}"
        )


def _stamp_action_contract(
    context: factory.BuildContext,
    profile: WalkDownProfileV02,
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
    scene["walk_down_support_foot_contact_refined"] = True
    scene["walk_down_loop_wrap_refined"] = True


def create_walk_down_actions_v03(context: factory.BuildContext) -> None:
    previous_builder._assert_rig_contract(context)
    _assert_approved_appearance(context)
    profile = load_walk_down_profile_v02(context.config.character_id)

    configured_frames = tuple(
        int(value) for value in context.config.animations["walk_down"]["frames"]
    )
    if configured_frames != (1, 2, 3, 4, 5, 6):
        raise RuntimeError("walk_down v03 requires the configured six-frame sequence")
    if int(context.config.animations["walk_down"]["fps"]) != profile.fps:
        raise RuntimeError("walk_down v03 FPS must match the structured profile")

    idle_action = previous_builder._create_idle_action(context)
    walk_action = previous_builder._create_walk_action(context, profile)
    _stamp_action_contract(context, profile, idle_action, walk_action)
    factory._assign_action(context.rig, idle_action)
