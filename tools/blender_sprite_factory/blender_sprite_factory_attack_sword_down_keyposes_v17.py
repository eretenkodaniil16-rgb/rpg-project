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
from attack_sword_down_keyposes_builder_v17 import (
    create_attack_sword_down_keypose_actions_v17,
)
from attack_sword_down_keyposes_profile_v17 import (
    AttackSwordDownGripV17,
    load_attack_sword_down_keyposes_profile_v17,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


PROFILE_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_profile_v17.py"
BUILDER_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_builder_v17.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v17.png"
MAX_ALLOWED_GUARD_LEFT_EDGE_PIXELS = 12


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
    if tuple(item.frame_number for item in matches) != (1, 2, 3, 4, 5):
        raise RuntimeError(f"attack sword down v17 missing frames: {animation_id}")
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
    grip_id: str,
) -> None:
    label = f"{grip_id}/down/f{artifact.frame_number:02d}"
    counts = _edge_alpha_counts(artifact.output_path)
    if grip_id == "onehand_ready" and artifact.frame_number == 1:
        forbidden = {
            edge: count
            for edge, count in counts.items()
            if edge != "left" and count > 0
        }
        if forbidden:
            raise RuntimeError(
                f"attack sword down v17 {label} touches forbidden boundaries: {forbidden}"
            )
        if counts["left"] > MAX_ALLOWED_GUARD_LEFT_EDGE_PIXELS:
            raise RuntimeError(
                f"attack sword down v17 {label} exceeds approved guard left-edge budget: "
                f"{counts['left']}"
            )
        return
    touched = {edge: count for edge, count in counts.items() if count > 0}
    if touched:
        raise RuntimeError(
            f"attack sword down v17 {label} touches canvas boundary: {touched}"
        )


def _assert_frame_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    label: str,
) -> None:
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            f"attack sword down v17 {label} baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )
    for item in frames:
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"attack sword down v17 {label} produced an empty frame: "
                f"f{item.frame_number:02d}"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                f"attack sword down v17 {label} exceeds 96x96 canvas: "
                f"f{item.frame_number:02d}={item.sprite_width}x{item.sprite_height}"
            )


def render_attack_sword_down_keyposes_v17(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_attack_sword_down_keyposes_profile_v17(config.character_id)
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
        for grip in profile.grips:
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{grip.action_id}"
            )
            if action is None or action.get("profile_revision") != "v17":
                raise RuntimeError(
                    f"attack sword down v17 action is missing: {grip.action_id}"
                )
            weapon_adapter._set_v12_weapon(grip.weapon_cycle_id, "down")
            context.rig.rotation_euler[2] = math.radians(config.directions["down"])

            for frame_number in profile.frame_order:
                artifact, _ = factory._render_frame(
                    context,
                    animation_id=grip.action_id,
                    direction="down",
                    frame_number=frame_number,
                    raw_dir=raw_dir,
                    frame_dir=frame_dir,
                    output_name=(
                        f"{config.character_id}_{grip.action_id}_"
                        f"f{frame_number:02d}_proxy_{revision}.png"
                    ),
                    fixed_scale=down_calibration.scale,
                    fixed_center_x=down_calibration.source_center_x,
                )
                artifacts.append(artifact)
                _assert_boundary_contract(artifact, grip_id=grip.grip_id)

            _assert_frame_contract(
                _find_frames(artifacts, animation_id=grip.action_id),
                label=grip.grip_id,
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
        if item.animation_id.startswith("attack_sword_01_")
        and item.animation_id.endswith("_keyposes_v17")
    )
    if rendered_count != 10:
        raise RuntimeError(
            f"attack sword down v17 requires 10 rendered key poses, got {rendered_count}"
        )
    return artifacts


def _write_keypose_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_attack_sword_down_keyposes_profile_v17(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(profile.frame_order)
    height = tile_height * len(profile.grips)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, grip in enumerate(profile.grips):
        destination_y = (len(profile.grips) - 1 - row_index) * tile_height
        frames = _find_frames(artifacts, animation_id=grip.action_id)
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

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_attack_sword_down_keyposes_v17",
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


def _write_contact_sheet_v17(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = _write_keypose_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_keypose_sheet(config, artifacts, named_path)
    return result


def _write_manifest_v17(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = factory._write_run_manifest(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = load_attack_sword_down_keyposes_profile_v17(
        context.config.character_id
    )
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("attack sword down v17 contact sheet is missing")

    grip_payloads: list[dict[str, object]] = []
    for grip in profile.grips:
        frames = _find_frames(artifacts, animation_id=grip.action_id)
        grip_payloads.append(
            {
                "grip_id": grip.grip_id,
                "display_name": grip.display_name,
                "action_id": grip.action_id,
                "stance_variant_id": grip.stance_variant_id,
                "stance_source_revision": grip.stance_source_revision,
                "weapon_cycle_id": grip.weapon_cycle_id,
                "trajectory_id": grip.trajectory_id,
                "frames": [
                    {
                        "frame": item.frame_number,
                        "phase": grip.poses[index].phase,
                        "width": item.sprite_width,
                        "height": item.sprite_height,
                        "baseline_y": item.baseline_y,
                    }
                    for index, item in enumerate(frames)
                ],
            }
        )

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": [grip.grip_id for grip in profile.grips],
        "columns_left_to_right": list(profile.phase_order),
    }
    payload["attack_sword_down_keyposes_v17"] = {
        "profile_revision": profile.revision,
        "animation_id": profile.animation_id,
        "direction": profile.direction,
        "fps": profile.fps,
        "loop": profile.loop,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "total_rendered_frames": 10,
        "appearance_revision": profile.appearance_revision,
        "head_revision": profile.head_revision,
        "proxy_revision": profile.proxy_revision,
        "combat_idle_source_revision": profile.combat_idle_source_revision,
        "directional_weapon_source_revision": (
            profile.directional_weapon_source_revision
        ),
        "grips": grip_payloads,
        "locked_contract": {
            "guard_pose_exactly_preserves_approved_stance": True,
            "direction_down_only": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "baseline_y_91_required": True,
            "manual_keypose_review_required": True,
            "full_attack_cycle_not_yet_approved": True,
        },
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_keyposes_v17",
            "attack_sword_01_keypose_count": 10,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_attack_sword_down_keypose_actions_v17
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_attack_sword_down_keyposes_v17
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_v17
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v17
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
