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
import blender_sprite_factory_attack_sword_down_cycle_v20 as down_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass05 as down_pass05
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_combat_idle_directional_v11 as directional_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from attack_sword_directional_cycle_builder_v21 import (
    create_attack_sword_directional_cycle_actions_v21,
)
from attack_sword_directional_cycle_profile_v21 import (
    DIRECTIONAL_CYCLE_REVISION,
    DIRECTION_ORDER,
    GRIP_ORDER,
    TOTAL_RENDERED_FRAME_COUNT,
    load_attack_sword_directional_cycle_profile_v21,
)
from combat_idle_directional_weapon_builder_v12 import (
    ONE_HAND_V12_OBJECTS_BY_DIRECTION,
)
from combat_idle_down_weapon_variants_builder_v06 import (
    TWO_HAND_HIGH_V06_OBJECT_NAMES,
)
from combat_idle_down_weapon_variants_builder_v09 import (
    ONE_HAND_READY_V09_OBJECT_NAMES,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


PROFILE_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_profile_v21.py"
BUILDER_PATH = SCRIPT_DIR / "attack_sword_directional_cycle_builder_v21.py"
DOWN_SOURCE_PATH = (
    SCRIPT_DIR / "blender_sprite_factory_attack_sword_down_cycle_v20_pass05.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
CLEARANCE_FRAMES = (2, 3, 4)
MIN_HEAD_CLEARANCE_BY_GRIP = {
    "onehand_ready": 2.0,
    "twohand_center_high": 4.0,
}
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _action_frames(
    artifacts: list[factory.FrameArtifact],
    *,
    animation_id: str,
    direction: str,
) -> tuple[factory.FrameArtifact, ...]:
    frames = tuple(
        sorted(
            (
                artifact
                for artifact in artifacts
                if artifact.animation_id == animation_id
                and artifact.direction == direction
            ),
            key=lambda artifact: artifact.frame_number,
        )
    )
    if tuple(frame.frame_number for frame in frames) != tuple(range(1, 9)):
        raise RuntimeError(
            f"attack sword directional v21 missing frames: "
            f"{animation_id}/{direction}"
        )
    return frames


def _weapon_object_names(grip_id: str, direction: str) -> tuple[str, ...]:
    if grip_id == "twohand_center_high":
        return TWO_HAND_HIGH_V06_OBJECT_NAMES
    if grip_id != "onehand_ready":
        raise KeyError(f"unknown attack sword directional v21 grip: {grip_id}")
    if direction == "down":
        return ONE_HAND_READY_V09_OBJECT_NAMES
    try:
        return ONE_HAND_V12_OBJECTS_BY_DIRECTION[direction]
    except KeyError as exc:
        raise KeyError(
            f"unknown attack sword directional v21 direction: {direction}"
        ) from exc


def _visible_weapon_objects(
    grip_id: str,
    direction: str,
) -> tuple[object, ...]:
    objects: list[object] = []
    for object_name in _weapon_object_names(grip_id, direction):
        obj = factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(
                f"attack sword directional v21 weapon object is missing: "
                f"{object_name}"
            )
        if obj.hide_render:
            raise RuntimeError(
                f"attack sword directional v21 active weapon object is hidden: "
                f"{object_name}"
            )
        objects.append(obj)
    return tuple(objects)


def _assert_boundary_contract(
    artifact: factory.FrameArtifact,
    *,
    grip_id: str,
    direction: str,
) -> None:
    if direction == "down":
        down_adapter._assert_boundary_contract(artifact, grip_id=grip_id)
        return
    counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
    touched = {edge: count for edge, count in counts.items() if count > 0}
    if touched:
        raise RuntimeError(
            f"attack sword directional v21 {grip_id}/{direction}/"
            f"f{artifact.frame_number:02d} touches canvas boundary: {touched}"
        )


def _assert_frame_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    grip_id: str,
    direction: str,
) -> None:
    if {frame.baseline_y for frame in frames} != {91}:
        raise RuntimeError(
            f"attack sword directional v21 {grip_id}/{direction} baseline drifted"
        )
    for frame in frames:
        if frame.sprite_width <= 0 or frame.sprite_height <= 0:
            raise RuntimeError(
                f"attack sword directional v21 {grip_id}/{direction} "
                f"produced an empty f{frame.frame_number:02d}"
            )
        if frame.sprite_width > 96 or frame.sprite_height > 96:
            raise RuntimeError(
                f"attack sword directional v21 {grip_id}/{direction} exceeds "
                f"96x96 at f{frame.frame_number:02d}: "
                f"{frame.sprite_width}x{frame.sprite_height}"
            )


def _validate_directional_clearance(
    context: factory.BuildContext,
    *,
    action_id: str,
    grip_id: str,
    weapon_cycle_id: str,
    direction: str,
) -> dict[int, float]:
    if direction == "down":
        if grip_id != "twohand_center_high":
            return {}
        return down_adapter._validate_twohand_clearance(
            context,
            action_id=action_id,
            weapon_cycle_id=weapon_cycle_id,
        )

    config = context.config
    action = factory.bpy.data.actions.get(
        f"{config.character_id}_{action_id}"
    )
    if action is None:
        raise RuntimeError(
            f"attack sword directional v21 clearance action is missing: "
            f"{action_id}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    clearances: dict[int, float] = {}
    minimum = MIN_HEAD_CLEARANCE_BY_GRIP[grip_id]
    try:
        weapon_adapter._set_v12_weapon(weapon_cycle_id, direction)
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[direction]
        )
        for frame_number in CLEARANCE_FRAMES:
            factory.bpy.context.scene.frame_set(frame_number)
            factory.bpy.context.view_layer.update()
            clearance = export_adapter._weapon_head_clearance(
                _visible_weapon_objects(grip_id, direction)
            )
            clearances[frame_number] = clearance
            print(
                "ATTACK_SWORD_DIRECTIONAL_V21_HEAD_CLEARANCE="
                f"{grip_id}/{direction}/f{frame_number:02d}:"
                f"{clearance:.3f}px"
            )
            if clearance < minimum:
                raise RuntimeError(
                    f"attack sword directional v21 {grip_id}/{direction} "
                    f"enters the projected head zone at f{frame_number:02d}: "
                    f"{clearance:.3f}px, required={minimum:.3f}px"
                )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions["down"]
        )
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
    return clearances


def render_attack_sword_directional_cycle_v21(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_attack_sword_directional_cycle_profile_v21(
        config.character_id
    )
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    raw_dir.mkdir(exist_ok=True)
    frame_dir.mkdir(exist_ok=True)
    artifacts: list[factory.FrameArtifact] = []
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    calibrations = directional_adapter._direction_calibrations(
        context,
        run_dir,
    )
    clearance_payload: dict[str, dict[str, float]] = {}

    try:
        for action_spec in profile.actions:
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{action_spec.action_id}"
            )
            if action is None:
                raise RuntimeError(
                    f"attack sword directional v21 action is missing: "
                    f"{action_spec.action_id}"
                )
            expected_revision = (
                "v20"
                if action_spec.direction == "down"
                else DIRECTIONAL_CYCLE_REVISION
            )
            if action.get("profile_revision") != expected_revision:
                raise RuntimeError(
                    f"attack sword directional v21 action revision drifted: "
                    f"{action_spec.action_id}"
                )

            calibration = calibrations[action_spec.direction]
            factory._assign_action(context.rig, action)
            weapon_adapter._set_v12_weapon(
                action_spec.weapon_cycle_id,
                action_spec.direction,
            )
            context.rig.rotation_euler[2] = math.radians(
                config.directions[action_spec.direction]
            )

            for frame_number in profile.frame_order:
                artifact, _ = down_pass05._render_frame_v20_pass05(
                    context,
                    animation_id=action_spec.action_id,
                    direction=action_spec.direction,
                    frame_number=frame_number,
                    raw_dir=raw_dir,
                    frame_dir=frame_dir,
                    output_name=(
                        f"{config.character_id}_{action_spec.action_id}_"
                        f"f{frame_number:02d}_proxy_{revision}.png"
                    ),
                    fixed_scale=calibration.scale,
                    fixed_center_x=calibration.source_center_x,
                    use_clearance_planner=(
                        action_spec.direction == "down"
                        and action_spec.grip_id == "twohand_center_high"
                        and frame_number
                        in down_adapter.TWOHAND_PLANNED_CLEARANCE_FRAMES
                    ),
                )
                artifacts.append(artifact)
                _assert_boundary_contract(
                    artifact,
                    grip_id=action_spec.grip_id,
                    direction=action_spec.direction,
                )

            _assert_frame_contract(
                _action_frames(
                    artifacts,
                    animation_id=action_spec.action_id,
                    direction=action_spec.direction,
                ),
                grip_id=action_spec.grip_id,
                direction=action_spec.direction,
            )
            clearances = _validate_directional_clearance(
                context,
                action_id=action_spec.action_id,
                grip_id=action_spec.grip_id,
                weapon_cycle_id=action_spec.weapon_cycle_id,
                direction=action_spec.direction,
            )
            clearance_payload[
                f"{action_spec.grip_id}/{action_spec.direction}"
            ] = {
                f"f{frame_number:02d}": value
                for frame_number, value in sorted(clearances.items())
            }
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions["down"]
        )
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    if len(artifacts) != TOTAL_RENDERED_FRAME_COUNT:
        raise RuntimeError(
            f"attack sword directional v21 requires "
            f"{TOTAL_RENDERED_FRAME_COUNT} rendered frames, got {len(artifacts)}"
        )
    if any(float(value) <= 0.0 for value in context.rig.scale):
        raise RuntimeError(
            "attack sword directional v21 detected negative or zero rig scale"
        )
    scene = factory.bpy.context.scene
    scene["attack_sword_directional_cycle_v21_clearances"] = json.dumps(
        clearance_payload,
        sort_keys=True,
    )
    scene["attack_sword_directional_cycle_v21_rendered_frames"] = len(
        artifacts
    )
    scene["attack_sword_directional_cycle_v21_boundary_contract_passed"] = True
    scene["attack_sword_directional_cycle_v21_no_mirroring_passed"] = True
    return artifacts


def _write_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    action_specs: tuple[object, ...],
    output_path: Path,
    *,
    image_name: str,
) -> Path:
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * 8
    height = tile_height * len(action_specs)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, action_spec in enumerate(action_specs):
        destination_y = (
            len(action_specs) - 1 - row_index
        ) * tile_height
        frames = _action_frames(
            artifacts,
            animation_id=action_spec.action_id,
            direction=action_spec.direction,
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

    sheet = factory.bpy.data.images.new(
        image_name,
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


def _write_contact_sheet_v21(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_attack_sword_directional_cycle_profile_v21(
        config.character_id
    )
    result = _write_sheet(
        config,
        artifacts,
        profile.actions,
        output_path,
        image_name="human_warrior_m01_attack_sword_directional_cycle_v21",
    )
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_sheet(
            config,
            artifacts,
            profile.actions,
            named_path,
            image_name=(
                "human_warrior_m01_attack_sword_directional_cycle_v21_named"
            ),
        )
    for direction in DIRECTION_ORDER:
        direction_actions = tuple(
            action
            for action in profile.actions
            if action.direction == direction
        )
        _write_sheet(
            config,
            artifacts,
            direction_actions,
            output_path.parent
            / f"attack_sword_01_{direction}_cycle_v21.png",
            image_name=(
                f"human_warrior_m01_attack_sword_{direction}_cycle_v21"
            ),
        )
    return result


def _write_manifest_v21(
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
    profile = load_attack_sword_directional_cycle_profile_v21(
        context.config.character_id
    )
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError(
            "attack sword directional v21 contact sheet is missing"
        )
    scene = factory.bpy.context.scene
    clearances = json.loads(
        str(scene["attack_sword_directional_cycle_v21_clearances"])
    )

    action_payloads: list[dict[str, object]] = []
    for action_spec in profile.actions:
        frames = _action_frames(
            artifacts,
            animation_id=action_spec.action_id,
            direction=action_spec.direction,
        )
        action_payloads.append(
            {
                "direction": action_spec.direction,
                "grip_id": action_spec.grip_id,
                "action_id": action_spec.action_id,
                "source_action_id": action_spec.source_action_id,
                "weapon_cycle_id": action_spec.weapon_cycle_id,
                "trajectory_id": action_spec.trajectory_id,
                "frames": [
                    {
                        "frame": frame.frame_number,
                        "phase": profile.phase_order[index],
                        "width": frame.sprite_width,
                        "height": frame.sprite_height,
                        "baseline_y": frame.baseline_y,
                    }
                    for index, frame in enumerate(frames)
                ],
            }
        )

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "combined_sheet": context.config.relative_to_repo(named_sheet),
        "rows_top_to_bottom": [
            f"{action.direction}/{action.grip_id}"
            for action in profile.actions
        ],
        "columns_left_to_right": list(profile.phase_order),
        "direction_sheets": {
            direction: context.config.relative_to_repo(
                run_dir / f"attack_sword_01_{direction}_cycle_v21.png"
            )
            for direction in DIRECTION_ORDER
        },
    }
    payload["attack_sword_directional_cycle_v21"] = {
        "profile_revision": profile.revision,
        "animation_family": profile.animation_family,
        "directions": list(profile.directions),
        "fps": profile.fps,
        "loop": profile.loop,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "down_source_path": context.config.relative_to_repo(DOWN_SOURCE_PATH),
        "down_source_sha256": hashlib.sha256(
            DOWN_SOURCE_PATH.read_bytes()
        ).hexdigest(),
        "source_keypose_revision": profile.source_keypose_revision,
        "total_actions": len(profile.actions),
        "total_rendered_frames": len(artifacts),
        "head_clearances": clearances,
        "actions": action_payloads,
        "locked_contract": {
            "approved_down_v20_pixels_preserved": True,
            "shared_local_attack_motion": True,
            "real_directional_rig_rotation_used": True,
            "directional_weapon_modules_v12_used": True,
            "physical_equipment_sides_preserved": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "weapon_geometry_deformed": False,
            "materials_changed": False,
            "baseline_y_91_required": True,
            "manual_directional_review_required": True,
            "runtime_connected": False,
        },
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "directional_full_cycle_v21",
            "attack_sword_01_directions": list(DIRECTION_ORDER),
            "attack_sword_01_grips": list(GRIP_ORDER),
            "attack_sword_01_frame_count_per_action": 8,
            "attack_sword_01_total_actions": len(profile.actions),
            "attack_sword_01_total_rendered_frames": len(artifacts),
            "attack_sword_01_manual_review_required": True,
            "attack_sword_01_runtime_connected": False,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_attack_sword_directional_cycle_actions_v21
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_attack_sword_directional_cycle_v21
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_v21
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v21
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
