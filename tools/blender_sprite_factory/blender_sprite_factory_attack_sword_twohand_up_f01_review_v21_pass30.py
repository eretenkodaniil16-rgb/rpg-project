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
import blender_sprite_factory_attack_sword_directional_cycle_v21 as directional_cycle
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass30 import (
    APPROVED_REFERENCE_ACTION_ID,
    APPROVED_REFERENCE_DIRECTION,
    APPROVED_REFERENCE_FRAME,
    CORRECTION_PASS,
    REVIEW_ARM_BLEND,
    REVIEW_SELECTIONS,
    REVIEW_SOURCE_FRAMES,
    REVIEW_VARIANTS_PER_SOURCE,
    SOURCE_DIAGNOSTIC_ARTIFACT_ID,
    SOURCE_DIAGNOSTIC_ARTIFACT_SHA256,
    SOURCE_DIAGNOSTIC_RUN_ID,
    SOURCE_SELECTED_ARM_BLEND,
    SOURCE_SELECTED_CAMERA_MARGIN_PIXELS,
    SOURCE_SELECTED_FRAME,
    SOURCE_SELECTED_HEAD_CLEARANCE_PIXELS,
    SOURCE_SELECTED_SCREEN_PROJECTION,
    SOURCE_SELECTED_VISIBLE_BLADE_SAMPLES,
    SOURCE_SELECTED_WEAPON_OFFSET_DEGREES,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_REVIEW_REVISION,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f01_review_v21_pass30"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f01_review_v21_pass30.png"


def _candidate_identity(candidate: dict[str, object]) -> tuple[object, ...]:
    return (
        int(candidate["source_frame"]),
        float(candidate["arm_blend"]),
        str(candidate["depth_branch"]),
        float(candidate["screen_projection"]),
        float(candidate["offset_degrees"]),
    )


def _review_candidates(
    candidates: list[dict[str, object]],
) -> tuple[tuple[str, dict[str, object]], ...]:
    if not candidates:
        return ()
    continuity = candidates[0]
    by_clearance = sorted(
        candidates,
        key=lambda item: (
            -float(item["head_clearance_pixels"]),
            -int(item["visible_blade_samples"]),
            -float(item["screen_projection"]),
            abs(float(item["offset_degrees"])),
            0 if item["depth_branch"] == "source" else 1,
        ),
    )
    clearance = by_clearance[0]
    if _candidate_identity(clearance) == _candidate_identity(continuity):
        clearance = next(
            (
                item
                for item in by_clearance[1:]
                if _candidate_identity(item) != _candidate_identity(continuity)
            ),
            continuity,
        )
    return (
        (REVIEW_SELECTIONS[0], continuity),
        (REVIEW_SELECTIONS[1], clearance),
    )


def _render_reference(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
) -> tuple[factory.FrameArtifact, dict[str, object]]:
    config = context.config
    action = factory.bpy.data.actions.get(
        f"{config.character_id}_{APPROVED_REFERENCE_ACTION_ID}"
    )
    if action is None:
        raise RuntimeError(
            "two-hand up f01 review approved reference action is missing: "
            f"{APPROVED_REFERENCE_ACTION_ID}"
        )
    weapon_adapter._set_v12_weapon(
        TARGET_GRIP_ID,
        APPROVED_REFERENCE_DIRECTION,
    )
    factory._assign_action(context.rig, action)
    context.rig.rotation_euler[2] = math.radians(
        config.directions[APPROVED_REFERENCE_DIRECTION]
    )
    factory.bpy.context.scene.frame_set(APPROVED_REFERENCE_FRAME)
    factory.bpy.context.view_layer.update()
    artifact, _ = export_adapter._render_candidate(
        context,
        animation_id="attack_sword_01_twohand_down_f01_approved_reference_v20",
        direction=APPROVED_REFERENCE_DIRECTION,
        frame_number=APPROVED_REFERENCE_FRAME,
        raw_dir=run_dir / "raw",
        frame_dir=run_dir / "frames",
        output_name=(
            f"{config.character_id}_attack_sword_01_twohand_down_"
            f"f01_approved_reference_v20_proxy_{context.proxy_revision}.png"
        ),
        fixed_scale=calibration.scale,
        fixed_center_x=calibration.source_center_x,
    )
    edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
    touched = {edge: count for edge, count in edge_counts.items() if count > 0}
    if touched:
        raise RuntimeError(
            "two-hand up f01 review approved reference touched canvas edges: "
            f"{touched}"
        )
    return artifact, {
        "label": "approved_down_f01",
        "action_id": APPROVED_REFERENCE_ACTION_ID,
        "direction": APPROVED_REFERENCE_DIRECTION,
        "frame": APPROVED_REFERENCE_FRAME,
        "edge_counts": edge_counts,
    }


def _render_up_candidate(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    action: object,
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    selection: str,
    candidate: dict[str, object],
    column_index: int,
) -> tuple[factory.FrameArtifact, dict[str, object]]:
    config = context.config
    weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
    factory._assign_action(context.rig, action)
    context.rig.rotation_euler[2] = math.radians(
        config.directions[TARGET_DIRECTION]
    )
    factory.bpy.context.scene.frame_set(TARGET_FRAME)
    factory.bpy.context.view_layer.update()
    applied_arm_deltas = pass29_adapter._set_arm_blend(
        context,
        target_rotations,
        source_rotations,
        float(candidate["arm_blend"]),
    )
    objects = directional_cycle._visible_weapon_objects(
        TARGET_GRIP_ID,
        TARGET_DIRECTION,
    )
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = pass02_adapter._weapon_world_direction(objects)
    pivot = pass02_adapter._weapon_pivot(objects)
    target_direction, source_projection, applied_projection = (
        pass29_adapter._target_direction(
            current_direction,
            requested_projection=float(candidate["requested_screen_projection"]),
            offset_degrees=float(candidate["offset_degrees"]),
            depth_branch=str(candidate["depth_branch"]),
        )
    )
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=target_direction,
    )
    source_frame = int(candidate["source_frame"])
    try:
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id=(
                "attack_sword_01_twohand_up_f01_review_v21_pass30_"
                f"source_{source_frame}_{selection}"
            ),
            direction=TARGET_DIRECTION,
            frame_number=TARGET_FRAME,
            raw_dir=run_dir / "raw",
            frame_dir=run_dir / "frames",
            output_name=(
                f"{config.character_id}_attack_sword_01_twohand_up_f01_"
                f"review_v21_pass30_c{column_index:02d}_source_{source_frame}_"
                f"{selection}_proxy_{context.proxy_revision}.png"
            ),
            fixed_scale=calibration.scale,
            fixed_center_x=calibration.source_center_x,
        )
        edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
        touched = {
            edge: count for edge, count in edge_counts.items() if count > 0
        }
        if touched:
            raise RuntimeError(
                "two-hand up f01 review candidate touched canvas edges: "
                f"source={source_frame}; selection={selection}; edges={touched}"
            )
        return artifact, {
            "label": f"source_{source_frame}_{selection}",
            "selection": selection,
            "source_frame": source_frame,
            "arm_blend": float(candidate["arm_blend"]),
            "depth_branch": str(candidate["depth_branch"]),
            "source_projection": float(source_projection),
            "requested_screen_projection": float(
                candidate["requested_screen_projection"]
            ),
            "screen_projection": float(applied_projection),
            "offset_degrees": float(candidate["offset_degrees"]),
            "head_clearance_pixels": float(
                candidate["head_clearance_pixels"]
            ),
            "visible_blade_samples": int(
                candidate["visible_blade_samples"]
            ),
            "occluded_blade_samples": int(
                candidate["occluded_blade_samples"]
            ),
            "camera_margin_pixels": float(
                candidate["camera_margin_pixels"]
            ),
            "edge_counts": edge_counts,
            "applied_arm_deltas_degrees": applied_arm_deltas,
        }
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        pass29_adapter._restore_arm(context, target_rotations)


def _render_review(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    calibrations = calibration_adapter._direction_calibrations(context, run_dir)
    up_action = factory.bpy.data.actions.get(
        f"{config.character_id}_{TARGET_ACTION_ID}"
    )
    if up_action is None:
        raise RuntimeError(
            "two-hand up f01 review action is missing: " f"{TARGET_ACTION_ID}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    artifacts: list[factory.FrameArtifact] = []
    columns: list[dict[str, object]] = []
    target_rotations: dict[str, object] = {}

    try:
        reference_artifact, reference_metadata = _render_reference(
            context,
            run_dir,
            calibration=calibrations[APPROVED_REFERENCE_DIRECTION],
        )
        artifacts.append(reference_artifact)
        columns.append(reference_metadata)

        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, up_action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        target_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
        source_rotations_by_frame = {
            source_frame: pass29_adapter._capture_arm(context, source_frame)
            for source_frame in REVIEW_SOURCE_FRAMES
        }

        for source_frame in REVIEW_SOURCE_FRAMES:
            candidates, _ = pass29_adapter._evaluate_arm_pose(
                context,
                target_rotations=target_rotations,
                source_rotations=source_rotations_by_frame[source_frame],
                source_frame=source_frame,
                source_frame_order=REVIEW_SOURCE_FRAMES.index(source_frame),
                arm_blend=REVIEW_ARM_BLEND,
            )
            selections = _review_candidates(candidates)
            if len(selections) != REVIEW_VARIANTS_PER_SOURCE:
                raise RuntimeError(
                    "two-hand up f01 review did not produce two variants for "
                    f"source f{source_frame:02d}; candidates={len(candidates)}"
                )
            for selection, candidate in selections:
                artifact, metadata = _render_up_candidate(
                    context,
                    run_dir,
                    calibration=calibrations[TARGET_DIRECTION],
                    action=up_action,
                    target_rotations=target_rotations,
                    source_rotations=source_rotations_by_frame[source_frame],
                    selection=selection,
                    candidate=candidate,
                    column_index=len(artifacts) + 1,
                )
                artifacts.append(artifact)
                columns.append(metadata)

        expected_count = 1 + len(REVIEW_SOURCE_FRAMES) * REVIEW_VARIANTS_PER_SOURCE
        if len(artifacts) != expected_count:
            raise RuntimeError(
                "two-hand up f01 review artifact count drifted: "
                f"expected {expected_count}, got {len(artifacts)}"
            )
        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_REVIEW_REVISION,
            "review_arm_blend": REVIEW_ARM_BLEND,
            "review_source_frames": list(REVIEW_SOURCE_FRAMES),
            "review_selections": list(REVIEW_SELECTIONS),
            "columns": columns,
            "manual_selection_required": True,
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


def _write_review_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    expected_count = 1 + len(REVIEW_SOURCE_FRAMES) * REVIEW_VARIANTS_PER_SOURCE
    if len(artifacts) != expected_count:
        raise RuntimeError(
            "two-hand up f01 review sheet artifact count drifted: "
            f"expected {expected_count}, got {len(artifacts)}"
        )
    tile_width = int(config.technical.canvas_width)
    tile_height = int(config.technical.canvas_height)
    width = tile_width * len(artifacts)
    height = tile_height
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
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
        "human_warrior_m01_attack_sword_twohand_up_f01_review_v21_pass30",
        width=width,
        height=height,
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
            "source_diagnostic_run_id": SOURCE_DIAGNOSTIC_RUN_ID,
            "source_diagnostic_artifact_id": SOURCE_DIAGNOSTIC_ARTIFACT_ID,
            "source_diagnostic_artifact_sha256": (
                SOURCE_DIAGNOSTIC_ARTIFACT_SHA256
            ),
            "source_selected_candidate": {
                "source_frame": SOURCE_SELECTED_FRAME,
                "arm_blend": SOURCE_SELECTED_ARM_BLEND,
                "screen_projection": SOURCE_SELECTED_SCREEN_PROJECTION,
                "weapon_offset_degrees": (
                    SOURCE_SELECTED_WEAPON_OFFSET_DEGREES
                ),
                "head_clearance_pixels": (
                    SOURCE_SELECTED_HEAD_CLEARANCE_PIXELS
                ),
                "visible_blade_samples": (
                    SOURCE_SELECTED_VISIBLE_BLADE_SAMPLES
                ),
                "camera_margin_pixels": (
                    SOURCE_SELECTED_CAMERA_MARGIN_PIXELS
                ),
            },
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
    base_entry.render_pilot_combat_idle_down_v01 = _render_review
    base_entry._write_contact_sheet_combat_idle_down_v01 = _write_review_sheet
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    pass29_adapter.depth_search_adapter.pass22_adapter._HEAD_DEPTH_CACHE.clear()
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
