from __future__ import annotations

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
import blender_sprite_factory_attack_sword_directional_cycle_v21 as directional_cycle
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_attack_sword_onehand_up_depth_search_diagnostic_v21 as depth_search_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass29 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    DEPTH_BRANCH_CANDIDATES,
    MAX_RENDER_CANDIDATES_PER_ARM_POSE,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    SOURCE_FRAME_CANDIDATES,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_ARM_DIAGNOSTIC_REVISION,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f01_arm_diagnostic_v21.png"


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _capture_arm(
    context: factory.BuildContext,
    frame_number: int,
) -> dict[str, object]:
    factory.bpy.context.scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    return {
        bone_name: context.rig.pose.bones[bone_name].rotation_euler.copy()
        for bone_name in TARGET_BONES
    }


def _set_arm_blend(
    context: factory.BuildContext,
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    blend: float,
) -> dict[str, float]:
    applied: dict[str, float] = {}
    for bone_name in TARGET_BONES:
        bone = context.rig.pose.bones[bone_name]
        target = target_rotations[bone_name]
        source = source_rotations[bone_name]
        bone.rotation_euler = target.copy()
        for axis_index in range(3):
            delta = _shortest_angle_delta(
                float(target[axis_index]),
                float(source[axis_index]),
            )
            applied_delta = delta * float(blend)
            bone.rotation_euler[axis_index] = (
                float(target[axis_index]) + applied_delta
            )
            applied[f"{bone_name}[{axis_index}]"] = math.degrees(
                applied_delta
            )
    factory.bpy.context.view_layer.update()
    return applied


def _restore_arm(
    context: factory.BuildContext,
    rotations: dict[str, object],
) -> None:
    for bone_name, value in rotations.items():
        context.rig.pose.bones[bone_name].rotation_euler = value.copy()
    factory.bpy.context.view_layer.update()


def _target_direction(
    current_direction: Vector,
    *,
    requested_projection: float,
    offset_degrees: float,
    depth_branch: str,
) -> tuple[Vector, float, float]:
    screen_x, screen_y, camera_forward = pass06_adapter._camera_axes()
    current_x = float(current_direction.dot(screen_x))
    current_y = float(current_direction.dot(screen_y))
    current_depth = float(current_direction.dot(camera_forward))
    source_projection = math.hypot(current_x, current_y)
    if source_projection <= 1.0e-6:
        raise RuntimeError(
            "two-hand up f01 arm diagnostic source projection is degenerate"
        )
    applied_projection = min(source_projection, float(requested_projection))
    if applied_projection <= 1.0e-6 or applied_projection >= 1.0:
        raise RuntimeError(
            "two-hand up f01 arm diagnostic projection is invalid: "
            f"{applied_projection:.6f}"
        )

    angle = math.atan2(current_y, current_x) + math.radians(offset_degrees)
    source_depth_sign = 1.0 if current_depth >= 0.0 else -1.0
    if depth_branch == "source":
        depth_sign = source_depth_sign
    elif depth_branch == "flipped":
        depth_sign = -source_depth_sign
    else:
        raise KeyError(
            "two-hand up f01 arm diagnostic unknown depth branch: "
            f"{depth_branch}"
        )
    depth_magnitude = math.sqrt(max(0.0, 1.0 - applied_projection**2))
    target_direction = (
        screen_x * (math.cos(angle) * applied_projection)
        + screen_y * (math.sin(angle) * applied_projection)
        + camera_forward * (depth_sign * depth_magnitude)
    ).normalized()
    return target_direction, source_projection, applied_projection


def _candidate_sort_key(candidate: dict[str, object]) -> tuple[object, ...]:
    return (
        -float(candidate["screen_projection"]),
        abs(float(candidate["offset_degrees"])),
        0 if candidate["depth_branch"] == "source" else 1,
        -float(candidate["head_clearance_pixels"]),
        -int(candidate["visible_blade_samples"]),
        -float(candidate["camera_margin_pixels"]),
        int(candidate["source_frame_order"]),
        float(candidate["offset_degrees"]),
    )


def _evaluate_arm_pose(
    context: factory.BuildContext,
    *,
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    source_frame: int,
    source_frame_order: int,
    arm_blend: float,
) -> tuple[list[dict[str, object]], dict[str, float]]:
    scene = factory.bpy.context.scene
    scene.frame_set(TARGET_FRAME)
    factory.bpy.context.view_layer.update()
    applied_arm_deltas = _set_arm_blend(
        context,
        target_rotations,
        source_rotations,
        arm_blend,
    )
    objects = directional_cycle._visible_weapon_objects(
        TARGET_GRIP_ID,
        TARGET_DIRECTION,
    )
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = pass02_adapter._weapon_world_direction(objects)
    pivot = pass02_adapter._weapon_pivot(objects)
    candidates: list[dict[str, object]] = []
    projection_keys: set[float] = set()

    try:
        for requested_projection in SCREEN_PROJECTION_CANDIDATES:
            applied_projection = min(
                math.hypot(
                    float(current_direction.dot(pass06_adapter._camera_axes()[0])),
                    float(current_direction.dot(pass06_adapter._camera_axes()[1])),
                ),
                float(requested_projection),
            )
            projection_key = round(applied_projection, 6)
            if projection_key in projection_keys:
                continue
            projection_keys.add(projection_key)
            for depth_branch in DEPTH_BRANCH_CANDIDATES:
                for offset_degrees in ANGLE_OFFSET_CANDIDATES:
                    target_direction, source_projection, resolved_projection = (
                        _target_direction(
                            current_direction,
                            requested_projection=float(requested_projection),
                            offset_degrees=float(offset_degrees),
                            depth_branch=depth_branch,
                        )
                    )
                    pass07_adapter._apply_world_rotation(
                        objects,
                        pivot=pivot,
                        current_direction=current_direction,
                        target_direction=target_direction,
                    )
                    try:
                        clearance = float(
                            depth_search_adapter
                            ._depth_search_visible_blade_head_clearance(objects)
                        )
                        visible_samples = int(
                            scene.get(
                                "attack_sword_onehand_up_pass22_visible_samples",
                                0,
                            )
                        )
                        occluded_samples = int(
                            scene.get(
                                "attack_sword_onehand_up_pass22_occluded_samples",
                                0,
                            )
                        )
                        margin = float(pass02_adapter._camera_margin(objects))
                    finally:
                        pass06_adapter._restore_weapon(saved_basis)

                    if (
                        clearance < MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
                        or visible_samples < MIN_VISIBLE_BLADE_SAMPLES
                        or margin < MIN_CAMERA_MARGIN_PIXELS
                    ):
                        continue
                    candidates.append(
                        {
                            "source_frame": source_frame,
                            "source_frame_order": source_frame_order,
                            "arm_blend": float(arm_blend),
                            "depth_branch": depth_branch,
                            "offset_degrees": float(offset_degrees),
                            "source_projection": float(source_projection),
                            "requested_screen_projection": float(
                                requested_projection
                            ),
                            "screen_projection": float(resolved_projection),
                            "head_clearance_pixels": float(clearance),
                            "visible_blade_samples": visible_samples,
                            "occluded_blade_samples": occluded_samples,
                            "camera_margin_pixels": float(margin),
                        }
                    )
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        _restore_arm(context, target_rotations)

    candidates.sort(key=_candidate_sort_key)
    return candidates, applied_arm_deltas


def _render_candidate(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    candidate: dict[str, object],
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    attempt_number: int,
) -> tuple[factory.FrameArtifact, dict[str, object], dict[str, float]]:
    scene = factory.bpy.context.scene
    scene.frame_set(TARGET_FRAME)
    factory.bpy.context.view_layer.update()
    applied_arm_deltas = _set_arm_blend(
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
    target_direction, _source_projection, _applied_projection = _target_direction(
        current_direction,
        requested_projection=float(candidate["requested_screen_projection"]),
        offset_degrees=float(candidate["offset_degrees"]),
        depth_branch=str(candidate["depth_branch"]),
    )
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=target_direction,
    )
    try:
        output_name = (
            f"{context.config.character_id}_attack_sword_01_twohand_up_"
            f"f01_arm_diagnostic_v21_pass29_proxy_{context.proxy_revision}.png"
        )
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id=(
                "attack_sword_01_twohand_up_f01_arm_diagnostic_v21_pass29"
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
        result = {
            **candidate,
            "render_attempt": attempt_number,
            "edge_counts": edge_counts,
            "accepted": not touched if REQUIRE_ZERO_EDGE_ALPHA else True,
        }
        print(
            "ATTACK_SWORD_TWOHAND_UP_F01_ARM_DIAGNOSTIC_V21_PASS29_ATTEMPT="
            f"source:{int(candidate['source_frame'])};"
            f"blend:{float(candidate['arm_blend']):.2f};"
            f"branch:{candidate['depth_branch']};"
            f"projection:{float(candidate['screen_projection']):.6f};"
            f"offset:{float(candidate['offset_degrees']):.1f}deg;"
            f"clearance:{float(candidate['head_clearance_pixels']):.3f}px;"
            f"visible:{int(candidate['visible_blade_samples'])};"
            f"margin:{float(candidate['camera_margin_pixels']):.3f}px;"
            f"edges:{touched}"
        )
        return artifact, result, applied_arm_deltas
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        _restore_arm(context, target_rotations)


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
            "two-hand up f01 arm diagnostic action is missing: "
            f"{TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    target_rotations: dict[str, object] = {}
    source_rotations_by_frame: dict[int, dict[str, object]] = {}
    geometry_safe_counts: dict[str, int] = {}
    selected_artifact: factory.FrameArtifact | None = None
    selected: dict[str, object] | None = None
    selected_arm_deltas: dict[str, float] = {}
    render_attempts: list[dict[str, object]] = []

    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        target_rotations = _capture_arm(context, TARGET_FRAME)
        for source_frame in SOURCE_FRAME_CANDIDATES:
            source_rotations_by_frame[int(source_frame)] = _capture_arm(
                context,
                int(source_frame),
            )

        for arm_blend in ARM_BLEND_CANDIDATES:
            blend_candidates: list[dict[str, object]] = []
            for source_order, source_frame in enumerate(
                SOURCE_FRAME_CANDIDATES
            ):
                candidates, _arm_deltas = _evaluate_arm_pose(
                    context,
                    target_rotations=target_rotations,
                    source_rotations=source_rotations_by_frame[int(source_frame)],
                    source_frame=int(source_frame),
                    source_frame_order=source_order,
                    arm_blend=float(arm_blend),
                )
                geometry_safe_counts[
                    f"source_{int(source_frame)}_blend_{float(arm_blend):.2f}"
                ] = len(candidates)
                blend_candidates.extend(candidates)

            blend_candidates.sort(key=_candidate_sort_key)
            for candidate in blend_candidates[
                :MAX_RENDER_CANDIDATES_PER_ARM_POSE
            ]:
                artifact, result, arm_deltas = _render_candidate(
                    context,
                    run_dir,
                    calibration=calibration,
                    candidate=candidate,
                    target_rotations=target_rotations,
                    source_rotations=source_rotations_by_frame[
                        int(candidate["source_frame"])
                    ],
                    attempt_number=len(render_attempts) + 1,
                )
                render_attempts.append(result)
                if bool(result["accepted"]):
                    selected_artifact = artifact
                    selected = result
                    selected_arm_deltas = arm_deltas
                    break
            if selected is not None:
                break

        if selected is None or selected_artifact is None:
            raise RuntimeError(
                "two-hand up f01 arm diagnostic found no safe coordinated "
                f"arm candidate; geometry_safe_counts={geometry_safe_counts}; "
                f"render_attempts={render_attempts}"
            )

        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_ARM_DIAGNOSTIC_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "target_frame": TARGET_FRAME,
            "target_bones": list(TARGET_BONES),
            "selected": selected,
            "selected_arm_deltas_degrees": selected_arm_deltas,
            "geometry_safe_counts": geometry_safe_counts,
            "render_attempts": render_attempts,
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        print(
            "ATTACK_SWORD_TWOHAND_UP_F01_ARM_DIAGNOSTIC_V21_PASS29_SELECTED="
            f"source:{int(selected['source_frame'])};"
            f"blend:{float(selected['arm_blend']):.2f};"
            f"branch:{selected['depth_branch']};"
            f"projection:{float(selected['screen_projection']):.6f};"
            f"offset:{float(selected['offset_degrees']):.1f}deg;"
            f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
            f"visible:{int(selected['visible_blade_samples'])};"
            f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
            f"attempts:{len(render_attempts)}"
        )
        return [selected_artifact]
    finally:
        if target_rotations:
            _restore_arm(context, target_rotations)
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_single_frame_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    if len(artifacts) != 1 or artifacts[0].frame_number != TARGET_FRAME:
        raise RuntimeError(
            "two-hand up f01 arm diagnostic expected exactly one f01 frame"
        )
    image = factory.bpy.data.images.load(
        str(artifacts[0].output_path),
        check_existing=False,
    )
    try:
        pixels = tuple(image.pixels[:])
        sheet = factory.bpy.data.images.new(
            "human_warrior_m01_attack_sword_twohand_up_f01_arm_diagnostic_v21",
            width=int(config.technical.canvas_width),
            height=int(config.technical.canvas_height),
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
            "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
            "source_failure": SOURCE_FAILURE,
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
    base_entry._write_contact_sheet_combat_idle_down_v01 = (
        _write_single_frame_sheet
    )
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    depth_search_adapter.pass22_adapter._HEAD_DEPTH_CACHE.clear()
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
