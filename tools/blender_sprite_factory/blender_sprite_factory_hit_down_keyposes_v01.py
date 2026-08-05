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
from factory_config import CONTACT_SHEET_BACKGROUND_HEX
from hit_down_cycle_profile_v01 import (
    HIT_DOWN_CYCLE_DURATION_SECONDS,
    load_hit_down_cycle_profile_v01,
)
from hit_down_keyposes_builder_v01 import create_hit_down_cycle_actions_v01


PROFILE_PATH = SCRIPT_DIR / "hit_down_cycle_profile_v01.py"
KEYPOSE_PROFILE_PATH = SCRIPT_DIR / "hit_down_keyposes_profile_v01.py"
BUILDER_PATH = SCRIPT_DIR / "hit_down_keyposes_builder_v01.py"
CONTACT_SHEET_NAME = "human_warrior_m01_hit_01_onehand_down_v01.png"
MAX_ALLOWED_LEFT_EDGE_PIXELS = 12
EXPECTED_FRAME_NUMBERS = (1, 2, 3, 4, 5, 6)
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _find_frames(
    artifacts: list[factory.FrameArtifact],
    *,
    animation_id: str,
) -> tuple[factory.FrameArtifact, ...]:
    matches = tuple(
        sorted(
            (
                item
                for item in artifacts
                if item.animation_id == animation_id and item.direction == "down"
            ),
            key=lambda item: item.frame_number,
        )
    )
    if tuple(item.frame_number for item in matches) != EXPECTED_FRAME_NUMBERS:
        raise RuntimeError(f"hit down cycle v01 missing frames: {animation_id}")
    return matches


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


def _assert_boundary_contract(artifact: factory.FrameArtifact) -> None:
    label = f"onehand/down/f{artifact.frame_number:02d}"
    counts = _edge_alpha_counts(artifact.output_path)
    forbidden = {
        edge: count
        for edge, count in counts.items()
        if edge != "left" and count > 0
    }
    if forbidden:
        raise RuntimeError(
            f"hit down cycle v01 {label} touches forbidden boundaries: {forbidden}"
        )
    if counts["left"] > MAX_ALLOWED_LEFT_EDGE_PIXELS:
        raise RuntimeError(
            f"hit down cycle v01 {label} exceeds approved onehand left-edge budget: "
            f"{counts['left']}"
        )


def _assert_frame_contract(
    frames: tuple[factory.FrameArtifact, ...],
) -> None:
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            "hit down cycle v01 baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )
    for item in frames:
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"hit down cycle v01 produced empty f{item.frame_number:02d}"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                "hit down cycle v01 exceeds 96x96 canvas: "
                f"f{item.frame_number:02d}={item.sprite_width}x{item.sprite_height}"
            )
        _assert_boundary_contract(item)


def render_hit_down_cycle_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_hit_down_cycle_profile_v01(config.character_id)
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    raw_dir.mkdir(exist_ok=True)
    frame_dir.mkdir(exist_ok=True)
    artifacts: list[factory.FrameArtifact] = []
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    weapon_adapter._set_v12_weapon(None, None)
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    down_calibration = calibrations["down"]

    try:
        action = factory.bpy.data.actions.get(
            f"{config.character_id}_{profile.animation_id}"
        )
        if action is None or action.get("profile_revision") != profile.revision:
            raise RuntimeError("hit down cycle v01 action is missing")
        factory._assign_action(context.rig, action)
        weapon_adapter._set_v12_weapon(profile.weapon_cycle_id, "down")
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])

        for frame_number in profile.frame_order:
            artifact, _ = factory._render_frame(
                context,
                animation_id=profile.animation_id,
                direction="down",
                frame_number=frame_number,
                raw_dir=raw_dir,
                frame_dir=frame_dir,
                output_name=(
                    f"{config.character_id}_{profile.animation_id}_"
                    f"f{frame_number:02d}_proxy_{revision}.png"
                ),
                fixed_scale=down_calibration.scale,
                fixed_center_x=down_calibration.source_center_x,
            )
            artifacts.append(artifact)

        frames = _find_frames(artifacts, animation_id=profile.animation_id)
        _assert_frame_contract(frames)
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    if len(artifacts) != 6:
        raise RuntimeError(
            f"hit down cycle v01 requires 6 rendered frames, got {len(artifacts)}"
        )
    return artifacts


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_hit_down_cycle_profile_v01(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(profile.frame_order)
    height = tile_height
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    frames = _find_frames(artifacts, animation_id=profile.animation_id)
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
                0,
            )
        finally:
            factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_hit_down_cycle_v01",
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
    result = _write_cycle_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_cycle_sheet(config, artifacts, named_path)
    return result


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
    profile = load_hit_down_cycle_profile_v01(context.config.character_id)
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("hit down cycle v01 contact sheet is missing")
    frames = _find_frames(artifacts, animation_id=profile.animation_id)

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": ["onehand_ready"],
        "columns_left_to_right": list(profile.phase_order),
    }
    payload["hit_down_cycle_v01"] = {
        "profile_revision": profile.revision,
        "source_keypose_revision": profile.source_keypose_revision,
        "animation_id": profile.animation_id,
        "direction": profile.direction,
        "incoming_direction": profile.incoming_direction,
        "fps": profile.fps,
        "duration_seconds": HIT_DOWN_CYCLE_DURATION_SECONDS,
        "loop": profile.loop,
        "stance_variant_id": profile.stance_variant_id,
        "stance_source_revision": profile.stance_source_revision,
        "weapon_cycle_id": profile.weapon_cycle_id,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "source_keypose_profile_path": context.config.relative_to_repo(
            KEYPOSE_PROFILE_PATH
        ),
        "source_keypose_profile_sha256": hashlib.sha256(
            KEYPOSE_PROFILE_PATH.read_bytes()
        ).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "total_rendered_frames": len(frames),
        "appearance_revision": profile.appearance_revision,
        "head_revision": profile.head_revision,
        "proxy_revision": profile.proxy_revision,
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
        "locked_contract": {
            "approved_keyposes_preserved_exactly": True,
            "starts_on_impact_without_idle_delay": True,
            "ends_on_exact_approved_guard": True,
            "direction_down_only": True,
            "shared_reaction_motion": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "baseline_y_91_required": True,
            "manual_cycle_review_required": True,
            "runtime_connected": False,
            "base_manifest_writer_restored": True,
        },
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "hit_01_current_stage": "down_cycle_v01",
            "hit_01_frame_count": len(frames),
            "hit_01_fps": profile.fps,
            "hit_01_duration_seconds": HIT_DOWN_CYCLE_DURATION_SECONDS,
            "hit_01_manual_cycle_review_required": True,
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
    base_adapter.render_pilot_combat_idle_down_v01 = render_hit_down_cycle_v01
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v01
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v01
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
