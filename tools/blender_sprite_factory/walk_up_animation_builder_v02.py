from __future__ import annotations

import blender_sprite_factory as factory
import walk_right_animation_builder_v01 as approved_right_builder
import walk_up_animation_builder_v01 as previous_builder
from walk_up_profile_v02 import load_walk_up_profile_v02


def create_walk_up_actions_v02(context: factory.BuildContext) -> None:
    approved_right_builder.create_walk_right_actions_v01(context)
    previous_builder._assert_rig_contract(context)
    profile = load_walk_up_profile_v02(context.config.character_id)
    action = previous_builder._create_walk_up_action(context, profile)
    action["rear_passing_silhouette_correction"] = True
    action["corrected_phase"] = "physical_right_passing"
    action["previous_animation_revision"] = "v01"

    scene = factory.bpy.context.scene
    scene["walk_down_artist_approved"] = True
    scene["walk_down_approved_revision"] = "v04"
    scene["walk_left_artist_approved"] = True
    scene["walk_left_approved_revision"] = "v01"
    scene["walk_right_artist_approved"] = True
    scene["walk_right_approved_revision"] = "v01"
    scene["walk_up_profile_revision"] = profile.revision
    scene["walk_up_animation_revision"] = profile.animation_revision
    scene["walk_up_direction"] = profile.direction
    scene["walk_up_phase_count"] = len(profile.poses)
    scene["walk_up_rear_view"] = True
    scene["walk_up_corrected_phase"] = "physical_right_passing"
    scene["walk_up_geometry_changed"] = False
    scene["walk_up_material_changed"] = False
    scene["walk_up_mirroring_used"] = False

    if action.name != f"{context.config.character_id}_walk_up":
        raise RuntimeError("walk_up v02 action name drifted")
    if action.get("animation_revision") != "v02":
        raise RuntimeError("walk_up v02 action revision drifted")
