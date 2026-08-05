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
import blender_sprite_factory_attack_sword_directional_cycle_v21 as directional_cycle
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_review_v21_pass30 as pass30_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass34 import (
    ARM_BLEND_CANDIDATES,
    CONTINUITY_WEIGHT_FROM_CORRECTED_F01,
    CONTINUITY_WEIGHT_TO_ORIGINAL_F03,
    CORRECTED_F01_ARM_BLEND,
    CORRECTED_F01_DEPTH_BRANCH,
    CORRECTED_F01_FRAME,
    CORRECTED_F01_SCREEN_PROJECTION,
    CORRECTED_F01_SOURCE_FRAME,
    CORRECTED_F01_WEAPON_OFFSET_DEGREES,
    CORRECTION_PASS,
    MAX_ABS_WEAPON_OFFSET_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    NEXT_REFERENCE_FRAME,
    REQUIRE_ZERO_EDGE_ALPHA,
    REVIEW_VARIANT_COUNT,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    SOURCE_POSE_CODES,
    SOURCE_POSE_LABELS,
    TARGET_ABS_WEAPON_OFFSET_DEGREES,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f02_review_v21_pass34"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f02_review_v21_pass34.png"
CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass34.py"


def _blended_rotations(
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    blend: float,
) -> dict[str, object]:
    result: dict[str, object] = {}
    for bone_name in pass29_adapter.TARGET_BONES:
        target = target_rotations[bone_name]
        source = source_rotations[bone_name]
        value = target.copy()
        for axis_index in range(3):
            delta = pass29_adapter._shortest_angle_delta(
                float(target[axis_index]),
                float(source[axis_index]),
            )
            value[axis_index] = float(target[axis_index]) + delta * float(blend)
        result[bone_name] = value
    return result


def _arm_rms_degrees(
    first: dict[str, object],
    second: dict[str, object],
) -> float:
    squared: list[float] = []
    for bone_name in pass29_adapter.TARGET_BONES:
        first_value = first[bone_name]
        second_value = second[bone_name]
        for axis_index in range(3):
            delta = pass29_adapter._shortest_angle_delta(
                float(first_value[axis_index]),
                float(second_value[axis_index]),
            )
            squared.append(math.degrees(delta) ** 2)
    return math.sqrt(sum(squared) / float(len(squared)))


def _candidate_pose(
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    blend: float,
) -> dict[str, object]:
    return _blended_rotations(target_rotations, source_rotations, blend)


def _candidate_sort_key(candidate: dict[str, object]) -> tuple[object, ...]:
    offset = abs(float(candidate["offset_degrees"]))
    return (
        0 if offset <= TARGET_ABS_WEAPON_OFFSET_DEGREES else 1,
        offset,
        float(candidate["continuity_score"]),
        float(candidate["continuity_from_corrected_f01_rms_degrees"]),
        float(candidate["continuity_to_original_f03_rms_degrees"]),
        float(candidate["arm_blend"]),
        -float(candidate["screen_projection"]),
        -float(candidate["head_clearance_pixels"]),
        -int(candidate["visible_blade_samples"]),
        0 if candidate["depth_branch"] == "source" else 1,
    )


def _select_diverse_candidates(
    candidates: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    selected: list[dict[str, object]] = []
    seen_poses: set[tuple[object, ...]] = set()
    for candidate in sorted(candidates, key=_candidate_sort_key):
        pose_key = (
            int(candidate["source_pose_code"]),
            round(float(candidate["arm_blend"]), 4),
            round(float(candidate["offset_degrees"]), 3),
            round(float(candidate["screen_projection"]), 4),
            str(candidate["depth_branch"]),
        )
        if pose_key in seen_poses:
            continue
        seen_poses.add(pose_key)
        selected.append(candidate)
        if len(selected) == REVIEW_VARIANT_COUNT:
            break
    return tuple(selected)


def _evaluate_candidates(
    context: factory.BuildContext,
    *,
    target_f02_rotations: dict[str, object],
    corrected_f01_rotations: dict[str, object],
    original_f03_rotations: dict[str, object],
    source_rotations_by_code: dict[int, dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    original_target_frame = pass29_adapter.TARGET_FRAME
    pass29_adapter.TARGET_FRAME = TARGET_FRAME
    all_candidates: list[dict[str, object]] = []
    safe_counts: dict[str, int] = {}
    try:
        for arm_blend in ARM_BLEND_CANDIDATES:
            for source_order, source_code in enumerate(SOURCE_POSE_CODES):
                source_rotations = source_rotations_by_code[int(source_code)]
                candidates, _ = pass29_adapter._evaluate_arm_pose(
                    context,
                    target_rotations=target_f02_rotations,
                    source_rotations=source_rotations,
                    source_frame=int(source_code),
                    source_frame_order=source_order,
                    arm_blend=float(arm_blend),
                )
                accepted_count = 0
                candidate_arm_pose = _candidate_pose(
                    target_f02_rotations,
                    source_rotations,
                    float(arm_blend),
                )
                continuity_from_f01 = _arm_rms_degrees(
                    corrected_f01_rotations,
                    candidate_arm_pose,
                )
                continuity_to_f03 = _arm_rms_degrees(
                    candidate_arm_pose,
                    original_f03_rotations,
                )
                continuity_score = (
                    continuity_from_f01
                    * CONTINUITY_WEIGHT_FROM_CORRECTED_F01
                    + continuity_to_f03
                    * CONTINUITY_WEIGHT_TO_ORIGINAL_F03
                )
                for candidate in candidates:
                    if (
                        abs(float(candidate["offset_degrees"]))
                        > MAX_ABS_WEAPON_OFFSET_DEGREES
                        or float(candidate["head_clearance_pixels"])
                        < MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
                        or int(candidate["visible_blade_samples"])
                        < MIN_VISIBLE_BLADE_SAMPLES
                        or float(candidate["camera_margin_pixels"])
                        < MIN_CAMERA_MARGIN_PIXELS
                    ):
                        continue
                    enriched = dict(candidate)
                    enriched.update(
                        {
                            "source_pose_code": int(source_code),
                            "source_pose_label": SOURCE_POSE_LABELS[int(source_code)],
                            "continuity_from_corrected_f01_rms_degrees": continuity_from_f01,
                            "continuity_to_original_f03_rms_degrees": continuity_to_f03,
                            "continuity_score": continuity_score,
                        }
                    )
                    all_candidates.append(enriched)
                    accepted_count += 1
                safe_counts[
                    f"{SOURCE_POSE_LABELS[int(source_code)]}_blend_{float(arm_blend):.2f}"
                ] = accepted_count
    finally:
        pass29_adapter.TARGET_FRAME = original_target_frame
    return all_candidates, safe_counts


def _render_corrected_f01_reference(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    action: object,
    original_f01_rotations: dict[str, object],
    original_f05_rotations: dict[str, object],
) -> tuple[factory.FrameArtifact, dict[str, object]]:
    candidate = {
        "source_frame": CORRECTED_F01_SOURCE_FRAME,
        "source_frame_order": 0,
        "arm_blend": CORRECTED_F01_ARM_BLEND,
        "depth_branch": CORRECTED_F01_DEPTH_BRANCH,
        "offset_degrees": CORRECTED_F01_WEAPON_OFFSET_DEGREES,
        "source_projection": 0.9441554673868896,
        "requested_screen_projection": CORRECTED_F01_SCREEN_PROJECTION,
        "screen_projection": CORRECTED_F01_SCREEN_PROJECTION,
        "head_clearance_pixels": 2.565845489501953,
        "visible_blade_samples": 612,
        "occluded_blade_samples": 0,
        "camera_margin_pixels": 32.02795886993408,
    }
    return pass30_adapter._render_up_candidate(
        context,
        run_dir,
        calibration=calibration,
        action=action,
        target_rotations=original_f01_rotations,
        source_rotations=original_f05_rotations,
        selection="pass34_corrected_f01_reference",
        candidate=candidate,
        column_index=1,
    )


def _render_f02_candidate(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    action: object,
    target_f02_rotations: dict[str, object],
    source_rotations: dict[str, object],
    candidate: dict[str, object],
    variant_index: int,
) -> tuple[factory.FrameArtifact, dict[str, object]]:
    config = context.config
    scene = factory.bpy.context.scene
    weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
    factory._assign_action(context.rig, action)
    context.rig.rotation_euler[2] = math.radians(config.directions[TARGET_DIRECTION])
    scene.frame_set(TARGET_FRAME)
    factory.bpy.context.view_layer.update()
    applied_arm_deltas = pass29_adapter._set_arm_blend(
        context,
        target_f02_rotations,
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
    try:
        output_name = (
            f"{config.character_id}_attack_sword_01_twohand_up_f02_"
            f"review_v21_pass34_c{variant_index:02d}_"
            f"{candidate['source_pose_label']}_"
            f"blend_{float(candidate['arm_blend']):.2f}_"
            f"proxy_{context.proxy_revision}.png"
        )
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id=(
                "attack_sword_01_twohand_up_f02_review_v21_pass34_"
                f"candidate_{variant_index:02d}"
            ),
            direction=TARGET_DIRECTION,
            frame_number=TARGET_FRAME,
            raw_dir=run_dir / "raw",
            frame_dir=run_dir / "frames",
            output_name=output_name,
            fixed_scale=calibration.scale,
            fixed_center_x=calibration.source_center_x,
        )
        edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
        touched = {
            edge: count for edge, count in edge_counts.items() if count > 0
        }
        if REQUIRE_ZERO_EDGE_ALPHA and touched:
            raise RuntimeError(
                "two-hand up f02 pass34 candidate touched canvas edges: "
                f"candidate={variant_index}; edges={touched}"
            )
        metadata = {
            **candidate,
            "variant_index": variant_index,
            "source_projection": float(source_projection),
            "screen_projection": float(applied_projection),
            "edge_counts": edge_counts,
            "applied_arm_deltas_degrees": applied_arm_deltas,
        }
        print(
            "ATTACK_SWORD_TWOHAND_UP_F02_REVIEW_V21_PASS34_CANDIDATE="
            f"variant:{variant_index};"
            f"source:{candidate['source_pose_label']};"
            f"blend:{float(candidate['arm_blend']):.2f};"
            f"offset:{float(candidate['offset_degrees']):.1f};"
            f"projection:{float(applied_projection):.3f};"
            f"continuity:{float(candidate['continuity_score']):.3f};"
            f"clearance:{float(candidate['head_clearance_pixels']):.3f};"
            f"visible:{int(candidate['visible_blade_samples'])};"
            f"margin:{float(candidate['camera_margin_pixels']):.3f}"
        )
        return artifact, metadata
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        pass29_adapter._restore_arm(context, target_f02_rotations)


def _render_original_f03_reference(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    action: object,
) -> tuple[factory.FrameArtifact, dict[str, object]]:
    config = context.config
    weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
    factory._assign_action(context.rig, action)
    context.rig.rotation_euler[2] = math.radians(config.directions[TARGET_DIRECTION])
    factory.bpy.context.scene.frame_set(NEXT_REFERENCE_FRAME)
    factory.bpy.context.view_layer.update()
    artifact, _ = export_adapter._render_candidate(
        context,
        animation_id="attack_sword_01_twohand_up_f03_original_reference_v21",
        direction=TARGET_DIRECTION,
        frame_number=NEXT_REFERENCE_FRAME,
        raw_dir=run_dir / "raw",
        frame_dir=run_dir / "frames",
        output_name=(
            f"{config.character_id}_attack_sword_01_twohand_up_f03_"
            f"original_reference_v21_proxy_{context.proxy_revision}.png"
        ),
        fixed_scale=calibration.scale,
        fixed_center_x=calibration.source_center_x,
    )
    edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
    touched = {edge: count for edge, count in edge_counts.items() if count > 0}
    if REQUIRE_ZERO_EDGE_ALPHA and touched:
        raise RuntimeError(
            "two-hand up f03 reference touched canvas edges: " f"{touched}"
        )
    return artifact, {
        "label": "original_f03_reference",
        "frame": NEXT_REFERENCE_FRAME,
        "edge_counts": edge_counts,
    }


def _render_review(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    calibration = calibration_adapter._direction_calibrations(context, run_dir)[
        TARGET_DIRECTION
    ]
    action = factory.bpy.data.actions.get(f"{config.character_id}_{TARGET_ACTION_ID}")
    if action is None:
        raise RuntimeError(
            "two-hand up f02 pass34 review action is missing: " f"{TARGET_ACTION_ID}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    artifacts: list[factory.FrameArtifact] = []
    columns: list[dict[str, object]] = []
    original_f02_rotations: dict[str, object] = {}

    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(config.directions[TARGET_DIRECTION])
        original_f01_rotations = pass29_adapter._capture_arm(
            context,
            CORRECTED_F01_FRAME,
        )
        original_f02_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
        original_f03_rotations = pass29_adapter._capture_arm(
            context,
            NEXT_REFERENCE_FRAME,
        )
        original_f04_rotations = pass29_adapter._capture_arm(context, 4)
        original_f05_rotations = pass29_adapter._capture_arm(
            context,
            CORRECTED_F01_SOURCE_FRAME,
        )
        original_f06_rotations = pass29_adapter._capture_arm(context, 6)
        original_f07_rotations = pass29_adapter._capture_arm(context, 7)
        original_f08_rotations = pass29_adapter._capture_arm(context, 8)
        corrected_f01_rotations = _blended_rotations(
            original_f01_rotations,
            original_f05_rotations,
            CORRECTED_F01_ARM_BLEND,
        )
        source_rotations_by_code = {
            101: corrected_f01_rotations,
            3: original_f03_rotations,
            5: original_f05_rotations,
            4: original_f04_rotations,
            6: original_f06_rotations,
            7: original_f07_rotations,
            8: original_f08_rotations,
        }

        all_candidates, safe_counts = _evaluate_candidates(
            context,
            target_f02_rotations=original_f02_rotations,
            corrected_f01_rotations=corrected_f01_rotations,
            original_f03_rotations=original_f03_rotations,
            source_rotations_by_code=source_rotations_by_code,
        )
        selected_candidates = _select_diverse_candidates(all_candidates)
        if not selected_candidates:
            raise RuntimeError(
                "two-hand up f02 pass34 found no continuity-safe candidate; "
                f"safe_counts={safe_counts}"
            )

        f01_artifact, f01_metadata = _render_corrected_f01_reference(
            context,
            run_dir,
            calibration=calibration,
            action=action,
            original_f01_rotations=original_f01_rotations,
            original_f05_rotations=original_f05_rotations,
        )
        artifacts.append(f01_artifact)
        columns.append({"label": "corrected_f01_reference", **f01_metadata})

        for variant_index, candidate in enumerate(selected_candidates, start=1):
            artifact, metadata = _render_f02_candidate(
                context,
                run_dir,
                calibration=calibration,
                action=action,
                target_f02_rotations=original_f02_rotations,
                source_rotations=source_rotations_by_code[
                    int(candidate["source_pose_code"])
                ],
                candidate=candidate,
                variant_index=variant_index,
            )
            artifacts.append(artifact)
            columns.append({"label": f"f02_candidate_{variant_index:02d}", **metadata})

        f03_artifact, f03_metadata = _render_original_f03_reference(
            context,
            run_dir,
            calibration=calibration,
            action=action,
        )
        artifacts.append(f03_artifact)
        columns.append(f03_metadata)

        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F02_CONTINUITY_REVIEW_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "target_frame": TARGET_FRAME,
            "source_pose_labels": SOURCE_POSE_LABELS,
            "arm_blends_evaluated": list(ARM_BLEND_CANDIDATES),
            "maximum_abs_weapon_offset_degrees": MAX_ABS_WEAPON_OFFSET_DEGREES,
            "target_abs_weapon_offset_degrees": TARGET_ABS_WEAPON_OFFSET_DEGREES,
            "continuity_weight_from_corrected_f01": CONTINUITY_WEIGHT_FROM_CORRECTED_F01,
            "continuity_weight_to_original_f03": CONTINUITY_WEIGHT_TO_ORIGINAL_F03,
            "safe_counts": safe_counts,
            "columns": columns,
            "manual_selection_required": True,
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        print(
            "ATTACK_SWORD_TWOHAND_UP_F02_REVIEW_V21_PASS34="
            f"candidates:{len(selected_candidates)};"
            f"offsets:{[float(item['offset_degrees']) for item in selected_candidates]};"
            f"sources:{[str(item['source_pose_label']) for item in selected_candidates]};"
            f"blends:{[float(item['arm_blend']) for item in selected_candidates]}"
        )
        return artifacts
    finally:
        if original_f02_rotations:
            pass29_adapter._restore_arm(context, original_f02_rotations)
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
    expected_count = REVIEW_VARIANT_COUNT + 2
    if len(artifacts) != expected_count:
        raise RuntimeError(
            "two-hand up f02 pass34 review sheet count drifted: "
            f"expected {expected_count}, got {len(artifacts)}"
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
        image = factory.bpy.data.images.load(str(artifact.output_path), check_existing=False)
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
        "human_warrior_m01_attack_sword_twohand_up_f02_review_v21_pass34",
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
            "source_failed_run_id": SOURCE_FAILED_RUN_ID,
            "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
            "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
            "source_failure": SOURCE_FAILURE,
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
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
