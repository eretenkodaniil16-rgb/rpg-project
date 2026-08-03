from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass38 as pass38_adapter
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass39 as pass39_adapter
from attack_sword_directional_cycle_correction_v21_pass40 import (
    CORRECTION_PASS,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_COMPLETE_ARTIFACT_ID,
    SOURCE_COMPLETE_ARTIFACT_SHA256,
    SOURCE_COMPLETE_FINDING,
    SOURCE_COMPLETE_RUN_ID,
    TARGETED_PROJECTION_SPECS,
    TWOHAND_UP_F03_TARGETED_PROJECTION_REVIEW_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass40.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f03_review_v21_pass40"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f03_review_v21_pass40.png"

ORIGINAL_SELECT_DIVERSE_CANDIDATES = pass38_adapter._select_diverse_candidates
ORIGINAL_PASS39_CORRECTION_PASS = pass39_adapter.CORRECTION_PASS
ORIGINAL_PASS39_REVISION = pass39_adapter.TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION
ORIGINAL_PASS39_CORRECTION_PATH = pass39_adapter.CORRECTION_PATH
ORIGINAL_PASS39_SCRIPT_PATH = pass39_adapter.SCRIPT_PATH
ORIGINAL_PASS39_SCENE_KEY = pass39_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS39_CONTACT_SHEET_NAME = pass39_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS39_WRITE_MANIFEST = pass39_adapter._write_manifest_v21_pass39


def _matches_spec(
    candidate: dict[str, object],
    spec: dict[str, object],
) -> bool:
    return (
        int(candidate["source_pose_code"]) == int(spec["source_pose_code"])
        and abs(float(candidate["arm_blend"]) - float(spec["arm_blend"])) < 1.0e-6
        and str(candidate["depth_branch"]) == str(spec["depth_branch"])
        and abs(
            float(candidate["offset_degrees"])
            - float(spec["weapon_offset_degrees"])
        )
        < 1.0e-6
        and abs(
            float(candidate["requested_screen_projection"])
            - float(spec["screen_projection"])
        )
        < 1.0e-6
    )


def _select_targeted_projection_candidates(
    candidates: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    selected: list[dict[str, object]] = []
    for index, spec in enumerate(TARGETED_PROJECTION_SPECS, start=1):
        matches = [
            candidate
            for candidate in candidates
            if _matches_spec(candidate, spec)
        ]
        if not matches:
            raise RuntimeError(
                "two-hand up f03 pass40 targeted projection candidate is missing: "
                f"index={index}; spec={spec}"
            )
        matches.sort(
            key=lambda candidate: (
                -int(candidate["visible_blade_samples"]),
                -float(candidate["camera_margin_pixels"]),
                float(candidate["continuity_score"]),
            )
        )
        selected.append(matches[0])
    return tuple(selected)


def _write_manifest_v21_pass40(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS39_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    review = payload.get(DIAGNOSTIC_SCENE_KEY, {})
    if not isinstance(review, dict):
        raise RuntimeError("two-hand up f03 pass40 review manifest is invalid")
    review.update(
        {
            "targeted_projection_specs": list(TARGETED_PROJECTION_SPECS),
            "selection_strategy": (
                "preserve the pass39 upward arc while reducing only the "
                "screen projection until the full rigid blade fits the 96x96 canvas"
            ),
            "manual_selection_required": True,
        }
    )
    payload[DIAGNOSTIC_SCENE_KEY] = review
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F03_TARGETED_PROJECTION_REVIEW_REVISION,
            "source_complete_run_id": SOURCE_COMPLETE_RUN_ID,
            "source_complete_artifact_id": SOURCE_COMPLETE_ARTIFACT_ID,
            "source_complete_artifact_sha256": SOURCE_COMPLETE_ARTIFACT_SHA256,
            "source_complete_finding": SOURCE_COMPLETE_FINDING,
            "adapter_path": (
                "tools/blender_sprite_factory/"
                "blender_sprite_factory_attack_sword_twohand_up_"
                "f03_review_v21_pass40.py"
            ),
            "correction_path": (
                "tools/blender_sprite_factory/"
                "attack_sword_directional_cycle_correction_v21_pass40.py"
            ),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "render_edge_touching_candidates_for_review": (
                RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
            ),
            "require_zero_edge_alpha_for_acceptance": (
                REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
            ),
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass40_contract() -> None:
    pass38_adapter._select_diverse_candidates = (
        _select_targeted_projection_candidates
    )
    pass39_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass39_adapter.TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION = (
        TWOHAND_UP_F03_TARGETED_PROJECTION_REVIEW_REVISION
    )
    pass39_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass39_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass39_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass39_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass39_adapter._write_manifest_v21_pass39 = _write_manifest_v21_pass40


def _restore_pass39_contract() -> None:
    pass38_adapter._select_diverse_candidates = (
        ORIGINAL_SELECT_DIVERSE_CANDIDATES
    )
    pass39_adapter.CORRECTION_PASS = ORIGINAL_PASS39_CORRECTION_PASS
    pass39_adapter.TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION = (
        ORIGINAL_PASS39_REVISION
    )
    pass39_adapter.CORRECTION_PATH = ORIGINAL_PASS39_CORRECTION_PATH
    pass39_adapter.SCRIPT_PATH = ORIGINAL_PASS39_SCRIPT_PATH
    pass39_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS39_SCENE_KEY
    pass39_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS39_CONTACT_SHEET_NAME
    pass39_adapter._write_manifest_v21_pass39 = ORIGINAL_PASS39_WRITE_MANIFEST


def main() -> int:
    _apply_pass40_contract()
    try:
        return pass39_adapter.main()
    finally:
        _restore_pass39_contract()


if __name__ == "__main__":
    raise SystemExit(main())
