from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass47 as pass47_adapter
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass48 as pass48_adapter
from attack_sword_directional_cycle_correction_v21_pass49 import (
    CORRECTION_PASS,
    F06_CAMERA_SHIFT_X_CANDIDATES,
    F06_FIXED_WEAPON_OFFSET_DEGREES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass49.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass49"
SELECTED_F06_SCENE_KEY = "attack_sword_twohand_up_selected_f06_v21_pass49"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass49.png"
CAMERA_OBJECT_NAME = "CAM_gameplay_ortho"

ORIGINAL_PASS02_CANDIDATE_OFFSETS = pass02_adapter._candidate_offsets
ORIGINAL_PASS48_BASE_RENDER = pass48_adapter.ORIGINAL_PASS47_BASE_RENDER
ORIGINAL_PASS47_WRITE_MANIFEST = pass47_adapter._write_manifest_v21_pass47

ORIGINAL_PASS48_CORRECTION_PASS = pass48_adapter.CORRECTION_PASS
ORIGINAL_PASS48_REVISION = (
    pass48_adapter.TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION
)
ORIGINAL_PASS48_SOURCE_RUN = pass48_adapter.SOURCE_FAILED_RUN_ID
ORIGINAL_PASS48_SOURCE_ARTIFACT = pass48_adapter.SOURCE_FAILED_ARTIFACT_ID
ORIGINAL_PASS48_SOURCE_SHA256 = pass48_adapter.SOURCE_FAILED_ARTIFACT_SHA256
ORIGINAL_PASS48_SOURCE_FAILURE = pass48_adapter.SOURCE_FAILURE
ORIGINAL_PASS48_SCRIPT_PATH = pass48_adapter.SCRIPT_PATH
ORIGINAL_PASS48_CORRECTION_PATH = pass48_adapter.CORRECTION_PATH
ORIGINAL_PASS48_SCENE_KEY = pass48_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS48_CONTACT_SHEET_NAME = pass48_adapter.CONTACT_SHEET_NAME


def _targeted_f06_candidate_offsets(
    objects: tuple[object, ...],
    *,
    saved_basis: dict[str, object],
    pivot: object,
    current_direction: object,
    minimum_clearance: float,
) -> tuple[dict[str, float], ...]:
    candidates = ORIGINAL_PASS02_CANDIDATE_OFFSETS(
        objects,
        saved_basis=saved_basis,
        pivot=pivot,
        current_direction=current_direction,
        minimum_clearance=minimum_clearance,
    )
    selected = tuple(
        candidate
        for candidate in candidates
        if abs(
            float(candidate["offset_degrees"])
            - F06_FIXED_WEAPON_OFFSET_DEGREES
        )
        < 1.0e-6
    )
    if len(selected) != 1:
        raise RuntimeError(
            "two-hand up pass49 expected exactly one geometry-safe f06 "
            f"candidate at {F06_FIXED_WEAPON_OFFSET_DEGREES:.1f} degrees: "
            f"{selected}"
        )
    return selected


def _render_pass48_base_with_f06_overscan(
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
        return ORIGINAL_PASS48_BASE_RENDER(
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

    camera = factory.bpy.data.objects.get(CAMERA_OBJECT_NAME)
    if camera is None or camera.data is None:
        raise RuntimeError("two-hand up pass49 gameplay camera is missing")

    original_shift_x = float(camera.data.shift_x)
    diagnostics: list[dict[str, object]] = []
    try:
        for attempt, shift_x in enumerate(F06_CAMERA_SHIFT_X_CANDIDATES, start=1):
            camera.data.shift_x = float(shift_x)
            factory.bpy.context.view_layer.update()
            pass02_adapter._candidate_offsets = _targeted_f06_candidate_offsets
            try:
                artifact, calibration = ORIGINAL_PASS48_BASE_RENDER(
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
                    "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS49_F06_ATTEMPT="
                    f"attempt:{attempt};shift_x:{shift_x:.3f};accepted:false;"
                    f"error:{exc}"
                )
                continue
            finally:
                pass02_adapter._candidate_offsets = (
                    ORIGINAL_PASS02_CANDIDATE_OFFSETS
                )

            edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
            touched = {
                edge: count for edge, count in edge_counts.items() if count > 0
            }
            if touched:
                diagnostics.append(
                    {
                        "attempt": attempt,
                        "camera_shift_x": float(shift_x),
                        "accepted": False,
                        "edge_counts": edge_counts,
                    }
                )
                continue

            metadata = {
                "camera_shift_x": float(shift_x),
                "weapon_offset_degrees": F06_FIXED_WEAPON_OFFSET_DEGREES,
                "edge_counts": edge_counts,
                "attempt": attempt,
                "diagnostics": diagnostics,
                "camera_shift_restored_after_render": True,
                "action_data_changed": False,
                "root_translation_used": False,
            }
            factory.bpy.context.scene[SELECTED_F06_SCENE_KEY] = json.dumps(
                metadata,
                sort_keys=True,
            )
            print(
                "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS49_F06_SELECTED="
                f"shift_x:{shift_x:.3f};offset:"
                f"{F06_FIXED_WEAPON_OFFSET_DEGREES:.1f};edges:{edge_counts};"
                f"attempt:{attempt}"
            )
            return artifact, calibration

        raise RuntimeError(
            "two-hand up pass49 found no export-contained f06 local overscan "
            f"candidate: {diagnostics}"
        )
    finally:
        pass02_adapter._candidate_offsets = ORIGINAL_PASS02_CANDIDATE_OFFSETS
        camera.data.shift_x = original_shift_x
        factory.bpy.context.view_layer.update()


def _write_manifest_v21_pass49(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS47_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up pass49 cycle manifest is invalid")
    if SELECTED_F06_SCENE_KEY not in factory.bpy.context.scene:
        raise RuntimeError("two-hand up pass49 selected f06 metadata is missing")
    selected_f06 = json.loads(
        str(factory.bpy.context.scene[SELECTED_F06_SCENE_KEY])
    )
    cycle["correction_pass"] = CORRECTION_PASS
    cycle["revision"] = TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION
    cycle["selected_f06"] = selected_f06
    frame_metrics = cycle.get("frame_metrics", {})
    if not isinstance(frame_metrics, dict):
        frame_metrics = {}
    frame_metrics["f06"] = selected_f06
    cycle["frame_metrics"] = frame_metrics
    cycle["camera_shift_persistent_change"] = False
    payload[DIAGNOSTIC_SCENE_KEY] = cycle
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION,
            "source_failed_run_id": SOURCE_FAILED_RUN_ID,
            "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
            "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
            "source_failure": SOURCE_FAILURE,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "selected_f06_changed": True,
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


def _apply_pass49_contract() -> None:
    pass48_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass48_adapter.TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION = (
        TWOHAND_UP_F01_TO_F06_SELECTED_CYCLE_REVISION
    )
    pass48_adapter.SOURCE_FAILED_RUN_ID = SOURCE_FAILED_RUN_ID
    pass48_adapter.SOURCE_FAILED_ARTIFACT_ID = SOURCE_FAILED_ARTIFACT_ID
    pass48_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = SOURCE_FAILED_ARTIFACT_SHA256
    pass48_adapter.SOURCE_FAILURE = SOURCE_FAILURE
    pass48_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass48_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass48_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass48_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass48_adapter.ORIGINAL_PASS47_BASE_RENDER = (
        _render_pass48_base_with_f06_overscan
    )
    pass47_adapter._write_manifest_v21_pass47 = _write_manifest_v21_pass49


def _restore_pass48_contract() -> None:
    pass02_adapter._candidate_offsets = ORIGINAL_PASS02_CANDIDATE_OFFSETS
    pass47_adapter._write_manifest_v21_pass47 = ORIGINAL_PASS47_WRITE_MANIFEST
    pass48_adapter.ORIGINAL_PASS47_BASE_RENDER = ORIGINAL_PASS48_BASE_RENDER
    pass48_adapter.CORRECTION_PASS = ORIGINAL_PASS48_CORRECTION_PASS
    pass48_adapter.TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION = (
        ORIGINAL_PASS48_REVISION
    )
    pass48_adapter.SOURCE_FAILED_RUN_ID = ORIGINAL_PASS48_SOURCE_RUN
    pass48_adapter.SOURCE_FAILED_ARTIFACT_ID = ORIGINAL_PASS48_SOURCE_ARTIFACT
    pass48_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = ORIGINAL_PASS48_SOURCE_SHA256
    pass48_adapter.SOURCE_FAILURE = ORIGINAL_PASS48_SOURCE_FAILURE
    pass48_adapter.SCRIPT_PATH = ORIGINAL_PASS48_SCRIPT_PATH
    pass48_adapter.CORRECTION_PATH = ORIGINAL_PASS48_CORRECTION_PATH
    pass48_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS48_SCENE_KEY
    pass48_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS48_CONTACT_SHEET_NAME


def main() -> int:
    _apply_pass49_contract()
    try:
        return pass48_adapter.main()
    finally:
        _restore_pass48_contract()


if __name__ == "__main__":
    raise SystemExit(main())
