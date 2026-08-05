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
from attack_sword_directional_cycle_builder_v21_pass03 import (
    BONE_DELTAS_DEGREES,
    create_attack_sword_directional_cycle_actions_v21_pass03,
)
from attack_sword_directional_cycle_correction_v21_pass04 import (
    BASE_WEIGHT,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TOTAL_WEIGHT_CANDIDATES,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest


def _set_incremental_weight(
    context: factory.BuildContext,
    base_rotations: dict[str, object],
    total_weight: float,
) -> None:
    incremental_weight = float(total_weight) - BASE_WEIGHT
    for bone_name, original in base_rotations.items():
        bone = context.rig.pose.bones[bone_name]
        bone.rotation_euler = original.copy()
        for axis_index, delta_degrees in BONE_DELTAS_DEGREES[bone_name].items():
            bone.rotation_euler[axis_index] += math.radians(
                float(delta_degrees) * incremental_weight
            )
    factory.bpy.context.view_layer.update()


def _restore(
    context: factory.BuildContext,
    base_rotations: dict[str, object],
) -> None:
    for bone_name, original in base_rotations.items():
        context.rig.pose.bones[bone_name].rotation_euler = original.copy()
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
            f"left anticipation diagnostic action is missing: {TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    base_rotations: dict[str, object] = {}
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
        objects = directional_cycle._visible_weapon_objects(
            TARGET_GRIP_ID,
            TARGET_DIRECTION,
        )
        base_rotations = {
            bone_name: context.rig.pose.bones[
                bone_name
            ].rotation_euler.copy()
            for bone_name in BONE_DELTAS_DEGREES
        }
        source_clearance = export_adapter._weapon_head_clearance(objects)
        source_margin = pass02._camera_margin(objects)

        for total_weight in TOTAL_WEIGHT_CANDIDATES:
            _set_incremental_weight(
                context,
                base_rotations,
                float(total_weight),
            )
            clearance = export_adapter._weapon_head_clearance(objects)
            margin = pass02._camera_margin(objects)
            diagnostic = {
                "total_weight": float(total_weight),
                "incremental_weight": float(total_weight) - BASE_WEIGHT,
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
                "left anticipation diagnostic found no safe total weight: "
                f"{diagnostics}"
            )

        _set_incremental_weight(
            context,
            base_rotations,
            float(selected["total_weight"]),
        )
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id=(
                "attack_sword_01_onehand_left_anticipation_diagnostic_v21"
            ),
            direction=TARGET_DIRECTION,
            frame_number=TARGET_FRAME,
            raw_dir=run_dir / "raw",
            frame_dir=run_dir / "frames",
            output_name=(
                f"{config.character_id}_attack_sword_01_onehand_left_"
                f"anticipation_diagnostic_v21_f03_proxy_"
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
            "attack_sword_left_anticipation_diagnostic_v21"
        ] = json.dumps(payload, sort_keys=True)
        print(
            "ATTACK_SWORD_LEFT_ANTICIPATION_DIAGNOSTIC_V21_SELECTED="
            f"weight:{selected['total_weight']:.2f};"
            f"clearance:{selected['head_clearance_pixels']:.3f}px;"
            f"margin:{selected['camera_margin_pixels']:.3f}px;"
            f"attempts:{len(diagnostics)}"
        )
        return [artifact]
    finally:
        if base_rotations:
            _restore(context, base_rotations)
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
            "left anticipation diagnostic expected one rendered frame"
        )
    source = artifacts[0].output_path
    output_path.write_bytes(source.read_bytes())
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
    payload["attack_sword_left_anticipation_diagnostic_v21"] = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_left_anticipation_diagnostic_v21"
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
        create_attack_sword_directional_cycle_actions_v21_pass03
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_diagnostic
    base_entry._write_contact_sheet_combat_idle_down_v01 = (
        _write_single_frame_sheet
    )
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
