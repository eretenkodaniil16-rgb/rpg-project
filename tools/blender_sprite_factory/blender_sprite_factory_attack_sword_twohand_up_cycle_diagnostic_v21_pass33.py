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
import blender_sprite_factory_attack_sword_twohand_up_f01_review_v21_pass30 as pass30_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass33 import (
    ARM_BLEND,
    CORRECTION_PASS,
    DEPTH_BRANCH,
    FRAME_ORDER,
    REQUESTED_SCREEN_PROJECTION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FRAME,
    SOURCE_REVIEW_ARTIFACT_ID,
    SOURCE_REVIEW_ARTIFACT_SHA256,
    SOURCE_REVIEW_COLUMN,
    SOURCE_REVIEW_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_CYCLE_DIAGNOSTIC_REVISION,
    VALIDATED_CAMERA_MARGIN_PIXELS,
    VALIDATED_HEAD_CLEARANCE_PIXELS,
    VALIDATED_SCREEN_PROJECTION,
    VALIDATED_VISIBLE_BLADE_SAMPLES,
    WEAPON_OFFSET_DEGREES,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_cycle_diagnostic_v21_pass33"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_cycle_diagnostic_v21_pass33.png"


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
            "two-hand up pass33 cycle diagnostic action is missing: "
            f"{TARGET_ACTION_ID}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    artifacts: list[factory.FrameArtifact] = []
    metrics: dict[str, object] = {}
    target_rotations: dict[str, object] = {}

    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        target_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
        source_rotations = pass29_adapter._capture_arm(context, SOURCE_FRAME)

        selected_candidate: dict[str, object] = {
            "source_frame": SOURCE_FRAME,
            "source_frame_order": 6,
            "arm_blend": ARM_BLEND,
            "depth_branch": DEPTH_BRANCH,
            "offset_degrees": WEAPON_OFFSET_DEGREES,
            "source_projection": 0.9441554673868896,
            "requested_screen_projection": REQUESTED_SCREEN_PROJECTION,
            "screen_projection": VALIDATED_SCREEN_PROJECTION,
            "head_clearance_pixels": VALIDATED_HEAD_CLEARANCE_PIXELS,
            "visible_blade_samples": VALIDATED_VISIBLE_BLADE_SAMPLES,
            "occluded_blade_samples": 0,
            "camera_margin_pixels": VALIDATED_CAMERA_MARGIN_PIXELS,
        }
        f01_artifact, f01_metrics = pass30_adapter._render_up_candidate(
            context,
            run_dir,
            calibration=calibration,
            action=action,
            target_rotations=target_rotations,
            source_rotations=source_rotations,
            selection="pass33_selected_f01",
            candidate=selected_candidate,
            column_index=1,
        )
        artifacts.append(f01_artifact)
        metrics["f01"] = f01_metrics

        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        raw_dir = run_dir / "raw"
        frame_dir = run_dir / "frames"
        for frame_number in FRAME_ORDER[1:]:
            artifact, _ = pass26_adapter._render_frame_v21_pass26(
                context,
                animation_id=TARGET_ACTION_ID,
                direction=TARGET_DIRECTION,
                frame_number=frame_number,
                raw_dir=raw_dir,
                frame_dir=frame_dir,
                output_name=(
                    f"{config.character_id}_{TARGET_ACTION_ID}_"
                    f"f{frame_number:02d}_pass33_proxy_{context.proxy_revision}.png"
                ),
                fixed_scale=calibration.scale,
                fixed_center_x=calibration.source_center_x,
                use_clearance_planner=True,
            )
            edge_counts = keypose_adapter._edge_alpha_counts(
                artifact.output_path
            )
            touched = {
                edge: count
                for edge, count in edge_counts.items()
                if count > 0
            }
            if REQUIRE_ZERO_EDGE_ALPHA and touched:
                raise RuntimeError(
                    "two-hand up pass33 cycle frame touched canvas edges: "
                    f"f{frame_number:02d}; {touched}"
                )
            artifacts.append(artifact)
            metrics[f"f{frame_number:02d}"] = {
                "edge_counts": edge_counts,
                "pass26_planner_used": True,
            }

        if tuple(item.frame_number for item in artifacts) != FRAME_ORDER:
            raise RuntimeError(
                "two-hand up pass33 cycle frame order drifted: "
                f"{[item.frame_number for item in artifacts]}"
            )
        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_CYCLE_DIAGNOSTIC_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "frame_order": list(FRAME_ORDER),
            "selected_f01": selected_candidate,
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
        if target_rotations:
            pass29_adapter._restore_arm(context, target_rotations)
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
        raise RuntimeError(
            "two-hand up pass33 cycle sheet frame order drifted"
        )
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
        "human_warrior_m01_attack_sword_twohand_up_cycle_diagnostic_v21_pass33",
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
            "source_review_column": SOURCE_REVIEW_COLUMN,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
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
