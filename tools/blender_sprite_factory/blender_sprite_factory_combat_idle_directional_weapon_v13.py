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
import blender_sprite_factory_combat_idle_directional_weapon_v12 as previous_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from combat_idle_directional_profile_v11 import DIRECTION_ORDER
from combat_idle_directional_weapon_builder_v13 import (
    ONE_HAND_V13_OBJECTS_BY_DIRECTION,
    create_combat_idle_directional_weapon_v13,
)
from combat_idle_directional_weapon_profile_v13 import (
    load_combat_idle_directional_weapon_profile_v13,
)
from combat_idle_down_animation_builder_v01 import SHEATHED_HILT_OBJECT_NAMES
from combat_idle_down_cycles_profile_v10 import load_combat_idle_cycles_profile_v10
from factory_config import CONTACT_SHEET_BACKGROUND_HEX

BASE_RENDER = previous_adapter.render_combat_idle_directional_weapon_v12
BASE_CONTACT_SHEET = previous_adapter._write_contact_sheet_v12
BASE_WRITE_MANIFEST = previous_adapter._write_manifest_v12
PROFILE_PATH = SCRIPT_DIR / "combat_idle_directional_weapon_profile_v13.py"
BUILDER_PATH = SCRIPT_DIR / "combat_idle_directional_weapon_builder_v13.py"
COMPARISON_SHEET_NAME = "combat_idle_directional_weapon_v13.png"
ONEHAND_RENDER_ID = "combat_idle_onehand_ready_directional_v13"
TWOHAND_RENDER_ID = "combat_idle_twohand_center_high_directional_v13"


def _hide_v13_modules() -> None:
    for names in ONE_HAND_V13_OBJECTS_BY_DIRECTION.values():
        for name in names:
            obj = factory.bpy.data.objects.get(name)
            if obj is None:
                raise RuntimeError(f"combat idle directional v13 missing object: {name}")
            obj.hide_render = True
            obj.hide_viewport = True


def _set_v13_weapon(candidate_id: str | None, direction: str | None) -> None:
    _hide_v13_modules()
    if candidate_id == "onehand_ready" and direction in {"left", "right"}:
        previous_adapter._set_v12_weapon(None, None)
        for name in SHEATHED_HILT_OBJECT_NAMES:
            obj = factory.bpy.data.objects.get(name)
            if obj is None:
                raise RuntimeError(f"combat idle directional v13 missing hilt: {name}")
            obj.hide_render = True
            obj.hide_viewport = True
        for name in ONE_HAND_V13_OBJECTS_BY_DIRECTION[direction]:
            obj = factory.bpy.data.objects[name]
            obj.hide_render = False
            obj.hide_viewport = False
        return
    previous_adapter._set_v12_weapon(candidate_id, direction)


def _find_artifact(
    artifacts: list[factory.FrameArtifact], animation_id: str, direction: str
) -> factory.FrameArtifact:
    matches = [
        item
        for item in artifacts
        if item.animation_id == animation_id
        and item.direction == direction
        and item.frame_number == 1
    ]
    if len(matches) != 1:
        raise RuntimeError(f"combat idle directional v13 missing {animation_id}/{direction}")
    return matches[0]


def _assert_no_boundary_touch(path: Path, label: str) -> None:
    image = factory.bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = (int(value) for value in image.size)
        pixels = tuple(image.pixels[:])
        def alpha(x: int, y: int) -> float:
            return pixels[(y * width + x) * 4 + 3]
        touched = []
        if any(alpha(0, y) >= 0.5 for y in range(height)):
            touched.append("left")
        if any(alpha(width - 1, y) >= 0.5 for y in range(height)):
            touched.append("right")
        if any(alpha(x, 0) >= 0.5 for x in range(width)):
            touched.append("bottom")
        if any(alpha(x, height - 1) >= 0.5 for x in range(width)):
            touched.append("top")
        if touched:
            raise RuntimeError(f"{label} touches canvas boundary: {touched}")
    finally:
        factory.bpy.data.images.remove(image)


def render_combat_idle_directional_weapon_v13(
    context: factory.BuildContext, run_dir: Path
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_combat_idle_directional_weapon_profile_v13(config.character_id)
    cycles = load_combat_idle_cycles_profile_v10(config.character_id)
    cycle_by_id = {cycle.cycle_id: cycle for cycle in cycles.cycles}
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    down_scale = calibrations["down"].scale
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    corrections = {item.direction: item for item in profile.corrected_sides}

    try:
        for candidate_id, render_id, previous_id in (
            ("onehand_ready", ONEHAND_RENDER_ID, previous_adapter.ONEHAND_RENDER_ID),
            ("twohand_center_high", TWOHAND_RENDER_ID, previous_adapter.TWOHAND_RENDER_ID),
        ):
            cycle = cycle_by_id[candidate_id]
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{cycle.animation_id}"
            )
            if action is None or action.get("profile_revision") != "v10":
                raise RuntimeError(f"combat idle directional v13 missing {cycle.animation_id}")
            factory._assign_action(context.rig, action)
            factory.bpy.context.scene.frame_set(1)

            for direction in DIRECTION_ORDER:
                _set_v13_weapon(candidate_id, direction)
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
                previous = _find_artifact(artifacts, previous_id, direction)
                locked = candidate_id == "twohand_center_high" or direction in profile.locked_directions
                if locked:
                    if artifact.output_path.read_bytes() != previous.output_path.read_bytes():
                        raise RuntimeError(
                            f"combat idle directional v13 changed locked pixels: "
                            f"{candidate_id}/{direction}"
                        )
                else:
                    correction = corrections[direction]
                    _assert_no_boundary_touch(artifact.output_path, f"one-hand {direction} v13")
                    if artifact.sprite_width < correction.minimum_sprite_width:
                        raise RuntimeError(
                            f"one-hand {direction} v13 width {artifact.sprite_width}px "
                            f"below {correction.minimum_sprite_width}px"
                        )
    finally:
        _set_v13_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
    return artifacts


def _ordered(artifacts: list[factory.FrameArtifact], animation_id: str) -> tuple[factory.FrameArtifact, ...]:
    return tuple(_find_artifact(artifacts, animation_id, direction) for direction in DIRECTION_ORDER)


def _write_v13_sheet(config: object, artifacts: list[factory.FrameArtifact], output_path: Path) -> Path:
    tile_w = config.technical.canvas_width
    tile_h = config.technical.canvas_height
    width, height = tile_w * 4, tile_h * 2
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [component for _ in range(width * height) for component in (*background, 1.0)]
    for row, animation_id in enumerate((ONEHAND_RENDER_ID, TWOHAND_RENDER_ID)):
        y = (1 - row) * tile_h
        for column, artifact in enumerate(_ordered(artifacts, animation_id)):
            image = factory.bpy.data.images.load(str(artifact.output_path), check_existing=False)
            try:
                factory._copy_tile(pixels, width, tuple(image.pixels[:]), tile_w, tile_h, column * tile_w, y)
            finally:
                factory.bpy.data.images.remove(image)
    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_combat_idle_directional_weapon_v13",
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


def _write_contact_sheet_v13(config: object, artifacts: list[factory.FrameArtifact], output_path: Path) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_v13_sheet(config, artifacts, output_path.parent / COMPARISON_SHEET_NAME)
    return result


def _write_manifest_v13(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST(context, run_dir, run_id, blend_path, artifacts, contact_sheet)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = load_combat_idle_directional_weapon_profile_v13(context.config.character_id)
    sheet = run_dir / COMPARISON_SHEET_NAME
    payload["combat_idle_directional_weapon_v13"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(sheet),
        "corrected_sides": [item.direction for item in profile.corrected_sides],
        "rejected_v12": {
            "left": "formal_width_passed_but_blade_remained_visually_occluded",
            "right": "blade_crossed_too_horizontally_in_front_of_lower_body",
        },
        "locked_contract": {
            "down_and_up_onehand_pixels_unchanged": True,
            "all_twohand_pixels_unchanged": True,
            "body_actions_unchanged": True,
            "appearance_v03_unchanged": True,
            "side_frames_clear_boundaries": True,
            "mirroring_used": False,
            "negative_scale_used": False,
        },
        "status": "corrected_onehand_side_candidates_require_manual_review",
    }
    payload.setdefault("animation_contract", {}).update({
        "combat_idle_active_stage": "directional_weapon_v13",
        "combat_idle_onehand_side_v13_review_required": True,
        "combat_idle_full_directional_cycles_not_started": True,
    })
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = create_combat_idle_directional_weapon_v13
    base_adapter.render_pilot_combat_idle_down_v01 = render_combat_idle_directional_weapon_v13
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v13
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v13
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
