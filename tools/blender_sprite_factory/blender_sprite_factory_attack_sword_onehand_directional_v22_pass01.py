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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass56 as pass56_adapter
from attack_sword_onehand_directional_builder_v22_pass01 import (
    create_attack_sword_onehand_directional_actions_v22_pass01,
)
from attack_sword_onehand_directional_correction_v22_pass01 import (
    APPROVED_TWOHAND_ARTIFACT_ID,
    APPROVED_TWOHAND_ARTIFACT_SHA256,
    APPROVED_TWOHAND_BASELINE_COMMIT,
    APPROVED_TWOHAND_WORKFLOW_RUN_ID,
    BONE_DELTAS_DEGREES_BY_DIRECTION,
    CORRECTION_PASS,
    FRAME_WEIGHTS,
    MATERIALS_CHANGED,
    MIRRORING_USED,
    NEGATIVE_SCALE_USED,
    ONEHAND_DIRECTIONAL_REVISION,
    PRESERVE_DOWN_PIXELS,
    PRESERVE_SOURCE_FCURVE_TIMING,
    PRESERVE_TWOHAND_BASELINE,
    ROOT_TRANSLATION_USED,
    SOURCE_MASTER_ACTION_ID,
    TARGET_ACTION_ID_BY_DIRECTION,
    TARGET_DIRECTIONS,
    TARGET_FRAMES,
    WEAPON_GEOMETRY_CHANGED,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_onehand_directional_correction_v22_pass01.py"
)
BUILDER_PATH = (
    SCRIPT_DIR / "attack_sword_onehand_directional_builder_v22_pass01.py"
)
MANIFEST_KEY = "attack_sword_onehand_directional_v22_pass01"

ORIGINAL_PASS54_CREATE_ACTIONS = (
    pass54_adapter.create_attack_sword_directional_cycle_actions_v21_pass54
)
ORIGINAL_PASS56_WRITE_MANIFEST = pass56_adapter._write_manifest_v21_pass56


def _write_manifest_v22_pass01(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_PASS56_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    expected_action_ids = set(TARGET_ACTION_ID_BY_DIRECTION.values())
    target_artifacts = [
        artifact
        for artifact in artifacts
        if any(
            f"_{action_id}_f" in artifact.output_path.name
            for action_id in expected_action_ids
        )
    ]
    expected_target_count = len(TARGET_DIRECTIONS) * 8
    if len(target_artifacts) != expected_target_count:
        raise RuntimeError(
            "onehand directional v22 expected 24 target frames, found "
            f"{len(target_artifacts)}"
        )

    action_metadata: dict[str, object] = {}
    for direction in TARGET_DIRECTIONS:
        action_id = TARGET_ACTION_ID_BY_DIRECTION[direction]
        action = factory.bpy.data.actions.get(
            f"{context.config.character_id}_{action_id}"
        )
        if action is None:
            raise RuntimeError(
                f"onehand directional v22 manifest action missing: {action_id}"
            )
        if str(action.get("onehand_directional_revision", "")) != (
            ONEHAND_DIRECTIONAL_REVISION
        ):
            raise RuntimeError(
                f"onehand directional v22 revision drifted: {action_id}"
            )
        action_metadata[direction] = {
            "action_id": action_id,
            "source_action_id": str(
                action.get("onehand_directional_source_action_id", "")
            ),
            "source_timing_preserved": bool(
                action.get(
                    "onehand_directional_source_timing_preserved",
                    False,
                )
            ),
            "corrected_frames": str(
                action.get("onehand_directional_corrected_frames", "")
            ),
            "action_only": bool(
                action.get("onehand_directional_action_only", False)
            ),
        }

    payload[MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": ONEHAND_DIRECTIONAL_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(
            BUILDER_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(
            SCRIPT_PATH.read_bytes()
        ).hexdigest(),
        "source_master_action_id": SOURCE_MASTER_ACTION_ID,
        "target_directions": list(TARGET_DIRECTIONS),
        "target_action_ids": TARGET_ACTION_ID_BY_DIRECTION,
        "target_frames": list(TARGET_FRAMES),
        "frame_weights": {
            str(frame): weight for frame, weight in FRAME_WEIGHTS.items()
        },
        "bone_deltas_degrees_by_direction": {
            direction: {
                bone: list(values)
                for bone, values in (
                    BONE_DELTAS_DEGREES_BY_DIRECTION[direction].items()
                )
            }
            for direction in TARGET_DIRECTIONS
        },
        "action_metadata": action_metadata,
        "target_rendered_frame_count": len(target_artifacts),
        "source_fcurve_timing_preserved": PRESERVE_SOURCE_FCURVE_TIMING,
        "approved_down_pixels_preserved": PRESERVE_DOWN_PIXELS,
        "approved_twohand_baseline_preserved": PRESERVE_TWOHAND_BASELINE,
        "approved_twohand_baseline_commit": APPROVED_TWOHAND_BASELINE_COMMIT,
        "approved_twohand_workflow_run_id": APPROVED_TWOHAND_WORKFLOW_RUN_ID,
        "approved_twohand_artifact_id": APPROVED_TWOHAND_ARTIFACT_ID,
        "approved_twohand_artifact_sha256": APPROVED_TWOHAND_ARTIFACT_SHA256,
        "root_translation_used": ROOT_TRANSLATION_USED,
        "mirroring_used": MIRRORING_USED,
        "negative_scale_used": NEGATIVE_SCALE_USED,
        "weapon_geometry_changed": WEAPON_GEOMETRY_CHANGED,
        "materials_changed": MATERIALS_CHANGED,
        "runtime_connected": False,
        "manual_directional_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": (
                "onehand_directional_v22_pass01_local_corrections"
            ),
            "attack_sword_01_onehand_directional_revision": (
                ONEHAND_DIRECTIONAL_REVISION
            ),
            "attack_sword_01_onehand_source_action_id": SOURCE_MASTER_ACTION_ID,
            "attack_sword_01_onehand_target_rendered_frames": len(target_artifacts),
            "attack_sword_01_twohand_approved_baseline_preserved": True,
            "attack_sword_01_runtime_connected": False,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_v22_contract() -> None:
    pass54_adapter.create_attack_sword_directional_cycle_actions_v21_pass54 = (
        create_attack_sword_onehand_directional_actions_v22_pass01
    )
    pass56_adapter._write_manifest_v21_pass56 = _write_manifest_v22_pass01


def _restore_v22_contract() -> None:
    pass54_adapter.create_attack_sword_directional_cycle_actions_v21_pass54 = (
        ORIGINAL_PASS54_CREATE_ACTIONS
    )
    pass56_adapter._write_manifest_v21_pass56 = ORIGINAL_PASS56_WRITE_MANIFEST


def main() -> int:
    _apply_v22_contract()
    try:
        return pass56_adapter.main()
    finally:
        _restore_v22_contract()


if __name__ == "__main__":
    raise SystemExit(main())
