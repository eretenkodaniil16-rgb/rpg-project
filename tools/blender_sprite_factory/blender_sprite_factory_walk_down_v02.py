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
import blender_sprite_factory_head_v21 as previous_adapter
from head_profile_v21 import load_head_profile_v21
from walk_animation_builder import create_walk_down_actions_v02
from walk_down_profile_v01 import load_walk_down_profile_v01


BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_v21
WALK_PROFILE_PATH = SCRIPT_DIR / "walk_down_profile_v01.py"
WALK_BUILDER_PATH = SCRIPT_DIR / "walk_animation_builder.py"


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


def _write_run_manifest_walk_down_v02(
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

    profile = load_walk_down_profile_v01(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    walk_action = factory.bpy.data.actions.get(f"{context.config.character_id}_walk_down")
    if walk_action is None:
        raise RuntimeError("walk_down v02 manifest cannot find the generated action")
    if walk_action.get("animation_revision") != profile.animation_revision:
        raise RuntimeError("walk_down v02 action revision drifted before manifest creation")

    walk_artifacts = [item for item in artifacts if item.animation_id == "walk_down"]
    if [item.frame_number for item in walk_artifacts] != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("walk_down v02 manifest requires all six rendered frames")

    payload["walk_down_profile"] = {
        "path": context.config.relative_to_repo(WALK_PROFILE_PATH),
        "sha256": hashlib.sha256(WALK_PROFILE_PATH.read_bytes()).hexdigest(),
        "revision": profile.revision,
        "animation_revision": profile.animation_revision,
        "animation_id": profile.animation_id,
        "fps": profile.fps,
        "loop": profile.loop,
        "poses": [_pose_payload(item) for item in profile.poses],
    }
    payload["walk_animation_builder"] = {
        "path": context.config.relative_to_repo(WALK_BUILDER_PATH),
        "sha256": hashlib.sha256(WALK_BUILDER_PATH.read_bytes()).hexdigest(),
    }
    payload["animation_builder_adapter"] = {
        "path": context.config.relative_to_repo(SCRIPT_PATH),
        "sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
    }
    payload["walk_down_candidate"] = {
        "revision": profile.animation_revision,
        "status": "technical_candidate_requires_manual_motion_review",
        "frame_count": len(walk_artifacts),
        "frame_numbers": [item.frame_number for item in walk_artifacts],
        "phase_order": [item.phase for item in profile.poses],
        "design": {
            "pelvis_weight_transfer": True,
            "pelvis_vertical_phases": True,
            "spine_contact_compression": True,
            "chest_counter_rotation": True,
            "head_stabilization": True,
            "foot_articulation": True,
            "asymmetric_arm_swing": True,
            "delayed_back_cloth": True,
        },
        "locked_contract": {
            "head_revision": context.head.revision,
            "proxy_revision": context.proxy_revision,
            "geometry_changed": False,
            "hair_geometry_changed": False,
            "equipment_sides_changed": False,
            "rig_bone_count_changed": False,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "baseline_y": context.config.technical.baseline_y,
        },
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "walk_down_revision": profile.animation_revision,
            "walk_down_profile_revision": profile.revision,
            "walk_down_fps": profile.fps,
            "walk_down_frames": [item.frame for item in profile.poses],
            "walk_down_loop": profile.loop,
            "idle_unchanged": True,
            "head_v21_proxy_v24_locked": True,
        }
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v21
    factory._build_head_and_hair = previous_adapter._build_head_and_hair_v21
    factory._create_actions = create_walk_down_actions_v02
    factory._write_run_manifest = _write_run_manifest_walk_down_v02
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
