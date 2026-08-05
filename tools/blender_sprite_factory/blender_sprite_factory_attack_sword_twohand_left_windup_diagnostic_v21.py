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
from attack_sword_directional_cycle_correction_v21_pass06 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
)


BASE_WRITE_MANIFEST = factory._write_run_manifest


def _angle_offsets() -> tuple[float, ...]:
    offsets: list[float] = [0.0]
    for magnitude in range(
        ANGLE_SEARCH_STEP_DEGREES,
        ANGLE_SEARCH_LIMIT_DEGREES + 1,
        ANGLE_SEARCH_STEP_DEGREES,
    ):
        offsets.extend((float(magnitude), -float(magnitude)))
    return tuple(offsets)


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
            f"two-hand left windup diagnostic action is missing: {TARGET_ACTION_ID}"
        )

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
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

        objects = directional_cycle._visible_weapon_objects(
            TARGET_GRIP_ID,
            TARGET_DIRECTION,
        )
        saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
        current_direction = pass02._weapon_world_direction(objects)
        pivot = pass02._weapon_pivot(objects)
        source_clearance = export_adapter._weapon_head_clearance(objects)
        source_margin = pass02._camera_margin(objects)

        for attempt_number, offset_degrees in enumerate(
            _angle_offsets(),
            start=1,
        ):
            pass07_adapter._apply_world_rotation(
                objects,
                pivot=pivot,
                current_direction=current_direction,
                target_direction=export_adapter._target_direction(
                    current_direction,
                    offset_degrees=float(offset_degrees),
                ),
            )
            try:
                clearance = export_adapter._weapon_head_clearance(objects)
                margin = pass02._camera_margin(objects)
                diagnostic: dict[str, object] = {
                    "attempt": attempt_number,
                    "offset_degrees": float(offset_degrees),
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
                        "windup_diagnostic_v21"
                    ),
                    direction=TARGET_DIRECTION,
                    frame_number=TARGET_FRAME,
                    raw_dir=run_dir / "raw",
                    frame_dir=run_dir / "frames",
                    output_name=(
                        f"{config.character_id}_attack_sword_01_twohand_left_"
                        f"windup_diagnostic_v21_f02_proxy_"
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
                    "ATTACK_SWORD_TWOHAND_LEFT_WINDUP_DIAGNOSTIC_V21_ATTEMPT="
                    f"offset:{float(offset_degrees):.1f}deg;"
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
                "two-hand left windup diagnostic found no safe rigid arc: "
                f"{diagnostics}"
            )

        payload = {
            "source_head_clearance_pixels": float(source_clearance),
            "source_camera_margin_pixels": float(source_margin),
            "selected": selected,
            "candidate_diagnostics": diagnostics,
        }
        factory.bpy.context.scene[
            "attack_sword_twohand_left_windup_diagnostic_v21"
        ] = json.dumps(payload, sort_keys=True)
        print(
            "ATTACK_SWORD_TWOHAND_LEFT_WINDUP_DIAGNOSTIC_V21_SELECTED="
            f"offset:{float(selected['offset_degrees']):.1f}deg;"
            f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
            f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
            f"attempts:{len(diagnostics)}"
        )
        return [selected_artifact]
    finally:
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
            "two-hand left windup diagnostic expected one rendered frame"
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
    payload["attack_sword_twohand_left_windup_diagnostic_v21"] = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_twohand_left_windup_diagnostic_v21"
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
