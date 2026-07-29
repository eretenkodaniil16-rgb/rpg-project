from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_walk_down_v03 as previous_adapter
from walk_animation_builder_v04 import create_walk_down_actions_v04
from walk_down_profile_v03 import WalkDownProfileV03, load_walk_down_profile_v03


BASE_WRITE_RUN_MANIFEST = previous_adapter.BASE_WRITE_RUN_MANIFEST
WALK_PROFILE_PATH = SCRIPT_DIR / "walk_down_profile_v03.py"
WALK_BUILDER_PATH = SCRIPT_DIR / "walk_animation_builder_v04.py"


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


def _pelvis_height_range(profile: WalkDownProfileV03) -> float:
    values = [pose.pelvis_z for pose in profile.poses]
    return max(values) - min(values)


def _maximum_loop_wrap(profile: WalkDownProfileV03) -> float:
    first = profile.poses[0].numeric_channels()
    last = profile.poses[-1].numeric_channels()
    return max(abs(end - start) for start, end in zip(first, last))


def _write_run_manifest_walk_down_v04(
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
    profile = load_walk_down_profile_v03(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    walk_action = factory.bpy.data.actions.get(f"{context.config.character_id}_walk_down")
    if walk_action is None:
        raise RuntimeError("walk_down v04 manifest cannot find the generated action")
    if walk_action.get("animation_revision") != profile.animation_revision:
        raise RuntimeError("walk_down v04 action revision drifted before manifest creation")
    if not bool(walk_action.get("appearance_locked")):
        raise RuntimeError("walk_down v04 must preserve the approved appearance lock")
    if not bool(walk_action.get("phase_height_balanced")):
        raise RuntimeError("walk_down v04 phase balancing stamp is missing")

    walk_artifacts = [item for item in artifacts if item.animation_id == "walk_down"]
    if [item.frame_number for item in walk_artifacts] != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("walk_down v04 manifest requires all six rendered frames")

    payload["walk_down_refinement_v04"] = {
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
            "vertical_amplitude_reduced_again": True,
            "left_recoil_straightened": True,
            "right_contact_compressed_for_perspective": True,
            "passing_spine_pitch_added": True,
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
            "status": "v04_technical_candidate_requires_manual_motion_review",
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
            "walk_down_v03_refined_keys": False,
            "walk_down_v04_balanced_keys": True,
            "approved_appearance_v03_locked": True,
            "idle_unchanged": True,
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["artist_approved"] = True
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_v03_with_walk_down_v04_motion_candidate"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _patch_manifest_chain_for_walk_v04() -> None:
    previous_adapter.walk_manifest_adapter.load_walk_down_profile_v01 = load_walk_down_profile_v03
    previous_adapter.walk_manifest_adapter.WALK_PROFILE_PATH = WALK_PROFILE_PATH
    previous_adapter.walk_manifest_adapter.WALK_BUILDER_PATH = WALK_BUILDER_PATH
    previous_adapter.walk_manifest_adapter.SCRIPT_PATH = SCRIPT_PATH


def main() -> int:
    previous_adapter.create_walk_down_actions_v03 = create_walk_down_actions_v04
    previous_adapter._write_run_manifest_walk_down_v03 = _write_run_manifest_walk_down_v04
    previous_adapter._patch_manifest_chain_for_walk_v03 = _patch_manifest_chain_for_walk_v04
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
