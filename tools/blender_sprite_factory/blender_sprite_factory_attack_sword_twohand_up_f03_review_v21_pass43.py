from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass42 as pass42_adapter
from attack_sword_directional_cycle_correction_v21_pass43 import (
    CORRECTION_PASS,
    DEPTH_CONTRACTION_ANGLE_CANDIDATES,
    DEPTH_CONTRACTION_PROJECTION_CANDIDATES,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_PASS42_ARTIFACT_ID,
    SOURCE_PASS42_ARTIFACT_SHA256,
    SOURCE_PASS42_FINDING,
    SOURCE_PASS42_RUN_ID,
    TARGETED_DEPTH_SPECS,
    TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass43.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f03_review_v21_pass43"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f03_review_v21_pass43.png"

ORIGINAL_PASS42_CORRECTION_PASS = pass42_adapter.CORRECTION_PASS
ORIGINAL_PASS42_REVISION = (
    pass42_adapter.TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION
)
ORIGINAL_PASS42_PROJECTIONS = (
    pass42_adapter.EXTENDED_SCREEN_PROJECTION_CANDIDATES
)
ORIGINAL_PASS42_OFFSETS = pass42_adapter.EXTENDED_ANGLE_OFFSET_CANDIDATES
ORIGINAL_PASS42_TARGETED_SPECS = pass42_adapter.TARGETED_OFFSET_SPECS
ORIGINAL_PASS42_RENDER_EDGE_TOUCHING = (
    pass42_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
)
ORIGINAL_PASS42_REQUIRE_ZERO_EDGES = (
    pass42_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
)
ORIGINAL_PASS42_CORRECTION_PATH = pass42_adapter.CORRECTION_PATH
ORIGINAL_PASS42_SCRIPT_PATH = pass42_adapter.SCRIPT_PATH
ORIGINAL_PASS42_SCENE_KEY = pass42_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS42_CONTACT_SHEET_NAME = pass42_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS42_WRITE_MANIFEST = pass42_adapter._write_manifest_v21_pass42


def _write_manifest_v21_pass43(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS42_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up f03 pass43 review manifest is invalid")
    review.update(
        {
            "depth_contraction_projection_candidates": list(
                DEPTH_CONTRACTION_PROJECTION_CANDIDATES
            ),
            "depth_contraction_angle_candidates": list(
                DEPTH_CONTRACTION_ANGLE_CANDIDATES
            ),
            "targeted_depth_specs": list(TARGETED_DEPTH_SPECS),
            "selection_strategy": (
                "preserve the original_f05 blend 0.60 arm pose and clockwise "
                "upward arc, then reduce only the rigid sword screen projection "
                "until the complete blade fits the 96x96 canvas"
            ),
            "manual_selection_required": True,
        }
    )
    payload[DIAGNOSTIC_SCENE_KEY] = review
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION,
            "source_pass42_run_id": SOURCE_PASS42_RUN_ID,
            "source_pass42_artifact_id": SOURCE_PASS42_ARTIFACT_ID,
            "source_pass42_artifact_sha256": SOURCE_PASS42_ARTIFACT_SHA256,
            "source_pass42_finding": SOURCE_PASS42_FINDING,
            "adapter_path": (
                "tools/blender_sprite_factory/"
                "blender_sprite_factory_attack_sword_twohand_up_"
                "f03_review_v21_pass43.py"
            ),
            "correction_path": (
                "tools/blender_sprite_factory/"
                "attack_sword_directional_cycle_correction_v21_pass43.py"
            ),
            "contact_sheet_name": CONTACT_SHEET_NAME,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass43_contract() -> None:
    pass42_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass42_adapter.TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION = (
        TWOHAND_UP_F03_DEPTH_CONTRACTION_REVIEW_REVISION
    )
    pass42_adapter.EXTENDED_SCREEN_PROJECTION_CANDIDATES = (
        DEPTH_CONTRACTION_PROJECTION_CANDIDATES
    )
    pass42_adapter.EXTENDED_ANGLE_OFFSET_CANDIDATES = (
        DEPTH_CONTRACTION_ANGLE_CANDIDATES
    )
    pass42_adapter.TARGETED_OFFSET_SPECS = TARGETED_DEPTH_SPECS
    pass42_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
    )
    pass42_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
    )
    pass42_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass42_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass42_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass42_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass42_adapter._write_manifest_v21_pass42 = _write_manifest_v21_pass43


def _restore_pass42_contract() -> None:
    pass42_adapter.CORRECTION_PASS = ORIGINAL_PASS42_CORRECTION_PASS
    pass42_adapter.TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION = (
        ORIGINAL_PASS42_REVISION
    )
    pass42_adapter.EXTENDED_SCREEN_PROJECTION_CANDIDATES = (
        ORIGINAL_PASS42_PROJECTIONS
    )
    pass42_adapter.EXTENDED_ANGLE_OFFSET_CANDIDATES = ORIGINAL_PASS42_OFFSETS
    pass42_adapter.TARGETED_OFFSET_SPECS = ORIGINAL_PASS42_TARGETED_SPECS
    pass42_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        ORIGINAL_PASS42_RENDER_EDGE_TOUCHING
    )
    pass42_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        ORIGINAL_PASS42_REQUIRE_ZERO_EDGES
    )
    pass42_adapter.CORRECTION_PATH = ORIGINAL_PASS42_CORRECTION_PATH
    pass42_adapter.SCRIPT_PATH = ORIGINAL_PASS42_SCRIPT_PATH
    pass42_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS42_SCENE_KEY
    pass42_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS42_CONTACT_SHEET_NAME
    pass42_adapter._write_manifest_v21_pass42 = ORIGINAL_PASS42_WRITE_MANIFEST


def main() -> int:
    _apply_pass43_contract()
    try:
        return pass42_adapter.main()
    finally:
        _restore_pass42_contract()


if __name__ == "__main__":
    raise SystemExit(main())
