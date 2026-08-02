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
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass05 import (
    create_attack_sword_directional_cycle_actions_v21_pass05,
)
from attack_sword_directional_cycle_correction_v21_pass07 import (
    BLEND_CANDIDATES,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ACTION_ID,
    TARGET_BONES,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    WEAPON_OFFSET_DEGREES,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _set_blend(
    context: factory.BuildContext,
    windup_rotations: dict[str, object],
    guard_rotations: dict[str, object],
    blend: float,
) -> None:
    for bone_name in TARGET_BONES:
        bone = context.rig.pose.bones[bone_name]
        source = windup_rotations[bone_name]
        target = guard_rotations[bone_name]
        bone.rotation_euler = source.copy()
        for axis_index in range(3):
            bone.rotation_euler[axis_index] = float(source[axis_index]) + (
                _shortest_angle_delta(
                    float(source[axis_index]),
                    float(target[axis_index]),
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
            f"two-hand left paired-arm diagnostic action is missing: {TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    windup_rotations: dict[str, object] = {}
    guard_rotations: dict[str, object] = {}
    selected: dict[str, object] | None = None
    selected_artifact: factory.FrameArtifact | None = None
    diagnostics: list[dict[str, object]] = []
    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )

        factory.bpy.context.scene.frame_set(TARGET_FRAME)
        factory.bpy.context.view_layer.update()
        windup_rotations = {
            bone_name: context.rig.pose.bones[bone_name].rotation_euler.copy()
            for bone_name in TARGET_BONES
        }

        factory.bpy.context.scene.frame_set(GUARD_FRAME)
        factory.bpy.context.view_layer.update()
        guard_rotations = {
            bone_name: context.rig.pose.bones[bone_name].rotation_euler.copy()
            for bone_name in TARGET_BONES
        }

        factory.bpy.context.scene.frame_set(TARGET_FRAME)
        factory.bpy.context.view_layer.update()
        objects = directional_cycle._visible_weapon_objects(
            TARGET_GRIP_ID,
            TARGET_DIRECTION,
        )

        for attempt_number, blend in enumerate(BLEND_CANDIDATES, start=1):
            _set_blend(
                context,
                windup_rotations,
                guard_rotations,
                float(blend),
            )
            saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
            current_direction = pass02._weapon_world_direction(objects)
            pivot = pass02._weapon_pivot(objects)
            pass07_adapter._apply_world_rotation(
                objects,
                pivot=pivot,
                current_direction=current_direction,
                target_direction=export_adapter._target_direction(
                    current_direction,
                    offset_degrees=WEAPON_OFFSET_DEGREES,
                ),
            )
            try:
                clearance = export_adapter._weapon_head_clearance(objects)
                margin = pass02._camera_margin(objects)
                diagnostic: dict[str, object] = {
                    "attempt": attempt_number,
                    "arm_blend": float(blend),
                    "offset_degrees": WEAPON_OFFSET_DEGREES,
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
                        "attack_sword_01_twohand_left_"
                        "arm_diagnostic_v21"
                    ),
                    direction=TARGET_DIRECTION,
                    frame_number=TARGET_FRAME,
                    raw_dir=run_dir / "raw",
                    frame_dir=run_dir / "frames",
                    output_name=(
                        f"{config.character_id}_attack_sword_01_twohand_left_"
                        f"arm_diagnostic_v21_f02_proxy_"
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
                    "ATTACK_SWORD_TWOHAND_LEFT_ARM_DIAGNOSTIC_V21_ATTEMPT="
                    f"blend:{float(blend):.2f};"
                    f"offset:{WEAPON_OFFSET_DEGREES:.1f}deg;"
                    f"clearance:{float(clearance):.3f}px;"
                    f"margin:{float(margin):.3f}px;"
                    f"edges:{touched}"
                )
                if bool(diagnostic["accepted"]):
                    selected = diagnostic
                    selected_artifact = artifact
                    break
            finally:
                pass06_adapter._restore_weapon(saved_basis)

        if selected is None or selected_artifact is None:
            raise RuntimeError(
                "two-hand left paired-arm diagnostic found no safe candidate: "
                f"{diagnostics}"
            )

        payload = {
            "selected": selected,
            "candidate_diagnostics": diagnostics,
        }
        factory.bpy.context.scene[
            "attack_sword_twohand_left_arm_diagnostic_v21"
        ] = json.dumps(payload, sort_keys=True)
        print(
            "ATTACK_SWORD_TWOHAND_LEFT_ARM_DIAGNOSTIC_V21_SELECTED="
            f"blend:{float(selected['arm_blend']):.2f};"
            f"offset:{WEAPON_OFFSET_DEGREES:.1f}deg;"
            f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
            f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
            f"attempts:{len(diagnostics)}"
        )
        return [selected_artifact]
    finally:
        if windup_rotations:
            _restore_arm(context, windup_rotations)
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions["down"]
        )
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_single_frame_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    if len(artifacts) != 1:
        raise RuntimeError(
            "two-hand left paired-arm diagnostic expected one rendered frame"
        )
    output_path.write_bytes(artifacts[0].output_path.read_bytes())
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
    payload["attack_sword_twohand_left_arm_diagnostic_v21"] = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_twohand_left_arm_diagnostic_v21"
            ]
        )
    )
    payload["diagnostic_only"] = True
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    base_entry.create_combat_idle_down_actions_v01 = (
        create_attack_sword_directional_cycle_actions_v21_pass05
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_diagnostic
    base_entry._write_contact_sheet_combat_idle_down_v01 = (
        _write_single_frame_sheet
    )
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
