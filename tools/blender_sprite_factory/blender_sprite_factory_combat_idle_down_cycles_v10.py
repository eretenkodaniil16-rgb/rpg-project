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
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
import blender_sprite_factory_combat_idle_down_weapon_variants_v06 as calibration_adapter
import blender_sprite_factory_combat_idle_down_weapon_variants_v09 as previous_adapter
from combat_idle_down_cycles_builder_v10 import create_combat_idle_cycles_v10
from combat_idle_down_cycles_profile_v10 import (
    CombatIdleCycleV10,
    load_combat_idle_cycles_profile_v10,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_RENDER = previous_adapter.render_weapon_stance_variants_v09
BASE_CONTACT_SHEET = previous_adapter._write_contact_sheet_v09
BASE_WRITE_MANIFEST = previous_adapter._write_manifest_v09
PROFILE_PATH = SCRIPT_DIR / "combat_idle_down_cycles_profile_v10.py"
BUILDER_PATH = SCRIPT_DIR / "combat_idle_down_cycles_builder_v10.py"
COMPARISON_SHEET_NAME = "combat_idle_down_cycles_v10.png"


def _set_cycle_weapon(cycle: CombatIdleCycleV10 | None) -> None:
    variant_id = None if cycle is None else cycle.weapon_variant_id
    previous_adapter._set_weapon_variant_v09(variant_id)


def render_combat_idle_cycles_v10(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_combat_idle_cycles_profile_v10(config.character_id)
    calibration = calibration_adapter.calibration_adapter._calibrate_idle_down(
        context,
        run_dir,
    )
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for cycle in profile.cycles:
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{cycle.animation_id}"
            )
            if action is None or action.get("profile_revision") != "v10":
                raise RuntimeError(
                    f"combat idle cycles v10 cannot find action {cycle.animation_id}"
                )
            factory._assign_action(context.rig, action)
            context.rig.rotation_euler[2] = math.radians(config.directions["down"])
            _set_cycle_weapon(cycle)
            for frame in cycle.frames:
                factory.bpy.context.scene.frame_set(frame.pose.frame)
                factory.bpy.context.view_layer.update()
                artifact, _ = factory._render_frame(
                    context,
                    animation_id=cycle.animation_id,
                    direction="down",
                    frame_number=frame.pose.frame,
                    raw_dir=raw_dir,
                    frame_dir=frame_dir,
                    output_name=(
                        f"{config.character_id}_{cycle.animation_id}_down_"
                        f"f{frame.pose.frame:02d}_proxy_{revision}.png"
                    ),
                    fixed_scale=calibration.scale,
                    fixed_center_x=calibration.source_center_x,
                )
                artifacts.append(artifact)
    finally:
        _set_cycle_weapon(None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    return artifacts


def _cycle_artifacts(
    artifacts: list[factory.FrameArtifact],
    cycle: CombatIdleCycleV10,
) -> tuple[factory.FrameArtifact, ...]:
    matches = sorted(
        (item for item in artifacts if item.animation_id == cycle.animation_id),
        key=lambda item: item.frame_number,
    )
    if tuple(item.frame_number for item in matches) != (1, 2, 3, 4):
        raise RuntimeError(
            f"combat idle cycles v10 requires four ordered frames for {cycle.cycle_id}"
        )
    return tuple(matches)


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_combat_idle_cycles_profile_v10(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * 4
    height = tile_height * len(profile.cycles)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, cycle in enumerate(profile.cycles):
        row_y = (len(profile.cycles) - 1 - row_index) * tile_height
        for column_index, artifact in enumerate(_cycle_artifacts(artifacts, cycle)):
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
                    row_y,
                )
            finally:
                factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_combat_idle_down_cycles_v10",
        width=width,
        height=height,
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


def _write_contact_sheet_v10(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_cycle_sheet(
        config,
        artifacts,
        output_path.parent / COMPARISON_SHEET_NAME,
    )
    return result


def _write_manifest_v10(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = load_combat_idle_cycles_profile_v10(context.config.character_id)
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("combat idle cycles v10 comparison sheet is missing")

    rendered_cycles: list[dict[str, object]] = []
    for cycle in profile.cycles:
        cycle_frames = _cycle_artifacts(artifacts, cycle)
        rendered_cycles.append(
            {
                "cycle_id": cycle.cycle_id,
                "display_name": cycle.display_name,
                "animation_id": cycle.animation_id,
                "grip_mode": cycle.grip_mode,
                "weapon_variant_id": cycle.weapon_variant_id,
                "weapon_id": cycle.weapon_id,
                "source_animation_id": cycle.source_animation_id,
                "source_revision": cycle.source_revision,
                "fps": cycle.fps,
                "loop": cycle.loop,
                "selected_best_candidate": True,
                "frames": [
                    {
                        "frame": artifact.frame_number,
                        "width": artifact.sprite_width,
                        "height": artifact.sprite_height,
                        "baseline_y": artifact.baseline_y,
                    }
                    for artifact in cycle_frames
                ],
            }
        )

    payload["combat_idle_down_cycles_v10"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "comparison_sheet_layout": {
            "columns": ["f01_base", "f02_inhale", "f03_settle", "f04_exhale"],
            "rows_top_to_bottom": ["onehand_ready_v09", "twohand_center_high_v06"],
        },
        "selected_sources": {
            "one_hand": "combat_idle_onehand_ready_v09",
            "two_hand": "combat_idle_twohand_center_high_v06",
        },
        "retained_alternatives": {
            "one_hand_low": "combat_idle_onehand_low_v09",
            "two_hand_low": "combat_idle_twohand_center_low_v06",
        },
        "cycles": rendered_cycles,
        "locked_contract": {
            "appearance_v03_unchanged": True,
            "approved_idle_and_walk_set_unchanged": True,
            "one_hand_ready_v09_is_frame_01_source": True,
            "two_hand_center_high_v06_is_frame_01_source": True,
            "planted_lower_body": True,
            "restrained_four_frame_breathing": True,
            "weapon_geometry_rebuilt": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "root_translation_used": False,
        },
        "status": "technical_cycles_require_manual_animation_review",
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "combat_idle_down_active_stage": "cycles_v10",
            "combat_idle_down_one_hand_revision": "v10_from_ready_v09",
            "combat_idle_down_two_hand_revision": "v10_from_high_v06",
            "combat_idle_down_selected_source_variants": True,
            "combat_idle_down_manual_animation_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = create_combat_idle_cycles_v10
    base_adapter.render_pilot_combat_idle_down_v01 = render_combat_idle_cycles_v10
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v10
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v10
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
