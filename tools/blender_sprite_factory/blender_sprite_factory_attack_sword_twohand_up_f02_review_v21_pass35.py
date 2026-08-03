from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f02_review_v21_pass34 as pass34_adapter
from attack_sword_directional_cycle_correction_v21_pass35 import (
    ALLOW_ZERO_SCREEN_GAP_WHEN_BLADE_IS_VISIBLE,
    CORRECTION_PASS,
    MAX_REFERENCE_RIGHT_EDGE_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    PREFER_SOURCE_DEPTH_BRANCH,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass35.py"
)
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f02_review_v21_pass35"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f02_review_v21_pass35.png"

ORIGINAL_PASS34_CORRECTION_PASS = pass34_adapter.CORRECTION_PASS
ORIGINAL_PASS34_REVISION = (
    pass34_adapter.TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION
)
ORIGINAL_PASS34_MIN_CLEARANCE = (
    pass34_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
)
ORIGINAL_PASS34_MIN_VISIBLE_SAMPLES = pass34_adapter.MIN_VISIBLE_BLADE_SAMPLES
ORIGINAL_PASS34_REQUIRE_ZERO_EDGES = pass34_adapter.REQUIRE_ZERO_EDGE_ALPHA
ORIGINAL_PASS34_SOURCE_RUN_ID = pass34_adapter.SOURCE_FAILED_RUN_ID
ORIGINAL_PASS34_SOURCE_ARTIFACT_ID = pass34_adapter.SOURCE_FAILED_ARTIFACT_ID
ORIGINAL_PASS34_SOURCE_ARTIFACT_SHA256 = (
    pass34_adapter.SOURCE_FAILED_ARTIFACT_SHA256
)
ORIGINAL_PASS34_SOURCE_FAILURE = pass34_adapter.SOURCE_FAILURE
ORIGINAL_PASS34_CORRECTION_PATH = pass34_adapter.CORRECTION_PATH
ORIGINAL_PASS34_SCRIPT_PATH = pass34_adapter.SCRIPT_PATH
ORIGINAL_PASS34_DIAGNOSTIC_SCENE_KEY = pass34_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS34_CONTACT_SHEET_NAME = pass34_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS34_SORT_KEY = pass34_adapter._candidate_sort_key
ORIGINAL_PASS34_RENDER_F03 = pass34_adapter._render_original_f03_reference
ORIGINAL_PASS29_MIN_CLEARANCE = (
    pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
)
ORIGINAL_PASS29_MIN_VISIBLE_SAMPLES = pass29_adapter.MIN_VISIBLE_BLADE_SAMPLES


def _candidate_sort_key_v21_pass35(
    candidate: dict[str, object],
) -> tuple[object, ...]:
    offset = abs(float(candidate["offset_degrees"]))
    continuity = float(candidate["continuity_score"])
    source_depth_rank = 0 if candidate["depth_branch"] == "source" else 1
    return (
        0 if offset <= pass34_adapter.TARGET_ABS_WEAPON_OFFSET_DEGREES else 1,
        offset,
        continuity,
        source_depth_rank if PREFER_SOURCE_DEPTH_BRANCH else 0,
        float(candidate["continuity_from_corrected_f01_rms_degrees"]),
        float(candidate["continuity_to_original_f03_rms_degrees"]),
        float(candidate["arm_blend"]),
        -float(candidate["screen_projection"]),
        -int(candidate["occluded_blade_samples"]),
        -int(candidate["visible_blade_samples"]),
        -float(candidate["camera_margin_pixels"]),
    )


def _render_original_f03_reference_v21_pass35(
    context: object,
    run_dir: Path,
    *,
    calibration: object,
    action: object,
) -> tuple[object, dict[str, object]]:
    previous_requirement = pass34_adapter.REQUIRE_ZERO_EDGE_ALPHA
    pass34_adapter.REQUIRE_ZERO_EDGE_ALPHA = False
    try:
        artifact, metadata = ORIGINAL_PASS34_RENDER_F03(
            context,
            run_dir,
            calibration=calibration,
            action=action,
        )
    finally:
        pass34_adapter.REQUIRE_ZERO_EDGE_ALPHA = previous_requirement

    edge_counts = metadata.get("edge_counts", {})
    if not isinstance(edge_counts, dict):
        raise RuntimeError("two-hand up pass35 f03 edge metrics are invalid")
    forbidden = {
        str(edge): int(count)
        for edge, count in edge_counts.items()
        if int(count) > 0
        and (
            str(edge) != "right"
            or int(count) > MAX_REFERENCE_RIGHT_EDGE_PIXELS
        )
    }
    if forbidden:
        raise RuntimeError(
            "two-hand up pass35 f03 reference exceeded the historical "
            f"boundary allowance: {forbidden}"
        )
    metadata["pass35_reference_right_edge_allowance"] = (
        MAX_REFERENCE_RIGHT_EDGE_PIXELS
    )
    metadata["pass35_reference_only"] = True
    return artifact, metadata


def _apply_pass35_contract() -> None:
    pass34_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass34_adapter.TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION = (
        TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION
    )
    pass34_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
        MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
    )
    pass34_adapter.MIN_VISIBLE_BLADE_SAMPLES = MIN_VISIBLE_BLADE_SAMPLES
    pass34_adapter.REQUIRE_ZERO_EDGE_ALPHA = (
        REQUIRE_ZERO_EDGE_ALPHA_FOR_CANDIDATES
    )
    pass34_adapter.SOURCE_FAILED_RUN_ID = SOURCE_FAILED_RUN_ID
    pass34_adapter.SOURCE_FAILED_ARTIFACT_ID = SOURCE_FAILED_ARTIFACT_ID
    pass34_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = (
        SOURCE_FAILED_ARTIFACT_SHA256
    )
    pass34_adapter.SOURCE_FAILURE = SOURCE_FAILURE
    pass34_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass34_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass34_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass34_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass34_adapter._candidate_sort_key = _candidate_sort_key_v21_pass35
    pass34_adapter._render_original_f03_reference = (
        _render_original_f03_reference_v21_pass35
    )
    pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
        MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
    )
    pass29_adapter.MIN_VISIBLE_BLADE_SAMPLES = MIN_VISIBLE_BLADE_SAMPLES


def _restore_pass34_contract() -> None:
    pass34_adapter.CORRECTION_PASS = ORIGINAL_PASS34_CORRECTION_PASS
    pass34_adapter.TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION = (
        ORIGINAL_PASS34_REVISION
    )
    pass34_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
        ORIGINAL_PASS34_MIN_CLEARANCE
    )
    pass34_adapter.MIN_VISIBLE_BLADE_SAMPLES = (
        ORIGINAL_PASS34_MIN_VISIBLE_SAMPLES
    )
    pass34_adapter.REQUIRE_ZERO_EDGE_ALPHA = ORIGINAL_PASS34_REQUIRE_ZERO_EDGES
    pass34_adapter.SOURCE_FAILED_RUN_ID = ORIGINAL_PASS34_SOURCE_RUN_ID
    pass34_adapter.SOURCE_FAILED_ARTIFACT_ID = ORIGINAL_PASS34_SOURCE_ARTIFACT_ID
    pass34_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = (
        ORIGINAL_PASS34_SOURCE_ARTIFACT_SHA256
    )
    pass34_adapter.SOURCE_FAILURE = ORIGINAL_PASS34_SOURCE_FAILURE
    pass34_adapter.CORRECTION_PATH = ORIGINAL_PASS34_CORRECTION_PATH
    pass34_adapter.SCRIPT_PATH = ORIGINAL_PASS34_SCRIPT_PATH
    pass34_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS34_DIAGNOSTIC_SCENE_KEY
    pass34_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS34_CONTACT_SHEET_NAME
    pass34_adapter._candidate_sort_key = ORIGINAL_PASS34_SORT_KEY
    pass34_adapter._render_original_f03_reference = ORIGINAL_PASS34_RENDER_F03
    pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
        ORIGINAL_PASS29_MIN_CLEARANCE
    )
    pass29_adapter.MIN_VISIBLE_BLADE_SAMPLES = (
        ORIGINAL_PASS29_MIN_VISIBLE_SAMPLES
    )


def main() -> int:
    if not ALLOW_ZERO_SCREEN_GAP_WHEN_BLADE_IS_VISIBLE:
        raise RuntimeError("two-hand up pass35 occlusion contract is disabled")
    _apply_pass35_contract()
    try:
        return pass34_adapter.main()
    finally:
        _restore_pass34_contract()


if __name__ == "__main__":
    raise SystemExit(main())
