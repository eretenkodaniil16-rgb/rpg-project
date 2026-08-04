from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass51 as pass51_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f02_review_v21_pass34 as pass34_adapter
import blender_sprite_factory_attack_sword_twohand_up_f08_review_v21_pass52 as pass52_adapter
from attack_sword_directional_cycle_correction_v21_pass53 import (
    CORRECTION_PASS,
    F08_ARM_BLEND,
    F08_CONTINUITY_FROM_SELECTED_F07_RMS_DEGREES,
    F08_CONTINUITY_SCORE,
    F08_DEPTH_BRANCH,
    F08_DEVIATION_FROM_GUARD_RMS_DEGREES,
    F08_EDGE_COUNTS,
    F08_MAXIMUM_TRANSITION_RMS_DEGREES,
    F08_REQUESTED_SCREEN_PROJECTION,
    F08_SOURCE_FRAME,
    F08_SOURCE_FRAME_ORDER,
    F08_SOURCE_POSE_CODE,
    F08_SOURCE_POSE_LABEL,
    F08_VALIDATED_CAMERA_MARGIN_PIXELS,
    F08_VALIDATED_HEAD_CLEARANCE_PIXELS,
    F08_VALIDATED_OCCLUDED_BLADE_SAMPLES,
    F08_VALIDATED_SCREEN_PROJECTION,
    F08_VALIDATED_SOURCE_PROJECTION,
    F08_VALIDATED_VISIBLE_BLADE_SAMPLES,
    F08_WEAPON_OFFSET_DEGREES,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_F07_ARM_BLEND,
    SELECTED_F07_SOURCE_FRAME,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_ARTIFACT_SHA256,
    SOURCE_REVIEW_FINDING,
    SOURCE_REVIEW_RUN_ID,
    SOURCE_REVIEW_VARIANT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TWOHAND_UP_F01_TO_F08_SELECTED_CYCLE_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass53.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass53"
SELECTED_F08_SCENE_KEY = "attack_sword_twohand_up_selected_f08_v21_pass53"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass53.png"

ORIGINAL_PASS51_BASE_RENDER = pass51_adapter.ORIGINAL_PASS49_BASE_RENDER
ORIGINAL_PASS51_WRITE_MANIFEST = pass51_adapter._write_manifest_v21_pass51
ORIGINAL_PASS51_CORRECTION_PASS = pass51_adapter.CORRECTION_PASS
ORIGINAL_PASS51_REVISION = pass51_adapter.TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION
ORIGINAL_PASS51_SOURCE_RUN = pass51_adapter.SOURCE_REVIEW_RUN_ID
ORIGINAL_PASS51_SOURCE_ARTIFACT = pass51_adapter.SOURCE_REVIEW_ARTIFACT_ID
ORIGINAL_PASS51_SOURCE_SHA256 = pass51_adapter.SOURCE_REVIEW_ARTIFACT_SHA256
ORIGINAL_PASS51_SOURCE_VARIANT = pass51_adapter.SOURCE_REVIEW_VARIANT
ORIGINAL_PASS51_SOURCE_FINDING = pass51_adapter.SOURCE_REVIEW_FINDING
ORIGINAL_PASS51_SCRIPT_PATH = pass51_adapter.SCRIPT_PATH
ORIGINAL_PASS51_CORRECTION_PATH = pass51_adapter.CORRECTION_PATH
ORIGINAL_PASS51_SCENE_KEY = pass51_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS51_CONTACT_SHEET_NAME = pass51_adapter.CONTACT_SHEET_NAME


def _selected_f08_candidate() -> dict[str, object]:
    return {
        "source_frame": F08_SOURCE_FRAME,
        "source_frame_order": F08_SOURCE_FRAME_ORDER,
        "source_pose_code": F08_SOURCE_POSE_CODE,
        "source_pose_label": F08_SOURCE_POSE_LABEL,
        "arm_blend": F08_ARM_BLEND,
        "depth_branch": F08_DEPTH_BRANCH,
        "offset_degrees": F08_WEAPON_OFFSET_DEGREES,
        "source_projection": F08_VALIDATED_SOURCE_PROJECTION,
        "requested_screen_projection": F08_REQUESTED_SCREEN_PROJECTION,
        "screen_projection": F08_VALIDATED_SCREEN_PROJECTION,
        "head_clearance_pixels": F08_VALIDATED_HEAD_CLEARANCE_PIXELS,
        "visible_blade_samples": F08_VALIDATED_VISIBLE_BLADE_SAMPLES,
        "occluded_blade_samples": F08_VALIDATED_OCCLUDED_BLADE_SAMPLES,
        "camera_margin_pixels": F08_VALIDATED_CAMERA_MARGIN_PIXELS,
        "continuity_from_selected_f07_rms_degrees": (
            F08_CONTINUITY_FROM_SELECTED_F07_RMS_DEGREES
        ),
        "deviation_from_guard_rms_degrees": (
            F08_DEVIATION_FROM_GUARD_RMS_DEGREES
        ),
        "continuity_score": F08_CONTINUITY_SCORE,
        "maximum_transition_rms_degrees": (
            F08_MAXIMUM_TRANSITION_RMS_DEGREES
        ),
    }


def _render_pass51_base_with_selected_f08(
    context: factory.BuildContext,
    *,
    animation_id: str,
    direction: str,
    frame_number: int,
    raw_dir: Path,
    frame_dir: Path,
    output_name: str,
    fixed_scale: float | None,
    fixed_center_x: float | None,
    use_clearance_planner: bool,
) -> tuple[factory.FrameArtifact, factory.FramingCalibration]:
    is_target = (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number == TARGET_FRAME
    )
    if not is_target:
        return ORIGINAL_PASS51_BASE_RENDER(
            context,
            animation_id=animation_id,
            direction=direction,
            frame_number=frame_number,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=output_name,
            fixed_scale=fixed_scale,
            fixed_center_x=fixed_center_x,
            use_clearance_planner=use_clearance_planner,
        )
    if fixed_scale is None or fixed_center_x is None:
        raise RuntimeError("two-hand up pass53 f08 requires fixed framing calibration")

    config = context.config
    action = factory.bpy.data.actions.get(f"{config.character_id}_{TARGET_ACTION_ID}")
    if action is None:
        raise RuntimeError("two-hand up pass53 selected f08 action is missing")

    target_f08_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
    original_f07_rotations = pass29_adapter._capture_arm(context, F08_SOURCE_FRAME)
    original_f06_rotations = pass29_adapter._capture_arm(
        context,
        SELECTED_F07_SOURCE_FRAME,
    )
    selected_f07_rotations = pass34_adapter._candidate_pose(
        original_f07_rotations,
        original_f06_rotations,
        SELECTED_F07_ARM_BLEND,
    )
    calibration = factory.FramingCalibration(
        scale=float(fixed_scale),
        source_center_x=float(fixed_center_x),
    )
    artifact, metadata = pass52_adapter._render_candidate(
        context,
        raw_dir.parent,
        calibration=calibration,
        action=action,
        target_rotations=target_f08_rotations,
        source_rotations=selected_f07_rotations,
        candidate=_selected_f08_candidate(),
        variant_index=SOURCE_REVIEW_VARIANT,
    )
    edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
    touched = {edge: count for edge, count in edge_counts.items() if count > 0}
    if REQUIRE_ZERO_EDGE_ALPHA and touched:
        raise RuntimeError(
            "two-hand up pass53 selected f08 touched canvas edges: "
            f"{touched}"
        )

    desired_path = frame_dir / output_name
    desired_path.parent.mkdir(parents=True, exist_ok=True)
    if desired_path.exists():
        desired_path.unlink()
    if artifact.output_path != desired_path:
        artifact.output_path.replace(desired_path)
    selected_artifact = factory.FrameArtifact(
        animation_id=animation_id,
        direction=direction,
        frame_number=frame_number,
        output_path=desired_path,
        sprite_width=artifact.sprite_width,
        sprite_height=artifact.sprite_height,
        baseline_y=artifact.baseline_y,
    )
    selected_metadata = {
        **metadata,
        "edge_counts": edge_counts,
        "selected_review_variant": SOURCE_REVIEW_VARIANT,
        "pass26_planner_used": False,
        "selected_manual_candidate_used": True,
        "output_name": output_name,
        "camera_shift_used": False,
        "action_data_changed": False,
        "root_translation_used": False,
    }
    factory.bpy.context.scene[SELECTED_F08_SCENE_KEY] = json.dumps(
        selected_metadata,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS53_F08_SELECTED="
        f"source:{F08_SOURCE_POSE_LABEL};blend:{F08_ARM_BLEND:.2f};"
        f"projection:{F08_VALIDATED_SCREEN_PROJECTION:.3f};"
        f"offset:{F08_WEAPON_OFFSET_DEGREES:.1f};"
        f"edges:{edge_counts};variant:{SOURCE_REVIEW_VARIANT}"
    )
    return selected_artifact, calibration


def _write_manifest_v21_pass53(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS51_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cycle = payload.get(DIAGNOSTIC_SCENE_KEY, {})
    if not isinstance(cycle, dict):
        raise RuntimeError("two-hand up pass53 cycle manifest is invalid")
    if SELECTED_F08_SCENE_KEY not in factory.bpy.context.scene:
        raise RuntimeError("two-hand up pass53 selected f08 metadata is missing")
    selected_f08 = json.loads(
        str(factory.bpy.context.scene[SELECTED_F08_SCENE_KEY])
    )
    cycle["correction_pass"] = CORRECTION_PASS
    cycle["revision"] = TWOHAND_UP_F01_TO_F08_SELECTED_CYCLE_REVISION
    cycle["selected_f08"] = selected_f08
    frame_metrics = cycle.get("frame_metrics", {})
    if not isinstance(frame_metrics, dict):
        frame_metrics = {}
    frame_metrics["f08"] = selected_f08
    cycle["frame_metrics"] = frame_metrics
    cycle["frame_order"] = list(FRAME_ORDER)
    cycle["all_eight_frames_selected"] = True
    cycle["all_eight_frames_zero_edge_alpha"] = True
    cycle["action_data_changed"] = False
    payload[DIAGNOSTIC_SCENE_KEY] = cycle
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_TO_F08_SELECTED_CYCLE_REVISION,
            "source_review_run_id": SOURCE_REVIEW_RUN_ID,
            "source_review_artifact_id": SOURCE_REVIEW_ARTIFACT_ID,
            "source_review_artifact_sha256": SOURCE_REVIEW_ARTIFACT_SHA256,
            "source_review_variant": SOURCE_REVIEW_VARIANT,
            "source_review_finding": SOURCE_REVIEW_FINDING,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "selected_f08_changed": True,
            "all_eight_frames_selected": True,
            "all_eight_frames_zero_edge_alpha": True,
            "twohand_up_action_data_changed": False,
            "camera_shift_persistent_change": False,
            "root_translation_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "manual_review_required": True,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass53_contract() -> None:
    pass51_adapter.ORIGINAL_PASS49_BASE_RENDER = (
        _render_pass51_base_with_selected_f08
    )
    pass51_adapter._write_manifest_v21_pass51 = _write_manifest_v21_pass53
    pass51_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass51_adapter.TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION = (
        TWOHAND_UP_F01_TO_F08_SELECTED_CYCLE_REVISION
    )
    pass51_adapter.SOURCE_REVIEW_RUN_ID = SOURCE_REVIEW_RUN_ID
    pass51_adapter.SOURCE_REVIEW_ARTIFACT_ID = SOURCE_REVIEW_ARTIFACT_ID
    pass51_adapter.SOURCE_REVIEW_ARTIFACT_SHA256 = SOURCE_REVIEW_ARTIFACT_SHA256
    pass51_adapter.SOURCE_REVIEW_VARIANT = SOURCE_REVIEW_VARIANT
    pass51_adapter.SOURCE_REVIEW_FINDING = SOURCE_REVIEW_FINDING
    pass51_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass51_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass51_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass51_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME


def _restore_pass51_contract() -> None:
    pass51_adapter.ORIGINAL_PASS49_BASE_RENDER = ORIGINAL_PASS51_BASE_RENDER
    pass51_adapter._write_manifest_v21_pass51 = ORIGINAL_PASS51_WRITE_MANIFEST
    pass51_adapter.CORRECTION_PASS = ORIGINAL_PASS51_CORRECTION_PASS
    pass51_adapter.TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION = (
        ORIGINAL_PASS51_REVISION
    )
    pass51_adapter.SOURCE_REVIEW_RUN_ID = ORIGINAL_PASS51_SOURCE_RUN
    pass51_adapter.SOURCE_REVIEW_ARTIFACT_ID = ORIGINAL_PASS51_SOURCE_ARTIFACT
    pass51_adapter.SOURCE_REVIEW_ARTIFACT_SHA256 = ORIGINAL_PASS51_SOURCE_SHA256
    pass51_adapter.SOURCE_REVIEW_VARIANT = ORIGINAL_PASS51_SOURCE_VARIANT
    pass51_adapter.SOURCE_REVIEW_FINDING = ORIGINAL_PASS51_SOURCE_FINDING
    pass51_adapter.SCRIPT_PATH = ORIGINAL_PASS51_SCRIPT_PATH
    pass51_adapter.CORRECTION_PATH = ORIGINAL_PASS51_CORRECTION_PATH
    pass51_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS51_SCENE_KEY
    pass51_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS51_CONTACT_SHEET_NAME


def main() -> int:
    _apply_pass53_contract()
    try:
        return pass51_adapter.main()
    finally:
        _restore_pass51_contract()


if __name__ == "__main__":
    raise SystemExit(main())
