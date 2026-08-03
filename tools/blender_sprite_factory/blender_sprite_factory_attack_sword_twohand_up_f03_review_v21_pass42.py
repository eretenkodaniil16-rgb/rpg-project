from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass41 as pass41_adapter
from attack_sword_directional_cycle_correction_v21_pass42 import (
    CORRECTION_PASS,
    EXTENDED_ANGLE_OFFSET_CANDIDATES,
    EXTENDED_SCREEN_PROJECTION_CANDIDATES,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SOURCE_PASS41_ARTIFACT_ID,
    SOURCE_PASS41_ARTIFACT_SHA256,
    SOURCE_PASS41_FINDING,
    SOURCE_PASS41_RUN_ID,
    TARGETED_OFFSET_SPECS,
    TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass42.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f03_review_v21_pass42"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f03_review_v21_pass42.png"

ORIGINAL_PASS41_CORRECTION_PASS = pass41_adapter.CORRECTION_PASS
ORIGINAL_PASS41_REVISION = pass41_adapter.TWOHAND_UP_F03_FINE_OFFSET_REVIEW_REVISION
ORIGINAL_PASS41_PROJECTIONS = pass41_adapter.FINE_SCREEN_PROJECTION_CANDIDATES
ORIGINAL_PASS41_OFFSETS = pass41_adapter.FINE_ANGLE_OFFSET_CANDIDATES
ORIGINAL_PASS41_TARGETED_SPECS = pass41_adapter.TARGETED_OFFSET_SPECS
ORIGINAL_PASS41_RENDER_EDGE_TOUCHING = (
    pass41_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
)
ORIGINAL_PASS41_REQUIRE_ZERO_EDGES = (
    pass41_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
)
ORIGINAL_PASS41_CORRECTION_PATH = pass41_adapter.CORRECTION_PATH
ORIGINAL_PASS41_SCRIPT_PATH = pass41_adapter.SCRIPT_PATH
ORIGINAL_PASS41_SCENE_KEY = pass41_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS41_CONTACT_SHEET_NAME = pass41_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS41_WRITE_MANIFEST = pass41_adapter._write_manifest_v21_pass41


def _write_manifest_v21_pass42(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS41_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up f03 pass42 review manifest is invalid")
    review.update(
        {
            "extended_screen_projection_candidates": list(
                EXTENDED_SCREEN_PROJECTION_CANDIDATES
            ),
            "extended_angle_offset_candidates": list(
                EXTENDED_ANGLE_OFFSET_CANDIDATES
            ),
            "targeted_offset_specs": list(TARGETED_OFFSET_SPECS),
            "selection_strategy": (
                "keep the pass41 original_f05 blend 0.60 pose and projection "
                "0.45, then extend only the clockwise screen-space blade angle "
                "until the complete rigid sword clears the top edge without "
                "touching the right edge"
            ),
            "manual_selection_required": True,
        }
    )
    payload[DIAGNOSTIC_SCENE_KEY] = review
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION,
            "source_pass41_run_id": SOURCE_PASS41_RUN_ID,
            "source_pass41_artifact_id": SOURCE_PASS41_ARTIFACT_ID,
            "source_pass41_artifact_sha256": SOURCE_PASS41_ARTIFACT_SHA256,
            "source_pass41_finding": SOURCE_PASS41_FINDING,
            "adapter_path": (
                "tools/blender_sprite_factory/"
                "blender_sprite_factory_attack_sword_twohand_up_"
                "f03_review_v21_pass42.py"
            ),
            "correction_path": (
                "tools/blender_sprite_factory/"
                "attack_sword_directional_cycle_correction_v21_pass42.py"
            ),
            "contact_sheet_name": CONTACT_SHEET_NAME,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass42_contract() -> None:
    pass41_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass41_adapter.TWOHAND_UP_F03_FINE_OFFSET_REVIEW_REVISION = (
        TWOHAND_UP_F03_EXTENDED_OFFSET_REVIEW_REVISION
    )
    pass41_adapter.FINE_SCREEN_PROJECTION_CANDIDATES = (
        EXTENDED_SCREEN_PROJECTION_CANDIDATES
    )
    pass41_adapter.FINE_ANGLE_OFFSET_CANDIDATES = (
        EXTENDED_ANGLE_OFFSET_CANDIDATES
    )
    pass41_adapter.TARGETED_OFFSET_SPECS = TARGETED_OFFSET_SPECS
    pass41_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
    )
    pass41_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
    )
    pass41_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass41_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass41_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass41_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass41_adapter._write_manifest_v21_pass41 = _write_manifest_v21_pass42


def _restore_pass41_contract() -> None:
    pass41_adapter.CORRECTION_PASS = ORIGINAL_PASS41_CORRECTION_PASS
    pass41_adapter.TWOHAND_UP_F03_FINE_OFFSET_REVIEW_REVISION = (
        ORIGINAL_PASS41_REVISION
    )
    pass41_adapter.FINE_SCREEN_PROJECTION_CANDIDATES = (
        ORIGINAL_PASS41_PROJECTIONS
    )
    pass41_adapter.FINE_ANGLE_OFFSET_CANDIDATES = ORIGINAL_PASS41_OFFSETS
    pass41_adapter.TARGETED_OFFSET_SPECS = ORIGINAL_PASS41_TARGETED_SPECS
    pass41_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        ORIGINAL_PASS41_RENDER_EDGE_TOUCHING
    )
    pass41_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        ORIGINAL_PASS41_REQUIRE_ZERO_EDGES
    )
    pass41_adapter.CORRECTION_PATH = ORIGINAL_PASS41_CORRECTION_PATH
    pass41_adapter.SCRIPT_PATH = ORIGINAL_PASS41_SCRIPT_PATH
    pass41_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS41_SCENE_KEY
    pass41_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS41_CONTACT_SHEET_NAME
    pass41_adapter._write_manifest_v21_pass41 = ORIGINAL_PASS41_WRITE_MANIFEST


def main() -> int:
    _apply_pass42_contract()
    try:
        return pass41_adapter.main()
    finally:
        _restore_pass41_contract()


if __name__ == "__main__":
    raise SystemExit(main())
