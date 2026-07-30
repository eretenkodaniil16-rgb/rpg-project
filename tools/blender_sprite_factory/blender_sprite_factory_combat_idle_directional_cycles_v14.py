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
import blender_sprite_factory_combat_idle_directional_weapon_v12 as static_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from combat_idle_directional_cycles_builder_v14 import (
    create_combat_idle_directional_cycles_v14,
)
from combat_idle_directional_cycles_profile_v14 import (
    DirectionalCombatIdleCycleV14,
    load_combat_idle_directional_cycles_profile_v14,
)
from combat_idle_down_cycles_profile_v10 import load_combat_idle_cycles_profile_v10
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_RENDER = static_adapter.render_combat_idle_directional_weapon_v12
BASE_CONTACT_SHEET = static_adapter._write_contact_sheet_v12
BASE_WRITE_MANIFEST = static_adapter._write_manifest_v12
PROFILE_PATH = SCRIPT_DIR / "combat_idle_directional_cycles_profile_v14.py"
BUILDER_PATH = SCRIPT_DIR / "combat_idle_directional_cycles_builder_v14.py"
COMPARISON_SHEET_NAME = "combat_idle_directional_cycles_v14.png"
MAX_WIDTH_DRIFT = 4
MAX_HEIGHT_DRIFT = 4


def _find_artifact(
    artifacts: list[factory.FrameArtifact],
    *,
    animation_id: str,
    direction: str,
    frame_number: int,
) -> factory.FrameArtifact:
    matches = [
        item
        for item in artifacts
        if item.animation_id == animation_id
        and item.direction == direction
        and item.frame_number == frame_number
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "combat idle directional cycles v14 requires one artifact: "
            f"{animation_id}/{direction}/f{frame_number:02d}; got {len(matches)}"
        )
    return matches[0]


def _cycle_artifacts(
    artifacts: list[factory.FrameArtifact],
    cycle: DirectionalCombatIdleCycleV14,
    direction: str,
) -> tuple[factory.FrameArtifact, ...]:
    matches = tuple(
        sorted(
            (
                item
                for item in artifacts
                if item.animation_id == cycle.render_animation_id
                and item.direction == direction
            ),
            key=lambda item: item.frame_number,
        )
    )
    if tuple(item.frame_number for item in matches) != (1, 2, 3, 4):
        raise RuntimeError(
            f"combat idle directional cycles v14 missing frames: "
            f"{cycle.cycle_id}/{direction}"
        )
    return matches


def _assert_cycle_dimensions(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    label: str,
) -> None:
    widths = [frame.sprite_width for frame in frames]
    heights = [frame.sprite_height for frame in frames]
    if max(widths) - min(widths) > MAX_WIDTH_DRIFT:
        raise RuntimeError(
            f"{label} width drift exceeds {MAX_WIDTH_DRIFT}px: {widths}"
        )
    if max(heights) - min(heights) > MAX_HEIGHT_DRIFT:
        raise RuntimeError(
            f"{label} height drift exceeds {MAX_HEIGHT_DRIFT}px: {heights}"
        )
    baselines = {frame.baseline_y for frame in frames}
    if len(baselines) != 1:
        raise RuntimeError(f"{label} baseline drifted: {sorted(baselines)}")


def render_combat_idle_directional_cycles_v14(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_combat_idle_directional_cycles_profile_v14(config.character_id)
    source_profile = load_combat_idle_cycles_profile_v10(config.character_id)
    source_by_id = {cycle.cycle_id: cycle for cycle in source_profile.cycles}
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    down_scale = calibrations["down"].scale
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for cycle in profile.cycles:
            source_cycle = source_by_id[cycle.cycle_id]
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{cycle.source_action_id}"
            )
            if action is None or action.get("profile_revision") != "v10":
                raise RuntimeError(
                    f"combat idle directional cycles v14 missing source action: "
                    f"{cycle.source_action_id}"
                )
            factory._assign_action(context.rig, action)

            for direction in profile.directions:
                static_adapter._set_v12_weapon(cycle.cycle_id, direction)
                context.rig.rotation_euler[2] = math.radians(
                    config.directions[direction]
                )
                for source_frame in source_cycle.frames:
                    frame_number = source_frame.pose.frame
                    factory.bpy.context.scene.frame_set(frame_number)
                    factory.bpy.context.view_layer.update()
                    artifact, _ = factory._render_frame(
                        context,
                        animation_id=cycle.render_animation_id,
                        direction=direction,
                        frame_number=frame_number,
                        raw_dir=raw_dir,
                        frame_dir=frame_dir,
                        output_name=(
                            f"{config.character_id}_{cycle.render_animation_id}_"
                            f"{direction}_f{frame_number:02d}_proxy_{revision}.png"
                        ),
                        fixed_scale=down_scale,
                        fixed_center_x=calibrations[direction].source_center_x,
                    )
                    artifacts.append(artifact)

                    if frame_number == 1:
                        static_source = _find_artifact(
                            artifacts,
                            animation_id=cycle.source_static_animation_id,
                            direction=direction,
                            frame_number=1,
                        )
                        if (
                            artifact.output_path.read_bytes()
                            != static_source.output_path.read_bytes()
                        ):
                            raise RuntimeError(
                                "combat idle directional cycles v14 changed approved "
                                f"v12 frame 01: {cycle.cycle_id}/{direction}"
                            )

                    if direction == "down":
                        approved_down = _find_artifact(
                            artifacts,
                            animation_id=cycle.source_action_id,
                            direction="down",
                            frame_number=frame_number,
                        )
                        if (
                            artifact.output_path.read_bytes()
                            != approved_down.output_path.read_bytes()
                        ):
                            raise RuntimeError(
                                "combat idle directional cycles v14 changed approved "
                                f"v10 down pixels: {cycle.cycle_id}/f{frame_number:02d}"
                            )
                    else:
                        static_adapter._assert_no_boundary_touch(
                            artifact.output_path,
                            f"{cycle.cycle_id} {direction} v14 f{frame_number:02d}",
                        )

                _assert_cycle_dimensions(
                    _cycle_artifacts(artifacts, cycle, direction),
                    label=f"{cycle.cycle_id}/{direction}",
                )
    finally:
        static_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    rendered_count = sum(
        1
        for item in artifacts
        if item.animation_id
        in {cycle.render_animation_id for cycle in profile.cycles}
    )
    if rendered_count != 32:
        raise RuntimeError(
            f"combat idle directional cycles v14 requires 32 frames, got {rendered_count}"
        )
    return artifacts


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_combat_idle_directional_cycles_profile_v14(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    rows = len(profile.cycles) * len(profile.directions)
    width = tile_width * len(profile.frame_order)
    height = tile_height * rows
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    row_index = 0
    for cycle in profile.cycles:
        for direction in profile.directions:
            destination_y = (rows - 1 - row_index) * tile_height
            for column_index, artifact in enumerate(
                _cycle_artifacts(artifacts, cycle, direction)
            ):
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
                        destination_y,
                    )
                finally:
                    factory.bpy.data.images.remove(image)
            row_index += 1

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_combat_idle_directional_cycles_v14",
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


def _write_contact_sheet_v14(
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


def _write_manifest_v14(
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
    profile = load_combat_idle_directional_cycles_profile_v14(
        context.config.character_id
    )
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("combat idle directional cycles v14 sheet is missing")

    rendered_cycles: list[dict[str, object]] = []
    for cycle in profile.cycles:
        directions: list[dict[str, object]] = []
        for direction in profile.directions:
            frames = _cycle_artifacts(artifacts, cycle, direction)
            directions.append(
                {
                    "direction": direction,
                    "frames": [
                        {
                            "frame": frame.frame_number,
                            "width": frame.sprite_width,
                            "height": frame.sprite_height,
                            "baseline_y": frame.baseline_y,
                        }
                        for frame in frames
                    ],
                }
            )
        rendered_cycles.append(
            {
                "cycle_id": cycle.cycle_id,
                "display_name": cycle.display_name,
                "source_action_id": cycle.source_action_id,
                "source_static_animation_id": cycle.source_static_animation_id,
                "render_animation_id": cycle.render_animation_id,
                "grip_mode": cycle.grip_mode,
                "fps": cycle.fps,
                "loop": cycle.loop,
                "directions": directions,
            }
        )

    payload["combat_idle_directional_cycles_v14"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "sheet_layout": {
            "columns": ["f01_base", "f02_inhale", "f03_settle", "f04_exhale"],
            "rows": [
                f"{cycle.cycle_id}_{direction}"
                for cycle in profile.cycles
                for direction in profile.directions
            ],
        },
        "static_source_revision": profile.static_source_revision,
        "rejected_experiment_revision": profile.rejected_experiment_revision,
        "total_rendered_frames": 32,
        "cycles": rendered_cycles,
        "locked_contract": {
            "all_frame_01_pixels_match_artist_approved_v12": True,
            "all_down_cycle_pixels_match_artist_approved_v10": True,
            "left_right_up_frames_clear_canvas_boundaries": True,
            "baseline_y_91_preserved": True,
            "v10_actions_reused_without_duplication": True,
            "weapon_geometry_rebuilt": False,
            "appearance_v03_unchanged": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "root_translation_used": False,
        },
        "status": "directional_cycles_require_manual_animation_review",
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "combat_idle_active_stage": "directional_cycles_v14",
            "combat_idle_artist_approved_static_source": "directional_weapon_v12",
            "combat_idle_rejected_experimental_source": "directional_weapon_v13_boundary_failure",
            "combat_idle_directional_cycle_frame_count": 32,
            "combat_idle_directional_cycles_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_combat_idle_directional_cycles_v14
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_combat_idle_directional_cycles_v14
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_v14
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v14
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
