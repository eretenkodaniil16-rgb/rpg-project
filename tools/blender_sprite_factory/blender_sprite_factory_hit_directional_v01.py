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
import blender_sprite_factory_hit_down_keyposes_v01 as down_adapter
from factory_config import CONTACT_SHEET_BACKGROUND_HEX
from hit_directional_cycles_profile_v01 import (
    load_hit_directional_cycles_profile_v01,
)
from hit_down_keyposes_builder_v01 import create_hit_down_cycle_actions_v01


PROFILE_PATH = SCRIPT_DIR / "hit_directional_cycles_profile_v01.py"
BUILDER_PATH = SCRIPT_DIR / "hit_down_keyposes_builder_v01.py"
DOWN_ADAPTER_PATH = SCRIPT_DIR / "blender_sprite_factory_hit_down_keyposes_v01.py"
CONTACT_SHEET_NAME = "human_warrior_m01_hit_01_directional_grips_v01.png"
EXPECTED_FRAME_NUMBERS = (1, 2, 3, 4, 5, 6)
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _profiles(character_id: str) -> tuple[object, ...]:
    return down_adapter._profiles(character_id)


def _find_frames(
    artifacts: list[factory.FrameArtifact],
    *,
    animation_id: str,
    direction: str,
) -> tuple[factory.FrameArtifact, ...]:
    matches = tuple(
        sorted(
            (
                item
                for item in artifacts
                if item.animation_id == animation_id
                and item.direction == direction
            ),
            key=lambda item: item.frame_number,
        )
    )
    if tuple(item.frame_number for item in matches) != EXPECTED_FRAME_NUMBERS:
        raise RuntimeError(
            f"hit directional v01 missing frames: {animation_id}/{direction}"
        )
    return matches


def _assert_no_boundary_touch(
    artifact: factory.FrameArtifact,
    *,
    label: str,
) -> None:
    counts = down_adapter._edge_alpha_counts(artifact.output_path)
    active = {edge: count for edge, count in counts.items() if count > 0}
    if active:
        raise RuntimeError(f"hit directional v01 {label} touches boundaries: {active}")


def _assert_direction_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    cycle_id: str,
    direction: str,
) -> None:
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            f"hit directional v01 {cycle_id}/{direction} baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )
    for item in frames:
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"hit directional v01 {cycle_id}/{direction}/"
                f"f{item.frame_number:02d} is empty"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                f"hit directional v01 {cycle_id}/{direction}/"
                f"f{item.frame_number:02d} exceeds 96x96: "
                f"{item.sprite_width}x{item.sprite_height}"
            )
        if direction != "down":
            _assert_no_boundary_touch(
                item,
                label=f"{cycle_id}/{direction}/f{item.frame_number:02d}",
            )


def render_hit_directional_cycles_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = down_adapter.render_hit_down_cycle_v01(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    directional = load_hit_directional_cycles_profile_v01(config.character_id)
    source_profiles = _profiles(config.character_id)
    source_by_cycle = {
        profile.stance_variant_id: profile for profile in source_profiles
    }
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    fixed_scale = calibrations["down"].scale
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for cycle in directional.cycles:
            profile = source_by_cycle[cycle.cycle_id]
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{profile.animation_id}"
            )
            if action is None or action.get("profile_revision") != profile.revision:
                raise RuntimeError(
                    f"hit directional v01 action is missing: {profile.animation_id}"
                )
            factory._assign_action(context.rig, action)

            for direction in directional.review_directions:
                weapon_adapter._set_v12_weapon(profile.weapon_cycle_id, direction)
                context.rig.rotation_euler[2] = math.radians(
                    config.directions[direction]
                )
                factory.bpy.context.view_layer.update()

                for frame_number in directional.frame_order:
                    artifact, _ = factory._render_frame(
                        context,
                        animation_id=profile.animation_id,
                        direction=direction,
                        frame_number=frame_number,
                        raw_dir=raw_dir,
                        frame_dir=frame_dir,
                        output_name=(
                            f"{config.character_id}_{profile.animation_id}_"
                            f"{direction}_f{frame_number:02d}_proxy_{revision}.png"
                        ),
                        fixed_scale=fixed_scale,
                        fixed_center_x=calibrations[direction].source_center_x,
                    )
                    artifacts.append(artifact)

                frames = _find_frames(
                    artifacts,
                    animation_id=profile.animation_id,
                    direction=direction,
                )
                _assert_direction_contract(
                    frames,
                    cycle_id=cycle.cycle_id,
                    direction=direction,
                )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    expected_count = (
        len(directional.cycles)
        * len(directional.directions)
        * len(directional.frame_order)
    )
    if len(artifacts) != expected_count:
        raise RuntimeError(
            f"hit directional v01 requires {expected_count} frames, "
            f"got {len(artifacts)}"
        )
    for cycle in directional.cycles:
        for direction in directional.directions:
            frames = _find_frames(
                artifacts,
                animation_id=cycle.animation_id,
                direction=direction,
            )
            _assert_direction_contract(
                frames,
                cycle_id=cycle.cycle_id,
                direction=direction,
            )
    return artifacts


def _row_specs(character_id: str) -> tuple[tuple[object, str], ...]:
    directional = load_hit_directional_cycles_profile_v01(character_id)
    source_by_cycle = {
        profile.stance_variant_id: profile for profile in _profiles(character_id)
    }
    return tuple(
        (source_by_cycle[cycle.cycle_id], direction)
        for cycle in directional.cycles
        for direction in directional.directions
    )


def _write_directional_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    rows = _row_specs(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(EXPECTED_FRAME_NUMBERS)
    height = tile_height * len(rows)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, (profile, direction) in enumerate(rows):
        frames = _find_frames(
            artifacts,
            animation_id=profile.animation_id,
            direction=direction,
        )
        row_y = (len(rows) - 1 - row_index) * tile_height
        for column_index, artifact in enumerate(frames):
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
        "human_warrior_m01_hit_directional_grips_v01",
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


def _write_contact_sheet_v01(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = _write_directional_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_directional_sheet(config, artifacts, named_path)
    return result


def _direction_payload(
    artifacts: list[factory.FrameArtifact],
    profile: object,
    direction: str,
) -> dict[str, object]:
    frames = _find_frames(
        artifacts,
        animation_id=profile.animation_id,
        direction=direction,
    )
    return {
        "direction": direction,
        "frame_count": len(frames),
        "frames": [
            {
                "frame": item.frame_number,
                "phase": profile.poses[index].phase,
                "width": item.sprite_width,
                "height": item.sprite_height,
                "baseline_y": item.baseline_y,
            }
            for index, item in enumerate(frames)
        ],
    }


def _write_manifest_v01(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_RUN_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    directional = load_hit_directional_cycles_profile_v01(
        context.config.character_id
    )
    source_by_cycle = {
        profile.stance_variant_id: profile
        for profile in _profiles(context.config.character_id)
    }
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("hit directional v01 contact sheet is missing")

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": [
            f"{profile.stance_variant_id}_{direction}"
            for profile, direction in _row_specs(context.config.character_id)
        ],
        "columns_left_to_right": list(directional.phase_order),
    }
    payload["hit_directional_cycles_v01"] = {
        "profile_revision": directional.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "down_adapter_path": context.config.relative_to_repo(DOWN_ADAPTER_PATH),
        "down_adapter_sha256": hashlib.sha256(
            DOWN_ADAPTER_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "directions": list(directional.directions),
        "frame_order": list(directional.frame_order),
        "phase_order": list(directional.phase_order),
        "fps": directional.fps,
        "duration_seconds": directional.duration_seconds,
        "grip_count": len(directional.cycles),
        "direction_count": len(directional.directions),
        "frames_per_direction": len(directional.frame_order),
        "total_rendered_frames": len(artifacts),
        "cycles": {
            cycle.cycle_id: {
                "animation_id": cycle.animation_id,
                "stance_source_revision": cycle.stance_source_revision,
                "weapon_cycle_id": cycle.weapon_cycle_id,
                "source_profile_revision": cycle.source_profile_revision,
                "directions": {
                    direction: _direction_payload(
                        artifacts,
                        source_by_cycle[cycle.cycle_id],
                        direction,
                    )
                    for direction in directional.directions
                },
            }
            for cycle in directional.cycles
        },
        "locked_contract": {
            "approved_down_renderer_reused": True,
            "approved_down_motion_unchanged": True,
            "directional_stance_source_v14": True,
            "directional_weapon_source_v12": True,
            "local_actions_reused_without_duplication": True,
            "left_right_up_rendered_independently": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "baseline_y_91_required": True,
            "manual_directional_review_required": True,
            "runtime_connected": False,
        },
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "hit_01_current_stage": "directional_grips_cycle_v01",
            "hit_01_grip_count": len(directional.cycles),
            "hit_01_direction_count": len(directional.directions),
            "hit_01_frame_count_per_direction": len(directional.frame_order),
            "hit_01_total_frame_count": len(artifacts),
            "hit_01_fps": directional.fps,
            "hit_01_duration_seconds": directional.duration_seconds,
            "hit_01_manual_directional_review_required": True,
            "hit_01_runtime_connected": False,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = create_hit_down_cycle_actions_v01
    base_adapter.render_pilot_combat_idle_down_v01 = render_hit_directional_cycles_v01
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v01
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v01
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
