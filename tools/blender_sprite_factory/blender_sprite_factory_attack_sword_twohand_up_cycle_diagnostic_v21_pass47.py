from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass26 as pass26_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass46 as pass46_adapter
from attack_sword_directional_cycle_correction_v21_pass47 import (
    CORRECTION_PASS,
    F04_CAMERA_SHIFT_X_CANDIDATES,
    F04_FIXED_CENTER_COMPENSATION_USED,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass47.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass47"
SELECTED_F04_SCENE_KEY = "attack_sword_twohand_up_selected_f04_v21_pass47"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass47.png"
CAMERA_OBJECT_NAME = "CAM_gameplay_ortho"

ORIGINAL_PASS46_RENDER_FRAME = pass46_adapter._render_frame_v21_pass46
ORIGINAL_PASS46_CORRECTION_PASS = pass46_adapter.CORRECTION_PASS
ORIGINAL_PASS46_REVISION = (
    pass46_adapter.TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION
)
ORIGINAL_PASS46_SCRIPT_PATH = pass46_adapter.SCRIPT_PATH
ORIGINAL_PASS46_CORRECTION_PATH = pass46_adapter.CORRECTION_PATH
ORIGINAL_PASS46_SCENE_KEY = pass46_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS46_CONTACT_SHEET_NAME = pass46_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS46_WRITE_MANIFEST = pass46_adapter._write_manifest_v21_pass46


def _render_frame_v21_pass47(
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
    if (
        animation_id != TARGET_ACTION_ID
        or direction != TARGET_DIRECTION
        or frame_number != TARGET_FRAME
    ):
        return ORIGINAL_PASS46_RENDER_FRAME(
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
        raise RuntimeError("two-hand up pass47 f04 requires fixed framing calibration")

    camera = factory.bpy.data.objects.get(CAMERA_OBJECT_NAME)
    if camera is None or camera.data is None:
        raise RuntimeError("two-hand up pass47 gameplay camera is missing")

    original_shift_x = float(camera.data.shift_x)
    diagnostics: list[dict[str, object]] = []
    try:
        for attempt, shift_x in enumerate(F04_CAMERA_SHIFT_X_CANDIDATES, start=1):
            camera.data.shift_x = float(shift_x)
            factory.bpy.context.view_layer.update()
            try:
                artifact, calibration = ORIGINAL_PASS46_RENDER_FRAME(
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
            except RuntimeError as exc:
                diagnostics.append(
                    {
                        "attempt": attempt,
                        "camera_shift_x": float(shift_x),
                        "accepted": False,
                        "error": str(exc),
                    }
                )
                print(
                    "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS47_F04_ATTEMPT="
                    f"attempt:{attempt};shift_x:{shift_x:.3f};accepted:false;"
                    f"error:{exc}"
                )
                continue

            edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
            touched = {
                edge: count for edge, count in edge_counts.items() if count > 0
            }
            accepted = not touched
            diagnostics.append(
                {
                    "attempt": attempt,
                    "camera_shift_x": float(shift_x),
                    "edge_counts": edge_counts,
                    "accepted": accepted,
                }
            )
            print(
                "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS47_F04_ATTEMPT="
                f"attempt:{attempt};shift_x:{shift_x:.3f};"
                f"edges:{touched};accepted:{str(accepted).lower()}"
            )
            if REQUIRE_ZERO_EDGE_ALPHA and not accepted:
                continue

            metadata = {
                "camera_shift_x": float(shift_x),
                "edge_counts": edge_counts,
                "attempt": attempt,
                "diagnostics": diagnostics,
                "camera_shift_restored_after_render": True,
                "fixed_center_compensation_used": (
                    F04_FIXED_CENTER_COMPENSATION_USED
                ),
                "pass26_planner_used": True,
                "action_data_changed": False,
                "root_translation_used": False,
            }
            factory.bpy.context.scene[SELECTED_F04_SCENE_KEY] = json.dumps(
                metadata,
                sort_keys=True,
            )
            print(
                "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS47_F04_SELECTED="
                f"shift_x:{shift_x:.3f};edges:{edge_counts};attempt:{attempt}"
            )
            return artifact, calibration

        raise RuntimeError(
            "two-hand up pass47 found no export-contained f04 horizontal "
            f"overscan candidate: {diagnostics}"
        )
    finally:
        camera.data.shift_x = original_shift_x
        factory.bpy.context.view_layer.update()


def _write_manifest_v21_pass47(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS46_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up pass47 cycle manifest is invalid")
    if SELECTED_F04_SCENE_KEY not in factory.bpy.context.scene:
        raise RuntimeError("two-hand up pass47 selected f04 metadata is missing")
    selected_f04 = json.loads(
        str(factory.bpy.context.scene[SELECTED_F04_SCENE_KEY])
    )
    cycle["correction_pass"] = CORRECTION_PASS
    cycle["revision"] = TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION
    cycle["selected_f04"] = selected_f04
    frame_metrics = cycle.get("frame_metrics", {})
    if not isinstance(frame_metrics, dict):
        frame_metrics = {}
    frame_metrics["f04"] = selected_f04
    cycle["frame_metrics"] = frame_metrics
    cycle["camera_shift_persistent_change"] = False
    payload[DIAGNOSTIC_SCENE_KEY] = cycle
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION,
            "source_failed_run_id": SOURCE_FAILED_RUN_ID,
            "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
            "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
            "source_failure": SOURCE_FAILURE,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "selected_f04_changed": True,
            "camera_shift_used_for_raw_overscan": True,
            "camera_shift_persistent_change": False,
            "fixed_center_compensation_used": F04_FIXED_CENTER_COMPENSATION_USED,
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


def _apply_pass47_contract() -> None:
    pass46_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass46_adapter.TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION = (
        TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION
    )
    pass46_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass46_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass46_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass46_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass46_adapter._write_manifest_v21_pass46 = _write_manifest_v21_pass47
    pass46_adapter._apply_pass46_contract()
    pass26_adapter._render_frame_v21_pass26 = _render_frame_v21_pass47


def _restore_pass46_contract() -> None:
    pass46_adapter._restore_pass37_contract()
    pass46_adapter.CORRECTION_PASS = ORIGINAL_PASS46_CORRECTION_PASS
    pass46_adapter.TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION = (
        ORIGINAL_PASS46_REVISION
    )
    pass46_adapter.SCRIPT_PATH = ORIGINAL_PASS46_SCRIPT_PATH
    pass46_adapter.CORRECTION_PATH = ORIGINAL_PASS46_CORRECTION_PATH
    pass46_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS46_SCENE_KEY
    pass46_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS46_CONTACT_SHEET_NAME
    pass46_adapter._write_manifest_v21_pass46 = ORIGINAL_PASS46_WRITE_MANIFEST


def main() -> int:
    _apply_pass47_contract()
    try:
        return pass46_adapter.pass37_adapter.main()
    finally:
        _restore_pass46_contract()


if __name__ == "__main__":
    raise SystemExit(main())
