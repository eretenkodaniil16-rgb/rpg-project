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
import blender_sprite_factory_combat_idle_directional_cycles_v14 as previous_adapter
import blender_sprite_factory_combat_idle_directional_v11 as directional_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from factory_config import CONTACT_SHEET_BACKGROUND_HEX
from walk_directional_weapon_builder_v15 import (
    create_walk_directional_weapon_actions_v15,
)
from walk_directional_weapon_profile_v15 import (
    ArmedWalkDirectionV15,
    ArmedWalkGripV15,
    load_walk_directional_weapon_profile_v15,
)


BASE_RENDER = previous_adapter.render_combat_idle_directional_cycles_v14
BASE_CONTACT_SHEET = previous_adapter._write_contact_sheet_v14
BASE_WRITE_MANIFEST = previous_adapter._write_manifest_v14
PROFILE_PATH = SCRIPT_DIR / "walk_directional_weapon_profile_v15.py"
BUILDER_PATH = SCRIPT_DIR / "walk_directional_weapon_builder_v15.py"
COMPARISON_SHEET_NAME = "walk_directional_weapon_v15.png"
MAX_WIDTH_DRIFT = 8
MAX_HEIGHT_DRIFT = 6
MAX_ALLOWED_ONEHAND_DOWN_LEFT_EDGE_PIXELS = 12


def _action_id(grip: ArmedWalkGripV15, direction: str) -> str:
    return f"{grip.action_prefix}_{direction}_v15"


def _find_armed_frames(
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
    if tuple(item.frame_number for item in matches) != (1, 2, 3, 4, 5, 6):
        raise RuntimeError(
            f"armed walk v15 missing frames: {animation_id}/{direction}"
        )
    return matches


def _lower_body_snapshot(rig: object) -> tuple[float, ...]:
    pelvis = rig.pose.bones["pelvis"]
    values = [
        float(pelvis.location[0]),
        float(pelvis.location[2]),
        float(pelvis.rotation_euler[2]),
    ]
    for bone_name in (
        "thigh.L",
        "thigh.R",
        "shin.L",
        "shin.R",
        "foot.L",
        "foot.R",
    ):
        values.append(float(rig.pose.bones[bone_name].rotation_euler[0]))
    return tuple(values)


def _assert_lower_body_matches_source(
    context: factory.BuildContext,
    *,
    source_action: object,
    armed_action: object,
    frame_number: int,
    label: str,
) -> None:
    factory._assign_action(context.rig, source_action)
    factory.bpy.context.scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    expected = _lower_body_snapshot(context.rig)

    factory._assign_action(context.rig, armed_action)
    factory.bpy.context.scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    actual = _lower_body_snapshot(context.rig)
    deltas = [abs(left - right) for left, right in zip(expected, actual)]
    if max(deltas, default=0.0) > 1e-8:
        raise RuntimeError(
            f"armed walk v15 changed approved lower body: {label}; deltas={deltas}"
        )


def _edge_alpha_counts(path: Path) -> dict[str, int]:
    image = factory.bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = (int(value) for value in image.size)
        pixels = tuple(image.pixels[:])

        def alpha(x: int, y: int) -> float:
            return pixels[(y * width + x) * 4 + 3]

        return {
            "left": sum(alpha(0, y) >= 0.5 for y in range(height)),
            "right": sum(alpha(width - 1, y) >= 0.5 for y in range(height)),
            "bottom": sum(alpha(x, 0) >= 0.5 for x in range(width)),
            "top": sum(alpha(x, height - 1) >= 0.5 for x in range(width)),
        }
    finally:
        factory.bpy.data.images.remove(image)


def _assert_boundary_contract(
    artifact: factory.FrameArtifact,
    *,
    grip_id: str,
    direction: str,
) -> None:
    label = f"{grip_id}/{direction}/f{artifact.frame_number:02d}"
    if grip_id == "onehand_ready" and direction == "down":
        counts = _edge_alpha_counts(artifact.output_path)
        forbidden = {
            edge: count
            for edge, count in counts.items()
            if edge != "left" and count > 0
        }
        if forbidden:
            raise RuntimeError(
                f"armed walk v15 {label} touches forbidden boundaries: {forbidden}"
            )
        if counts["left"] > MAX_ALLOWED_ONEHAND_DOWN_LEFT_EDGE_PIXELS:
            raise RuntimeError(
                f"armed walk v15 {label} exceeds approved left-edge budget: "
                f"{counts['left']}"
            )
        return
    weapon_adapter._assert_no_boundary_touch(artifact.output_path, label)


def _assert_cycle_dimensions(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    label: str,
) -> None:
    widths = [item.sprite_width for item in frames]
    heights = [item.sprite_height for item in frames]
    if max(widths) - min(widths) > MAX_WIDTH_DRIFT:
        raise RuntimeError(
            f"armed walk v15 {label} width drift exceeds {MAX_WIDTH_DRIFT}px: {widths}"
        )
    if max(heights) - min(heights) > MAX_HEIGHT_DRIFT:
        raise RuntimeError(
            f"armed walk v15 {label} height drift exceeds {MAX_HEIGHT_DRIFT}px: {heights}"
        )
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            f"armed walk v15 {label} baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )


def render_walk_directional_weapon_v15(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_walk_directional_weapon_profile_v15(config.character_id)
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    down_scale = calibrations["down"].scale
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for grip in profile.grips:
            for direction in profile.directions:
                animation_id = _action_id(grip, direction.direction)
                armed_action = factory.bpy.data.actions.get(
                    f"{config.character_id}_{animation_id}"
                )
                source_action = factory.bpy.data.actions.get(
                    f"{config.character_id}_{direction.source_action_id}"
                )
                if armed_action is None or armed_action.get("profile_revision") != "v15":
                    raise RuntimeError(
                        f"armed walk v15 action is missing: {animation_id}"
                    )
                if source_action is None:
                    raise RuntimeError(
                        f"armed walk v15 source action is missing: "
                        f"{direction.source_action_id}"
                    )

                weapon_adapter._set_v12_weapon(
                    grip.weapon_cycle_id,
                    direction.direction,
                )
                context.rig.rotation_euler[2] = math.radians(
                    config.directions[direction.direction]
                )

                for frame_number in profile.frame_order:
                    _assert_lower_body_matches_source(
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
                        fixed_scale=down_scale,
                        fixed_center_x=(
                            calibrations[direction.direction].source_center_x
                        ),
                    )
                    artifacts.append(artifact)
                    _assert_boundary_contract(
                        artifact,
                        grip_id=grip.grip_id,
                        direction=direction.direction,
                    )

                _assert_cycle_dimensions(
                    _find_armed_frames(
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
            f"armed walk v15 requires 48 frames, got {rendered_count}"
        )
    return artifacts


def _write_walk_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_walk_directional_weapon_profile_v15(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    rows = len(profile.grips) * len(profile.directions)
    width = tile_width * len(profile.frame_order)
    height = tile_height * rows
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    row_index = 0
    for grip in profile.grips:
        for direction in profile.directions:
            animation_id = _action_id(grip, direction.direction)
            destination_y = (rows - 1 - row_index) * tile_height
            frames = _find_armed_frames(
                artifacts,
                animation_id=animation_id,
                direction=direction.direction,
            )
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
                        destination_y,
                    )
                finally:
                    factory.bpy.data.images.remove(image)
            row_index += 1

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_walk_directional_weapon_v15",
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


def _write_contact_sheet_v15(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_walk_sheet(
        config,
        artifacts,
        output_path.parent / COMPARISON_SHEET_NAME,
    )
    return result


def _write_manifest_v15(
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
    profile = load_walk_directional_weapon_profile_v15(
        context.config.character_id
    )
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("armed walk v15 comparison sheet is missing")

    rendered_grips: list[dict[str, object]] = []
    for grip in profile.grips:
        directions: list[dict[str, object]] = []
        for direction in profile.directions:
            animation_id = _action_id(grip, direction.direction)
            frames = _find_armed_frames(
                artifacts,
                animation_id=animation_id,
                direction=direction.direction,
            )
            directions.append(
                {
                    "direction": direction.direction,
                    "source_action_id": direction.source_action_id,
                    "source_profile_revision": direction.source_profile_revision,
                    "source_animation_revision": direction.source_animation_revision,
                    "animation_id": animation_id,
                    "frames": [
                        {
                            "frame": item.frame_number,
                            "width": item.sprite_width,
                            "height": item.sprite_height,
                            "baseline_y": item.baseline_y,
                        }
                        for item in frames
                    ],
                }
            )
        rendered_grips.append(
            {
                "grip_id": grip.grip_id,
                "display_name": grip.display_name,
                "stance_variant_id": grip.stance_variant_id,
                "stance_source_revision": grip.stance_source_revision,
                "weapon_cycle_id": grip.weapon_cycle_id,
                "fps": profile.fps,
                "loop": profile.loop,
                "directions": directions,
            }
        )

    payload["walk_directional_weapon_v15"] = {
        "profile_revision": profile.revision,
        "animation_revision": profile.animation_revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "sheet_layout": {
            "columns": [f"f{frame:02d}" for frame in profile.frame_order],
            "rows": [
                f"{grip.grip_id}_{direction.direction}"
                for grip in profile.grips
                for direction in profile.directions
            ],
        },
        "total_rendered_frames": 48,
        "static_weapon_source_revision": profile.static_weapon_source_revision,
        "combat_idle_source_revision": profile.combat_idle_source_revision,
        "grips": rendered_grips,
        "locked_contract": {
            "approved_walk_lower_body_channels_preserved": True,
            "onehand_weapon_arm_stabilized": True,
            "onehand_free_arm_restrained": True,
            "twohand_guard_remains_symmetric": True,
            "weapon_directions_reuse_artist_approved_v12": True,
            "baseline_y_91_preserved": True,
            "appearance_v03_unchanged": True,
            "head_v22_proxy_v25_unchanged": True,
            "weapon_geometry_rebuilt": False,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
        },
        "status": "armed_directional_walk_cycles_require_manual_animation_review",
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "armed_walk_active_stage": "walk_directional_weapon_v15",
            "armed_walk_frame_count": 48,
            "armed_walk_grips": "onehand_ready,twohand_center_high",
            "armed_walk_directions": "down,left,right,up",
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
        create_walk_directional_weapon_actions_v15
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_walk_directional_weapon_v15
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_v15
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v15
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
