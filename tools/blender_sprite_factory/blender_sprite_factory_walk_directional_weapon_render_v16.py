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
import blender_sprite_factory_combat_idle_directional_v11 as directional_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
import blender_sprite_factory_walk_directional_weapon_v15 as previous_adapter
from walk_directional_weapon_profile_v15 import (
    load_walk_directional_weapon_profile_v15,
)


TWOHAND_RIGHT_RENDER_SCALE_FACTOR = 0.975
RENDER_STAGE_ID = "walk_directional_weapon_render_v16"


def _render_scale(
    *,
    base_scale: float,
    grip_id: str,
    direction: str,
) -> float:
    if grip_id == "twohand_center_high" and direction == "right":
        return base_scale * TWOHAND_RIGHT_RENDER_SCALE_FACTOR
    return base_scale


def render_walk_directional_weapon_v16(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_walk_directional_weapon_profile_v15(config.character_id)
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    down_scale = calibrations["down"].scale
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    raw_dir.mkdir(exist_ok=True)
    frame_dir.mkdir(exist_ok=True)
    artifacts: list[factory.FrameArtifact] = []
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for grip in profile.grips:
            for direction in profile.directions:
                animation_id = previous_adapter._action_id(
                    grip,
                    direction.direction,
                )
                armed_action = factory.bpy.data.actions.get(
                    f"{config.character_id}_{animation_id}"
                )
                source_action = factory.bpy.data.actions.get(
                    f"{config.character_id}_{direction.source_action_id}"
                )
                if armed_action is None or armed_action.get("profile_revision") != "v15":
                    raise RuntimeError(
                        f"armed walk render v16 action is missing: {animation_id}"
                    )
                if source_action is None:
                    raise RuntimeError(
                        "armed walk render v16 source action is missing: "
                        f"{direction.source_action_id}"
                    )

                weapon_adapter._set_v12_weapon(
                    grip.weapon_cycle_id,
                    direction.direction,
                )
                context.rig.rotation_euler[2] = math.radians(
                    config.directions[direction.direction]
                )
                fixed_scale = _render_scale(
                    base_scale=down_scale,
                    grip_id=grip.grip_id,
                    direction=direction.direction,
                )

                for frame_number in profile.frame_order:
                    previous_adapter._assert_lower_body_matches_source(
                        context,
                        source_action=source_action,
                        armed_action=armed_action,
                        frame_number=frame_number,
                        label=(
                            f"{grip.grip_id}/{direction.direction}/"
                            f"f{frame_number:02d}"
                        ),
                    )
                    artifact, _ = factory._render_frame(
                        context,
                        animation_id=animation_id,
                        direction=direction.direction,
                        frame_number=frame_number,
                        raw_dir=raw_dir,
                        frame_dir=frame_dir,
                        output_name=(
                            f"{config.character_id}_{animation_id}_"
                            f"f{frame_number:02d}_proxy_{revision}.png"
                        ),
                        fixed_scale=fixed_scale,
                        fixed_center_x=(
                            calibrations[direction.direction].source_center_x
                        ),
                    )
                    artifacts.append(artifact)
                    previous_adapter._assert_boundary_contract(
                        artifact,
                        grip_id=grip.grip_id,
                        direction=direction.direction,
                    )

                previous_adapter._assert_cycle_dimensions(
                    previous_adapter._find_armed_frames(
                        artifacts,
                        animation_id=animation_id,
                        direction=direction.direction,
                    ),
                    label=f"{grip.grip_id}/{direction.direction}",
                )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    rendered_count = sum(
        1
        for item in artifacts
        if item.animation_id.startswith(("walk_onehand_", "walk_twohand_"))
        and item.animation_id.endswith("_v15")
    )
    if rendered_count != 48:
        raise RuntimeError(
            f"armed walk render v16 requires 48 frames, got {rendered_count}"
        )
    return artifacts


def _write_manifest_v16(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_manifest_v15(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload[RENDER_STAGE_ID] = {
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "source_animation_stage": "walk_directional_weapon_v15",
        "total_rendered_frames": 48,
        "twohand_right_render_scale_factor": TWOHAND_RIGHT_RENDER_SCALE_FACTOR,
        "reason": "preserve_complete_twohand_right_blade_tip_inside_96x96_canvas",
        "animation_channels_changed": False,
        "weapon_geometry_changed": False,
        "materials_changed": False,
        "baseline_y_91_preserved": True,
        "manual_animation_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "armed_walk_active_stage": RENDER_STAGE_ID,
            "armed_walk_frame_count": 48,
            "armed_walk_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        previous_adapter.create_walk_directional_weapon_actions_v15
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_walk_directional_weapon_v16
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        previous_adapter._write_contact_sheet_v15
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v16
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
