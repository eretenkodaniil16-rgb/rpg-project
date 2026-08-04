from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass47 as pass47_adapter
from attack_sword_directional_cycle_correction_v21_pass48 import (
    CORRECTION_PASS,
    F04_CAMERA_SHIFT_X_CANDIDATES,
    F04_FIXED_CENTER_COMPENSATION_USED,
    F04_FIXED_WEAPON_OFFSET_DEGREES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass48.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass48"
SELECTED_F04_SCENE_KEY = "attack_sword_twohand_up_selected_f04_v21_pass48"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass48.png"

ORIGINAL_PASS02_CANDIDATE_OFFSETS = pass02_adapter._candidate_offsets
ORIGINAL_PASS47_BASE_RENDER = pass47_adapter.ORIGINAL_PASS46_RENDER_FRAME
ORIGINAL_PASS47_CORRECTION_PASS = pass47_adapter.CORRECTION_PASS
ORIGINAL_PASS47_REVISION = (
    pass47_adapter.TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION
)
ORIGINAL_PASS47_SHIFT_CANDIDATES = pass47_adapter.F04_CAMERA_SHIFT_X_CANDIDATES
ORIGINAL_PASS47_FIXED_CENTER = pass47_adapter.F04_FIXED_CENTER_COMPENSATION_USED
ORIGINAL_PASS47_SOURCE_RUN = pass47_adapter.SOURCE_FAILED_RUN_ID
ORIGINAL_PASS47_SOURCE_ARTIFACT = pass47_adapter.SOURCE_FAILED_ARTIFACT_ID
ORIGINAL_PASS47_SOURCE_SHA256 = pass47_adapter.SOURCE_FAILED_ARTIFACT_SHA256
ORIGINAL_PASS47_SOURCE_FAILURE = pass47_adapter.SOURCE_FAILURE
ORIGINAL_PASS47_SCRIPT_PATH = pass47_adapter.SCRIPT_PATH
ORIGINAL_PASS47_CORRECTION_PATH = pass47_adapter.CORRECTION_PATH
ORIGINAL_PASS47_SCENE_KEY = pass47_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS47_SELECTED_F04_SCENE_KEY = pass47_adapter.SELECTED_F04_SCENE_KEY
ORIGINAL_PASS47_CONTACT_SHEET_NAME = pass47_adapter.CONTACT_SHEET_NAME


def _targeted_f04_candidate_offsets(
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
            - F04_FIXED_WEAPON_OFFSET_DEGREES
        )
        < 1.0e-6
    )
    if len(selected) != 1:
        raise RuntimeError(
            "two-hand up pass48 expected exactly one geometry-safe f04 "
            f"candidate at {F04_FIXED_WEAPON_OFFSET_DEGREES:.1f} degrees: "
            f"{selected}"
        )
    return selected


def _render_pass46_with_targeted_f04(
    context: object,
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
) -> tuple[object, object]:
    is_target = (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number == TARGET_FRAME
    )
    if not is_target:
        return ORIGINAL_PASS47_BASE_RENDER(
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

    pass02_adapter._candidate_offsets = _targeted_f04_candidate_offsets
    try:
        return ORIGINAL_PASS47_BASE_RENDER(
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
    finally:
        pass02_adapter._candidate_offsets = ORIGINAL_PASS02_CANDIDATE_OFFSETS


def _apply_pass48_contract() -> None:
    pass47_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass47_adapter.TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION = (
        TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION
    )
    pass47_adapter.F04_CAMERA_SHIFT_X_CANDIDATES = (
        F04_CAMERA_SHIFT_X_CANDIDATES
    )
    pass47_adapter.F04_FIXED_CENTER_COMPENSATION_USED = (
        F04_FIXED_CENTER_COMPENSATION_USED
    )
    pass47_adapter.SOURCE_FAILED_RUN_ID = SOURCE_FAILED_RUN_ID
    pass47_adapter.SOURCE_FAILED_ARTIFACT_ID = SOURCE_FAILED_ARTIFACT_ID
    pass47_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = SOURCE_FAILED_ARTIFACT_SHA256
    pass47_adapter.SOURCE_FAILURE = SOURCE_FAILURE
    pass47_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass47_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass47_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass47_adapter.SELECTED_F04_SCENE_KEY = SELECTED_F04_SCENE_KEY
    pass47_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass47_adapter.ORIGINAL_PASS46_RENDER_FRAME = (
        _render_pass46_with_targeted_f04
    )


def _restore_pass47_contract() -> None:
    pass02_adapter._candidate_offsets = ORIGINAL_PASS02_CANDIDATE_OFFSETS
    pass47_adapter.ORIGINAL_PASS46_RENDER_FRAME = ORIGINAL_PASS47_BASE_RENDER
    pass47_adapter.CORRECTION_PASS = ORIGINAL_PASS47_CORRECTION_PASS
    pass47_adapter.TWOHAND_UP_F01_F02_F03_F04_SELECTED_CYCLE_REVISION = (
        ORIGINAL_PASS47_REVISION
    )
    pass47_adapter.F04_CAMERA_SHIFT_X_CANDIDATES = (
        ORIGINAL_PASS47_SHIFT_CANDIDATES
    )
    pass47_adapter.F04_FIXED_CENTER_COMPENSATION_USED = (
        ORIGINAL_PASS47_FIXED_CENTER
    )
    pass47_adapter.SOURCE_FAILED_RUN_ID = ORIGINAL_PASS47_SOURCE_RUN
    pass47_adapter.SOURCE_FAILED_ARTIFACT_ID = ORIGINAL_PASS47_SOURCE_ARTIFACT
    pass47_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = ORIGINAL_PASS47_SOURCE_SHA256
    pass47_adapter.SOURCE_FAILURE = ORIGINAL_PASS47_SOURCE_FAILURE
    pass47_adapter.SCRIPT_PATH = ORIGINAL_PASS47_SCRIPT_PATH
    pass47_adapter.CORRECTION_PATH = ORIGINAL_PASS47_CORRECTION_PATH
    pass47_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS47_SCENE_KEY
    pass47_adapter.SELECTED_F04_SCENE_KEY = ORIGINAL_PASS47_SELECTED_F04_SCENE_KEY
    pass47_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS47_CONTACT_SHEET_NAME


def main() -> int:
    _apply_pass48_contract()
    try:
        return pass47_adapter.main()
    finally:
        _restore_pass47_contract()


if __name__ == "__main__":
    raise SystemExit(main())
