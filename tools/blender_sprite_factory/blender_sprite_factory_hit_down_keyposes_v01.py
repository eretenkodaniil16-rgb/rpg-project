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
from hit_down_twohand_cycle_profile_v01 import (
    load_hit_down_twohand_cycle_profile_v01,
)


ONEHAND_PROFILE_PATH = SCRIPT_DIR / "hit_down_cycle_profile_v01.py"
TWOHAND_PROFILE_PATH = SCRIPT_DIR / "hit_down_twohand_cycle_profile_v01.py"
KEYPOSE_PROFILE_PATH = SCRIPT_DIR / "hit_down_keyposes_profile_v01.py"
BUILDER_PATH = SCRIPT_DIR / "hit_down_keyposes_builder_v01.py"
CONTACT_SHEET_NAME = "human_warrior_m01_hit_01_down_grips_v01.png"
MAX_ALLOWED_LEFT_EDGE_PIXELS = 12
EXPECTED_FRAME_NUMBERS = (1, 2, 3, 4, 5, 6)
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _profiles(character_id: str) -> tuple[object, ...]:
    return (
        load_hit_down_cycle_profile_v01(character_id),
        load_hit_down_twohand_cycle_profile_v01(character_id),
    )


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


def _assert_boundary_contract(
    artifact: factory.FrameArtifact,
    *,
    stance_variant_id: str,
) -> None:
    label = f"{stance_variant_id}/down/f{artifact.frame_number:02d}"
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
            f"hit down cycle v01 {label} exceeds approved left-edge budget: "
            f"{counts['left']}"
        )


def _assert_frame_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    stance_variant_id: str,
) -> None:
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            f"hit down cycle v01 {stance_variant_id} baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )
    for item in frames:
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"hit down cycle v01 {stance_variant_id} produced empty "
                f"f{item.frame_number:02d}"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                f"hit down cycle v01 {stance_variant_id} exceeds 96x96 canvas: "
                f"f{item.frame_number:02d}={item.sprite_width}x{item.sprite_height}"
            )
        _assert_boundary_contract(
            item,
            stance_variant_id=stance_variant_id,
        )


def render_hit_down_cycle_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profiles = _profiles(config.character_id)
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
        for profile in profiles:
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{profile.animation_id}"
            )
            if action is None or action.get("profile_revision") != profile.revision:
                raise RuntimeError(
                    f"hit down cycle v01 action is missing: {profile.animation_id}"
                )
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

            frames = _find_frames(
                artifacts,
                animation_id=profile.animation_id,
            )
            _assert_frame_contract(
                frames,
                stance_variant_id=profile.stance_variant_id,
            )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    expected_count = len(profiles) * len(EXPECTED_FRAME_NUMBERS)
    if len(artifacts) != expected_count:
        raise RuntimeError(
            f"hit down cycle v01 requires {expected_count} rendered frames, "
            f"got {len(artifacts)}"
        )
    return artifacts


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profiles = _profiles(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(EXPECTED_FRAME_NUMBERS)
    height = tile_height * len(profiles)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, profile in enumerate(profiles):
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
                    row_index * tile_height,
                )
            finally:
                factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_hit_down_grips_v01",
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


def _profile_payload(
    context: factory.BuildContext,
    profile: object,
    artifacts: list[factory.FrameArtifact],
    profile_path: Path,
    named_sheet: Path,
) -> dict[str, object]:
    frames = _find_frames(artifacts, animation_id=profile.animation_id)
    is_onehand = profile.stance_variant_id == "onehand_ready"
    return {
        "profile_revision": profile.revision,
        "source_motion_revision": profile.source_keypose_revision,
        "animation_id": profile.animation_id,
        "direction": profile.direction,
        "incoming_direction": profile.incoming_direction,
        "fps": profile.fps,
        "duration_seconds": HIT_DOWN_CYCLE_DURATION_SECONDS,
        "loop": profile.loop,
        "stance_variant_id": profile.stance_variant_id,
        "stance_source_revision": profile.stance_source_revision,
        "weapon_cycle_id": profile.weapon_cycle_id,
        "profile_path": context.config.relative_to_repo(profile_path),
        "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
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
            "approved_keyposes_preserved_exactly": is_onehand,
            "approved_body_motion_preserved_exactly": True,
            "twohand_grip_preservation_adjustment": not is_onehand,
            "starts_on_impact_without_idle_delay": True,
            "ends_on_exact_approved_guard": True,
            "direction_down_only": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "baseline_y_91_required": True,
            "manual_cycle_review_required": True,
            "runtime_connected": False,
        },
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
    profiles = _profiles(context.config.character_id)
    profile_paths = (ONEHAND_PROFILE_PATH, TWOHAND_PROFILE_PATH)
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("hit down cycle v01 contact sheet is missing")

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": [
            profile.stance_variant_id for profile in profiles
        ],
        "columns_left_to_right": list(profiles[0].phase_order),
    }
    payload["hit_down_cycles_v01"] = {
        profile.stance_variant_id: _profile_payload(
            context,
            profile,
            artifacts,
            profile_path,
            named_sheet,
        )
        for profile, profile_path in zip(profiles, profile_paths)
    }
    payload["hit_down_cycles_v01_shared"] = {
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
        "grip_count": len(profiles),
        "frames_per_grip": len(EXPECTED_FRAME_NUMBERS),
        "total_rendered_frames": len(artifacts),
        "base_manifest_writer_restored": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "hit_01_current_stage": "down_grips_cycle_v01",
            "hit_01_grip_count": len(profiles),
            "hit_01_frame_count_per_grip": len(EXPECTED_FRAME_NUMBERS),
            "hit_01_total_frame_count": len(artifacts),
            "hit_01_fps": profiles[0].fps,
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
