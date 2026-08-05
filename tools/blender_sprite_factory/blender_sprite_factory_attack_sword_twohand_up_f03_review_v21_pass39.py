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
from attack_sword_directional_cycle_correction_v21_pass39 import (
    CORRECTION_PASS,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    SOURCE_PARTIAL_ARTIFACT_ID,
    SOURCE_PARTIAL_ARTIFACT_SHA256,
    SOURCE_PARTIAL_FINDING,
    SOURCE_PARTIAL_RUN_ID,
    TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass39.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f03_review_v21_pass39"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f03_review_v21_pass39.png"

ORIGINAL_REQUIRE_ZERO_EDGES = pass38_adapter.REQUIRE_ZERO_EDGE_ALPHA
ORIGINAL_CORRECTION_PASS = pass38_adapter.CORRECTION_PASS
ORIGINAL_REVISION = pass38_adapter.TWOHAND_UP_F03_CONTINUITY_REVIEW_REVISION
ORIGINAL_CORRECTION_PATH = pass38_adapter.CORRECTION_PATH
ORIGINAL_SCRIPT_PATH = pass38_adapter.SCRIPT_PATH
ORIGINAL_SCENE_KEY = pass38_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_CONTACT_SHEET_NAME = pass38_adapter.CONTACT_SHEET_NAME
ORIGINAL_SOURCE_RUN_ID = pass38_adapter.SOURCE_FAILED_RUN_ID
ORIGINAL_SOURCE_ARTIFACT_ID = pass38_adapter.SOURCE_FAILED_ARTIFACT_ID
ORIGINAL_SOURCE_ARTIFACT_SHA256 = pass38_adapter.SOURCE_FAILED_ARTIFACT_SHA256
ORIGINAL_SOURCE_FAILURE = pass38_adapter.SOURCE_FAILURE
ORIGINAL_WRITE_MANIFEST = pass38_adapter._write_manifest


def _write_manifest_v21_pass39(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up f03 pass39 review manifest is invalid")
    columns = review.get("columns", [])
    if not isinstance(columns, list):
        raise RuntimeError("two-hand up f03 pass39 review columns are invalid")
    for column in columns:
        if not isinstance(column, dict):
            continue
        edge_counts = column.get("edge_counts", {})
        if not isinstance(edge_counts, dict):
            edge_counts = {}
        touched = {
            str(edge): int(count)
            for edge, count in edge_counts.items()
            if int(count) > 0
        }
        column["edge_touching"] = bool(touched)
        column["accepted_by_boundary_contract"] = (
            not touched if REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE else True
        )
    payload[DIAGNOSTIC_SCENE_KEY] = review
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION,
            "source_partial_run_id": SOURCE_PARTIAL_RUN_ID,
            "source_partial_artifact_id": SOURCE_PARTIAL_ARTIFACT_ID,
            "source_partial_artifact_sha256": SOURCE_PARTIAL_ARTIFACT_SHA256,
            "source_partial_finding": SOURCE_PARTIAL_FINDING,
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


def _apply_pass39_contract() -> None:
    if not RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW:
        raise RuntimeError("two-hand up f03 pass39 complete review is disabled")
    pass38_adapter.REQUIRE_ZERO_EDGE_ALPHA = False
    pass38_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass38_adapter.TWOHAND_UP_F03_CONTINUITY_REVIEW_REVISION = (
        TWOHAND_UP_F03_COMPLETE_REVIEW_REVISION
    )
    pass38_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass38_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass38_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass38_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass38_adapter.SOURCE_FAILED_RUN_ID = SOURCE_PARTIAL_RUN_ID
    pass38_adapter.SOURCE_FAILED_ARTIFACT_ID = SOURCE_PARTIAL_ARTIFACT_ID
    pass38_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = SOURCE_PARTIAL_ARTIFACT_SHA256
    pass38_adapter.SOURCE_FAILURE = SOURCE_PARTIAL_FINDING
    pass38_adapter._write_manifest = _write_manifest_v21_pass39


def _restore_pass38_contract() -> None:
    pass38_adapter.REQUIRE_ZERO_EDGE_ALPHA = ORIGINAL_REQUIRE_ZERO_EDGES
    pass38_adapter.CORRECTION_PASS = ORIGINAL_CORRECTION_PASS
    pass38_adapter.TWOHAND_UP_F03_CONTINUITY_REVIEW_REVISION = ORIGINAL_REVISION
    pass38_adapter.CORRECTION_PATH = ORIGINAL_CORRECTION_PATH
    pass38_adapter.SCRIPT_PATH = ORIGINAL_SCRIPT_PATH
    pass38_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_SCENE_KEY
    pass38_adapter.CONTACT_SHEET_NAME = ORIGINAL_CONTACT_SHEET_NAME
    pass38_adapter.SOURCE_FAILED_RUN_ID = ORIGINAL_SOURCE_RUN_ID
    pass38_adapter.SOURCE_FAILED_ARTIFACT_ID = ORIGINAL_SOURCE_ARTIFACT_ID
    pass38_adapter.SOURCE_FAILED_ARTIFACT_SHA256 = ORIGINAL_SOURCE_ARTIFACT_SHA256
    pass38_adapter.SOURCE_FAILURE = ORIGINAL_SOURCE_FAILURE
    pass38_adapter._write_manifest = ORIGINAL_WRITE_MANIFEST


def main() -> int:
    _apply_pass39_contract()
    try:
        return pass38_adapter.main()
    finally:
        _restore_pass38_contract()


if __name__ == "__main__":
    raise SystemExit(main())
