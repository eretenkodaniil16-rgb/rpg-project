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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass19 import (
    create_attack_sword_directional_cycle_actions_v21_pass19,
)
from attack_sword_directional_cycle_correction_v21_pass20 import (
    ANGLE_OFFSET_CANDIDATES,
    ARM_BLEND_CANDIDATES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_UP_TAIL_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_PROJECTION_CANDIDATES,
    SOURCE_FRAME_BY_TARGET,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_onehand_up_tail_diagnostic_v21"
CONTACT_SHEET_NAME = "attack_sword_01_onehand_up_tail_diagnostic_v21.png"


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _set_arm_blend(
    context: factory.BuildContext,
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    blend: float,
) -> None:
    for bone_name in TARGET_BONES:
        bone = context.rig.pose.bones[bone_name]
        target = target_rotations[bone_name]
        source = source_rotations[bone_name]
        bone.rotation_euler = target.copy()
        for axis_index in range(3):
            bone.rotation_euler[axis_index] = float(target[axis_index]) + (
                _shortest_angle_delta(
                    float(target[axis_index]),
                    float(source[axis_index]),
                )
                * float(blend)
            )
    factory.bpy.context.view_layer.update()


def _restore_arm(
    context: factory.BuildContext,
    rotations: dict[str, object],
) -> None:
    for bone_name, value in rotations.items():
        context.rig.pose.bones[bone_name].rotation_euler = value.copy()
    factory.bpy.context.view_layer.update()


def _capture_current_arm(
    context: factory.BuildContext,
) -> dict[str, object]:
    return {
        bone_name: context.rig.pose.bones[bone_name].rotation_euler.copy()
        for bone_name in TARGET_BONES
    }


def _capture_action_arm(
    context: factory.BuildContext,
    frame_number: int,
) -> dict[str, object]:
    factory.bpy.context.scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    return _capture_current_arm(context)


def _projection_target_direction(
    current_direction: Vector,
    *,
    offset_degrees: float,
    requested_projection: float,
) -> tuple[Vector, float, float]:
    screen_x, screen_y, camera_forward = pass06_adapter._camera_axes()
    current_x = current_direction.dot(screen_x)
    current_y = current_direction.dot(screen_y)
    current_depth = current_direction.dot(camera_forward)
    source_projection = math.hypot(current_x, current_y)
    if source_projection <= 1.0e-6:
        raise RuntimeError(
            "one-hand up tail diagnostic source projection is degenerate"
        )
    target_projection = min(source_projection, float(requested_projection))
    angle = math.atan2(current_y, current_x) + math.radians(offset_degrees)
    depth_sign = 1.0 if current_depth >= 0.0 else -1.0
    depth_magnitude = math.sqrt(max(0.0, 1.0 - target_projection**2))
    target_direction = (
        screen_x * (math.cos(angle) * target_projection)
        + screen_y * (math.sin(angle) * target_projection)
        + camera_forward * (depth_sign * depth_magnitude)
    ).normalized()
    return target_direction, source_projection, target_projection


def _diagnose_frame(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    target_frame: int,
    selected_pose_by_frame: dict[int, dict[str, object]],
) -> tuple[factory.FrameArtifact, dict[str, object], dict[str, object]]:
    source_frame = int(SOURCE_FRAME_BY_TARGET[target_frame])
    target_rotations = _capture_action_arm(context, target_frame)
    source_rotations = selected_pose_by_frame.get(source_frame)
    source_kind = "selected_previous_frame"
    if source_rotations is None:
        source_rotations = _capture_action_arm(context, source_frame)
        source_kind = "action_frame"
    factory.bpy.context.scene.frame_set(target_frame)
    factory.bpy.context.view_layer.update()

    objects = directional_cycle._visible_weapon_objects(
        TARGET_GRIP_ID,
        TARGET_DIRECTION,
    )
    selected: dict[str, object] | None = None
    selected_artifact: factory.FrameArtifact | None = None
    selected_pose: dict[str, object] | None = None
    diagnostics: list[dict[str, object]] = []
    attempt_number = 0

    try:
        for arm_blend in ARM_BLEND_CANDIDATES:
            _set_arm_blend(
                context,
                target_rotations,
                source_rotations,
                float(arm_blend),
            )
            blended_pose = _capture_current_arm(context)
            saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
            current_direction = pass02._weapon_world_direction(objects)
            pivot = pass02._weapon_pivot(objects)

            for requested_projection in SCREEN_PROJECTION_CANDIDATES:
                for offset_degrees in ANGLE_OFFSET_CANDIDATES:
                    attempt_number += 1
                    target_direction, source_projection, applied_projection = (
                        _projection_target_direction(
                            current_direction,
                            offset_degrees=float(offset_degrees),
                            requested_projection=float(requested_projection),
                        )
                    )
                    pass07_adapter._apply_world_rotation(
                        objects,
                        pivot=pivot,
                        current_direction=current_direction,
                        target_direction=target_direction,
                    )
                    try:
                        clearance = export_adapter._weapon_head_clearance(objects)
                        margin = pass02._camera_margin(objects)
                        diagnostic: dict[str, object] = {
                            "attempt": attempt_number,
                            "target_frame": target_frame,
                            "source_frame": source_frame,
                            "source_kind": source_kind,
                            "arm_blend": float(arm_blend),
                            "offset_degrees": float(offset_degrees),
                            "source_projection": float(source_projection),
                            "requested_projection": float(requested_projection),
                            "applied_projection": float(applied_projection),
                            "head_clearance_pixels": float(clearance),
                            "camera_margin_pixels": float(margin),
                            "edge_counts": None,
                            "accepted": False,
                        }
                        if (
                            clearance < MIN_HEAD_CLEARANCE_PIXELS
                            or margin < MIN_CAMERA_MARGIN_PIXELS
                        ):
                            diagnostics.append(diagnostic)
                            continue

                        artifact, _ = export_adapter._render_candidate(
                            context,
                            animation_id=(
                                "attack_sword_01_onehand_up_"
                                "tail_diagnostic_v21"
                            ),
                            direction=TARGET_DIRECTION,
                            frame_number=target_frame,
                            raw_dir=run_dir / "raw",
                            frame_dir=run_dir / "frames",
                            output_name=(
                                f"{context.config.character_id}_attack_sword_01_"
                                f"onehand_up_tail_diagnostic_v21_"
                                f"f{target_frame:02d}_proxy_"
                                f"{context.proxy_revision}.png"
                            ),
                            fixed_scale=calibration.scale,
                            fixed_center_x=calibration.source_center_x,
                        )
                        edge_counts = keypose_adapter._edge_alpha_counts(
                            artifact.output_path
                        )
                        touched = {
                            edge: count
                            for edge, count in edge_counts.items()
                            if count > 0
                        }
                        diagnostic["edge_counts"] = edge_counts
                        diagnostic["accepted"] = (
                            not touched if REQUIRE_ZERO_EDGE_ALPHA else True
                        )
                        diagnostics.append(diagnostic)
                        print(
                            "ATTACK_SWORD_ONEHAND_UP_TAIL_"
                            "DIAGNOSTIC_V21_ATTEMPT="
                            f"frame:{target_frame};"
                            f"source:{source_frame};"
                            f"blend:{float(arm_blend):.2f};"
                            f"projection:{float(applied_projection):.3f};"
                            f"offset:{float(offset_degrees):.1f}deg;"
                            f"clearance:{float(clearance):.3f}px;"
                            f"margin:{float(margin):.3f}px;"
                            f"edges:{touched}"
                        )
                        if bool(diagnostic["accepted"]):
                            selected = diagnostic
                            selected_artifact = artifact
                            selected_pose = {
                                key: value.copy()
                                for key, value in blended_pose.items()
                            }
                            break
                    finally:
                        pass06_adapter._restore_weapon(saved_basis)

                if selected is not None:
                    break
            if selected is not None:
                break

        if selected is None or selected_artifact is None or selected_pose is None:
            raise RuntimeError(
                "one-hand up tail diagnostic found no safe candidate for "
                f"f{target_frame:02d}: {diagnostics}"
            )

        result = {
            "selected": selected,
            "candidate_diagnostics": diagnostics,
        }
        print(
            "ATTACK_SWORD_ONEHAND_UP_TAIL_DIAGNOSTIC_V21_SELECTED="
            f"frame:{target_frame};"
            f"source:{source_frame};"
            f"source_kind:{source_kind};"
            f"blend:{float(selected['arm_blend']):.2f};"
            f"projection:{float(selected['applied_projection']):.3f};"
            f"offset:{float(selected['offset_degrees']):.1f}deg;"
            f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
            f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
            f"attempts:{len(diagnostics)}"
        )
        return selected_artifact, result, selected_pose
    finally:
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
            f"one-hand up tail action is missing: {TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    artifacts: list[factory.FrameArtifact] = []
    frame_results: dict[str, object] = {}
    selected_pose_by_frame: dict[int, dict[str, object]] = {}
    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        for target_frame in TARGET_FRAMES:
            artifact, result, selected_pose = _diagnose_frame(
                context,
                run_dir,
                calibration=calibration,
                target_frame=int(target_frame),
                selected_pose_by_frame=selected_pose_by_frame,
            )
            artifacts.append(artifact)
            frame_results[f"f{int(target_frame):02d}"] = result
            selected_pose_by_frame[int(target_frame)] = selected_pose

        payload = {
            "revision": ONEHAND_UP_TAIL_DIAGNOSTIC_REVISION,
            "target_action_id": TARGET_ACTION_ID,
            "target_grip_id": TARGET_GRIP_ID,
            "target_direction": TARGET_DIRECTION,
            "frames": frame_results,
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        return artifacts
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_four_frame_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    ordered = sorted(artifacts, key=lambda item: item.frame_number)
    if [item.frame_number for item in ordered] != list(TARGET_FRAMES):
        raise RuntimeError("one-hand up tail diagnostic expected frames f05-f08")
    tile_width = int(config.technical.canvas_width)
    tile_height = int(config.technical.canvas_height)
    width = tile_width * len(ordered)
    pixels = [0.0] * (width * tile_height * 4)
    for column_index, artifact in enumerate(ordered):
        image = factory.bpy.data.images.load(
            str(artifact.output_path), check_existing=False
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
        "human_warrior_m01_attack_sword_onehand_up_tail_diagnostic_v21",
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
    payload["diagnostic_only"] = True
    payload["approved_down_v20_changed"] = False
    payload["left_direction_changed"] = False
    payload["right_direction_changed"] = False
    payload["onehand_up_f01_f04_changed"] = False
    payload["twohand_up_changed"] = False
    payload["root_translation_used"] = False
    payload["mirroring_used"] = False
    payload["negative_scale_used"] = False
    payload["weapon_geometry_changed"] = False
    payload["weapon_geometry_deformed"] = False
    payload["materials_changed"] = False
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    base_entry.create_combat_idle_down_actions_v01 = (
        create_attack_sword_directional_cycle_actions_v21_pass19
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_diagnostic
    base_entry._write_contact_sheet_combat_idle_down_v01 = _write_four_frame_sheet
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
