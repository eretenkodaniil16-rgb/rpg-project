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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass26 as pass26_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass27 as pass27_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass28 as pass28_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
from attack_sword_directional_cycle_builder_v21_pass54 import (
    create_attack_sword_directional_cycle_actions_v21_pass54,
)
from attack_sword_directional_cycle_correction_v21_pass54 import (
    ACTION_BONE_DELTAS_DEGREES_BY_FRAME,
    ACTION_CHANGED_FRAMES,
    ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME,
    CAMERA_SHIFT_X_BY_FRAME,
    CAMERA_SHIFT_Y_BY_FRAME,
    CORRECTION_PASS,
    EXPECTED_SOURCE_PROJECTION_BY_FRAME,
    PROJECTED_WEAPON_PROFILE_BY_FRAME,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_SELECTED_ARTIFACT_ID,
    SOURCE_SELECTED_ARTIFACT_SHA256,
    SOURCE_SELECTED_COMMIT,
    SOURCE_SELECTED_FINDING,
    SOURCE_SELECTED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_UP_INTEGRATED_ACTION_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass54.py"
BUILDER_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_builder_v21_pass54.py"
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
CAMERA_OBJECT_NAME = "CAM_gameplay_ortho"
METRICS_SCENE_KEY = "attack_sword_directional_cycle_v21_pass02_metrics"
PASS54_SCENE_KEY = "attack_sword_directional_cycle_v21_pass54"

ORIGINAL_PASS28_RENDER = pass28_adapter._render_frame_v21_pass28
ORIGINAL_PASS28_WRITE_MANIFEST = pass28_adapter._write_manifest_v21_pass28
ORIGINAL_PASS26_CREATE_ACTIONS = (
    pass26_adapter.create_attack_sword_directional_cycle_actions_v21_pass26
)
ORIGINAL_PASS02_VALIDATE_CLEARANCE = (
    pass02_adapter._validate_directional_clearance_v21_pass02
)


def _is_target_frame(
    animation_id: str,
    direction: str,
    frame_number: int,
) -> bool:
    return (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number in TARGET_FRAMES
    )


def _screen_projection(direction: object) -> float:
    screen_x, screen_y, _camera_forward = pass06_adapter._camera_axes()
    return math.hypot(
        float(direction.dot(screen_x)),
        float(direction.dot(screen_y)),
    )


def _render_frame_v21_pass54(
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
        return ORIGINAL_PASS28_RENDER(
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
    if fixed_scale is None or fixed_center_x is None:
        raise RuntimeError(
            "attack sword directional v21 pass54 requires fixed framing calibration"
        )

    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_{TARGET_ACTION_ID}"
    )
    if action is None:
        raise RuntimeError("attack sword directional v21 pass54 action is missing")
    if action.get("directional_twohand_up_final_revision") != (
        TWOHAND_UP_INTEGRATED_ACTION_REVISION
    ):
        raise RuntimeError(
            "attack sword directional v21 pass54 action metadata drifted"
        )

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    camera = factory.bpy.data.objects.get(CAMERA_OBJECT_NAME)
    if camera is None or camera.data is None:
        raise RuntimeError("attack sword directional v21 pass54 camera is missing")

    objects = base_adapter._visible_weapon_objects(TARGET_GRIP_ID, direction)
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = pass02_adapter._weapon_world_direction(objects)
    pivot = pass02_adapter._weapon_pivot(objects)
    source_projection = _screen_projection(current_direction)

    if frame_number in PROJECTED_WEAPON_PROFILE_BY_FRAME:
        profile = PROJECTED_WEAPON_PROFILE_BY_FRAME[frame_number]
        expected_source = EXPECTED_SOURCE_PROJECTION_BY_FRAME[frame_number]
        if not math.isclose(
            source_projection,
            float(expected_source),
            rel_tol=0.0,
            abs_tol=2.0e-4,
        ):
            raise RuntimeError(
                "attack sword directional v21 pass54 source projection drifted "
                f"at f{frame_number:02d}: {source_projection:.6f}, "
                f"expected={expected_source:.6f}"
            )
        target_direction, _source, applied_projection = (
            pass27_adapter._target_direction_v21_pass27(
                current_direction,
                requested_projection=float(profile["projection"]),
                offset_degrees=float(profile["offset_degrees"]),
                depth_branch=str(profile["depth_branch"]),
            )
        )
        depth_branch = str(profile["depth_branch"])
        offset_degrees = float(profile["offset_degrees"])
    else:
        offset_degrees = float(
            ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME[frame_number]
        )
        target_direction = export_adapter._target_direction(
            current_direction,
            offset_degrees=offset_degrees,
        )
        applied_projection = source_projection
        depth_branch = "source_preserved"

    original_shift_x = float(camera.data.shift_x)
    original_shift_y = float(camera.data.shift_y)
    camera.data.shift_x = float(CAMERA_SHIFT_X_BY_FRAME[frame_number])
    camera.data.shift_y = float(CAMERA_SHIFT_Y_BY_FRAME[frame_number])
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=target_direction,
    )
    try:
        factory.bpy.context.view_layer.update()
        clearance = float(
            pass27_adapter.depth_aware_adapter
            ._depth_aware_visible_blade_head_clearance(objects)
        )
        margin = float(pass02_adapter._camera_margin(objects))
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
        touched = {edge: count for edge, count in edge_counts.items() if count > 0}
        if REQUIRE_ZERO_EDGE_ALPHA and touched:
            raise RuntimeError(
                "attack sword directional v21 pass54 selected frame touched "
                f"canvas edges at f{frame_number:02d}: {touched}"
            )
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        camera.data.shift_x = original_shift_x
        camera.data.shift_y = original_shift_y
        factory.bpy.context.view_layer.update()

    metrics = json.loads(str(scene.get(METRICS_SCENE_KEY, "{}")))
    key = f"{TARGET_GRIP_ID}/{direction}/f{frame_number:02d}"
    metrics[key] = {
        "offset_degrees": offset_degrees,
        "depth_branch": depth_branch,
        "source_projection": source_projection,
        "screen_projection": float(applied_projection),
        "head_clearance_pixels": clearance,
        "camera_margin_pixels": margin,
        "camera_shift_x": float(CAMERA_SHIFT_X_BY_FRAME[frame_number]),
        "camera_shift_y": float(CAMERA_SHIFT_Y_BY_FRAME[frame_number]),
        "edge_counts": edge_counts,
        "render_attempts": 1,
        "pass54_integrated_action": True,
        "pass54_rigid_weapon_export_profile": True,
        "camera_shift_persistent_change": False,
    }
    scene[METRICS_SCENE_KEY] = json.dumps(metrics, sort_keys=True)
    print(
        "ATTACK_SWORD_DIRECTIONAL_V21_PASS54_SELECTED="
        f"{key};branch:{depth_branch};"
        f"projection:{float(applied_projection):.6f};"
        f"offset:{offset_degrees:.1f}deg;"
        f"clearance:{clearance:.3f}px;margin:{margin:.3f}px;"
        f"shift_x:{CAMERA_SHIFT_X_BY_FRAME[frame_number]:.3f};"
        f"shift_y:{CAMERA_SHIFT_Y_BY_FRAME[frame_number]:.3f};"
        f"edges:{edge_counts}"
    )
    return artifact, calibration


def _validate_directional_clearance_v21_pass54(
    context: factory.BuildContext,
    *,
    action_id: str,
    grip_id: str,
    weapon_cycle_id: str,
    direction: str,
) -> dict[int, float]:
    if not (
        action_id == TARGET_ACTION_ID
        and grip_id == TARGET_GRIP_ID
        and direction == TARGET_DIRECTION
    ):
        return ORIGINAL_PASS02_VALIDATE_CLEARANCE(
            context,
            action_id=action_id,
            grip_id=grip_id,
            weapon_cycle_id=weapon_cycle_id,
            direction=direction,
        )

    metrics = json.loads(
        str(factory.bpy.context.scene.get(METRICS_SCENE_KEY, "{}"))
    )
    clearances: dict[int, float] = {}
    for frame_number in (2, 3, 4):
        key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{frame_number:02d}"
        if key not in metrics:
            raise RuntimeError(
                "attack sword directional v21 pass54 clearance metrics missing: "
                f"{key}"
            )
        if any(int(value) > 0 for value in metrics[key]["edge_counts"].values()):
            raise RuntimeError(
                "attack sword directional v21 pass54 clearance frame touched edge: "
                f"{key}"
            )
        clearances[frame_number] = float(metrics[key]["head_clearance_pixels"])
    factory.bpy.context.scene["attack_sword_directional_cycle_v21_pass54_depth_clearance_contract"] = True
    return clearances


def _write_manifest_v21_pass54(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_PASS28_WRITE_MANIFEST(
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
        raise RuntimeError("attack sword directional v21 pass54 manifest action missing")
    metrics = json.loads(
        str(factory.bpy.context.scene.get(METRICS_SCENE_KEY, "{}"))
    )
    target_metrics: dict[str, object] = {}
    for frame_number in TARGET_FRAMES:
        key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{frame_number:02d}"
        if key not in metrics:
            raise RuntimeError(
                "attack sword directional v21 pass54 manifest metrics missing: "
                f"{key}"
            )
        target_metrics[f"f{frame_number:02d}"] = metrics[key]

    payload[PASS54_SCENE_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": TWOHAND_UP_INTEGRATED_ACTION_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
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
        "action_changed_frames": list(ACTION_CHANGED_FRAMES),
        "target_bones": list(TARGET_BONES),
        "action_bone_deltas_degrees_by_frame": {
            str(frame): {
                bone: list(values)
                for bone, values in ACTION_BONE_DELTAS_DEGREES_BY_FRAME[frame].items()
            }
            for frame in ACTION_CHANGED_FRAMES
        },
        "projected_weapon_profile_by_frame": {
            str(frame): profile
            for frame, profile in PROJECTED_WEAPON_PROFILE_BY_FRAME.items()
        },
        "angle_only_weapon_offset_degrees_by_frame": {
            str(frame): value
            for frame, value in ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME.items()
        },
        "camera_shift_x_by_frame": {
            str(frame): value for frame, value in CAMERA_SHIFT_X_BY_FRAME.items()
        },
        "camera_shift_y_by_frame": {
            str(frame): value for frame, value in CAMERA_SHIFT_Y_BY_FRAME.items()
        },
        "target_render_metrics": target_metrics,
        "source_selected_run_id": SOURCE_SELECTED_RUN_ID,
        "source_selected_artifact_id": SOURCE_SELECTED_ARTIFACT_ID,
        "source_selected_artifact_sha256": SOURCE_SELECTED_ARTIFACT_SHA256,
        "source_selected_commit": SOURCE_SELECTED_COMMIT,
        "source_selected_finding": SOURCE_SELECTED_FINDING,
        "action_data_changed": True,
        "rigid_weapon_transform_used": True,
        "temporary_camera_overscan_used": True,
        "camera_shift_persistent_change": False,
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
                "directional_full_cycle_v21_pass54_integrated"
            ),
            "attack_sword_01_twohand_up_integrated_revision": (
                TWOHAND_UP_INTEGRATED_ACTION_REVISION
            ),
            "attack_sword_01_twohand_up_action_data_changed": True,
            "attack_sword_01_total_rendered_frames": len(artifacts),
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_pass54_contract() -> None:
    pass26_adapter.create_attack_sword_directional_cycle_actions_v21_pass26 = (
        create_attack_sword_directional_cycle_actions_v21_pass54
    )
    pass28_adapter._render_frame_v21_pass28 = _render_frame_v21_pass54
    pass28_adapter._write_manifest_v21_pass28 = _write_manifest_v21_pass54
    pass02_adapter._validate_directional_clearance_v21_pass02 = (
        _validate_directional_clearance_v21_pass54
    )


def _restore_pass54_contract() -> None:
    pass26_adapter.create_attack_sword_directional_cycle_actions_v21_pass26 = (
        ORIGINAL_PASS26_CREATE_ACTIONS
    )
    pass28_adapter._render_frame_v21_pass28 = ORIGINAL_PASS28_RENDER
    pass28_adapter._write_manifest_v21_pass28 = ORIGINAL_PASS28_WRITE_MANIFEST
    pass02_adapter._validate_directional_clearance_v21_pass02 = (
        ORIGINAL_PASS02_VALIDATE_CLEARANCE
    )


def main() -> int:
    _apply_pass54_contract()
    try:
        return pass28_adapter.main()
    finally:
        _restore_pass54_contract()


if __name__ == "__main__":
    raise SystemExit(main())
