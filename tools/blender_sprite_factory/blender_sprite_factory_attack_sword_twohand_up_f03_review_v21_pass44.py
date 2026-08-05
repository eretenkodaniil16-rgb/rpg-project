from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass43 as pass43_adapter
from attack_sword_directional_cycle_correction_v21_pass44 import (
    COMPACT_ANGLE_OFFSET_CANDIDATES,
    COMPACT_PROJECTION_CANDIDATES,
    CORRECTION_PASS,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_PASS43_ARTIFACT_ID,
    SOURCE_PASS43_ARTIFACT_SHA256,
    SOURCE_PASS43_FINDING,
    SOURCE_PASS43_RUN_ID,
    TARGETED_COMPACT_SPECS,
    TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass44.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f03_review_v21_pass44"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f03_review_v21_pass44.png"

ORIGINAL_PASS43_CORRECTION_PASS = pass43_adapter.CORRECTION_PASS
ORIGINAL_PASS43_REVISION = (
    pass43_adapter.TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION
)
ORIGINAL_PASS43_PROJECTIONS = (
    pass43_adapter.DEPTH_CONTRACTION_PROJECTION_CANDIDATES
)
ORIGINAL_PASS43_OFFSETS = pass43_adapter.DEPTH_CONTRACTION_ANGLE_CANDIDATES
ORIGINAL_PASS43_TARGETED_SPECS = pass43_adapter.TARGETED_DEPTH_SPECS
ORIGINAL_PASS43_RENDER_EDGE_TOUCHING = (
    pass43_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
)
ORIGINAL_PASS43_REQUIRE_ZERO_EDGES = (
    pass43_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
)
ORIGINAL_PASS43_CORRECTION_PATH = pass43_adapter.CORRECTION_PATH
ORIGINAL_PASS43_SCRIPT_PATH = pass43_adapter.SCRIPT_PATH
ORIGINAL_PASS43_SCENE_KEY = pass43_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS43_CONTACT_SHEET_NAME = pass43_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS43_WRITE_MANIFEST = pass43_adapter._write_manifest_v21_pass43


def _write_manifest_v21_pass44(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS43_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up f03 pass44 review manifest is invalid")
    review.update(
        {
            "compact_projection_candidates": list(COMPACT_PROJECTION_CANDIDATES),
            "compact_angle_offset_candidates": list(
                COMPACT_ANGLE_OFFSET_CANDIDATES
            ),
            "targeted_compact_specs": list(TARGETED_COMPACT_SPECS),
            "selection_strategy": (
                "preserve the original_f05 blend 0.60 arm pose and rigid sword "
                "geometry, then choose the largest compact screen projection "
                "whose full blade has zero alpha pixels on every canvas edge"
            ),
            "manual_selection_required": True,
        }
    )
    payload[DIAGNOSTIC_SCENE_KEY] = review
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION,
            "source_pass43_run_id": SOURCE_PASS43_RUN_ID,
            "source_pass43_artifact_id": SOURCE_PASS43_ARTIFACT_ID,
            "source_pass43_artifact_sha256": SOURCE_PASS43_ARTIFACT_SHA256,
            "source_pass43_finding": SOURCE_PASS43_FINDING,
            "adapter_path": (
                "tools/blender_sprite_factory/"
                "blender_sprite_factory_attack_sword_twohand_up_"
                "f03_review_v21_pass44.py"
            ),
            "correction_path": (
                "tools/blender_sprite_factory/"
                "attack_sword_directional_cycle_correction_v21_pass44.py"
            ),
            "contact_sheet_name": CONTACT_SHEET_NAME,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass44_contract() -> None:
    pass43_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass43_adapter.TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION = (
        TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION
    )
    pass43_adapter.DEPTH_CONTRACTION_PROJECTION_CANDIDATES = (
        COMPACT_PROJECTION_CANDIDATES
    )
    pass43_adapter.DEPTH_CONTRACTION_ANGLE_CANDIDATES = (
        COMPACT_ANGLE_OFFSET_CANDIDATES
    )
    pass43_adapter.TARGETED_DEPTH_SPECS = TARGETED_COMPACT_SPECS
    pass43_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
    )
    pass43_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
    )
    pass43_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass43_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass43_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass43_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass43_adapter._write_manifest_v21_pass43 = _write_manifest_v21_pass44


def _restore_pass43_contract() -> None:
    pass43_adapter.CORRECTION_PASS = ORIGINAL_PASS43_CORRECTION_PASS
    pass43_adapter.TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION = (
        ORIGINAL_PASS43_REVISION
    )
    pass43_adapter.DEPTH_CONTRACTION_PROJECTION_CANDIDATES = (
        ORIGINAL_PASS43_PROJECTIONS
    )
    pass43_adapter.DEPTH_CONTRACTION_ANGLE_CANDIDATES = ORIGINAL_PASS43_OFFSETS
    pass43_adapter.TARGETED_DEPTH_SPECS = ORIGINAL_PASS43_TARGETED_SPECS
    pass43_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        ORIGINAL_PASS43_RENDER_EDGE_TOUCHING
    )
    pass43_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        ORIGINAL_PASS43_REQUIRE_ZERO_EDGES
    )
    pass43_adapter.CORRECTION_PATH = ORIGINAL_PASS43_CORRECTION_PATH
    pass43_adapter.SCRIPT_PATH = ORIGINAL_PASS43_SCRIPT_PATH
    pass43_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS43_SCENE_KEY
    pass43_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS43_CONTACT_SHEET_NAME
    pass43_adapter._write_manifest_v21_pass43 = ORIGINAL_PASS43_WRITE_MANIFEST


def main() -> int:
    _apply_pass44_contract()
    try:
        return pass43_adapter.main()
    finally:
        _restore_pass43_contract()


if __name__ == "__main__":
    raise SystemExit(main())
