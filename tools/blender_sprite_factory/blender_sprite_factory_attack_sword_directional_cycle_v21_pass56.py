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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass54 as pass54_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass55 as pass55_adapter
from attack_sword_directional_cycle_correction_v21_pass56 import (
    BOUNDARY_FIX_PRESERVED,
    CORRECTION_PASS,
    FRONT_DEPTH_SELECTION_PRESERVED,
    MAX_BLENDER_IDPROPERTY_NAME_LENGTH,
    SHORT_CLEARANCE_SCENE_KEY,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_COMMIT,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TWOHAND_UP_FRONT_DEPTH_CONTRACT_REVISION,
    VISUAL_OUTPUT_CHANGED_FROM_PASS55,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass56.py"
)
PASS56_MANIFEST_KEY = "attack_sword_directional_cycle_v21_pass56"
ORIGINAL_PASS54_VALIDATE = pass54_adapter._validate_directional_clearance_v21_pass54
ORIGINAL_PASS55_WRITE_MANIFEST = pass55_adapter._write_manifest_v21_pass55


def _validate_directional_clearance_v21_pass56(
    context: factory.BuildContext,
    *,
    action_id: str,
    grip_id: str,
    weapon_cycle_id: str,
    direction: str,
) -> dict[int, float]:
    if not (
        action_id == pass54_adapter.TARGET_ACTION_ID
        and grip_id == pass54_adapter.TARGET_GRIP_ID
        and direction == pass54_adapter.TARGET_DIRECTION
    ):
        return pass54_adapter.ORIGINAL_PASS02_VALIDATE_CLEARANCE(
            context,
            action_id=action_id,
            grip_id=grip_id,
            weapon_cycle_id=weapon_cycle_id,
            direction=direction,
        )

    metrics = json.loads(
        str(
            factory.bpy.context.scene.get(
                pass54_adapter.METRICS_SCENE_KEY,
                "{}",
            )
        )
    )
    clearances: dict[int, float] = {}
    for frame_number in (2, 3, 4):
        key = (
            f"{pass54_adapter.TARGET_GRIP_ID}/"
            f"{pass54_adapter.TARGET_DIRECTION}/f{frame_number:02d}"
        )
        if key not in metrics:
            raise RuntimeError(
                "attack sword directional v21 pass56 clearance metrics missing: "
                f"{key}"
            )
        edge_counts = {
            str(edge): int(value)
            for edge, value in dict(metrics[key]["edge_counts"]).items()
        }
        if any(edge_counts.values()):
            raise RuntimeError(
                "attack sword directional v21 pass56 clearance frame touched "
                f"edge: {key}={edge_counts}"
            )
        clearances[frame_number] = float(
            metrics[key]["head_clearance_pixels"]
        )

    if len(SHORT_CLEARANCE_SCENE_KEY) > MAX_BLENDER_IDPROPERTY_NAME_LENGTH:
        raise RuntimeError(
            "attack sword directional v21 pass56 scene key exceeds Blender "
            "IDProperty limit"
        )
    factory.bpy.context.scene[SHORT_CLEARANCE_SCENE_KEY] = True
    return clearances


def _write_manifest_v21_pass56(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_PASS55_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene_value = bool(
        factory.bpy.context.scene.get(SHORT_CLEARANCE_SCENE_KEY, False)
    )
    if not scene_value:
        raise RuntimeError(
            "attack sword directional v21 pass56 short clearance contract "
            "was not recorded"
        )

    payload[PASS56_MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": TWOHAND_UP_FRONT_DEPTH_CONTRACT_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "short_clearance_scene_key": SHORT_CLEARANCE_SCENE_KEY,
        "short_clearance_scene_key_length": len(SHORT_CLEARANCE_SCENE_KEY),
        "maximum_blender_idproperty_name_length": (
            MAX_BLENDER_IDPROPERTY_NAME_LENGTH
        ),
        "short_clearance_contract_recorded": scene_value,
        "visual_output_changed_from_pass55": VISUAL_OUTPUT_CHANGED_FROM_PASS55,
        "front_depth_selection_preserved": FRONT_DEPTH_SELECTION_PRESERVED,
        "boundary_fix_preserved": BOUNDARY_FIX_PRESERVED,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failed_commit": SOURCE_FAILED_COMMIT,
        "source_failure": SOURCE_FAILURE,
        "approved_down_v20_changed": False,
        "left_direction_changed": False,
        "right_direction_changed": False,
        "onehand_up_changed": False,
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
                "directional_full_cycle_v21_pass56_front_depth_contract"
            ),
            "attack_sword_01_twohand_up_front_depth_contract_revision": (
                TWOHAND_UP_FRONT_DEPTH_CONTRACT_REVISION
            ),
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_pass56_contract() -> None:
    pass54_adapter._validate_directional_clearance_v21_pass54 = (
        _validate_directional_clearance_v21_pass56
    )
    pass55_adapter._write_manifest_v21_pass55 = _write_manifest_v21_pass56


def _restore_pass56_contract() -> None:
    pass54_adapter._validate_directional_clearance_v21_pass54 = (
        ORIGINAL_PASS54_VALIDATE
    )
    pass55_adapter._write_manifest_v21_pass55 = ORIGINAL_PASS55_WRITE_MANIFEST


def main() -> int:
    _apply_pass56_contract()
    try:
        return pass55_adapter.main()
    finally:
        _restore_pass56_contract()


if __name__ == "__main__":
    raise SystemExit(main())
