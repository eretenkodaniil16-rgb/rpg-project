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
import blender_sprite_factory_combat_idle_down_weapon_variants_v08 as previous_adapter
from combat_idle_down_animation_builder_v01 import (
    COMBAT_WEAPON_OBJECT_NAMES,
    SHEATHED_HILT_OBJECT_NAMES,
)
from combat_idle_down_weapon_variants_builder_v05 import (
    ONE_HAND_LONG_OBJECT_NAMES,
    TWO_HAND_LONG_OBJECT_NAMES,
)
from combat_idle_down_weapon_variants_builder_v06 import (
    ONE_HAND_V06_OBJECT_NAMES,
    TWO_HAND_HIGH_V06_OBJECT_NAMES,
    TWO_HAND_LOW_V06_OBJECT_NAMES,
)
from combat_idle_down_weapon_variants_builder_v07 import (
    ONE_HAND_LOW_V07_OBJECT_NAMES,
    ONE_HAND_READY_V07_OBJECT_NAMES,
)
from combat_idle_down_weapon_variants_builder_v08 import (
    ONE_HAND_LOW_V08_OBJECT_NAMES,
    ONE_HAND_READY_V08_OBJECT_NAMES,
)
from combat_idle_down_weapon_variants_builder_v09 import (
    ONE_HAND_LOW_V09_OBJECT_NAMES,
    ONE_HAND_READY_V09_OBJECT_NAMES,
    create_weapon_stance_actions_v09,
)
from combat_idle_down_weapon_variants_profile_v06 import (
    BLADE_TIP_LENGTH,
    ONE_HAND_BLADE_LENGTH,
    ONE_HAND_GRIP_LENGTH,
    TWO_HAND_AWAY_Y,
    TWO_HAND_BLADE_LENGTH,
    TWO_HAND_CENTER_X_OFFSET,
    TWO_HAND_GRIP_LENGTH,
)
from combat_idle_down_weapon_variants_profile_v09 import (
    ONE_HAND_BEHIND_Y,
    ONE_HAND_DOWN_Z,
    ONE_HAND_SIDE_X,
    WeaponStanceProfileV05,
    load_weapon_stance_profile_v09,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_RENDER = previous_adapter.BASE_RENDER
BASE_CONTACT_SHEET = previous_adapter.BASE_CONTACT_SHEET
BASE_WRITE_MANIFEST = previous_adapter.BASE_WRITE_MANIFEST
PROFILE_PATH = SCRIPT_DIR / "combat_idle_down_weapon_variants_profile_v09.py"
BUILDER_PATH = SCRIPT_DIR / "combat_idle_down_weapon_variants_builder_v09.py"
COMPARISON_SHEET_NAME = "combat_idle_down_weapon_variants_v09.png"


def _require_objects(names: tuple[str, ...], label: str) -> None:
    missing = [name for name in names if factory.bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError(f"combat idle v09 is missing {label} objects: {missing}")


def _set_weapon_variant_v09(variant_id: str | None) -> None:
    groups = (
        ("baseline", COMBAT_WEAPON_OBJECT_NAMES),
        ("onehand_v05", ONE_HAND_LONG_OBJECT_NAMES),
        ("twohand_v05", TWO_HAND_LONG_OBJECT_NAMES),
        ("onehand_v06", ONE_HAND_V06_OBJECT_NAMES),
        ("onehand_low_v07", ONE_HAND_LOW_V07_OBJECT_NAMES),
        ("onehand_ready_v07", ONE_HAND_READY_V07_OBJECT_NAMES),
        ("onehand_low_v08", ONE_HAND_LOW_V08_OBJECT_NAMES),
        ("onehand_ready_v08", ONE_HAND_READY_V08_OBJECT_NAMES),
        ("onehand_low_v09", ONE_HAND_LOW_V09_OBJECT_NAMES),
        ("onehand_ready_v09", ONE_HAND_READY_V09_OBJECT_NAMES),
        ("twohand_center_low", TWO_HAND_LOW_V06_OBJECT_NAMES),
        ("twohand_center_high", TWO_HAND_HIGH_V06_OBJECT_NAMES),
    )
    selected = {
        "onehand_low": ONE_HAND_LOW_V09_OBJECT_NAMES,
        "onehand_ready": ONE_HAND_READY_V09_OBJECT_NAMES,
        "twohand_center_low": TWO_HAND_LOW_V06_OBJECT_NAMES,
        "twohand_center_high": TWO_HAND_HIGH_V06_OBJECT_NAMES,
        "baseline": COMBAT_WEAPON_OBJECT_NAMES,
    }.get(variant_id, ())

    enabled_names = set(selected)
    for label, names in groups:
        _require_objects(names, label)
        for name in names:
            obj = factory.bpy.data.objects[name]
            enabled = name in enabled_names
            obj.hide_render = not enabled
            obj.hide_viewport = not enabled

    drawn = variant_id is not None
    _require_objects(SHEATHED_HILT_OBJECT_NAMES, "sheathed hilt")
    for name in SHEATHED_HILT_OBJECT_NAMES:
        obj = factory.bpy.data.objects[name]
        obj.hide_render = drawn
        obj.hide_viewport = drawn


def render_weapon_stance_variants_v09(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_weapon_stance_profile_v09(config.character_id)
    calibration = calibration_adapter.calibration_adapter._calibrate_idle_down(
        context,
        run_dir,
    )
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for variant in profile.variants:
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{variant.animation_id}"
            )
            expected_revision = "v09" if variant.grip_mode == "one_handed" else "v06"
            if action is None or action.get("profile_revision") != expected_revision:
                raise RuntimeError(
                    f"combat idle v09 cannot find {expected_revision} action "
                    f"{variant.animation_id}"
                )
            factory._assign_action(context.rig, action)
            context.rig.rotation_euler[2] = math.radians(config.directions["down"])
            factory.bpy.context.scene.frame_set(variant.pose.frame)
            _set_weapon_variant_v09(variant.variant_id)
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
        _set_weapon_variant_v09(None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    return artifacts


def _comparison_paths(
    artifacts: list[factory.FrameArtifact],
) -> tuple[Path, ...]:
    animation_ids = (
        "combat_idle_onehand_low_v09",
        "combat_idle_onehand_ready_v09",
        "combat_idle_twohand_center_low_v06",
        "combat_idle_twohand_center_high_v06",
    )
    paths: list[Path] = []
    for animation_id in animation_ids:
        matches = [
            item.output_path for item in artifacts if item.animation_id == animation_id
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"combat idle v09 requires one {animation_id} frame, got {len(matches)}"
            )
        paths.append(matches[0])
    return tuple(paths)


def _write_variant_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    paths = _comparison_paths(artifacts)
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
        "human_warrior_m01_combat_idle_down_weapon_variants_v09",
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


def _write_contact_sheet_v09(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_variant_sheet(
        config,
        artifacts,
        output_path.parent / COMPARISON_SHEET_NAME,
    )
    return result


def _write_manifest_v09(
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
    profile = load_weapon_stance_profile_v09(context.config.character_id)
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("combat idle v09 comparison sheet is missing")

    rendered_variants: list[dict[str, object]] = []
    for variant in profile.variants:
        matches = [
            item for item in artifacts if item.animation_id == variant.animation_id
        ]
        if len(matches) != 1:
            raise RuntimeError(f"combat idle v09 artifact drifted: {variant.variant_id}")
        artifact = matches[0]
        rendered_variants.append(
            {
                "variant_id": variant.variant_id,
                "display_name": variant.display_name,
                "animation_id": variant.animation_id,
                "grip_mode": variant.grip_mode,
                "weapon_id": variant.weapon_id,
                "blade_tip": variant.blade_tip,
                "source_revision": (
                    "v09" if variant.grip_mode == "one_handed" else "v06"
                ),
                "rendered_frame": {
                    "width": artifact.sprite_width,
                    "height": artifact.sprite_height,
                    "baseline_y": artifact.baseline_y,
                },
            }
        )

    payload["combat_idle_down_weapon_variants_v09"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "rejected_one_hand_revision": {
            "revision": "v08",
            "reason": "blade_projected_across_lower_torso_instead_of_outward_side",
        },
        "one_hand_correction": {
            "source_body_pose_revision": "v06",
            "weapon_id": "sword_01_onehand_outward_back_v09",
            "blade_length": ONE_HAND_BLADE_LENGTH,
            "grip_length": ONE_HAND_GRIP_LENGTH,
            "tip_length": BLADE_TIP_LENGTH,
            "blade_tip": "down",
            "side_x": ONE_HAND_SIDE_X,
            "behind_y": ONE_HAND_BEHIND_Y,
            "down_z": ONE_HAND_DOWN_Z,
            "separate_pose_fitted_modules": True,
            "trajectory": "physical_right_outward_and_partly_behind",
        },
        "two_hand_locked_source": {
            "revision": "v06",
            "weapon_id": "sword_02_twohand_long_v06",
            "blade_length": TWO_HAND_BLADE_LENGTH,
            "grip_length": TWO_HAND_GRIP_LENGTH,
            "tip_length": BLADE_TIP_LENGTH,
            "center_x_offset": TWO_HAND_CENTER_X_OFFSET,
            "away_y": TWO_HAND_AWAY_Y,
            "geometry_rebuilt": False,
            "actions_rebuilt": False,
        },
        "variants": rendered_variants,
        "locked_contract": {
            "appearance_v03_unchanged": True,
            "approved_idle_and_walk_set_unchanged": True,
            "baseline_combat_idle_v01_unchanged": True,
            "one_hand_body_pose_v06_unchanged": True,
            "one_hand_free_arm_away_from_torso": True,
            "one_hand_blade_tip_down": True,
            "one_hand_blade_physical_right_outward_and_partly_behind": True,
            "two_hand_v06_preserved_exactly": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "root_translation_used": False,
        },
        "status": "technical_one_hand_revision_requires_manual_selection",
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "combat_idle_down_active_stage": "weapon_variants_v09",
            "combat_idle_down_one_hand_revision": "v09",
            "combat_idle_down_two_hand_revision": "v06",
            "combat_idle_down_manual_selection_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = create_weapon_stance_actions_v09
    base_adapter.render_pilot_combat_idle_down_v01 = render_weapon_stance_variants_v09
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v09
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v09
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
