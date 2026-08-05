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
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass44 as pass44_adapter
from attack_sword_directional_cycle_correction_v21_pass45 import (
    CAMERA_SHIFT_Y_CANDIDATES,
    CORRECTION_PASS,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    SELECTED_SCREEN_PROJECTION,
    SELECTED_WEAPON_OFFSET_DEGREES,
    SOURCE_PASS44_ARTIFACT_ID,
    SOURCE_PASS44_ARTIFACT_SHA256,
    SOURCE_PASS44_FINDING,
    SOURCE_PASS44_RUN_ID,
    TARGETED_OVERSCAN_SPECS,
    TWOHAND_UP_F03_CAMERA_OVERSCAN_REVIEW_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass45.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f03_review_v21_pass45"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f03_review_v21_pass45.png"
CAMERA_OBJECT_NAME = "CAM_gameplay_ortho"

ORIGINAL_RENDER_F03_CANDIDATE = pass38_adapter._render_f03_candidate
ORIGINAL_PASS44_CORRECTION_PASS = pass44_adapter.CORRECTION_PASS
ORIGINAL_PASS44_REVISION = (
    pass44_adapter.TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION
)
ORIGINAL_PASS44_PROJECTIONS = pass44_adapter.COMPACT_PROJECTION_CANDIDATES
ORIGINAL_PASS44_OFFSETS = pass44_adapter.COMPACT_ANGLE_OFFSET_CANDIDATES
ORIGINAL_PASS44_TARGETED_SPECS = pass44_adapter.TARGETED_COMPACT_SPECS
ORIGINAL_PASS44_RENDER_EDGE_TOUCHING = (
    pass44_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
)
ORIGINAL_PASS44_REQUIRE_ZERO_EDGES = (
    pass44_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
)
ORIGINAL_PASS44_CORRECTION_PATH = pass44_adapter.CORRECTION_PATH
ORIGINAL_PASS44_SCRIPT_PATH = pass44_adapter.SCRIPT_PATH
ORIGINAL_PASS44_SCENE_KEY = pass44_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS44_CONTACT_SHEET_NAME = pass44_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS44_WRITE_MANIFEST = pass44_adapter._write_manifest_v21_pass44


def _render_f03_candidate_v21_pass45(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    action: object,
    target_f03_rotations: dict[str, object],
    source_rotations: dict[str, object],
    candidate: dict[str, object],
    variant_index: int,
) -> tuple[factory.FrameArtifact, dict[str, object]]:
    if not 1 <= variant_index <= len(CAMERA_SHIFT_Y_CANDIDATES):
        raise RuntimeError(
            "two-hand up f03 pass45 variant index is outside camera shift grid: "
            f"{variant_index}"
        )
    camera = factory.bpy.data.objects.get(CAMERA_OBJECT_NAME)
    if camera is None or camera.data is None:
        raise RuntimeError("two-hand up f03 pass45 gameplay camera is missing")
    original_shift_y = float(camera.data.shift_y)
    shift_y = float(CAMERA_SHIFT_Y_CANDIDATES[variant_index - 1])
    camera.data.shift_y = shift_y
    factory.bpy.context.view_layer.update()
    try:
        artifact, metadata = ORIGINAL_RENDER_F03_CANDIDATE(
            context,
            run_dir,
            calibration=calibration,
            action=action,
            target_f03_rotations=target_f03_rotations,
            source_rotations=source_rotations,
            candidate=candidate,
            variant_index=variant_index,
        )
        enriched = dict(metadata)
        enriched["camera_shift_y"] = shift_y
        enriched["camera_shift_restored_after_render"] = True
        print(
            "ATTACK_SWORD_TWOHAND_UP_F03_CAMERA_OVERSCAN_V21_PASS45="
            f"variant:{variant_index};shift_y:{shift_y:.3f};"
            f"projection:{float(candidate['requested_screen_projection']):.3f};"
            f"offset:{float(candidate['offset_degrees']):.1f}"
        )
        return artifact, enriched
    finally:
        camera.data.shift_y = original_shift_y
        factory.bpy.context.view_layer.update()


def _write_manifest_v21_pass45(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS44_WRITE_MANIFEST(
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
        raise RuntimeError("two-hand up f03 pass45 review manifest is invalid")
    review.update(
        {
            "camera_shift_y_candidates": list(CAMERA_SHIFT_Y_CANDIDATES),
            "targeted_overscan_specs": list(TARGETED_OVERSCAN_SPECS),
            "selected_screen_projection": SELECTED_SCREEN_PROJECTION,
            "selected_weapon_offset_degrees": SELECTED_WEAPON_OFFSET_DEGREES,
            "selection_strategy": (
                "use the smallest temporary positive camera shift_y that keeps "
                "the complete raw sword inside the render while preserving the "
                "approved output scale, baseline, camera rotation and arm pose"
            ),
            "camera_shift_persistent_change": False,
            "manual_selection_required": True,
        }
    )
    payload[DIAGNOSTIC_SCENE_KEY] = review
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F03_CAMERA_OVERSCAN_REVIEW_REVISION,
            "source_pass44_run_id": SOURCE_PASS44_RUN_ID,
            "source_pass44_artifact_id": SOURCE_PASS44_ARTIFACT_ID,
            "source_pass44_artifact_sha256": SOURCE_PASS44_ARTIFACT_SHA256,
            "source_pass44_finding": SOURCE_PASS44_FINDING,
            "adapter_path": (
                "tools/blender_sprite_factory/"
                "blender_sprite_factory_attack_sword_twohand_up_"
                "f03_review_v21_pass45.py"
            ),
            "correction_path": (
                "tools/blender_sprite_factory/"
                "attack_sword_directional_cycle_correction_v21_pass45.py"
            ),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "camera_object_name": CAMERA_OBJECT_NAME,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass45_contract() -> None:
    pass38_adapter._render_f03_candidate = _render_f03_candidate_v21_pass45
    pass44_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass44_adapter.TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION = (
        TWOHAND_UP_F03_CAMERA_OVERSCAN_REVIEW_REVISION
    )
    pass44_adapter.COMPACT_PROJECTION_CANDIDATES = (SELECTED_SCREEN_PROJECTION,)
    pass44_adapter.COMPACT_ANGLE_OFFSET_CANDIDATES = (
        SELECTED_WEAPON_OFFSET_DEGREES,
    )
    pass44_adapter.TARGETED_COMPACT_SPECS = TARGETED_OVERSCAN_SPECS
    pass44_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
    )
    pass44_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE
    )
    pass44_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass44_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass44_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass44_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass44_adapter._write_manifest_v21_pass44 = _write_manifest_v21_pass45


def _restore_pass44_contract() -> None:
    pass38_adapter._render_f03_candidate = ORIGINAL_RENDER_F03_CANDIDATE
    pass44_adapter.CORRECTION_PASS = ORIGINAL_PASS44_CORRECTION_PASS
    pass44_adapter.TWOHAND_UP_F03_COMPACT_PROJECTION_REVIEW_REVISION = (
        ORIGINAL_PASS44_REVISION
    )
    pass44_adapter.COMPACT_PROJECTION_CANDIDATES = ORIGINAL_PASS44_PROJECTIONS
    pass44_adapter.COMPACT_ANGLE_OFFSET_CANDIDATES = ORIGINAL_PASS44_OFFSETS
    pass44_adapter.TARGETED_COMPACT_SPECS = ORIGINAL_PASS44_TARGETED_SPECS
    pass44_adapter.RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW = (
        ORIGINAL_PASS44_RENDER_EDGE_TOUCHING
    )
    pass44_adapter.REQUIRE_ZERO_EDGE_ALPHA_FOR_ACCEPTANCE = (
        ORIGINAL_PASS44_REQUIRE_ZERO_EDGES
    )
    pass44_adapter.CORRECTION_PATH = ORIGINAL_PASS44_CORRECTION_PATH
    pass44_adapter.SCRIPT_PATH = ORIGINAL_PASS44_SCRIPT_PATH
    pass44_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS44_SCENE_KEY
    pass44_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS44_CONTACT_SHEET_NAME
    pass44_adapter._write_manifest_v21_pass44 = ORIGINAL_PASS44_WRITE_MANIFEST


def main() -> int:
    _apply_pass45_contract()
    try:
        return pass44_adapter.main()
    finally:
        _restore_pass44_contract()


if __name__ == "__main__":
    raise SystemExit(main())
