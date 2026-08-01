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
import blender_sprite_factory_combat_idle_down_variants_v02 as rejected_adapter
from combat_idle_down_variants_builder_v03 import (
    create_combat_idle_down_variant_actions_v03,
)
from combat_idle_down_variants_profile_v02 import CombatIdleDownVariantV02
from combat_idle_down_variants_profile_v03 import (
    load_combat_idle_down_variants_profile_v03,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_RENDER = base_adapter.render_pilot_combat_idle_down_v01
BASE_CONTACT_SHEET = base_adapter._write_contact_sheet_combat_idle_down_v01
BASE_WRITE_MANIFEST = base_adapter._write_run_manifest_combat_idle_down_v01
PROFILE_PATH = SCRIPT_DIR / "combat_idle_down_variants_profile_v03.py"
BUILDER_PATH = SCRIPT_DIR / "combat_idle_down_variants_builder_v03.py"
COMPARISON_SHEET_NAME = "combat_idle_down_variants_v03.png"


def render_pilot_combat_idle_down_variants_v03(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_combat_idle_down_variants_profile_v03(config.character_id)
    calibration = rejected_adapter._calibrate_idle_down(context, run_dir)
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        base_adapter._set_combat_weapon_state(True)
        for variant in profile.variants:
            action_name = f"{config.character_id}_{variant.animation_id}"
            action = factory.bpy.data.actions.get(action_name)
            if action is None:
                raise RuntimeError(
                    f"combat_idle_down variants v03 cannot find action {action_name}"
                )
            factory._assign_action(context.rig, action)
            context.rig.rotation_euler[2] = math.radians(config.directions["down"])
            factory.bpy.context.scene.frame_set(variant.pose.frame)
            factory.bpy.context.view_layer.update()
            artifact, _ = factory._render_frame(
                context,
                animation_id=variant.animation_id,
                direction="down",
                frame_number=variant.pose.frame,
                raw_dir=raw_dir,
                frame_dir=frame_dir,
                output_name=(
                    f"{config.character_id}_{variant.animation_id}_down_f01_"
                    f"proxy_{revision}.png"
                ),
                fixed_scale=calibration.scale,
                fixed_center_x=calibration.source_center_x,
            )
            artifacts.append(artifact)
    finally:
        base_adapter._set_combat_weapon_state(False)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    return artifacts


def _candidate_paths(
    artifacts: list[factory.FrameArtifact],
) -> tuple[Path, ...]:
    animation_ids = (
        "combat_idle",
        "combat_idle_center_low_v03",
        "combat_idle_center_mid_v03",
        "combat_idle_center_vertical_v03",
    )
    paths: list[Path] = []
    for animation_id in animation_ids:
        matches = [
            item.output_path
            for item in artifacts
            if item.animation_id == animation_id
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"combat_idle_down variants v03 requires one {animation_id} frame, "
                f"got {len(matches)}"
            )
        paths.append(matches[0])
    return tuple(paths)


def _write_variant_comparison_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    paths = _candidate_paths(artifacts)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = len(paths) * tile_width
    height = tile_height
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]
    for index, image_path in enumerate(paths):
        image = factory.bpy.data.images.load(str(image_path), check_existing=False)
        try:
            factory._copy_tile(
                pixels,
                width,
                tuple(image.pixels[:]),
                tile_width,
                tile_height,
                index * tile_width,
                0,
            )
        finally:
            factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_combat_idle_down_variants_v03",
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


def _write_contact_sheet_combat_idle_down_variants_v03(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_variant_comparison_sheet(
        config,
        artifacts,
        output_path.parent / COMPARISON_SHEET_NAME,
    )
    return result


def _pose_payload(variant: CombatIdleDownVariantV02) -> dict[str, object]:
    pose = variant.pose
    return {
        "variant_id": variant.variant_id,
        "display_name": variant.display_name,
        "animation_id": variant.animation_id,
        "frame": pose.frame,
        "pelvis": {
            "x": pose.pelvis_x,
            "z": pose.pelvis_z,
            "roll_z_degrees": pose.pelvis_roll_z_degrees,
        },
        "chest_yaw_z_degrees": pose.chest_yaw_z_degrees,
        "arms": {
            "upper_arm_left_x_degrees": pose.upper_arm_left_x_degrees,
            "upper_arm_left_z_degrees": pose.upper_arm_left_z_degrees,
            "forearm_left_x_degrees": pose.forearm_left_x_degrees,
            "forearm_left_z_degrees": pose.forearm_left_z_degrees,
            "upper_arm_right_x_degrees": pose.upper_arm_right_x_degrees,
            "upper_arm_right_z_degrees": pose.upper_arm_right_z_degrees,
            "forearm_right_x_degrees": pose.forearm_right_x_degrees,
            "forearm_right_z_degrees": pose.forearm_right_z_degrees,
            "hand_right_x_degrees": pose.hand_right_x_degrees,
            "hand_right_z_degrees": pose.hand_right_z_degrees,
        },
    }


def _write_run_manifest_combat_idle_down_variants_v03(
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
    profile = load_combat_idle_down_variants_profile_v03(context.config.character_id)
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("combat_idle_down variants v03 comparison sheet is missing")

    rendered_variants: list[dict[str, object]] = []
    for variant in profile.variants:
        action = factory.bpy.data.actions.get(
            f"{context.config.character_id}_{variant.animation_id}"
        )
        if action is None or action.get("profile_revision") != "v03":
            raise RuntimeError(
                f"combat_idle_down variants v03 action drifted: {variant.variant_id}"
            )
        matches = [
            item for item in artifacts if item.animation_id == variant.animation_id
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"combat_idle_down variants v03 artifact drifted: {variant.variant_id}"
            )
        artifact = matches[0]
        rendered_variants.append(
            {
                **_pose_payload(variant),
                "rendered_frame": {
                    "width": artifact.sprite_width,
                    "height": artifact.sprite_height,
                    "baseline_y": artifact.baseline_y,
                },
            }
        )

    payload["combat_idle_down_variants_v03"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "direction": profile.direction,
        "weapon_id": profile.weapon_id,
        "weapon_hand": profile.weapon_hand,
        "baseline_candidate": "combat_idle_down v01",
        "rejected_revision": {
            "revision": "v02",
            "reason": "blade_moved_outward_instead_of_toward_center",
        },
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "variants": rendered_variants,
        "locked_contract": {
            "appearance_v03_unchanged": True,
            "approved_idle_and_walk_set_unchanged": True,
            "single_shared_weapon_module": True,
            "single_shared_scale_and_baseline": True,
            "left_arm_remains_more_open_than_v01": True,
            "right_hand_rotates_blade_toward_center": True,
            "scabbard_remains_physical_left": True,
            "mirroring_used": False,
            "negative_scale_used": False,
        },
        "status": "technical_variant_set_requires_manual_selection",
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "combat_idle_down_active_stage": "variants_v03",
            "combat_idle_down_variant_count": len(profile.variants),
            "combat_idle_down_manual_selection_required": True,
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_and_walk_set_with_centered_sword_"
        "combat_idle_down_variants_v03_pending_selection"
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_combat_idle_down_variant_actions_v03
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_pilot_combat_idle_down_variants_v03
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_combat_idle_down_variants_v03
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = (
        _write_run_manifest_combat_idle_down_variants_v03
    )
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
