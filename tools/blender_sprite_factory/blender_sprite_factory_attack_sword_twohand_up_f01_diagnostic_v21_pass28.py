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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass27 as pass27_adapter
import blender_sprite_factory_attack_sword_onehand_up_depth_search_diagnostic_v21 as pass23_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass28 import (
    FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_GRIP_ID,
    TWOHAND_UP_FALLBACK_REVISION,
    USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f01_diagnostic_v21_pass28"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f01_diagnostic_v21.png"
TARGET_FRAME = 1
ORIGINAL_CLEARANCE = (
    pass27_adapter.depth_aware_adapter._depth_aware_visible_blade_head_clearance
)


def _render_diagnostic(
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
            "two-hand up f01 pass28 diagnostic action is missing: "
            f"{TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        factory.bpy.context.scene.frame_set(TARGET_FRAME)
        factory.bpy.context.view_layer.update()

        output_name = (
            f"{config.character_id}_attack_sword_01_twohand_up_"
            f"f01_diagnostic_v21_pass28_proxy_{context.proxy_revision}.png"
        )
        artifact, _ = pass27_adapter._render_frame_v21_pass27(
            context,
            animation_id=TARGET_ACTION_ID,
            direction=TARGET_DIRECTION,
            frame_number=TARGET_FRAME,
            raw_dir=run_dir / "raw",
            frame_dir=run_dir / "frames",
            output_name=output_name,
            fixed_scale=calibration.scale,
            fixed_center_x=calibration.source_center_x,
            use_clearance_planner=True,
        )
        key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{TARGET_FRAME:02d}"
        metrics = json.loads(
            str(
                factory.bpy.context.scene[
                    "attack_sword_directional_cycle_v21_pass02_metrics"
                ]
            )
        )
        if key not in metrics:
            raise RuntimeError(
                "two-hand up f01 pass28 diagnostic metrics missing: " + key
            )
        payload = {
            "revision": TWOHAND_UP_FALLBACK_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "target_frame": TARGET_FRAME,
            "fully_occluded_candidates_are_rejected": (
                FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED
            ),
            "minimum_visible_blade_sample_guard_used": (
                USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD
            ),
            "selected_metrics": metrics[key],
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        return [artifact]
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_one_frame_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    if len(artifacts) != 1 or artifacts[0].frame_number != TARGET_FRAME:
        raise RuntimeError(
            "two-hand up f01 pass28 diagnostic expected exactly frame f01"
        )
    artifact = artifacts[0]
    image = factory.bpy.data.images.load(
        str(artifact.output_path),
        check_existing=False,
    )
    try:
        image.file_format = "PNG"
        image.filepath_raw = str(output_path)
        image.save()
    finally:
        factory.bpy.data.images.remove(image)
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
            "source_failed_run_id": SOURCE_FAILED_RUN_ID,
            "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
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
    base_entry.render_pilot_combat_idle_down_v01 = _render_diagnostic
    base_entry._write_contact_sheet_combat_idle_down_v01 = _write_one_frame_sheet
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    pass27_adapter.depth_aware_adapter._depth_aware_visible_blade_head_clearance = (
        pass23_adapter._depth_search_visible_blade_head_clearance
    )
    try:
        pass27_adapter.depth_aware_adapter._HEAD_DEPTH_CACHE.clear()
        return base_entry.main()
    finally:
        pass27_adapter.depth_aware_adapter._depth_aware_visible_blade_head_clearance = (
            ORIGINAL_CLEARANCE
        )


if __name__ == "__main__":
    raise SystemExit(main())
