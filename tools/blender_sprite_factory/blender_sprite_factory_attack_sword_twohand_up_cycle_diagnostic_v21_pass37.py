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
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f02_review_v21_pass34 as pass34_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass37 import (
    CORRECTION_PASS,
    F01_ARM_BLEND,
    F01_DEPTH_BRANCH,
    F01_REQUESTED_SCREEN_PROJECTION,
    F01_SOURCE_FRAME,
    F01_VALIDATED_CAMERA_MARGIN_PIXELS,
    F01_VALIDATED_HEAD_CLEARANCE_PIXELS,
    F01_VALIDATED_SCREEN_PROJECTION,
    F01_VALIDATED_VISIBLE_BLADE_SAMPLES,
    F01_WEAPON_OFFSET_DEGREES,
    F02_ARM_BLEND,
    F02_CONTINUITY_FROM_F01_RMS_DEGREES,
    F02_CONTINUITY_SCORE,
    F02_CONTINUITY_TO_F03_RMS_DEGREES,
    F02_DEPTH_BRANCH,
    F02_REQUESTED_SCREEN_PROJECTION,
    F02_SOURCE_FRAME,
    F02_SOURCE_FRAME_ORDER,
    F02_SOURCE_POSE_LABEL,
    F02_VALIDATED_CAMERA_MARGIN_PIXELS,
    F02_VALIDATED_HEAD_CLEARANCE_PIXELS,
    F02_VALIDATED_OCCLUDED_BLADE_SAMPLES,
    F02_VALIDATED_SCREEN_PROJECTION,
    F02_VALIDATED_SOURCE_PROJECTION,
    F02_VALIDATED_VISIBLE_BLADE_SAMPLES,
    F02_WEAPON_OFFSET_DEGREES,
    FRAME_ORDER,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_ARTIFACT_SHA256,
    SOURCE_REVIEW_FINDING,
    SOURCE_REVIEW_RUN_ID,
    SOURCE_REVIEW_VARIANT,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_GRIP_ID,
    TWOHAND_UP_SELECTED_CYCLE_REVISION,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass37"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass37.png"
CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass37.py"


def _f01_candidate() -> dict[str, object]:
    return {
        "source_frame": F01_SOURCE_FRAME,
        "source_frame_order": 6,
        "arm_blend": F01_ARM_BLEND,
        "depth_branch": F01_DEPTH_BRANCH,
        "offset_degrees": F01_WEAPON_OFFSET_DEGREES,
        "source_projection": 0.9441554673868896,
        "requested_screen_projection": F01_REQUESTED_SCREEN_PROJECTION,
        "screen_projection": F01_VALIDATED_SCREEN_PROJECTION,
        "head_clearance_pixels": F01_VALIDATED_HEAD_CLEARANCE_PIXELS,
        "visible_blade_samples": F01_VALIDATED_VISIBLE_BLADE_SAMPLES,
        "occluded_blade_samples": 0,
        "camera_margin_pixels": F01_VALIDATED_CAMERA_MARGIN_PIXELS,
    }


def _f02_candidate() -> dict[str, object]:
    return {
        "source_frame": F02_SOURCE_FRAME,
        "source_frame_order": F02_SOURCE_FRAME_ORDER,
        "source_pose_code": F02_SOURCE_FRAME,
        "source_pose_label": F02_SOURCE_POSE_LABEL,
        "arm_blend": F02_ARM_BLEND,
        "depth_branch": F02_DEPTH_BRANCH,
        "offset_degrees": F02_WEAPON_OFFSET_DEGREES,
        "source_projection": F02_VALIDATED_SOURCE_PROJECTION,
        "requested_screen_projection": F02_REQUESTED_SCREEN_PROJECTION,
        "screen_projection": F02_VALIDATED_SCREEN_PROJECTION,
        "head_clearance_pixels": F02_VALIDATED_HEAD_CLEARANCE_PIXELS,
        "visible_blade_samples": F02_VALIDATED_VISIBLE_BLADE_SAMPLES,
        "occluded_blade_samples": F02_VALIDATED_OCCLUDED_BLADE_SAMPLES,
        "camera_margin_pixels": F02_VALIDATED_CAMERA_MARGIN_PIXELS,
        "continuity_from_corrected_f01_rms_degrees": (
            F02_CONTINUITY_FROM_F01_RMS_DEGREES
        ),
        "continuity_to_original_f03_rms_degrees": (
            F02_CONTINUITY_TO_F03_RMS_DEGREES
        ),
        "continuity_score": F02_CONTINUITY_SCORE,
    }


def _render_cycle(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    calibration = calibration_adapter._direction_calibrations(context, run_dir)[
        TARGET_DIRECTION
    ]
    action = factory.bpy.data.actions.get(
        f"{config.character_id}_{TARGET_ACTION_ID}"
    )
    if action is None:
        raise RuntimeError(
            "two-hand up pass37 cycle action is missing: " f"{TARGET_ACTION_ID}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    artifacts: list[factory.FrameArtifact] = []
    metrics: dict[str, object] = {}
    original_f01_rotations: dict[str, object] = {}
    original_f02_rotations: dict[str, object] = {}

    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        original_f01_rotations = pass29_adapter._capture_arm(context, 1)
        original_f02_rotations = pass29_adapter._capture_arm(context, 2)
        original_f04_rotations = pass29_adapter._capture_arm(context, F02_SOURCE_FRAME)
        original_f05_rotations = pass29_adapter._capture_arm(context, F01_SOURCE_FRAME)

        f01_artifact, f01_metrics = pass34_adapter._render_corrected_f01_reference(
            context,
            run_dir,
            calibration=calibration,
            action=action,
            original_f01_rotations=original_f01_rotations,
            original_f05_rotations=original_f05_rotations,
        )
        artifacts.append(f01_artifact)
        metrics["f01"] = {**_f01_candidate(), **f01_metrics}

        f02_artifact, f02_metrics = pass34_adapter._render_f02_candidate(
            context,
            run_dir,
            calibration=calibration,
            action=action,
            target_f02_rotations=original_f02_rotations,
            source_rotations=original_f04_rotations,
            candidate=_f02_candidate(),
            variant_index=SOURCE_REVIEW_VARIANT,
        )
        artifacts.append(f02_artifact)
        metrics["f02"] = f02_metrics

        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        raw_dir = run_dir / "raw"
        frame_dir = run_dir / "frames"
        for frame_number in FRAME_ORDER[2:]:
            artifact, _ = pass26_adapter._render_frame_v21_pass26(
                context,
                animation_id=TARGET_ACTION_ID,
                direction=TARGET_DIRECTION,
                frame_number=frame_number,
                raw_dir=raw_dir,
                frame_dir=frame_dir,
                output_name=(
                    f"{config.character_id}_{TARGET_ACTION_ID}_"
                    f"f{frame_number:02d}_pass37_proxy_{context.proxy_revision}.png"
                ),
                fixed_scale=calibration.scale,
                fixed_center_x=calibration.source_center_x,
                use_clearance_planner=True,
            )
            edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
            touched = {
                edge: count for edge, count in edge_counts.items() if count > 0
            }
            if REQUIRE_ZERO_EDGE_ALPHA and touched:
                raise RuntimeError(
                    "two-hand up pass37 cycle frame touched canvas edges: "
                    f"f{frame_number:02d}; {touched}"
                )
            artifacts.append(artifact)
            metrics[f"f{frame_number:02d}"] = {
                "edge_counts": edge_counts,
                "pass26_planner_used": True,
            }

        if tuple(item.frame_number for item in artifacts) != FRAME_ORDER:
            raise RuntimeError(
                "two-hand up pass37 cycle frame order drifted: "
                f"{[item.frame_number for item in artifacts]}"
            )
        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_SELECTED_CYCLE_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "frame_order": list(FRAME_ORDER),
            "selected_f01": _f01_candidate(),
            "selected_f02": _f02_candidate(),
            "frame_metrics": metrics,
            "action_data_changed": False,
            "manual_animation_review_required": True,
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        return artifacts
    finally:
        if original_f02_rotations:
            pass29_adapter._restore_arm(context, original_f02_rotations)
        elif original_f01_rotations:
            pass29_adapter._restore_arm(context, original_f01_rotations)
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    if tuple(item.frame_number for item in artifacts) != FRAME_ORDER:
        raise RuntimeError("two-hand up pass37 cycle sheet frame order drifted")
    tile_width = int(config.technical.canvas_width)
    tile_height = int(config.technical.canvas_height)
    width = tile_width * len(artifacts)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * tile_height)
        for component in (*background, 1.0)
    ]
    for column_index, artifact in enumerate(artifacts):
        image = factory.bpy.data.images.load(
            str(artifact.output_path),
            check_existing=False,
        )
        try:
            factory._copy_tile(
                pixels,
                width,
                tuple(image.pixels[:]),
                tile_width,
                tile_height,
                column_index * tile_width,
                0,
            )
        finally:
            factory.bpy.data.images.remove(image)
    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_attack_sword_twohand_up_cycle_diagnostic_v21_pass37",
        width=width,
        height=tile_height,
        alpha=True,
        float_buffer=False,
    )
    try:
        sheet.pixels[:] = pixels
        sheet.file_format = "PNG"
        sheet.filepath_raw = str(output_path)
        sheet.save()
    finally:
        factory.bpy.data.images.remove(sheet)
    return output_path


def _write_manifest(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = BASE_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[DIAGNOSTIC_SCENE_KEY] = json.loads(
        str(factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY])
    )
    payload.update(
        {
            "diagnostic_only": True,
            "source_review_run_id": SOURCE_REVIEW_RUN_ID,
            "source_review_artifact_id": SOURCE_REVIEW_ARTIFACT_ID,
            "source_review_artifact_sha256": SOURCE_REVIEW_ARTIFACT_SHA256,
            "source_review_variant": SOURCE_REVIEW_VARIANT,
            "source_review_finding": SOURCE_REVIEW_FINDING,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "approved_down_v20_changed": False,
            "left_direction_changed": False,
            "right_direction_changed": False,
            "onehand_up_changed": False,
            "twohand_up_action_data_changed": False,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "weapon_geometry_deformed": False,
            "materials_changed": False,
            "manual_review_required": True,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    base_entry.create_combat_idle_down_actions_v01 = (
        create_attack_sword_directional_cycle_actions_v21_pass26
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_cycle
    base_entry._write_contact_sheet_combat_idle_down_v01 = _write_cycle_sheet
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    pass29_adapter.depth_search_adapter.pass22_adapter._HEAD_DEPTH_CACHE.clear()
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
