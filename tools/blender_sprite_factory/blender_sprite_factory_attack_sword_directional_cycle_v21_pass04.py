from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass03 as pass03_adapter
from attack_sword_directional_cycle_builder_v21_pass03 import (
    BONE_DELTAS_DEGREES,
)
from attack_sword_directional_cycle_builder_v21_pass04 import (
    create_attack_sword_directional_cycle_actions_v21_pass04,
)
from attack_sword_directional_cycle_correction_v21_pass04 import (
    ANTICIPATION_CLEARANCE_REVISION,
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_ARTIFACT_SHA256,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    SELECTED_ATTEMPT,
    SELECTED_CAMERA_MARGIN_PIXELS,
    SELECTED_HEAD_CLEARANCE_PIXELS,
    SELECTED_INCREMENTAL_WEIGHT,
    SELECTED_TOTAL_WEIGHT,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass04.py"
)
BUILDER_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_builder_v21_pass04.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
BASE_WRITE_MANIFEST_PASS03 = pass03_adapter._write_manifest_v21_pass03


def _write_manifest_v21_pass04(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS03(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_{TARGET_ACTION_ID}"
    )
    if action is None:
        raise RuntimeError(
            "attack sword directional v21 pass04 manifest action is missing"
        )
    if (
        action.get("directional_anticipation_revision")
        != ANTICIPATION_CLEARANCE_REVISION
    ):
        raise RuntimeError(
            "attack sword directional v21 pass04 action metadata drifted"
        )

    payload["attack_sword_directional_cycle_v21_pass04"] = {
        "correction_pass": CORRECTION_PASS,
        "anticipation_clearance_revision": ANTICIPATION_CLEARANCE_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(
            run_dir / CONTACT_SHEET_NAME
        ),
        "target_action_id": TARGET_ACTION_ID,
        "target_grip_id": TARGET_GRIP_ID,
        "target_direction": TARGET_DIRECTION,
        "target_frame": TARGET_FRAME,
        "selected_total_weight": SELECTED_TOTAL_WEIGHT,
        "selected_incremental_weight": SELECTED_INCREMENTAL_WEIGHT,
        "bone_deltas_degrees_at_full_weight": BONE_DELTAS_DEGREES,
        "validated_head_clearance_pixels": SELECTED_HEAD_CLEARANCE_PIXELS,
        "validated_camera_margin_pixels": SELECTED_CAMERA_MARGIN_PIXELS,
        "minimum_head_clearance_pixels": MIN_HEAD_CLEARANCE_PIXELS,
        "minimum_camera_margin_pixels": MIN_CAMERA_MARGIN_PIXELS,
        "selected_diagnostic_attempt": SELECTED_ATTEMPT,
        "diagnostic_run_id": DIAGNOSTIC_RUN_ID,
        "diagnostic_artifact_id": DIAGNOSTIC_ARTIFACT_ID,
        "diagnostic_artifact_sha256": DIAGNOSTIC_ARTIFACT_SHA256,
        "diagnostic_frame_size": list(DIAGNOSTIC_FRAME_SIZE),
        "diagnostic_alpha_bbox": list(DIAGNOSTIC_ALPHA_BBOX),
        "diagnostic_edge_alpha_counts": DIAGNOSTIC_EDGE_ALPHA_COUNTS,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "action_data_changed": True,
        "body_scope": ["upper_arm.R", "forearm.R", "hand.R"],
        "approved_down_v20_changed": False,
        "other_direction_actions_changed": False,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_directional_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": (
                "directional_full_cycle_v21_pass04"
            ),
            "attack_sword_01_left_onehand_anticipation_fixed": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    pass03_adapter.create_attack_sword_directional_cycle_actions_v21_pass03 = (
        create_attack_sword_directional_cycle_actions_v21_pass04
    )
    pass03_adapter._write_manifest_v21_pass03 = _write_manifest_v21_pass04
    return pass03_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
