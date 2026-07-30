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
import blender_sprite_factory_combat_idle_directional_v11 as previous_adapter
import blender_sprite_factory_combat_idle_down_cycles_v10 as cycle_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from combat_idle_directional_profile_v11 import (
    DIRECTION_ORDER,
    load_combat_idle_directional_profile_v11,
)
from combat_idle_directional_weapon_builder_v12 import (
    ONE_HAND_V12_OBJECTS_BY_DIRECTION,
    create_combat_idle_directional_weapon_v12,
)
from combat_idle_directional_weapon_profile_v12 import (
    load_combat_idle_directional_weapon_profile_v12,
)
from combat_idle_down_animation_builder_v01 import SHEATHED_HILT_OBJECT_NAMES
from combat_idle_down_cycles_profile_v10 import load_combat_idle_cycles_profile_v10
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_RENDER = previous_adapter.render_combat_idle_directional_v11
BASE_CONTACT_SHEET = previous_adapter._write_contact_sheet_v11
BASE_WRITE_MANIFEST = previous_adapter._write_manifest_v11
PROFILE_PATH = SCRIPT_DIR / "combat_idle_directional_weapon_profile_v12.py"
BUILDER_PATH = SCRIPT_DIR / "combat_idle_directional_weapon_builder_v12.py"
COMPARISON_SHEET_NAME = "combat_idle_directional_weapon_v12.png"
ONEHAND_RENDER_ID = "combat_idle_onehand_ready_directional_v12"
TWOHAND_RENDER_ID = "combat_idle_twohand_center_high_directional_v12"


def _require_objects(names: tuple[str, ...], label: str) -> None:
    missing = [name for name in names if factory.bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError(f"combat idle directional weapon v12 missing {label}: {missing}")


def _hide_v12_onehand_modules() -> None:
    for direction, names in ONE_HAND_V12_OBJECTS_BY_DIRECTION.items():
        _require_objects(names, f"one-hand {direction} v12")
        for name in names:
            obj = factory.bpy.data.objects[name]
            obj.hide_render = True
            obj.hide_viewport = True


def _set_v12_weapon(
    candidate_id: str | None,
    direction: str | None,
) -> None:
    _hide_v12_onehand_modules()
    cycles = load_combat_idle_cycles_profile_v10("human_warrior_m01")
    cycle_by_id = {cycle.cycle_id: cycle for cycle in cycles.cycles}

    if candidate_id is None:
        cycle_adapter._set_cycle_weapon(None)
        return
    if candidate_id == "twohand_center_high":
        cycle_adapter._set_cycle_weapon(cycle_by_id[candidate_id])
        return
    if candidate_id != "onehand_ready" or direction is None:
        raise KeyError(f"Unknown combat idle directional v12 weapon: {candidate_id}/{direction}")
    if direction == "down":
        cycle_adapter._set_cycle_weapon(cycle_by_id[candidate_id])
        return

    cycle_adapter._set_cycle_weapon(None)
    names = ONE_HAND_V12_OBJECTS_BY_DIRECTION[direction]
    for name in SHEATHED_HILT_OBJECT_NAMES:
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"combat idle directional v12 missing sheathed hilt: {name}")
        obj.hide_render = True
        obj.hide_viewport = True
    for name in names:
        obj = factory.bpy.data.objects[name]
        obj.hide_render = False
        obj.hide_viewport = False


def _previous_artifact(
    artifacts: list[factory.FrameArtifact],
    animation_id: str,
    direction: str,
) -> factory.FrameArtifact:
    matches = [
        item
        for item in artifacts
        if item.animation_id == animation_id
        and item.direction == direction
        and item.frame_number == 1
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"combat idle directional v12 requires one previous artifact "
            f"{animation_id}/{direction}"
        )
    return matches[0]


def _assert_no_boundary_touch(path: Path, label: str) -> None:
    image = factory.bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = (int(value) for value in image.size)
        pixels = tuple(image.pixels[:])
        def alpha_at(x: int, y: int) -> float:
            return pixels[(y * width + x) * 4 + 3]
        touches = {
            "left": any(alpha_at(0, y) >= 0.5 for y in range(height)),
            "right": any(alpha_at(width - 1, y) >= 0.5 for y in range(height)),
            "bottom": any(alpha_at(x, 0) >= 0.5 for x in range(width)),
            "top": any(alpha_at(x, height - 1) >= 0.5 for x in range(width)),
        }
        active = [edge for edge, touched in touches.items() if touched]
        if active:
            raise RuntimeError(f"{label} touches canvas boundary: {active}")
    finally:
        factory.bpy.data.images.remove(image)


def render_combat_idle_directional_weapon_v12(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    directional_profile = load_combat_idle_directional_profile_v11(config.character_id)
    weapon_profile = load_combat_idle_directional_weapon_profile_v12(config.character_id)
    cycles = load_combat_idle_cycles_profile_v10(config.character_id)
    cycle_by_id = {cycle.cycle_id: cycle for cycle in cycles.cycles}
    calibrations = previous_adapter._direction_calibrations(context, run_dir)
    down_scale = calibrations["down"].scale
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    minimum_width = {
        item.direction: item.minimum_sprite_width
        for item in weapon_profile.corrected_onehand_directions
    }
    previous_id_by_candidate = {
        candidate.candidate_id: candidate.render_animation_id
        for candidate in directional_profile.candidates
    }

    try:
        for candidate_id, render_id in (
            ("onehand_ready", ONEHAND_RENDER_ID),
            ("twohand_center_high", TWOHAND_RENDER_ID),
        ):
            cycle = cycle_by_id[candidate_id]
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{cycle.animation_id}"
            )
            if action is None or action.get("profile_revision") != "v10":
                raise RuntimeError(
                    f"combat idle directional weapon v12 cannot find {cycle.animation_id}"
                )
            factory._assign_action(context.rig, action)
            factory.bpy.context.scene.frame_set(1)

            for direction in DIRECTION_ORDER:
                _set_v12_weapon(candidate_id, direction)
                context.rig.rotation_euler[2] = math.radians(config.directions[direction])
                factory.bpy.context.view_layer.update()
                artifact, _ = factory._render_frame(
                    context,
                    animation_id=render_id,
                    direction=direction,
                    frame_number=1,
                    raw_dir=raw_dir,
                    frame_dir=frame_dir,
                    output_name=(
                        f"{config.character_id}_{render_id}_{direction}_f01_"
                        f"proxy_{revision}.png"
                    ),
                    fixed_scale=down_scale,
                    fixed_center_x=calibrations[direction].source_center_x,
                )
                artifacts.append(artifact)

                previous = _previous_artifact(
                    artifacts,
                    previous_id_by_candidate[candidate_id],
                    direction,
                )
                must_match_previous = (
                    candidate_id == "twohand_center_high" or direction == "down"
                )
                if must_match_previous:
                    if artifact.output_path.read_bytes() != previous.output_path.read_bytes():
                        raise RuntimeError(
                            f"combat idle directional v12 changed locked pixels for "
                            f"{candidate_id}/{direction}"
                        )
                else:
                    _assert_no_boundary_touch(
                        artifact.output_path,
                        f"one-hand {direction} v12",
                    )
                    if artifact.sprite_width < minimum_width[direction]:
                        raise RuntimeError(
                            f"one-hand {direction} v12 width {artifact.sprite_width}px "
                            f"is below readability budget {minimum_width[direction]}px"
                        )
    finally:
        _set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    return artifacts


def _v12_artifacts(
    artifacts: list[factory.FrameArtifact],
    animation_id: str,
) -> tuple[factory.FrameArtifact, ...]:
    by_direction = {
        item.direction: item
        for item in artifacts
        if item.animation_id == animation_id and item.frame_number == 1
    }
    if tuple(direction for direction in DIRECTION_ORDER if direction in by_direction) != DIRECTION_ORDER:
        raise RuntimeError(f"combat idle directional v12 missing directions: {animation_id}")
    return tuple(by_direction[direction] for direction in DIRECTION_ORDER)


def _write_v12_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(DIRECTION_ORDER)
    height = tile_height * 2
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]
    rows = (ONEHAND_RENDER_ID, TWOHAND_RENDER_ID)
    for row_index, animation_id in enumerate(rows):
        row_y = (len(rows) - 1 - row_index) * tile_height
        for column_index, artifact in enumerate(_v12_artifacts(artifacts, animation_id)):
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
        "human_warrior_m01_combat_idle_directional_weapon_v12",
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


def _write_contact_sheet_v12(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_v12_sheet(config, artifacts, output_path.parent / COMPARISON_SHEET_NAME)
    return result


def _write_manifest_v12(
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
    profile = load_combat_idle_directional_weapon_profile_v12(
        context.config.character_id
    )
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("combat idle directional weapon v12 sheet is missing")

    vectors = {
        item.direction: {
            "side_x": item.side_x,
            "depth_y": item.depth_y,
            "vertical_z": item.vertical_z,
            "minimum_sprite_width": item.minimum_sprite_width,
        }
        for item in profile.corrected_onehand_directions
    }
    payload["combat_idle_directional_weapon_v12"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "columns_left_to_right": list(DIRECTION_ORDER),
        "rows_top_to_bottom": ["onehand_ready_v12", "twohand_center_high_v11_locked"],
        "onehand_direction_vectors": vectors,
        "rejected_v11_projections": {
            "left": "blade_over_occluded_by_far_side_body",
            "right": "weapon_pommel_projection_touched_top_boundary",
            "up": "blade_projection_touched_right_boundary",
        },
        "locked_contract": {
            "approved_down_pixels_unchanged": True,
            "twohand_all_direction_pixels_unchanged": True,
            "body_pose_actions_unchanged": True,
            "appearance_v03_unchanged": True,
            "onehand_corrected_frames_clear_canvas_boundaries": True,
            "weapon_geometry_lengths_unchanged": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "root_translation_used": False,
        },
        "status": "corrected_directional_static_candidates_require_manual_review",
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "combat_idle_active_stage": "directional_weapon_v12",
            "combat_idle_directional_down_locked": True,
            "combat_idle_directional_twohand_v11_locked": True,
            "combat_idle_directional_onehand_v12_review_required": True,
            "combat_idle_directional_cycles_not_started": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_combat_idle_directional_weapon_v12
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_combat_idle_directional_weapon_v12
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v12
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v12
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
