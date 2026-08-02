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
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass04 import (
    create_attack_sword_directional_cycle_actions_v21_pass04,
)
from attack_sword_directional_cycle_correction_v21_pass05 import (
    BLEND_CANDIDATES,
    GUARD_FRAME,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest
TARGET_BONES = ("upper_arm.R", "forearm.R", "hand.R")


def _shortest_angle_delta(start: float, end: float) -> float:
    return (float(end) - float(start) + math.pi) % (2.0 * math.pi) - math.pi


def _set_blend(
    context: factory.BuildContext,
    recovery_rotations: dict[str, object],
    guard_rotations: dict[str, object],
    blend: float,
) -> None:
    for bone_name in TARGET_BONES:
        bone = context.rig.pose.bones[bone_name]
        source = recovery_rotations[bone_name]
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


def _restore(
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
            f"left recovery diagnostic action is missing: {TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    recovery_rotations: dict[str, object] = {}
    guard_rotations: dict[str, object] = {}
    selected: dict[str, float] | None = None
    diagnostics: list[dict[str, float]] = []
    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )

        factory.bpy.context.scene.frame_set(TARGET_FRAME)
        factory.bpy.context.view_layer.update()
        recovery_rotations = {
            bone_name: context.rig.pose.bones[
                bone_name
            ].rotation_euler.copy()
            for bone_name in TARGET_BONES
        }
        objects = directional_cycle._visible_weapon_objects(
            TARGET_GRIP_ID,
            TARGET_DIRECTION,
        )
        source_clearance = export_adapter._weapon_head_clearance(objects)
        source_margin = pass02._camera_margin(objects)

        factory.bpy.context.scene.frame_set(GUARD_FRAME)
        factory.bpy.context.view_layer.update()
        guard_rotations = {
            bone_name: context.rig.pose.bones[
                bone_name
            ].rotation_euler.copy()
            for bone_name in TARGET_BONES
        }

        factory.bpy.context.scene.frame_set(TARGET_FRAME)
        factory.bpy.context.view_layer.update()
        for blend in BLEND_CANDIDATES:
            _set_blend(
                context,
                recovery_rotations,
                guard_rotations,
                float(blend),
            )
            clearance = export_adapter._weapon_head_clearance(objects)
            margin = pass02._camera_margin(objects)
            diagnostic = {
                "blend": float(blend),
                "head_clearance_pixels": float(clearance),
                "camera_margin_pixels": float(margin),
            }
            diagnostics.append(diagnostic)
            if (
                clearance >= MIN_HEAD_CLEARANCE_PIXELS
                and margin >= MIN_CAMERA_MARGIN_PIXELS
            ):
                selected = diagnostic
                break

        if selected is None:
            raise RuntimeError(
                "left recovery diagnostic found no safe guard blend: "
                f"{diagnostics}"
            )

        _set_blend(
            context,
            recovery_rotations,
            guard_rotations,
            float(selected["blend"]),
        )
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id=(
                "attack_sword_01_onehand_left_recovery_diagnostic_v21"
            ),
            direction=TARGET_DIRECTION,
            frame_number=TARGET_FRAME,
            raw_dir=run_dir / "raw",
            frame_dir=run_dir / "frames",
            output_name=(
                f"{config.character_id}_attack_sword_01_onehand_left_"
                f"recovery_diagnostic_v21_f07_proxy_"
                f"{context.proxy_revision}.png"
            ),
            fixed_scale=calibration.scale,
            fixed_center_x=calibration.source_center_x,
        )
        payload = {
            "source_head_clearance_pixels": float(source_clearance),
            "source_camera_margin_pixels": float(source_margin),
            "selected": selected,
            "candidate_diagnostics": diagnostics,
        }
        factory.bpy.context.scene[
            "attack_sword_left_recovery_diagnostic_v21"
        ] = json.dumps(payload, sort_keys=True)
        print(
            "ATTACK_SWORD_LEFT_RECOVERY_DIAGNOSTIC_V21_SELECTED="
            f"blend:{selected['blend']:.2f};"
            f"clearance:{selected['head_clearance_pixels']:.3f}px;"
            f"margin:{selected['camera_margin_pixels']:.3f}px;"
            f"attempts:{len(diagnostics)}"
        )
        return [artifact]
    finally:
        if recovery_rotations:
            _restore(context, recovery_rotations)
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
        raise RuntimeError("left recovery diagnostic expected one rendered frame")
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
    payload["attack_sword_left_recovery_diagnostic_v21"] = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_left_recovery_diagnostic_v21"
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
        create_attack_sword_directional_cycle_actions_v21_pass04
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_diagnostic
    base_entry._write_contact_sheet_combat_idle_down_v01 = (
        _write_single_frame_sheet
    )
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
