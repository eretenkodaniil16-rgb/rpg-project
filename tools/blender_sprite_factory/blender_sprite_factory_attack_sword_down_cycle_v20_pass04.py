from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as previous_adapter
from attack_sword_down_cycle_correction_v20_pass04 import (
    ANGLE_CANDIDATES_DEGREES,
    CORRECTION_PASS,
    KNOWN_FAILED_ARTIFACT_ID,
    KNOWN_FAILED_ARTIFACT_SHA256,
    KNOWN_FAILED_OFFSET_MAX_DEGREES,
    KNOWN_FAILED_OFFSET_MIN_DEGREES,
    KNOWN_FAILED_RUN_ID,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_CONTAINMENT_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_cycle_correction_v20_pass04.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_cycle_v20.png"
BASE_WRITE_MANIFEST_V20_PASS03 = previous_adapter._write_manifest_v20_pass03


def _candidate_offsets_v20_pass04(
    objects: tuple[object, ...],
    *,
    saved_basis: dict[str, object],
    pivot: object,
    current_direction: object,
) -> tuple[float, ...]:
    del objects, saved_basis, pivot, current_direction
    return ANGLE_CANDIDATES_DEGREES


def _write_manifest_v20_pass04(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_V20_PASS03(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene = previous_adapter.factory.bpy.context.scene
    payload["attack_sword_down_cycle_v20_pass04"] = {
        "correction_pass": CORRECTION_PASS,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(run_dir / CONTACT_SHEET_NAME),
        "onehand_containment_revision": ONEHAND_CONTAINMENT_REVISION,
        "target_animation_id": TARGET_ANIMATION_ID,
        "target_frame": TARGET_FRAME,
        "angle_candidates_degrees": list(ANGLE_CANDIDATES_DEGREES),
        "selected_angle_offset_degrees": float(
            scene["attack_sword_down_cycle_v20_pass03_angle_offset_degrees"]
        ),
        "head_clearance_pixels": float(
            scene["attack_sword_down_cycle_v20_pass03_head_clearance"]
        ),
        "projected_min_x": float(
            scene["attack_sword_down_cycle_v20_pass03_projected_min_x"]
        ),
        "projection_before": float(
            scene["attack_sword_down_cycle_v20_pass03_projection_before"]
        ),
        "projection_after": float(
            scene["attack_sword_down_cycle_v20_pass03_projection_after"]
        ),
        "render_attempts": int(
            scene["attack_sword_down_cycle_v20_pass03_render_attempts"]
        ),
        "edge_counts": json.loads(
            str(scene["attack_sword_down_cycle_v20_pass03_edge_counts"])
        ),
        "candidate_diagnostics": json.loads(
            str(scene["attack_sword_down_cycle_v20_pass03_diagnostics"])
        ),
        "minimum_head_clearance_pixels": MIN_HEAD_CLEARANCE_PIXELS,
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "known_failed_pass03": {
            "run_id": KNOWN_FAILED_RUN_ID,
            "artifact_id": KNOWN_FAILED_ARTIFACT_ID,
            "artifact_sha256": KNOWN_FAILED_ARTIFACT_SHA256,
            "offset_min_degrees": KNOWN_FAILED_OFFSET_MIN_DEGREES,
            "offset_max_degrees": KNOWN_FAILED_OFFSET_MAX_DEGREES,
        },
        "export_space_validated": True,
        "body_pose_changed": False,
        "approved_v19_anchor_frames_changed": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_full_cycle_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_full_cycle_v20_pass04",
            "attack_sword_01_onehand_rebound_export_contained": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter._candidate_offsets = _candidate_offsets_v20_pass04
    previous_adapter._write_manifest_v20_pass03 = _write_manifest_v20_pass04
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
