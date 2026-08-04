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
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass49 as pass49_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f07_review_v21_pass50 as pass50_adapter
from attack_sword_directional_cycle_correction_v21_pass51 import (
    CORRECTION_PASS,
    F07_ARM_BLEND,
    F07_CAMERA_SHIFT_X_CANDIDATES,
    F07_CONTINUITY_FROM_F06_RMS_DEGREES,
    F07_CONTINUITY_SCORE,
    F07_CONTINUITY_TO_F08_RMS_DEGREES,
    F07_DEPTH_BRANCH,
    F07_MAXIMUM_TRANSITION_RMS_DEGREES,
    F07_REQUESTED_SCREEN_PROJECTION,
    F07_SOURCE_FRAME,
    F07_SOURCE_FRAME_LABEL,
    F07_SOURCE_FRAME_ORDER,
    F07_UNSHIFTED_EDGE_COUNTS,
    F07_VALIDATED_CAMERA_MARGIN_PIXELS,
    F07_VALIDATED_HEAD_CLEARANCE_PIXELS,
    F07_VALIDATED_OCCLUDED_BLADE_SAMPLES,
    F07_VALIDATED_SCREEN_PROJECTION,
    F07_VALIDATED_SOURCE_PROJECTION,
    F07_VALIDATED_VISIBLE_BLADE_SAMPLES,
    F07_WEAPON_OFFSET_DEGREES,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_ARTIFACT_SHA256,
    SOURCE_REVIEW_FINDING,
    SOURCE_REVIEW_RUN_ID,
    SOURCE_REVIEW_VARIANT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass51.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass51"
SELECTED_F07_SCENE_KEY = "attack_sword_twohand_up_selected_f07_v21_pass51"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass51.png"
CAMERA_OBJECT_NAME = "CAM_gameplay_ortho"

ORIGINAL_PASS49_BASE_RENDER = pass49_adapter.ORIGINAL_PASS48_BASE_RENDER
ORIGINAL_PASS49_WRITE_MANIFEST = pass49_adapter._write_manifest_v21_pass49
ORIGINAL_PASS49_CORRECTION_PASS = pass49_adapter.CORRECTION_PASS
ORIGINAL_PASS49_REVISION = pass49_adapter.TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION
ORIGINAL_PASS49_SOURCE_RUN = pass49_adapter.SOURCE_FAILED_RUN_ID
ORIGINAL_PASS49_SOURCE_ARTIFACT = pass49_adapter.SOURCE_FAILED_ARTIFACT_ID
ORIGINAL_PASS49_SOURCE_SHA256 = pass49_adapter.SOURCE_FAILED_ARTIFACT_SHA256
ORIGINAL_PASS49_SOURCE_FAILURE = pass49_adapter.SOURCE_FAILURE
ORIGINAL_PASS49_SCRIPT_PATH = pass49_adapter.SCRIPT_PATH
ORIGINAL_PASS49_CORRECTION_PATH = pass49_adapter.CORRECTION_PATH
ORIGINAL_PASS49_SCENE_KEY = pass49_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS49_CONTACT_SHEET_NAME = pass49_adapter.CONTACT_SHEET_NAME


def _selected_f07_candidate() -> dict[str, object]:
    return {
        "source_frame": F07_SOURCE_FRAME,
        "source_frame_order": F07_SOURCE_FRAME_ORDER,
        "source_frame_label": F07_SOURCE_FRAME_LABEL,
        "arm_blend": F07_ARM_BLEND,
        "depth_branch": F07_DEPTH_BRANCH,
        "offset_degrees": F07_WEAPON_OFFSET_DEGREES,
        "source_projection": F07_VALIDATED_SOURCE_PROJECTION,
        "requested_screen_projection": F07_REQUESTED_SCREEN_PROJECTION,
        "screen_projection": F07_VALIDATED_SCREEN_PROJECTION,
        "head_clearance_pixels": F07_VALIDATED_HEAD_CLEARANCE_PIXELS,
        "visible_blade_samples": F07_VALIDATED_VISIBLE_BLADE_SAMPLES,
        "occluded_blade_samples": F07_VALIDATED_OCCLUDED_BLADE_SAMPLES,
        "camera_margin_pixels": F07_VALIDATED_CAMERA_MARGIN_PIXELS,
        "continuity_from_f06_rms_degrees": (
            F07_CONTINUITY_FROM_F06_RMS_DEGREES
        ),
        "continuity_to_f08_rms_degrees": F07_CONTINUITY_TO_F08_RMS_DEGREES,
        "continuity_score": F07_CONTINUITY_SCORE,
        "maximum_transition_rms_degrees": F07_MAXIMUM_TRANSITION_RMS_DEGREES,
    }


def _render_pass49_base_with_selected_f07(
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
        return ORIGINAL_PASS49_BASE_RENDER(
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
        raise RuntimeError("two-hand up pass51 f07 requires fixed framing calibration")

    config = context.config
    action = factory.bpy.data.actions.get(f"{config.character_id}_{TARGET_ACTION_ID}")
    if action is None:
        raise RuntimeError("two-hand up pass51 selected f07 action is missing")
    camera = factory.bpy.data.objects.get(CAMERA_OBJECT_NAME)
    if camera is None or camera.data is None:
        raise RuntimeError("two-hand up pass51 gameplay camera is missing")

    target_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
    source_rotations = pass29_adapter._capture_arm(context, F07_SOURCE_FRAME)
    calibration = factory.FramingCalibration(
        scale=float(fixed_scale),
        source_center_x=float(fixed_center_x),
    )
    original_shift_x = float(camera.data.shift_x)
    diagnostics: list[dict[str, object]] = []
    try:
        for attempt, shift_x in enumerate(F07_CAMERA_SHIFT_X_CANDIDATES, start=1):
            camera.data.shift_x = float(shift_x)
            factory.bpy.context.view_layer.update()
            artifact, metadata = pass50_adapter._render_candidate(
                context,
                raw_dir.parent,
                calibration=calibration,
                action=action,
                target_rotations=target_rotations,
                source_rotations=source_rotations,
                candidate=_selected_f07_candidate(),
                variant_index=attempt,
            )
            edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
            touched = {
                edge: count for edge, count in edge_counts.items() if count > 0
            }
            diagnostic = {
                "attempt": attempt,
                "camera_shift_x": float(shift_x),
                "edge_counts": edge_counts,
                "accepted": not touched,
            }
            diagnostics.append(diagnostic)
            print(
                "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS51_F07_ATTEMPT="
                f"attempt:{attempt};shift_x:{shift_x:.3f};"
                f"edges:{touched};accepted:{str(not touched).lower()}"
            )
            if REQUIRE_ZERO_EDGE_ALPHA and touched:
                continue

            desired_path = frame_dir / output_name
            desired_path.parent.mkdir(parents=True, exist_ok=True)
            if desired_path.exists():
                desired_path.unlink()
            artifact.output_path.replace(desired_path)
            selected_metadata = {
                **metadata,
                "camera_shift_x": float(shift_x),
                "edge_counts": edge_counts,
                "camera_shift_restored_after_render": True,
                "diagnostics": diagnostics,
                "selected_review_variant": SOURCE_REVIEW_VARIANT,
                "pass26_planner_used": False,
                "selected_manual_candidate_used": True,
                "output_name": output_name,
            }
            factory.bpy.context.scene[SELECTED_F07_SCENE_KEY] = json.dumps(
                selected_metadata,
                sort_keys=True,
            )
            selected_artifact = factory.FrameArtifact(
                animation_id=animation_id,
                direction=direction,
                frame_number=frame_number,
                output_path=desired_path,
                sprite_width=artifact.sprite_width,
                sprite_height=artifact.sprite_height,
                baseline_y=artifact.baseline_y,
            )
            print(
                "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS51_F07_SELECTED="
                f"source:{F07_SOURCE_FRAME_LABEL};blend:{F07_ARM_BLEND:.2f};"
                f"projection:{F07_VALIDATED_SCREEN_PROJECTION:.3f};"
                f"offset:{F07_WEAPON_OFFSET_DEGREES:.1f};"
                f"shift_x:{shift_x:.3f};edges:{edge_counts};attempt:{attempt}"
            )
            return selected_artifact, calibration

        raise RuntimeError(
            "two-hand up pass51 found no export-contained selected f07 "
            f"overscan candidate: {diagnostics}"
        )
    finally:
        camera.data.shift_x = original_shift_x
        pass29_adapter._restore_arm(context, target_rotations)
        factory.bpy.context.view_layer.update()


def _write_manifest_v21_pass51(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS49_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up pass51 cycle manifest is invalid")
    if SELECTED_F07_SCENE_KEY not in factory.bpy.context.scene:
        raise RuntimeError("two-hand up pass51 selected f07 metadata is missing")
    selected_f07 = json.loads(
        str(factory.bpy.context.scene[SELECTED_F07_SCENE_KEY])
    )
    cycle["correction_pass"] = CORRECTION_PASS
    cycle["revision"] = TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION
    cycle["selected_f07"] = selected_f07
    frame_metrics = cycle.get("frame_metrics", {})
    if not isinstance(frame_metrics, dict):
        frame_metrics = {}
    frame_metrics["f07"] = selected_f07
    cycle["frame_metrics"] = frame_metrics
    cycle["camera_shift_persistent_change"] = False
    cycle["action_data_changed"] = False
    payload[DIAGNOSTIC_SCENE_KEY] = cycle
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION,
            "source_review_run_id": SOURCE_REVIEW_RUN_ID,
            "source_review_artifact_id": SOURCE_REVIEW_ARTIFACT_ID,
            "source_review_artifact_sha256": SOURCE_REVIEW_ARTIFACT_SHA256,
            "source_review_variant": SOURCE_REVIEW_VARIANT,
            "source_review_finding": SOURCE_REVIEW_FINDING,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "selected_f07_changed": True,
            "unshifted_f07_edge_counts": dict(F07_UNSHIFTED_EDGE_COUNTS),
            "camera_shift_used_for_raw_overscan": True,
            "camera_shift_persistent_change": False,
            "twohand_up_action_data_changed": False,
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


def _apply_pass51_contract() -> None:
    pass49_adapter.ORIGINAL_PASS48_BASE_RENDER = (
        _render_pass49_base_with_selected_f07
    )
    pass49_adapter._write_manifest_v21_pass49 = _write_manifest_v21_pass51
    pass49_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass49_adapter.TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION = (
        TWOHAND_UP_F01_TO_F07_SELECTED_CYCLE_REVISION
    )
    pass49_adapter.SOURCE_FAILED_RUN_ID = SOURCE_REVIEW_RUN_ID
    pass49_adapter.SOURCE_FAILED_ARTIFACT_ID = SOURCE_REVIEW_ARTIFACT_ID
    pass49_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = SOURCE_REVIEW_ARTIFACT_SHA256
    pass49_adapter.SOURCE_FAILURE = SOURCE_REVIEW_FINDING
    pass49_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass49_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass49_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass49_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME


def _restore_pass49_contract() -> None:
    pass49_adapter.ORIGINAL_PASS48_BASE_RENDER = ORIGINAL_PASS49_BASE_RENDER
    pass49_adapter._write_manifest_v21_pass49 = ORIGINAL_PASS49_WRITE_MANIFEST
    pass49_adapter.CORRECTION_PASS = ORIGINAL_PASS49_CORRECTION_PASS
    pass49_adapter.TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION = (
        ORIGINAL_PASS49_REVISION
    )
    pass49_adapter.SOURCE_FAILED_RUN_ID = ORIGINAL_PASS49_SOURCE_RUN
    pass49_adapter.SOURCE_FAILED_ARTIFACT_ID = ORIGINAL_PASS49_SOURCE_ARTIFACT
    pass49_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = ORIGINAL_PASS49_SOURCE_SHA256
    pass49_adapter.SOURCE_FAILURE = ORIGINAL_PASS49_SOURCE_FAILURE
    pass49_adapter.SCRIPT_PATH = ORIGINAL_PASS49_SCRIPT_PATH
    pass49_adapter.CORRECTION_PATH = ORIGINAL_PASS49_CORRECTION_PATH
    pass49_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS49_SCENE_KEY
    pass49_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS49_CONTACT_SHEET_NAME


def main() -> int:
    _apply_pass51_contract()
    try:
        return pass49_adapter.main()
    finally:
        _restore_pass49_contract()


if __name__ == "__main__":
    raise SystemExit(main())
