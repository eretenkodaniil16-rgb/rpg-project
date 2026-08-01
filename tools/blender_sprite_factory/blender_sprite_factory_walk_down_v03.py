from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import appearance_builder_v01 as appearance_builder
import blender_sprite_factory as factory
import blender_sprite_factory_appearance_v01 as appearance_adapter_v01
import blender_sprite_factory_appearance_v03 as appearance_adapter_v03
import blender_sprite_factory_walk_down_v02 as walk_manifest_adapter
from appearance_readability_correction_v03 import (
    load_appearance_readability_corrected_v03,
)
from head_profile_v22 import load_head_profile_v22
from walk_animation_builder_v03 import create_walk_down_actions_v03
from walk_down_profile_v02 import WalkDownProfileV02, load_walk_down_profile_v02


BASE_WRITE_RUN_MANIFEST = appearance_adapter_v03._write_run_manifest_appearance_v03
WALK_PROFILE_PATH = SCRIPT_DIR / "walk_down_profile_v02.py"
WALK_BUILDER_PATH = SCRIPT_DIR / "walk_animation_builder_v03.py"


def _pose_payload(pose: object) -> dict[str, object]:
    return {
        "frame": pose.frame,
        "phase": pose.phase,
        "pelvis": {
            "x": pose.pelvis_x,
            "z": pose.pelvis_z,
            "roll_z_degrees": pose.pelvis_roll_z_degrees,
        },
        "spine_pitch_x_degrees": pose.spine_pitch_x_degrees,
        "chest_yaw_z_degrees": pose.chest_yaw_z_degrees,
        "head_yaw_z_degrees": pose.head_yaw_z_degrees,
        "legs": {
            "thigh_left_x_degrees": pose.thigh_left_x_degrees,
            "thigh_right_x_degrees": pose.thigh_right_x_degrees,
            "shin_left_x_degrees": pose.shin_left_x_degrees,
            "shin_right_x_degrees": pose.shin_right_x_degrees,
            "foot_left_x_degrees": pose.foot_left_x_degrees,
            "foot_right_x_degrees": pose.foot_right_x_degrees,
        },
        "arms": {
            "upper_arm_left_x_degrees": pose.upper_arm_left_x_degrees,
            "upper_arm_right_x_degrees": pose.upper_arm_right_x_degrees,
        },
        "cloth": {
            "left_x_degrees": pose.cloth_left_x_degrees,
            "center_x_degrees": pose.cloth_center_x_degrees,
            "right_x_degrees": pose.cloth_right_x_degrees,
        },
    }


def _pelvis_height_range(profile: WalkDownProfileV02) -> float:
    values = [pose.pelvis_z for pose in profile.poses]
    return max(values) - min(values)


def _maximum_loop_wrap(profile: WalkDownProfileV02) -> float:
    first = profile.poses[0].numeric_channels()
    last = profile.poses[-1].numeric_channels()
    return max(abs(end - start) for start, end in zip(first, last))


def _write_run_manifest_walk_down_v03(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_RUN_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    profile = load_walk_down_profile_v02(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    walk_action = factory.bpy.data.actions.get(f"{context.config.character_id}_walk_down")
    if walk_action is None:
        raise RuntimeError("walk_down v03 manifest cannot find the generated action")
    if walk_action.get("animation_revision") != profile.animation_revision:
        raise RuntimeError("walk_down v03 action revision drifted before manifest creation")
    if not bool(walk_action.get("appearance_locked")):
        raise RuntimeError("walk_down v03 must preserve the approved appearance lock")

    walk_artifacts = [item for item in artifacts if item.animation_id == "walk_down"]
    if [item.frame_number for item in walk_artifacts] != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("walk_down v03 manifest requires all six rendered frames")

    payload["walk_down_refinement_v03"] = {
        "profile_path": context.config.relative_to_repo(WALK_PROFILE_PATH),
        "profile_sha256": hashlib.sha256(WALK_PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(WALK_BUILDER_PATH),
        "builder_sha256": hashlib.sha256(WALK_BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "profile_revision": profile.revision,
        "animation_revision": profile.animation_revision,
        "fps": profile.fps,
        "loop": profile.loop,
        "poses": [_pose_payload(item) for item in profile.poses],
        "pelvis_height_range": _pelvis_height_range(profile),
        "maximum_loop_wrap": _maximum_loop_wrap(profile),
        "changes": {
            "vertical_amplitude_reduced": True,
            "extreme_leg_arcs_reduced": True,
            "support_foot_contact_refined": True,
            "head_motion_restrained": True,
            "pauldron_asymmetric_arm_swing_preserved": True,
            "back_cloth_swing_restrained": True,
        },
        "locked_appearance": {
            "head_revision": context.head.revision,
            "proxy_revision": context.proxy_revision,
            "appearance_revision": "v03",
            "geometry_changed": False,
            "materials_changed": False,
            "hair_changed": False,
            "scarf_changed": False,
            "equipment_sides_changed": False,
            "mirroring_used": False,
            "negative_scale_used": False,
        },
        "status": "technical_candidate_requires_manual_motion_review",
    }

    payload.setdefault("walk_down_candidate", {})
    payload["walk_down_candidate"].update(
        {
            "revision": profile.animation_revision,
            "profile_revision": profile.revision,
            "status": "v03_technical_candidate_requires_manual_motion_review",
            "frame_count": len(walk_artifacts),
            "frame_numbers": [item.frame_number for item in walk_artifacts],
            "phase_order": [item.phase for item in profile.poses],
        }
    )
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "walk_down_revision": profile.animation_revision,
            "walk_down_profile_revision": profile.revision,
            "walk_down_fps": profile.fps,
            "walk_down_frames": [item.frame for item in profile.poses],
            "walk_down_loop": profile.loop,
            "walk_down_v02_reused_without_key_change": False,
            "walk_down_v03_refined_keys": True,
            "approved_appearance_v03_locked": True,
            "idle_unchanged": True,
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["artist_approved"] = True
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_v03_with_walk_down_v03_motion_candidate"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _patch_manifest_chain_for_walk_v03() -> None:
    walk_manifest_adapter.load_walk_down_profile_v01 = load_walk_down_profile_v02
    walk_manifest_adapter.WALK_PROFILE_PATH = WALK_PROFILE_PATH
    walk_manifest_adapter.WALK_BUILDER_PATH = WALK_BUILDER_PATH
    walk_manifest_adapter.SCRIPT_PATH = SCRIPT_PATH


def main() -> int:
    corrected_profile = load_appearance_readability_corrected_v03("human_warrior_m01")
    _patch_manifest_chain_for_walk_v03()

    appearance_builder._PROFILE = corrected_profile
    appearance_builder._rgb = factory._hex_to_linear_rgb
    appearance_builder.load_appearance_readability_profile_v01 = (
        lambda character_id: load_appearance_readability_corrected_v03(character_id)
    )
    appearance_adapter_v01.load_appearance_readability_profile_v01 = (
        lambda character_id: load_appearance_readability_corrected_v03(character_id)
    )

    factory.load_factory_config = appearance_builder.load_factory_config_appearance_v01
    factory.load_head_profile = load_head_profile_v22
    factory._create_material = appearance_builder.create_material_appearance_v01
    factory._build_head_and_hair = appearance_builder.build_head_and_hair_appearance_v01
    factory._build_armor = appearance_adapter_v03._build_armor_appearance_v03
    factory._build_arms = appearance_builder.build_arms_appearance_v01
    factory._build_legs = appearance_builder.build_legs_appearance_v01
    factory._build_accessories = appearance_builder.build_accessories_appearance_v01
    factory._create_actions = create_walk_down_actions_v03
    factory._write_run_manifest = _write_run_manifest_walk_down_v03
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
