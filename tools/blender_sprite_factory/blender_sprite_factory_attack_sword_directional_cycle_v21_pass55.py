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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass54 as pass54_adapter
from attack_sword_directional_cycle_correction_v21_pass55 import (
    BOUNDARY_FIX_FRAME,
    CAMERA_SHIFT_X_OVERRIDES_BY_FRAME,
    CORRECTION_PASS,
    EXPECTED_SOURCE_PROJECTION_OVERRIDES_BY_FRAME,
    FRONT_DEPTH_FRAMES,
    PRESERVE_ACTION_DATA,
    PRESERVE_SCREEN_SPACE_TRAJECTORY,
    PROJECTED_WEAPON_PROFILE_OVERRIDES_BY_FRAME,
    REQUIRE_FRONT_DEPTH_BRANCH,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_COMMIT,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_GRIP_ID,
    TWOHAND_UP_FRONT_DEPTH_REVISION,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass55.py"
)
PASS55_SCENE_KEY = "attack_sword_directional_cycle_v21_pass55"
ORIGINAL_PASS54_WRITE_MANIFEST = pass54_adapter._write_manifest_v21_pass54
ORIGINAL_PROJECTED_PROFILE = dict(pass54_adapter.PROJECTED_WEAPON_PROFILE_BY_FRAME)
ORIGINAL_EXPECTED_SOURCE = dict(pass54_adapter.EXPECTED_SOURCE_PROJECTION_BY_FRAME)
ORIGINAL_ANGLE_ONLY = dict(pass54_adapter.ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME)
ORIGINAL_CAMERA_SHIFT_X = dict(pass54_adapter.CAMERA_SHIFT_X_BY_FRAME)


def _target_metric_key(frame_number: int) -> str:
    return f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{frame_number:02d}"


def _write_manifest_v21_pass55(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_PASS54_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = json.loads(
        str(
            factory.bpy.context.scene.get(
                pass54_adapter.METRICS_SCENE_KEY,
                "{}",
            )
        )
    )

    selected_metrics: dict[str, object] = {}
    for frame_number in (*FRONT_DEPTH_FRAMES, BOUNDARY_FIX_FRAME):
        key = _target_metric_key(frame_number)
        if key not in metrics:
            raise RuntimeError(
                "attack sword directional v21 pass55 metrics missing: "
                f"{key}"
            )
        metric = metrics[key]
        edge_counts = {
            str(edge): int(count)
            for edge, count in dict(metric["edge_counts"]).items()
        }
        if REQUIRE_ZERO_EDGE_ALPHA and any(edge_counts.values()):
            raise RuntimeError(
                "attack sword directional v21 pass55 frame touched canvas edge: "
                f"{key}={edge_counts}"
            )
        if (
            frame_number in FRONT_DEPTH_FRAMES
            and REQUIRE_FRONT_DEPTH_BRANCH
            and str(metric["depth_branch"]) != "flipped"
        ):
            raise RuntimeError(
                "attack sword directional v21 pass55 front-depth branch drifted: "
                f"{key}={metric['depth_branch']}"
            )
        selected_metrics[f"f{frame_number:02d}"] = metric

    payload[PASS55_SCENE_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": TWOHAND_UP_FRONT_DEPTH_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "target_action_id": TARGET_ACTION_ID,
        "target_grip_id": TARGET_GRIP_ID,
        "target_direction": TARGET_DIRECTION,
        "front_depth_frames": list(FRONT_DEPTH_FRAMES),
        "boundary_fix_frame": BOUNDARY_FIX_FRAME,
        "projected_weapon_profile_overrides_by_frame": {
            str(frame): profile
            for frame, profile in (
                PROJECTED_WEAPON_PROFILE_OVERRIDES_BY_FRAME.items()
            )
        },
        "expected_source_projection_overrides_by_frame": {
            str(frame): value
            for frame, value in (
                EXPECTED_SOURCE_PROJECTION_OVERRIDES_BY_FRAME.items()
            )
        },
        "camera_shift_x_overrides_by_frame": {
            str(frame): value
            for frame, value in CAMERA_SHIFT_X_OVERRIDES_BY_FRAME.items()
        },
        "selected_metrics": selected_metrics,
        "require_front_depth_branch": REQUIRE_FRONT_DEPTH_BRANCH,
        "require_zero_edge_alpha": REQUIRE_ZERO_EDGE_ALPHA,
        "screen_space_trajectory_preserved": PRESERVE_SCREEN_SPACE_TRAJECTORY,
        "action_data_preserved_from_pass54": PRESERVE_ACTION_DATA,
        "camera_shift_persistent_change": False,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failed_commit": SOURCE_FAILED_COMMIT,
        "source_failure": SOURCE_FAILURE,
        "approved_down_v20_changed": False,
        "left_direction_changed": False,
        "right_direction_changed": False,
        "onehand_up_changed": False,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "weapon_scale_changed": False,
        "materials_changed": False,
        "manual_directional_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": (
                "directional_full_cycle_v21_pass55_front_depth"
            ),
            "attack_sword_01_twohand_up_front_depth_revision": (
                TWOHAND_UP_FRONT_DEPTH_REVISION
            ),
            "attack_sword_01_twohand_up_f04_f05_front_depth": True,
            "attack_sword_01_twohand_up_f08_boundary_fixed": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_pass55_contract() -> None:
    for frame_number in FRONT_DEPTH_FRAMES:
        pass54_adapter.ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME.pop(
            frame_number,
            None,
        )
    pass54_adapter.PROJECTED_WEAPON_PROFILE_BY_FRAME.update(
        PROJECTED_WEAPON_PROFILE_OVERRIDES_BY_FRAME
    )
    pass54_adapter.EXPECTED_SOURCE_PROJECTION_BY_FRAME.update(
        EXPECTED_SOURCE_PROJECTION_OVERRIDES_BY_FRAME
    )
    pass54_adapter.CAMERA_SHIFT_X_BY_FRAME.update(
        CAMERA_SHIFT_X_OVERRIDES_BY_FRAME
    )
    pass54_adapter._write_manifest_v21_pass54 = _write_manifest_v21_pass55


def _restore_pass55_contract() -> None:
    pass54_adapter.PROJECTED_WEAPON_PROFILE_BY_FRAME.clear()
    pass54_adapter.PROJECTED_WEAPON_PROFILE_BY_FRAME.update(
        ORIGINAL_PROJECTED_PROFILE
    )
    pass54_adapter.EXPECTED_SOURCE_PROJECTION_BY_FRAME.clear()
    pass54_adapter.EXPECTED_SOURCE_PROJECTION_BY_FRAME.update(
        ORIGINAL_EXPECTED_SOURCE
    )
    pass54_adapter.ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME.clear()
    pass54_adapter.ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME.update(
        ORIGINAL_ANGLE_ONLY
    )
    pass54_adapter.CAMERA_SHIFT_X_BY_FRAME.clear()
    pass54_adapter.CAMERA_SHIFT_X_BY_FRAME.update(ORIGINAL_CAMERA_SHIFT_X)
    pass54_adapter._write_manifest_v21_pass54 = ORIGINAL_PASS54_WRITE_MANIFEST


def main() -> int:
    _apply_pass55_contract()
    try:
        return pass54_adapter.main()
    finally:
        _restore_pass55_contract()


if __name__ == "__main__":
    raise SystemExit(main())
