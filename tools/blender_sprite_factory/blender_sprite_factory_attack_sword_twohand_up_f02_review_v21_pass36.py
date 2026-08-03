from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_twohand_up_f02_review_v21_pass34 as pass34_adapter
import blender_sprite_factory_attack_sword_twohand_up_f02_review_v21_pass35 as pass35_adapter
from attack_sword_directional_cycle_correction_v21_pass36 import (
    CORRECTION_PASS,
    PREFER_SOURCE_DEPTH_BRANCH,
    REVIEW_VARIANT_COUNT,
    SELECT_UNIQUE_ARM_PROFILES_FIRST,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_ARTIFACT_SHA256,
    SOURCE_REVIEW_FINDING,
    SOURCE_REVIEW_RUN_ID,
    TARGET_ABS_WEAPON_OFFSET_DEGREES,
    TWOHAND_UP_F02_BALANCED_REVIEW_REVISION,
    USE_MINIMAX_CONTINUITY,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass36.py"
)
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f02_review_v21_pass36"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f02_review_v21_pass36.png"

ORIGINAL_PASS35_CORRECTION_PASS = pass35_adapter.CORRECTION_PASS
ORIGINAL_PASS35_REVISION = pass35_adapter.TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION
ORIGINAL_PASS35_SOURCE_RUN_ID = pass35_adapter.SOURCE_FAILED_RUN_ID
ORIGINAL_PASS35_SOURCE_ARTIFACT_ID = pass35_adapter.SOURCE_FAILED_ARTIFACT_ID
ORIGINAL_PASS35_SOURCE_ARTIFACT_SHA256 = (
    pass35_adapter.SOURCE_FAILED_ARTIFACT_SHA256
)
ORIGINAL_PASS35_SOURCE_FAILURE = pass35_adapter.SOURCE_FAILURE
ORIGINAL_PASS35_CORRECTION_PATH = pass35_adapter.CORRECTION_PATH
ORIGINAL_PASS35_SCRIPT_PATH = pass35_adapter.SCRIPT_PATH
ORIGINAL_PASS35_DIAGNOSTIC_SCENE_KEY = pass35_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS35_CONTACT_SHEET_NAME = pass35_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS35_SORT_KEY = pass35_adapter._candidate_sort_key_v21_pass35
ORIGINAL_PASS34_SELECT_DIVERSE = pass34_adapter._select_diverse_candidates


def _candidate_sort_key_v21_pass36(
    candidate: dict[str, object],
) -> tuple[object, ...]:
    offset = abs(float(candidate["offset_degrees"]))
    from_f01 = float(candidate["continuity_from_corrected_f01_rms_degrees"])
    to_f03 = float(candidate["continuity_to_original_f03_rms_degrees"])
    maximum_transition = max(from_f01, to_f03)
    transition_imbalance = abs(from_f01 - to_f03)
    source_depth_rank = 0 if candidate["depth_branch"] == "source" else 1
    return (
        0 if offset <= TARGET_ABS_WEAPON_OFFSET_DEGREES else 1,
        maximum_transition if USE_MINIMAX_CONTINUITY else from_f01 + to_f03,
        transition_imbalance,
        source_depth_rank if PREFER_SOURCE_DEPTH_BRANCH else 0,
        offset,
        from_f01 + to_f03,
        -float(candidate["screen_projection"]),
        -int(candidate["visible_blade_samples"]),
        -int(candidate["occluded_blade_samples"]),
        -float(candidate["camera_margin_pixels"]),
    )


def _select_diverse_candidates_v21_pass36(
    candidates: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    ordered = sorted(candidates, key=_candidate_sort_key_v21_pass36)
    selected: list[dict[str, object]] = []
    selected_ids: set[int] = set()
    seen_arm_profiles: set[tuple[object, ...]] = set()

    if SELECT_UNIQUE_ARM_PROFILES_FIRST:
        for candidate in ordered:
            arm_key = (
                int(candidate["source_pose_code"]),
                round(float(candidate["arm_blend"]), 4),
            )
            if arm_key in seen_arm_profiles:
                continue
            seen_arm_profiles.add(arm_key)
            selected.append(candidate)
            selected_ids.add(id(candidate))
            if len(selected) == REVIEW_VARIANT_COUNT:
                return tuple(selected)

    seen_full_profiles: set[tuple[object, ...]] = set()
    for candidate in ordered:
        if id(candidate) in selected_ids:
            continue
        full_key = (
            int(candidate["source_pose_code"]),
            round(float(candidate["arm_blend"]), 4),
            str(candidate["depth_branch"]),
            round(float(candidate["offset_degrees"]), 3),
            round(float(candidate["screen_projection"]), 4),
        )
        if full_key in seen_full_profiles:
            continue
        seen_full_profiles.add(full_key)
        selected.append(candidate)
        if len(selected) == REVIEW_VARIANT_COUNT:
            break
    return tuple(selected)


def _apply_pass36_contract() -> None:
    pass35_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass35_adapter.TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION = (
        TWOHAND_UP_F02_BALANCED_REVIEW_REVISION
    )
    pass35_adapter.SOURCE_FAILED_RUN_ID = SOURCE_REVIEW_RUN_ID
    pass35_adapter.SOURCE_FAILED_ARTIFACT_ID = SOURCE_REVIEW_ARTIFACT_ID
    pass35_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = (
        SOURCE_REVIEW_ARTIFACT_SHA256
    )
    pass35_adapter.SOURCE_FAILURE = SOURCE_REVIEW_FINDING
    pass35_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass35_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass35_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass35_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass35_adapter._candidate_sort_key_v21_pass35 = (
        _candidate_sort_key_v21_pass36
    )
    pass34_adapter._select_diverse_candidates = (
        _select_diverse_candidates_v21_pass36
    )


def _restore_pass35_contract() -> None:
    pass35_adapter.CORRECTION_PASS = ORIGINAL_PASS35_CORRECTION_PASS
    pass35_adapter.TWOHAND_UP_F02_OCCLUSION_REVIEW_REVISION = (
        ORIGINAL_PASS35_REVISION
    )
    pass35_adapter.SOURCE_FAILED_RUN_ID = ORIGINAL_PASS35_SOURCE_RUN_ID
    pass35_adapter.SOURCE_FAILED_ARTIFACT_ID = ORIGINAL_PASS35_SOURCE_ARTIFACT_ID
    pass35_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = (
        ORIGINAL_PASS35_SOURCE_ARTIFACT_SHA256
    )
    pass35_adapter.SOURCE_FAILURE = ORIGINAL_PASS35_SOURCE_FAILURE
    pass35_adapter.CORRECTION_PATH = ORIGINAL_PASS35_CORRECTION_PATH
    pass35_adapter.SCRIPT_PATH = ORIGINAL_PASS35_SCRIPT_PATH
    pass35_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS35_DIAGNOSTIC_SCENE_KEY
    pass35_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS35_CONTACT_SHEET_NAME
    pass35_adapter._candidate_sort_key_v21_pass35 = ORIGINAL_PASS35_SORT_KEY
    pass34_adapter._select_diverse_candidates = ORIGINAL_PASS34_SELECT_DIVERSE


def main() -> int:
    _apply_pass36_contract()
    try:
        return pass35_adapter.main()
    finally:
        _restore_pass35_contract()


if __name__ == "__main__":
    raise SystemExit(main())
