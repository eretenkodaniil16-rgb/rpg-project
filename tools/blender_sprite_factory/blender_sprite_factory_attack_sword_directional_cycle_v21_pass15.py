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

from mathutils import Vector

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21 as base_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass13 as pass13_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
from attack_sword_directional_cycle_builder_v21_pass15 import (
    create_attack_sword_directional_cycle_actions_v21_pass15,
)
from attack_sword_directional_cycle_correction_v21_pass15 import (
    CORRECTION_PASS,
    DIAGNOSTIC_ALPHA_BBOX_BY_FRAME,
    DIAGNOSTIC_ARTIFACT_ID,
    DIAGNOSTIC_ARTIFACT_SHA256,
    DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME,
    DIAGNOSTIC_FRAME_SIZE,
    DIAGNOSTIC_RUN_ID,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SELECTED_APPLIED_SCREEN_PROJECTION_BY_FRAME,
    SELECTED_ARM_BLEND_BY_FRAME,
    SELECTED_ATTEMPT_BY_FRAME,
    SELECTED_CAMERA_MARGIN_PIXELS_BY_FRAME,
    SELECTED_HEAD_CLEARANCE_PIXELS_BY_FRAME,
    SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME,
    SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_LEFT_TAIL_REVISION,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass15.py"
)
BUILDER_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_builder_v21_pass15.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
BASE_RENDER_FRAME_PASS13 = pass13_adapter._render_frame_v21_pass13
BASE_WRITE_MANIFEST_PASS13 = pass13_adapter._write_manifest_v21_pass13


def _is_tail_frame(
    animation_id: str,
    direction: str,
    frame_number: int,
) -> bool:
    return (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number in TARGET_FRAMES
    )


def _target_direction_v21_pass15(
    current_direction: Vector,
    frame_number: int,
) -> tuple[Vector, float, float]:
    screen_x, screen_y, camera_forward = pass06_adapter._camera_axes()
    current_x = current_direction.dot(screen_x)
    current_y = current_direction.dot(screen_y)
    current_depth = current_direction.dot(camera_forward)
    source_projection = math.hypot(current_x, current_y)
    if source_projection <= 1.0e-6:
        raise RuntimeError(
            "attack sword directional v21 pass15 source projection is degenerate"
        )
    requested_projection = float(
        SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME[frame_number]
    )
    target_projection = min(source_projection, requested_projection)
    angle = (
        math.atan2(current_y, current_x)
        + math.radians(
            SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME[frame_number]
        )
    )
    depth_sign = 1.0 if current_depth >= 0.0 else -1.0
    depth_magnitude = math.sqrt(max(0.0, 1.0 - target_projection**2))
    target_direction = (
        screen_x * (math.cos(angle) * target_projection)
        + screen_y * (math.sin(angle) * target_projection)
        + camera_forward * (depth_sign * depth_magnitude)
    ).normalized()
    return target_direction, source_projection, target_projection


def _render_frame_v21_pass15(
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
    if not _is_tail_frame(animation_id, direction, frame_number):
        return BASE_RENDER_FRAME_PASS13(
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
            "attack sword directional v21 pass15 target action is missing"
        )
    if (
        action.get("directional_twohand_left_tail_revision")
        != TWOHAND_LEFT_TAIL_REVISION
    ):
        raise RuntimeError(
            "attack sword directional v21 pass15 tail metadata drifted"
        )
    if frame_number == 5 and not math.isclose(
        float(
            action.get(
                "directional_twohand_left_tail_f05_arm_blend",
                -1.0,
            )
        ),
        SELECTED_ARM_BLEND_BY_FRAME[5],
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "attack sword directional v21 pass15 f05 arm blend drifted"
        )

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    objects = base_adapter._visible_weapon_objects(TARGET_GRIP_ID, direction)
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = pass02_adapter._weapon_world_direction(objects)
    pivot = pass02_adapter._weapon_pivot(objects)
    target_direction, source_projection, applied_projection = (
        _target_direction_v21_pass15(current_direction, frame_number)
    )
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=target_direction,
    )
    try:
        clearance = export_adapter._weapon_head_clearance(objects)
        margin = pass02_adapter._camera_margin(objects)
        if clearance < MIN_HEAD_CLEARANCE_PIXELS:
            raise RuntimeError(
                "attack sword directional v21 pass15 tail clearance drifted "
                f"for f{frame_number:02d}: {clearance:.3f}px"
            )
        if margin < MIN_CAMERA_MARGIN_PIXELS:
            raise RuntimeError(
                "attack sword directional v21 pass15 tail margin drifted "
                f"for f{frame_number:02d}: {margin:.3f}px"
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
                "attack sword directional v21 pass15 tail touched export "
                f"edges for f{frame_number:02d}: {touched}"
            )
    finally:
        pass06_adapter._restore_weapon(saved_basis)

    metrics_raw = str(
        scene.get("attack_sword_directional_cycle_v21_pass02_metrics", "{}")
    )
    metrics = json.loads(metrics_raw)
    key = f"{TARGET_GRIP_ID}/{direction}/f{frame_number:02d}"
    metrics[key] = {
        "offset_degrees": (
            SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME[frame_number]
        ),
        "source_projection": float(source_projection),
        "requested_screen_projection": (
            SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME[frame_number]
        ),
        "screen_projection": float(applied_projection),
        "head_clearance_pixels": float(clearance),
        "camera_margin_pixels": float(margin),
        "edge_counts": edge_counts,
        "render_attempts": 1,
        "candidate_diagnostics": [
            {
                "attempt": 1,
                "arm_blend": SELECTED_ARM_BLEND_BY_FRAME[frame_number],
                "source_frame": SOURCE_FRAME_BY_TARGET[frame_number],
                "offset_degrees": (
                    SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME[frame_number]
                ),
                "source_projection": float(source_projection),
                "requested_screen_projection": (
                    SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME[frame_number]
                ),
                "screen_projection": float(applied_projection),
                "head_clearance_pixels": float(clearance),
                "camera_margin_pixels": float(margin),
                "edge_counts": edge_counts,
                "accepted": True,
            }
        ],
        "pass15_arm_blend": SELECTED_ARM_BLEND_BY_FRAME[frame_number],
        "pass15_screen_projection": float(applied_projection),
    }
    scene["attack_sword_directional_cycle_v21_pass02_metrics"] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_DIRECTIONAL_V21_PASS15_SELECTED="
        f"{key};"
        f"blend:{SELECTED_ARM_BLEND_BY_FRAME[frame_number]:.2f};"
        f"projection:{float(applied_projection):.6f};"
        f"offset:{SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME[frame_number]:.1f}deg;"
        f"clearance:{float(clearance):.3f}px;"
        f"margin:{float(margin):.3f}px;"
        f"edges:{touched}"
    )
    return artifact, calibration


def _write_manifest_v21_pass15(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS13(
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
            "attack sword directional v21 pass15 manifest action is missing"
        )
    if (
        action.get("directional_twohand_left_tail_revision")
        != TWOHAND_LEFT_TAIL_REVISION
    ):
        raise RuntimeError(
            "attack sword directional v21 pass15 manifest tail metadata drifted"
        )

    metrics = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_directional_cycle_v21_pass02_metrics"
            ]
        )
    )
    target_metrics: dict[str, object] = {}
    for frame_number in TARGET_FRAMES:
        key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{frame_number:02d}"
        if key not in metrics:
            raise RuntimeError(
                "attack sword directional v21 pass15 tail metrics missing: "
                f"{key}"
            )
        item = metrics[key]
        if float(item["head_clearance_pixels"]) < MIN_HEAD_CLEARANCE_PIXELS:
            raise RuntimeError(
                "attack sword directional v21 pass15 manifest clearance drifted"
            )
        if float(item["camera_margin_pixels"]) < MIN_CAMERA_MARGIN_PIXELS:
            raise RuntimeError(
                "attack sword directional v21 pass15 manifest margin drifted"
            )
        if REQUIRE_ZERO_EDGE_ALPHA and any(
            int(count) > 0 for count in item.get("edge_counts", {}).values()
        ):
            raise RuntimeError(
                "attack sword directional v21 pass15 manifest edge drifted"
            )
        target_metrics[f"f{frame_number:02d}"] = item

    payload["attack_sword_directional_cycle_v21_pass15"] = {
        "correction_pass": CORRECTION_PASS,
        "tail_revision": TWOHAND_LEFT_TAIL_REVISION,
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
        "target_frames": list(TARGET_FRAMES),
        "source_frame_by_target": {
            str(key): value for key, value in SOURCE_FRAME_BY_TARGET.items()
        },
        "body_scope": list(TARGET_BONES),
        "selected_arm_blend_by_frame": {
            str(key): value
            for key, value in SELECTED_ARM_BLEND_BY_FRAME.items()
        },
        "selected_requested_screen_projection_by_frame": {
            str(key): value
            for key, value in (
                SELECTED_REQUESTED_SCREEN_PROJECTION_BY_FRAME.items()
            )
        },
        "selected_applied_screen_projection_by_frame": {
            str(key): value
            for key, value in (
                SELECTED_APPLIED_SCREEN_PROJECTION_BY_FRAME.items()
            )
        },
        "selected_weapon_offset_degrees_by_frame": {
            str(key): value
            for key, value in (
                SELECTED_WEAPON_OFFSET_DEGREES_BY_FRAME.items()
            )
        },
        "validated_head_clearance_pixels_by_frame": {
            str(key): value
            for key, value in (
                SELECTED_HEAD_CLEARANCE_PIXELS_BY_FRAME.items()
            )
        },
        "validated_camera_margin_pixels_by_frame": {
            str(key): value
            for key, value in (
                SELECTED_CAMERA_MARGIN_PIXELS_BY_FRAME.items()
            )
        },
        "selected_attempt_by_frame": {
            str(key): value
            for key, value in SELECTED_ATTEMPT_BY_FRAME.items()
        },
        "diagnostic_run_id": DIAGNOSTIC_RUN_ID,
        "diagnostic_artifact_id": DIAGNOSTIC_ARTIFACT_ID,
        "diagnostic_artifact_sha256": DIAGNOSTIC_ARTIFACT_SHA256,
        "diagnostic_frame_size": list(DIAGNOSTIC_FRAME_SIZE),
        "diagnostic_alpha_bbox_by_frame": {
            str(key): list(value)
            for key, value in DIAGNOSTIC_ALPHA_BBOX_BY_FRAME.items()
        },
        "diagnostic_edge_alpha_counts_by_frame": {
            str(key): value
            for key, value in DIAGNOSTIC_EDGE_ALPHA_COUNTS_BY_FRAME.items()
        },
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "target_render_metrics": target_metrics,
        "action_data_changed": True,
        "action_data_changed_frames": [5],
        "rigid_weapon_transform_used": True,
        "approved_down_v20_changed": False,
        "onehand_left_changed": False,
        "twohand_left_f02_f04_changed": False,
        "right_up_actions_changed": False,
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
                "directional_full_cycle_v21_pass15"
            ),
            "attack_sword_01_left_twohand_tail_fixed": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    pass13_adapter._render_frame_v21_pass13 = _render_frame_v21_pass15
    pass13_adapter.create_attack_sword_directional_cycle_actions_v21_pass13 = (
        create_attack_sword_directional_cycle_actions_v21_pass15
    )
    pass13_adapter._write_manifest_v21_pass13 = _write_manifest_v21_pass15
    return pass13_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
