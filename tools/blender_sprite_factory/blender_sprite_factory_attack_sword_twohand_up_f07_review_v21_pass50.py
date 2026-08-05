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
import blender_sprite_factory_attack_sword_twohand_up_f02_review_v21_pass34 as pass34_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass50 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    DEPTH_BRANCH_CANDIDATES,
    MAX_ABS_WEAPON_OFFSET_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    NEXT_REFERENCE_FRAME,
    PREVIOUS_REFERENCE_FRAME,
    RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW,
    REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE,
    REVIEW_VARIANT_COUNT,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    SOURCE_FRAME_CANDIDATES,
    SOURCE_FRAME_LABELS,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F07_CONTINUITY_REVIEW_REVISION,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f07_review_v21_pass50"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f07_review_v21_pass50.png"
CORRECTION_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass50.py"

ORIGINAL_TARGET_FRAME = pass29_adapter.TARGET_FRAME
ORIGINAL_SCREEN_PROJECTIONS = pass29_adapter.SCREEN_PROJECTION_CANDIDATES
ORIGINAL_ANGLE_OFFSETS = pass29_adapter.ANGLE_OFFSET_CANDIDATES
ORIGINAL_DEPTH_BRANCHES = pass29_adapter.DEPTH_BRANCH_CANDIDATES
ORIGINAL_MIN_CLEARANCE = pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
ORIGINAL_MIN_VISIBLE = pass29_adapter.MIN_VISIBLE_BLADE_SAMPLES
ORIGINAL_MIN_MARGIN = pass29_adapter.MIN_CAMERA_MARGIN_PIXELS


def _candidate_sort_key(candidate: dict[str, object]) -> tuple[object, ...]:
    from_f06 = float(candidate["continuity_from_f06_rms_degrees"])
    to_f08 = float(candidate["continuity_to_f08_rms_degrees"])
    return (
        max(from_f06, to_f08),
        abs(from_f06 - to_f08),
        from_f06 + to_f08,
        0 if str(candidate["depth_branch"]) == "source" else 1,
        abs(float(candidate["offset_degrees"])),
        -float(candidate["screen_projection"]),
        -int(candidate["visible_blade_samples"]),
        -float(candidate["head_clearance_pixels"]),
        -float(candidate["camera_margin_pixels"]),
        int(candidate["source_frame_order"]),
    )


def _select_review_candidates(
    candidates: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    ordered = sorted(candidates, key=_candidate_sort_key)
    selected: list[dict[str, object]] = []
    selected_ids: set[int] = set()
    seen_arm_profiles: set[tuple[int, float]] = set()

    for candidate in ordered:
        arm_key = (
            int(candidate["source_frame"]),
            round(float(candidate["arm_blend"]), 4),
        )
        if arm_key in seen_arm_profiles:
            continue
        seen_arm_profiles.add(arm_key)
        selected.append(candidate)
        selected_ids.add(id(candidate))
        if len(selected) == REVIEW_VARIANT_COUNT:
            return tuple(selected)

    seen_full_profiles: set[tuple[object, ...]] = set()
    for candidate in ordered:
        if id(candidate) in selected_ids:
            continue
        full_key = (
            int(candidate["source_frame"]),
            round(float(candidate["arm_blend"]), 4),
            str(candidate["depth_branch"]),
            round(float(candidate["offset_degrees"]), 3),
            round(float(candidate["screen_projection"]), 4),
        )
        if full_key in seen_full_profiles:
            continue
        seen_full_profiles.add(full_key)
        selected.append(candidate)
        if len(selected) == REVIEW_VARIANT_COUNT:
            break
    return tuple(selected)


def _evaluate_candidates(
    context: factory.BuildContext,
    *,
    target_rotations: dict[str, object],
    previous_rotations: dict[str, object],
    next_rotations: dict[str, object],
    source_rotations_by_frame: dict[int, dict[str, object]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    pass29_adapter.TARGET_FRAME = TARGET_FRAME
    pass29_adapter.SCREEN_PROJECTION_CANDIDATES = SCREEN_PROJECTION_CANDIDATES
    pass29_adapter.ANGLE_OFFSET_CANDIDATES = ANGLE_OFFSET_CANDIDATES
    pass29_adapter.DEPTH_BRANCH_CANDIDATES = DEPTH_BRANCH_CANDIDATES
    pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
        MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
    )
    pass29_adapter.MIN_VISIBLE_BLADE_SAMPLES = MIN_VISIBLE_BLADE_SAMPLES
    pass29_adapter.MIN_CAMERA_MARGIN_PIXELS = MIN_CAMERA_MARGIN_PIXELS

    candidates: list[dict[str, object]] = []
    safe_counts: dict[str, int] = {}
    try:
        for arm_blend in ARM_BLEND_CANDIDATES:
            for source_order, source_frame in enumerate(SOURCE_FRAME_CANDIDATES):
                source_rotations = source_rotations_by_frame[int(source_frame)]
                evaluated, _ = pass29_adapter._evaluate_arm_pose(
                    context,
                    target_rotations=target_rotations,
                    source_rotations=source_rotations,
                    source_frame=int(source_frame),
                    source_frame_order=source_order,
                    arm_blend=float(arm_blend),
                )
                candidate_pose = pass34_adapter._candidate_pose(
                    target_rotations,
                    source_rotations,
                    float(arm_blend),
                )
                from_f06 = pass34_adapter._arm_rms_degrees(
                    previous_rotations,
                    candidate_pose,
                )
                to_f08 = pass34_adapter._arm_rms_degrees(
                    candidate_pose,
                    next_rotations,
                )
                accepted_count = 0
                for candidate in evaluated:
                    if (
                        abs(float(candidate["offset_degrees"]))
                        > MAX_ABS_WEAPON_OFFSET_DEGREES
                    ):
                        continue
                    enriched = dict(candidate)
                    enriched.update(
                        {
                            "source_frame_label": SOURCE_FRAME_LABELS[
                                int(source_frame)
                            ],
                            "continuity_from_f06_rms_degrees": from_f06,
                            "continuity_to_f08_rms_degrees": to_f08,
                            "continuity_score": from_f06 + to_f08,
                            "maximum_transition_rms_degrees": max(
                                from_f06,
                                to_f08,
                            ),
                        }
                    )
                    candidates.append(enriched)
                    accepted_count += 1
                safe_counts[
                    f"{SOURCE_FRAME_LABELS[int(source_frame)]}_"
                    f"blend_{float(arm_blend):.2f}"
                ] = accepted_count
    finally:
        pass29_adapter.TARGET_FRAME = ORIGINAL_TARGET_FRAME
        pass29_adapter.SCREEN_PROJECTION_CANDIDATES = ORIGINAL_SCREEN_PROJECTIONS
        pass29_adapter.ANGLE_OFFSET_CANDIDATES = ORIGINAL_ANGLE_OFFSETS
        pass29_adapter.DEPTH_BRANCH_CANDIDATES = ORIGINAL_DEPTH_BRANCHES
        pass29_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
            ORIGINAL_MIN_CLEARANCE
        )
        pass29_adapter.MIN_VISIBLE_BLADE_SAMPLES = ORIGINAL_MIN_VISIBLE
        pass29_adapter.MIN_CAMERA_MARGIN_PIXELS = ORIGINAL_MIN_MARGIN
    return candidates, safe_counts


def _render_candidate(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    action: object,
    target_rotations: dict[str, object],
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
    try:
        output_name = (
            f"{config.character_id}_attack_sword_01_twohand_up_f07_"
            f"review_v21_pass50_c{variant_index:02d}_"
            f"{candidate['source_frame_label']}_"
            f"blend_{float(candidate['arm_blend']):.2f}_"
            f"proxy_{context.proxy_revision}.png"
        )
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id=(
                "attack_sword_01_twohand_up_f07_review_v21_pass50_"
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
        accepted_by_final_contract = not touched
        metadata = {
            **candidate,
            "variant_index": variant_index,
            "source_projection": float(source_projection),
            "screen_projection": float(applied_projection),
            "edge_counts": edge_counts,
            "edge_touching": bool(touched),
            "accepted_by_final_boundary_contract": accepted_by_final_contract,
            "applied_arm_deltas_degrees": applied_arm_deltas,
        }
        print(
            "ATTACK_SWORD_TWOHAND_UP_F07_REVIEW_V21_PASS50_CANDIDATE="
            f"variant:{variant_index};"
            f"source:{candidate['source_frame_label']};"
            f"blend:{float(candidate['arm_blend']):.2f};"
            f"branch:{candidate['depth_branch']};"
            f"offset:{float(candidate['offset_degrees']):.1f};"
            f"projection:{float(applied_projection):.3f};"
            f"from_f06:{float(candidate['continuity_from_f06_rms_degrees']):.3f};"
            f"to_f08:{float(candidate['continuity_to_f08_rms_degrees']):.3f};"
            f"clearance:{float(candidate['head_clearance_pixels']):.3f};"
            f"visible:{int(candidate['visible_blade_samples'])};"
            f"margin:{float(candidate['camera_margin_pixels']):.3f};"
            f"edges:{touched}"
        )
        if (
            REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE
            and touched
            and not RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
        ):
            raise RuntimeError(
                "two-hand up f07 pass50 candidate touched canvas edges: "
                f"candidate={variant_index}; edges={touched}"
            )
        return artifact, metadata
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        pass29_adapter._restore_arm(context, target_rotations)


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
            "two-hand up f07 pass50 review action is missing: "
            f"{TARGET_ACTION_ID}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    target_rotations: dict[str, object] = {}
    artifacts: list[factory.FrameArtifact] = []
    rendered_metadata: list[dict[str, object]] = []

    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        target_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
        previous_rotations = pass29_adapter._capture_arm(
            context,
            PREVIOUS_REFERENCE_FRAME,
        )
        next_rotations = pass29_adapter._capture_arm(
            context,
            NEXT_REFERENCE_FRAME,
        )
        source_rotations_by_frame = {
            int(frame): pass29_adapter._capture_arm(context, int(frame))
            for frame in SOURCE_FRAME_CANDIDATES
        }
        candidates, safe_counts = _evaluate_candidates(
            context,
            target_rotations=target_rotations,
            previous_rotations=previous_rotations,
            next_rotations=next_rotations,
            source_rotations_by_frame=source_rotations_by_frame,
        )
        selected = _select_review_candidates(candidates)
        if not selected:
            raise RuntimeError(
                "two-hand up f07 pass50 found no geometry-safe coordinated "
                f"candidate: safe_counts={safe_counts}"
            )

        for variant_index, candidate in enumerate(selected, start=1):
            artifact, metadata = _render_candidate(
                context,
                run_dir,
                calibration=calibration,
                action=action,
                target_rotations=target_rotations,
                source_rotations=source_rotations_by_frame[
                    int(candidate["source_frame"])
                ],
                candidate=candidate,
                variant_index=variant_index,
            )
            artifacts.append(artifact)
            rendered_metadata.append(metadata)

        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F07_CONTINUITY_REVIEW_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "target_frame": TARGET_FRAME,
            "previous_reference_frame": PREVIOUS_REFERENCE_FRAME,
            "next_reference_frame": NEXT_REFERENCE_FRAME,
            "target_bones": list(TARGET_BONES),
            "source_frame_candidates": list(SOURCE_FRAME_CANDIDATES),
            "geometry_safe_candidate_count": len(candidates),
            "geometry_safe_counts": safe_counts,
            "rendered_candidates": rendered_metadata,
            "manual_selection_required": True,
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        print(
            "ATTACK_SWORD_TWOHAND_UP_F07_REVIEW_V21_PASS50="
            f"geometry_safe:{len(candidates)};"
            f"rendered:{len(rendered_metadata)};"
            f"final_boundary_safe:"
            f"{sum(1 for item in rendered_metadata if item['accepted_by_final_boundary_contract'])}"
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
    if not artifacts:
        raise RuntimeError("two-hand up f07 pass50 review sheet is empty")
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
        "human_warrior_m01_attack_sword_twohand_up_f07_review_v21_pass50",
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
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F07_CONTINUITY_REVIEW_REVISION,
            "diagnostic_only": True,
            "source_failed_run_id": SOURCE_FAILED_RUN_ID,
            "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
            "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
            "source_failure": SOURCE_FAILURE,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "render_edge_touching_candidates_for_review": (
                RENDER_EDGE_TOUCHING_CANDIDATES_FOR_REVIEW
            ),
            "require_zero_edge_alpha_for_final_acceptance": (
                REQUIRE_ZERO_EDGE_ALPHA_FOR_FINAL_ACCEPTANCE
            ),
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
