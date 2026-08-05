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
from attack_sword_directional_cycle_builder_v21 import (
    create_attack_sword_directional_cycle_actions_v21,
)
from attack_sword_directional_cycle_correction_v21_pass03 import (
    DEPTH_VALUES_DEGREES,
    LIFT_VALUES_DEGREES,
    MAX_CORRECTION_COST_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    SWEEP_VALUES_DEGREES,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


BASE_WRITE_CONTACT_SHEET = factory._write_contact_sheet
BASE_WRITE_MANIFEST = factory._write_run_manifest
BONE_FACTORS = {
    "upper_arm.R": ((0.70, 0.0, 0.0), (0.0, 0.70, 0.0), (0.0, 0.0, 0.55)),
    "forearm.R": ((1.00, 0.0, 0.0), (0.0, 1.00, 0.0), (0.0, 0.0, 1.00)),
    "hand.R": ((0.35, 0.0, 0.0), (0.0, 0.45, 0.0), (0.0, 0.0, 0.35)),
}


def _delta(candidate: dict[str, float], factors: tuple[float, float, float]) -> float:
    return (
        candidate["lift_degrees"] * factors[0]
        + candidate["depth_degrees"] * factors[1]
        + candidate["sweep_degrees"] * factors[2]
    )


def _candidates() -> tuple[dict[str, float], ...]:
    result: list[dict[str, float]] = []
    for lift in LIFT_VALUES_DEGREES:
        for sweep in SWEEP_VALUES_DEGREES:
            for depth in DEPTH_VALUES_DEGREES:
                if lift == sweep == depth == 0:
                    continue
                cost = math.sqrt(lift * lift + sweep * sweep + depth * depth * 0.75)
                if cost <= MAX_CORRECTION_COST_DEGREES:
                    result.append(
                        {
                            "lift_degrees": float(lift),
                            "sweep_degrees": float(sweep),
                            "depth_degrees": float(depth),
                            "cost_degrees": float(cost),
                        }
                    )
    result.sort(
        key=lambda item: (
            item["cost_degrees"],
            abs(item["lift_degrees"]),
            abs(item["sweep_degrees"]),
            abs(item["depth_degrees"]),
        )
    )
    return tuple(result)


def _set_candidate(
    context: factory.BuildContext,
    base_rotations: dict[str, object],
    candidate: dict[str, float],
) -> None:
    for bone_name, original in base_rotations.items():
        bone = context.rig.pose.bones[bone_name]
        bone.rotation_euler = original.copy()
        for axis_index, factors in enumerate(BONE_FACTORS[bone_name]):
            bone.rotation_euler[axis_index] += math.radians(
                _delta(candidate, factors)
            )
    factory.bpy.context.view_layer.update()


def _restore(context: factory.BuildContext, base_rotations: dict[str, object]) -> None:
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
        raise RuntimeError(f"left windup diagnostic action is missing: {TARGET_ACTION_ID}")

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    base_rotations: dict[str, object] = {}
    selected: dict[str, float] | None = None
    attempts = 0
    try:
        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(config.directions[TARGET_DIRECTION])
        factory.bpy.context.scene.frame_set(TARGET_FRAME)
        factory.bpy.context.view_layer.update()
        objects = directional_cycle._visible_weapon_objects(
            TARGET_GRIP_ID,
            TARGET_DIRECTION,
        )
        base_rotations = {
            name: context.rig.pose.bones[name].rotation_euler.copy()
            for name in BONE_FACTORS
        }
        source_clearance = export_adapter._weapon_head_clearance(objects)
        source_margin = pass02._camera_margin(objects)
        for candidate in _candidates():
            attempts += 1
            _set_candidate(context, base_rotations, candidate)
            clearance = export_adapter._weapon_head_clearance(objects)
            margin = pass02._camera_margin(objects)
            if (
                clearance >= MIN_HEAD_CLEARANCE_PIXELS
                and margin >= MIN_CAMERA_MARGIN_PIXELS
            ):
                selected = {
                    **candidate,
                    "head_clearance_pixels": float(clearance),
                    "camera_margin_pixels": float(margin),
                }
                break
        if selected is None:
            raise RuntimeError(
                f"left windup diagnostic found no safe arm candidate after {attempts} attempts"
            )
        _set_candidate(context, base_rotations, selected)
        artifact, _ = export_adapter._render_candidate(
            context,
            animation_id="attack_sword_01_onehand_left_windup_diagnostic_v21",
            direction=TARGET_DIRECTION,
            frame_number=TARGET_FRAME,
            raw_dir=run_dir / "raw",
            frame_dir=run_dir / "frames",
            output_name=(
                f"{config.character_id}_attack_sword_01_onehand_left_"
                f"windup_diagnostic_v21_f02_proxy_{context.proxy_revision}.png"
            ),
            fixed_scale=calibration.scale,
            fixed_center_x=calibration.source_center_x,
        )
        payload = {
            "source_head_clearance_pixels": float(source_clearance),
            "source_camera_margin_pixels": float(source_margin),
            "selected": selected,
            "attempts": attempts,
        }
        factory.bpy.context.scene["attack_sword_left_windup_diagnostic_v21"] = (
            json.dumps(payload, sort_keys=True)
        )
        print(
            "ATTACK_SWORD_LEFT_WINDUP_DIAGNOSTIC_V21_SELECTED="
            f"lift:{selected['lift_degrees']:.1f}deg;"
            f"sweep:{selected['sweep_degrees']:.1f}deg;"
            f"depth:{selected['depth_degrees']:.1f}deg;"
            f"clearance:{selected['head_clearance_pixels']:.3f}px;"
            f"margin:{selected['camera_margin_pixels']:.3f}px;"
            f"attempts:{attempts}"
        )
        return [artifact]
    finally:
        if base_rotations:
            _restore(context, base_rotations)
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_manifest(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = BASE_WRITE_MANIFEST(
        context, run_dir, run_id, blend_path, artifacts, contact_sheet
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["attack_sword_left_windup_diagnostic_v21"] = json.loads(
        str(factory.bpy.context.scene["attack_sword_left_windup_diagnostic_v21"])
    )
    payload["diagnostic_only"] = True
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    base_entry.create_combat_idle_down_actions_v01 = (
        create_attack_sword_directional_cycle_actions_v21
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_diagnostic
    base_entry._write_contact_sheet_combat_idle_down_v01 = (
        BASE_WRITE_CONTACT_SHEET
    )
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
