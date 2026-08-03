from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass26 as pass26_adapter
import blender_sprite_factory_attack_sword_twohand_up_cycle_diagnostic_v21_pass37 as pass37_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f03_review_v21_pass38 as pass38_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
from attack_sword_directional_cycle_correction_v21_pass46 import (
    CORRECTION_PASS,
    F03_ARM_BLEND,
    F03_CAMERA_SHIFT_Y,
    F03_CONTINUITY_FROM_F02_RMS_DEGREES,
    F03_CONTINUITY_SCORE,
    F03_CONTINUITY_TO_F04_RMS_DEGREES,
    F03_DEPTH_BRANCH,
    F03_EDGE_COUNTS,
    F03_MAXIMUM_TRANSITION_RMS_DEGREES,
    F03_REQUESTED_SCREEN_PROJECTION,
    F03_SOURCE_FRAME,
    F03_SOURCE_FRAME_ORDER,
    F03_SOURCE_POSE_CODE,
    F03_SOURCE_POSE_LABEL,
    F03_VALIDATED_CAMERA_MARGIN_PIXELS,
    F03_VALIDATED_HEAD_CLEARANCE_PIXELS,
    F03_VALIDATED_OCCLUDED_BLADE_SAMPLES,
    F03_VALIDATED_SCREEN_PROJECTION,
    F03_VALIDATED_SOURCE_PROJECTION,
    F03_VALIDATED_VISIBLE_BLADE_SAMPLES,
    F03_WEAPON_OFFSET_DEGREES,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_OVERSCAN_ARTIFACT_ID,
    SOURCE_OVERSCAN_ARTIFACT_SHA256,
    SOURCE_OVERSCAN_FINDING,
    SOURCE_OVERSCAN_RUN_ID,
    SOURCE_OVERSCAN_VARIANT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass46.py"
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass46"
SELECTED_F03_SCENE_KEY = "attack_sword_twohand_up_selected_f03_v21_pass46"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass46.png"
CAMERA_OBJECT_NAME = "CAM_gameplay_ortho"

ORIGINAL_RENDER_FRAME_V21_PASS26 = pass26_adapter._render_frame_v21_pass26
ORIGINAL_PASS37_CORRECTION_PASS = pass37_adapter.CORRECTION_PASS
ORIGINAL_PASS37_REVISION = pass37_adapter.TWOHAND_UP_SELECTED_CYCLE_REVISION
ORIGINAL_PASS37_REQUIRE_ZERO_EDGES = pass37_adapter.REQUIRE_ZERO_EDGE_ALPHA
ORIGINAL_PASS37_SCRIPT_PATH = pass37_adapter.SCRIPT_PATH
ORIGINAL_PASS37_CORRECTION_PATH = pass37_adapter.CORRECTION_PATH
ORIGINAL_PASS37_SCENE_KEY = pass37_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS37_CONTACT_SHEET_NAME = pass37_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS37_WRITE_MANIFEST = pass37_adapter._write_manifest


def _selected_f03_candidate() -> dict[str, object]:
    return {
        "source_frame": F03_SOURCE_FRAME,
        "source_frame_order": F03_SOURCE_FRAME_ORDER,
        "source_pose_code": F03_SOURCE_POSE_CODE,
        "source_pose_label": F03_SOURCE_POSE_LABEL,
        "arm_blend": F03_ARM_BLEND,
        "depth_branch": F03_DEPTH_BRANCH,
        "offset_degrees": F03_WEAPON_OFFSET_DEGREES,
        "source_projection": F03_VALIDATED_SOURCE_PROJECTION,
        "requested_screen_projection": F03_REQUESTED_SCREEN_PROJECTION,
        "screen_projection": F03_VALIDATED_SCREEN_PROJECTION,
        "head_clearance_pixels": F03_VALIDATED_HEAD_CLEARANCE_PIXELS,
        "visible_blade_samples": F03_VALIDATED_VISIBLE_BLADE_SAMPLES,
        "occluded_blade_samples": F03_VALIDATED_OCCLUDED_BLADE_SAMPLES,
        "camera_margin_pixels": F03_VALIDATED_CAMERA_MARGIN_PIXELS,
        "continuity_from_selected_f02_rms_degrees": (
            F03_CONTINUITY_FROM_F02_RMS_DEGREES
        ),
        "continuity_to_original_f04_rms_degrees": (
            F03_CONTINUITY_TO_F04_RMS_DEGREES
        ),
        "continuity_score": F03_CONTINUITY_SCORE,
        "maximum_transition_rms_degrees": (
            F03_MAXIMUM_TRANSITION_RMS_DEGREES
        ),
        "camera_shift_y": F03_CAMERA_SHIFT_Y,
        "edge_counts": dict(F03_EDGE_COUNTS),
    }


def _render_frame_v21_pass46(
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
    if (
        animation_id != TARGET_ACTION_ID
        or direction != TARGET_DIRECTION
        or frame_number != TARGET_FRAME
    ):
        return ORIGINAL_RENDER_FRAME_V21_PASS26(
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
        raise RuntimeError("two-hand up pass46 f03 requires fixed framing calibration")

    config = context.config
    action = factory.bpy.data.actions.get(f"{config.character_id}_{TARGET_ACTION_ID}")
    if action is None:
        raise RuntimeError("two-hand up pass46 selected f03 action is missing")
    camera = factory.bpy.data.objects.get(CAMERA_OBJECT_NAME)
    if camera is None or camera.data is None:
        raise RuntimeError("two-hand up pass46 gameplay camera is missing")

    weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
    factory._assign_action(context.rig, action)
    context.rig.rotation_euler[2] = math.radians(config.directions[TARGET_DIRECTION])
    target_f03_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
    source_f05_rotations = pass29_adapter._capture_arm(context, F03_SOURCE_FRAME)
    calibration = factory.FramingCalibration(
        scale=float(fixed_scale),
        source_center_x=float(fixed_center_x),
    )
    original_shift_y = float(camera.data.shift_y)
    camera.data.shift_y = F03_CAMERA_SHIFT_Y
    factory.bpy.context.view_layer.update()
    try:
        rendered, metadata = pass38_adapter._render_f03_candidate(
            context,
            raw_dir.parent,
            calibration=calibration,
            action=action,
            target_f03_rotations=target_f03_rotations,
            source_rotations=source_f05_rotations,
            candidate=_selected_f03_candidate(),
            variant_index=SOURCE_OVERSCAN_VARIANT,
        )
        desired_path = frame_dir / output_name
        if rendered.output_path != desired_path:
            desired_path.parent.mkdir(parents=True, exist_ok=True)
            if desired_path.exists():
                desired_path.unlink()
            rendered.output_path.replace(desired_path)
        artifact = factory.FrameArtifact(
            animation_id=animation_id,
            direction=direction,
            frame_number=frame_number,
            output_path=desired_path,
            sprite_width=rendered.sprite_width,
            sprite_height=rendered.sprite_height,
            baseline_y=rendered.baseline_y,
        )
        selected_metadata = {
            **_selected_f03_candidate(),
            **metadata,
            "camera_shift_y": F03_CAMERA_SHIFT_Y,
            "camera_shift_restored_after_render": True,
            "pass26_planner_used": False,
            "selected_manual_candidate_used": True,
            "output_name": output_name,
        }
        factory.bpy.context.scene[SELECTED_F03_SCENE_KEY] = json.dumps(
            selected_metadata,
            sort_keys=True,
        )
        print(
            "ATTACK_SWORD_TWOHAND_UP_CYCLE_V21_PASS46_F03_SELECTED="
            f"source:{F03_SOURCE_POSE_LABEL};blend:{F03_ARM_BLEND:.2f};"
            f"projection:{F03_VALIDATED_SCREEN_PROJECTION:.3f};"
            f"offset:{F03_WEAPON_OFFSET_DEGREES:.1f};"
            f"shift_y:{F03_CAMERA_SHIFT_Y:.3f};edges:{F03_EDGE_COUNTS}"
        )
        return artifact, calibration
    finally:
        camera.data.shift_y = original_shift_y
        factory.bpy.context.view_layer.update()


def _write_manifest_v21_pass46(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS37_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    cycle = payload.get(DIAGNOSTIC_SCENE_KEY, {})
    if not isinstance(cycle, dict):
        raise RuntimeError("two-hand up pass46 cycle manifest is invalid")
    if SELECTED_F03_SCENE_KEY not in factory.bpy.context.scene:
        raise RuntimeError("two-hand up pass46 selected f03 metadata is missing")
    selected_f03 = json.loads(
        str(factory.bpy.context.scene[SELECTED_F03_SCENE_KEY])
    )
    cycle["correction_pass"] = CORRECTION_PASS
    cycle["revision"] = TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION
    cycle["selected_f03"] = selected_f03
    frame_metrics = cycle.get("frame_metrics", {})
    if not isinstance(frame_metrics, dict):
        frame_metrics = {}
    frame_metrics["f03"] = {
        "edge_counts": dict(F03_EDGE_COUNTS),
        "pass26_planner_used": False,
        "selected_manual_candidate_used": True,
        "camera_shift_y": F03_CAMERA_SHIFT_Y,
    }
    cycle["frame_metrics"] = frame_metrics
    cycle["action_data_changed"] = False
    cycle["camera_shift_persistent_change"] = False
    payload[DIAGNOSTIC_SCENE_KEY] = cycle
    payload.update(
        {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION,
            "source_overscan_run_id": SOURCE_OVERSCAN_RUN_ID,
            "source_overscan_artifact_id": SOURCE_OVERSCAN_ARTIFACT_ID,
            "source_overscan_artifact_sha256": SOURCE_OVERSCAN_ARTIFACT_SHA256,
            "source_overscan_variant": SOURCE_OVERSCAN_VARIANT,
            "source_overscan_finding": SOURCE_OVERSCAN_FINDING,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "selected_f03_changed": True,
            "twohand_up_action_data_changed": False,
            "camera_shift_used_for_raw_overscan": True,
            "camera_shift_persistent_change": False,
            "root_translation_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "manual_review_required": True,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _apply_pass46_contract() -> None:
    pass26_adapter._render_frame_v21_pass26 = _render_frame_v21_pass46
    pass37_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass37_adapter.TWOHAND_UP_SELECTED_CYCLE_REVISION = (
        TWOHAND_UP_F01_F02_F03_SELECTED_CYCLE_REVISION
    )
    pass37_adapter.REQUIRE_ZERO_EDGE_ALPHA = REQUIRE_ZERO_EDGE_ALPHA
    pass37_adapter.SCRIPT_PATH = SCRIPT_PATH
    pass37_adapter.CORRECTION_PATH = CORRECTION_PATH
    pass37_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass37_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass37_adapter._write_manifest = _write_manifest_v21_pass46


def _restore_pass37_contract() -> None:
    pass26_adapter._render_frame_v21_pass26 = ORIGINAL_RENDER_FRAME_V21_PASS26
    pass37_adapter.CORRECTION_PASS = ORIGINAL_PASS37_CORRECTION_PASS
    pass37_adapter.TWOHAND_UP_SELECTED_CYCLE_REVISION = ORIGINAL_PASS37_REVISION
    pass37_adapter.REQUIRE_ZERO_EDGE_ALPHA = ORIGINAL_PASS37_REQUIRE_ZERO_EDGES
    pass37_adapter.SCRIPT_PATH = ORIGINAL_PASS37_SCRIPT_PATH
    pass37_adapter.CORRECTION_PATH = ORIGINAL_PASS37_CORRECTION_PATH
    pass37_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS37_SCENE_KEY
    pass37_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS37_CONTACT_SHEET_NAME
    pass37_adapter._write_manifest = ORIGINAL_PASS37_WRITE_MANIFEST


def main() -> int:
    _apply_pass46_contract()
    try:
        return pass37_adapter.main()
    finally:
        _restore_pass37_contract()


if __name__ == "__main__":
    raise SystemExit(main())
