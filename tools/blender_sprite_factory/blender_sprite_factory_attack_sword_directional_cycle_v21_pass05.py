from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21 as base_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass04 as pass04_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
from attack_sword_directional_cycle_builder_v21_pass05 import (
    create_attack_sword_directional_cycle_actions_v21_pass05,
)
from attack_sword_directional_cycle_correction_v21_pass05 import (
    ARM_ONLY_DIAGNOSTIC_ARTIFACT_ID,
    ARM_ONLY_DIAGNOSTIC_ARTIFACT_SHA256,
    ARM_ONLY_DIAGNOSTIC_MAX_CLEARANCE_PIXELS,
    ARM_ONLY_DIAGNOSTIC_RUN_ID,
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_ARTIFACT_SHA256,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    RECOVERY_CLEARANCE_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_ARM_BLEND,
    SELECTED_ATTEMPT,
    SELECTED_CAMERA_MARGIN_PIXELS,
    SELECTED_HEAD_CLEARANCE_PIXELS,
    SELECTED_WEAPON_OFFSET_DEGREES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass05.py"
)
BUILDER_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_builder_v21_pass05.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
BASE_RENDER_FRAME_PASS02 = pass02_adapter._render_frame_v21_pass02
BASE_WRITE_MANIFEST_PASS04 = pass04_adapter._write_manifest_v21_pass04


def _is_target_frame(
    animation_id: str,
    direction: str,
    frame_number: int,
) -> bool:
    return (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number == TARGET_FRAME
    )


def _render_frame_v21_pass05(
    context: factory.BuildContext,
    *,
    animation_id: str,
    direction: str,
    frame_number: int,
    raw_dir: Path,
    frame_dir: Path,
    output_name: str,
    fixed_scale: float | None,
    fixed_center_x: float | None,
    use_clearance_planner: bool,
) -> tuple[factory.FrameArtifact, factory.FramingCalibration]:
    if not _is_target_frame(animation_id, direction, frame_number):
        return BASE_RENDER_FRAME_PASS02(
            context,
            animation_id=animation_id,
            direction=direction,
            frame_number=frame_number,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=output_name,
            fixed_scale=fixed_scale,
            fixed_center_x=fixed_center_x,
            use_clearance_planner=use_clearance_planner,
        )

    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_{TARGET_ACTION_ID}"
    )
    if action is None:
        raise RuntimeError(
            "attack sword directional v21 pass05 target action is missing"
        )
    if action.get("directional_recovery_revision") != RECOVERY_CLEARANCE_REVISION:
        raise RuntimeError(
            "attack sword directional v21 pass05 recovery metadata drifted"
        )
    if not math.isclose(
        float(action.get("directional_recovery_arm_blend", -1.0)),
        SELECTED_ARM_BLEND,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "attack sword directional v21 pass05 arm blend drifted"
        )

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    objects = base_adapter._visible_weapon_objects(TARGET_GRIP_ID, direction)
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = pass02_adapter._weapon_world_direction(objects)
    pivot = pass02_adapter._weapon_pivot(objects)
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=export_adapter._target_direction(
            current_direction,
            offset_degrees=SELECTED_WEAPON_OFFSET_DEGREES,
        ),
    )
    try:
        clearance = export_adapter._weapon_head_clearance(objects)
        margin = pass02_adapter._camera_margin(objects)
        if clearance < MIN_HEAD_CLEARANCE_PIXELS:
            raise RuntimeError(
                "attack sword directional v21 pass05 head clearance drifted: "
                f"{clearance:.3f}px"
            )
        if margin < MIN_CAMERA_MARGIN_PIXELS:
            raise RuntimeError(
                "attack sword directional v21 pass05 camera margin drifted: "
                f"{margin:.3f}px"
            )
        artifact, calibration = export_adapter._render_candidate(
            context,
            animation_id=animation_id,
            direction=direction,
            frame_number=frame_number,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=output_name,
            fixed_scale=fixed_scale,
            fixed_center_x=fixed_center_x,
        )
        edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
        touched = {
            edge: count
            for edge, count in edge_counts.items()
            if count > 0
        }
        if REQUIRE_ZERO_EDGE_ALPHA and touched:
            raise RuntimeError(
                "attack sword directional v21 pass05 target frame touched export "
                f"edges: {touched}"
            )
    finally:
        pass06_adapter._restore_weapon(saved_basis)

    metrics_raw = str(
        scene.get("attack_sword_directional_cycle_v21_pass02_metrics", "{}")
    )
    metrics = json.loads(metrics_raw)
    key = f"{TARGET_GRIP_ID}/{direction}/f{frame_number:02d}"
    metrics[key] = {
        "offset_degrees": SELECTED_WEAPON_OFFSET_DEGREES,
        "head_clearance_pixels": float(clearance),
        "camera_margin_pixels": float(margin),
        "edge_counts": edge_counts,
        "render_attempts": 1,
        "candidate_diagnostics": [
            {
                "attempt": 1,
                "arm_blend": SELECTED_ARM_BLEND,
                "offset_degrees": SELECTED_WEAPON_OFFSET_DEGREES,
                "head_clearance_pixels": float(clearance),
                "camera_margin_pixels": float(margin),
                "edge_counts": edge_counts,
                "accepted": True,
            }
        ],
        "pass05_arm_blend": SELECTED_ARM_BLEND,
    }
    scene["attack_sword_directional_cycle_v21_pass02_metrics"] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_DIRECTIONAL_V21_PASS05_SELECTED="
        f"{key};"
        f"blend:{SELECTED_ARM_BLEND:.2f};"
        f"offset:{SELECTED_WEAPON_OFFSET_DEGREES:.1f}deg;"
        f"clearance:{float(clearance):.3f}px;"
        f"margin:{float(margin):.3f}px;"
        f"edges:{touched}"
    )
    return artifact, calibration


def _write_manifest_v21_pass05(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS04(
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
            "attack sword directional v21 pass05 manifest action is missing"
        )
    if action.get("directional_recovery_revision") != RECOVERY_CLEARANCE_REVISION:
        raise RuntimeError(
            "attack sword directional v21 pass05 manifest metadata drifted"
        )

    metrics = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_directional_cycle_v21_pass02_metrics"
            ]
        )
    )
    target_key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{TARGET_FRAME:02d}"
    if target_key not in metrics:
        raise RuntimeError(
            "attack sword directional v21 pass05 target metrics are missing"
        )

    payload["attack_sword_directional_cycle_v21_pass05"] = {
        "correction_pass": CORRECTION_PASS,
        "recovery_clearance_revision": RECOVERY_CLEARANCE_REVISION,
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
        "guard_frame": GUARD_FRAME,
        "body_scope": list(TARGET_BONES),
        "selected_arm_blend": SELECTED_ARM_BLEND,
        "selected_weapon_offset_degrees": SELECTED_WEAPON_OFFSET_DEGREES,
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
        "arm_only_diagnostic_run_id": ARM_ONLY_DIAGNOSTIC_RUN_ID,
        "arm_only_diagnostic_artifact_id": ARM_ONLY_DIAGNOSTIC_ARTIFACT_ID,
        "arm_only_diagnostic_artifact_sha256": (
            ARM_ONLY_DIAGNOSTIC_ARTIFACT_SHA256
        ),
        "arm_only_diagnostic_max_clearance_pixels": (
            ARM_ONLY_DIAGNOSTIC_MAX_CLEARANCE_PIXELS
        ),
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "target_render_metrics": metrics[target_key],
        "action_data_changed": True,
        "rigid_weapon_transform_used": True,
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
                "directional_full_cycle_v21_pass05"
            ),
            "attack_sword_01_left_onehand_recovery_fixed": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    pass02_adapter._render_frame_v21_pass02 = _render_frame_v21_pass05
    pass04_adapter.create_attack_sword_directional_cycle_actions_v21_pass04 = (
        create_attack_sword_directional_cycle_actions_v21_pass05
    )
    pass04_adapter._write_manifest_v21_pass04 = _write_manifest_v21_pass05
    return pass04_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
