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
import blender_sprite_factory_walk_up_v01 as walk_up_v01_adapter
import blender_sprite_factory_walk_up_v02 as previous_adapter
from combat_idle_down_animation_builder_v01 import (
    COMBAT_WEAPON_OBJECT_NAMES,
    SHEATHED_HILT_OBJECT_NAMES,
    create_combat_idle_down_actions_v01,
)
from combat_idle_down_profile_v01 import (
    CombatIdleDownProfileV01,
    load_combat_idle_down_profile_v01,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_walk_up_v02
COMBAT_IDLE_PROFILE_PATH = SCRIPT_DIR / "combat_idle_down_profile_v01.py"
COMBAT_IDLE_BUILDER_PATH = SCRIPT_DIR / "combat_idle_down_animation_builder_v01.py"


def _set_combat_weapon_state(enabled: bool) -> None:
    missing_weapon = [
        name for name in COMBAT_WEAPON_OBJECT_NAMES if factory.bpy.data.objects.get(name) is None
    ]
    if missing_weapon:
        raise RuntimeError(
            f"combat_idle_down v01 is missing drawn weapon objects: {missing_weapon}"
        )
    missing_sheathed = [
        name for name in SHEATHED_HILT_OBJECT_NAMES if factory.bpy.data.objects.get(name) is None
    ]
    if missing_sheathed:
        raise RuntimeError(
            f"combat_idle_down v01 is missing sheathed hilt objects: {missing_sheathed}"
        )

    for name in COMBAT_WEAPON_OBJECT_NAMES:
        obj = factory.bpy.data.objects[name]
        obj.hide_render = not enabled
        obj.hide_viewport = not enabled
    for name in SHEATHED_HILT_OBJECT_NAMES:
        obj = factory.bpy.data.objects[name]
        obj.hide_render = enabled
        obj.hide_viewport = enabled


def render_pilot_combat_idle_down_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    combat_profile = load_combat_idle_down_profile_v01(config.character_id)
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    raw_dir.mkdir()
    frame_dir.mkdir()
    artifacts: list[factory.FrameArtifact] = []

    _set_combat_weapon_state(False)
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    direction_calibrations: dict[str, factory.FramingCalibration] = {}
    down_calibration: factory.FramingCalibration | None = None
    for direction in ("down", "left", "right", "up"):
        context.rig.rotation_euler[2] = math.radians(config.directions[direction])
        artifact, calibration = factory._render_frame(
            context,
            animation_id="idle",
            direction=direction,
            frame_number=1,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=f"{config.character_id}_idle_{direction}_proxy_{revision}.png",
            fixed_scale=(down_calibration.scale if down_calibration else None),
            fixed_center_x=None,
        )
        artifacts.append(artifact)
        direction_calibrations[direction] = calibration
        if direction == "down":
            down_calibration = calibration

    if down_calibration is None:
        raise RuntimeError("combat_idle_down v01 could not calibrate idle_down")
    for direction in ("left", "right", "up"):
        if direction not in direction_calibrations:
            raise RuntimeError(
                f"combat_idle_down v01 could not calibrate idle_{direction}"
            )

    animation_specs = (
        ("walk_down", "down", config.animations["walk_down"]["frames"]),
        ("walk_left", "left", range(1, 7)),
        ("walk_right", "right", range(1, 7)),
        ("walk_up", "up", range(1, 7)),
    )
    for animation_id, direction, frame_numbers in animation_specs:
        action = factory.bpy.data.actions.get(f"{config.character_id}_{animation_id}")
        if action is None:
            raise RuntimeError(
                f"combat_idle_down v01 render cannot find action {animation_id}"
            )
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(config.directions[direction])
        calibration = (
            down_calibration if direction == "down" else direction_calibrations[direction]
        )
        for frame_number in frame_numbers:
            frame = int(frame_number)
            artifact, _ = factory._render_frame(
                context,
                animation_id=animation_id,
                direction=direction,
                frame_number=frame,
                raw_dir=raw_dir,
                frame_dir=frame_dir,
                output_name=(
                    f"{config.character_id}_{animation_id}_f{frame:02d}"
                    f"_proxy_{revision}.png"
                ),
                fixed_scale=down_calibration.scale,
                fixed_center_x=calibration.source_center_x,
            )
            artifacts.append(artifact)

    combat_action = factory.bpy.data.actions.get(
        f"{config.character_id}_{combat_profile.animation_id}"
    )
    if combat_action is None:
        raise RuntimeError("combat_idle_down v01 render cannot find combat_idle action")
    try:
        factory._assign_action(context.rig, combat_action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[combat_profile.direction]
        )
        factory.bpy.context.scene.frame_set(combat_profile.pose.frame)
        _set_combat_weapon_state(True)
        factory.bpy.context.view_layer.update()
        artifact, _ = factory._render_frame(
            context,
            animation_id=combat_profile.animation_id,
            direction=combat_profile.direction,
            frame_number=combat_profile.pose.frame,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=(
                f"{config.character_id}_combat_idle_down_f01_proxy_{revision}.png"
            ),
            fixed_scale=down_calibration.scale,
            fixed_center_x=down_calibration.source_center_x,
        )
        artifacts.append(artifact)
    finally:
        _set_combat_weapon_state(False)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    return artifacts


def _write_contact_sheet_combat_idle_down_v01(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    columns = 6
    rows = 7
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = columns * tile_width
    height = rows * tile_height
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    idle_by_direction = {
        item.direction: item for item in artifacts if item.animation_id == "idle"
    }
    idle_directions = ("down", "left", "right", "up")
    missing_idle = [
        direction for direction in idle_directions if direction not in idle_by_direction
    ]
    if missing_idle:
        raise RuntimeError(
            f"combat_idle contact sheet is missing idle directions: {missing_idle}"
        )

    proxy_idle_paths = tuple(
        idle_by_direction[direction].output_path for direction in idle_directions
    )
    approved_idle_paths = tuple(
        config.idle_reference_root / f"{config.character_id}_idle_{direction}.png"
        for direction in idle_directions
    )

    def animation_paths(animation_id: str, expected_count: int = 6) -> tuple[Path, ...]:
        paths = tuple(
            item.output_path
            for item in sorted(
                (
                    artifact
                    for artifact in artifacts
                    if artifact.animation_id == animation_id
                ),
                key=lambda artifact: artifact.frame_number,
            )
        )
        if len(paths) != expected_count:
            raise RuntimeError(
                f"combat_idle contact sheet requires {expected_count} "
                f"{animation_id} frames, got {len(paths)}"
            )
        return paths

    rows_data = (
        proxy_idle_paths,
        approved_idle_paths,
        animation_paths("walk_down"),
        animation_paths("walk_left"),
        animation_paths("walk_right"),
        animation_paths("walk_up"),
        animation_paths("combat_idle", expected_count=1),
    )
    for row_index, row_paths in enumerate(rows_data):
        for column_index, image_path in enumerate(row_paths):
            image = factory.bpy.data.images.load(str(image_path), check_existing=False)
            try:
                tile_pixels = tuple(image.pixels[:])
                destination_row = rows - 1 - row_index
                factory._copy_tile(
                    pixels,
                    width,
                    tile_pixels,
                    tile_width,
                    tile_height,
                    column_index * tile_width,
                    destination_row * tile_height,
                )
            finally:
                factory.bpy.data.images.remove(image)

    contact_sheet = factory.bpy.data.images.new(
        "human_warrior_m01_combat_idle_down_v01_contact_sheet",
        width=width,
        height=height,
        alpha=True,
        float_buffer=False,
    )
    try:
        contact_sheet.pixels[:] = pixels
        contact_sheet.file_format = "PNG"
        contact_sheet.filepath_raw = str(output_path)
        contact_sheet.save()
    finally:
        factory.bpy.data.images.remove(contact_sheet)
    return output_path


def _pose_payload(profile: CombatIdleDownProfileV01) -> dict[str, object]:
    pose = profile.pose
    return {
        "frame": pose.frame,
        "phase": pose.phase,
        "pelvis": {
            "x": pose.pelvis_x,
            "z": pose.pelvis_z,
            "roll_z_degrees": pose.pelvis_roll_z_degrees,
        },
        "spine_pitch_x_degrees": pose.spine_pitch_x_degrees,
        "chest_yaw_z_degrees": pose.chest_yaw_z_degrees,
        "head_yaw_z_degrees": pose.head_yaw_z_degrees,
        "legs": {
            "thigh_left_x_degrees": pose.thigh_left_x_degrees,
            "thigh_right_x_degrees": pose.thigh_right_x_degrees,
            "thigh_left_z_degrees": pose.thigh_left_z_degrees,
            "thigh_right_z_degrees": pose.thigh_right_z_degrees,
            "shin_left_x_degrees": pose.shin_left_x_degrees,
            "shin_right_x_degrees": pose.shin_right_x_degrees,
            "foot_left_x_degrees": pose.foot_left_x_degrees,
            "foot_right_x_degrees": pose.foot_right_x_degrees,
        },
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
        "cloth": {
            "left_x_degrees": pose.cloth_left_x_degrees,
            "center_x_degrees": pose.cloth_center_x_degrees,
            "right_x_degrees": pose.cloth_right_x_degrees,
        },
    }


def _write_run_manifest_combat_idle_down_v01(
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
    profile = load_combat_idle_down_profile_v01(context.config.character_id)
    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_{profile.animation_id}"
    )
    if action is None:
        raise RuntimeError("combat_idle_down v01 manifest cannot find combat action")
    if action.get("pose_revision") != profile.pose_revision:
        raise RuntimeError("combat_idle_down v01 pose revision drifted")
    if action.get("weapon_hand") != "right" or bool(action.get("mirroring_used")):
        raise RuntimeError("combat_idle_down v01 weapon-hand contract drifted")

    combat_artifacts = [
        item for item in artifacts if item.animation_id == profile.animation_id
    ]
    if len(combat_artifacts) != 1:
        raise RuntimeError("combat_idle_down v01 manifest requires one rendered frame")
    combat_artifact = combat_artifacts[0]
    if (
        combat_artifact.direction != "down"
        or combat_artifact.frame_number != 1
        or combat_artifact.baseline_y != context.config.technical.baseline_y
    ):
        raise RuntimeError("combat_idle_down v01 rendered-frame contract drifted")

    payload["contact_sheet_review"]["rows_top_to_bottom"] = [
        "proxy_idle",
        "approved_idle_reference",
        "proxy_walk_down",
        "proxy_walk_left",
        "proxy_walk_right",
        "proxy_walk_up",
        "proxy_combat_idle_down",
    ]
    payload.setdefault("walk_up_candidate_v02", {})
    payload["walk_up_candidate_v02"]["artist_approved"] = True
    payload["walk_up_candidate_v02"]["status"] = "artist_approved_walk_up_v02"
    payload["combat_idle_down_candidate_v01"] = {
        "profile_path": context.config.relative_to_repo(COMBAT_IDLE_PROFILE_PATH),
        "profile_sha256": hashlib.sha256(
            COMBAT_IDLE_PROFILE_PATH.read_bytes()
        ).hexdigest(),
        "builder_path": context.config.relative_to_repo(COMBAT_IDLE_BUILDER_PATH),
        "builder_sha256": hashlib.sha256(
            COMBAT_IDLE_BUILDER_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "profile_revision": profile.revision,
        "pose_revision": profile.pose_revision,
        "animation_id": profile.animation_id,
        "direction": profile.direction,
        "direction_rotation_degrees": context.config.directions[profile.direction],
        "fps": profile.fps,
        "loop": profile.loop,
        "pose": _pose_payload(profile),
        "rendered_frame": {
            "frame": combat_artifact.frame_number,
            "width": combat_artifact.sprite_width,
            "height": combat_artifact.sprite_height,
            "baseline_y": combat_artifact.baseline_y,
        },
        "weapon_contract": {
            "weapon_id": profile.weapon_id,
            "drawn_weapon_parent_bone": "hand.R",
            "drawn_weapon_physical_hand": "right",
            "scabbard_remains_physical_left": True,
            "sheathed_grip_guard_hidden_only_for_combat_frame": True,
            "weapon_object_names": list(COMBAT_WEAPON_OBJECT_NAMES),
            "mirroring_used": False,
            "negative_scale_used": False,
        },
        "locked_appearance": {
            "head_revision": context.head.revision,
            "proxy_revision": context.proxy_revision,
            "appearance_revision": "v03",
            "character_geometry_changed": False,
            "character_materials_changed": False,
            "hair_changed": False,
            "scarf_changed": False,
            "combat_weapon_geometry_added": True,
        },
        "status": "technical_candidate_requires_manual_static_pose_review",
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "walk_up_artist_approved": True,
            "walk_up_approved_revision": "v02",
            "combat_idle_down_revision": profile.pose_revision,
            "combat_idle_down_direction": profile.direction,
            "combat_idle_down_static_pose_only": True,
            "combat_idle_down_frame": profile.pose.frame,
            "combat_idle_down_weapon_id": profile.weapon_id,
            "combat_idle_down_weapon_hand": profile.weapon_hand,
            "combat_idle_down_real_rotation_without_mirroring": True,
            "approved_appearance_v03_locked": True,
            "approved_walk_set_unchanged": True,
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_v03_with_complete_approved_walk_set_"
        "and_combat_idle_down_v01_candidate"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter.create_walk_up_actions_v02 = create_combat_idle_down_actions_v01
    previous_adapter._write_run_manifest_walk_up_v02 = (
        _write_run_manifest_combat_idle_down_v01
    )
    walk_up_v01_adapter.render_pilot_walk_up_v01 = (
        render_pilot_combat_idle_down_v01
    )
    walk_up_v01_adapter._write_contact_sheet_walk_up_v01 = (
        _write_contact_sheet_combat_idle_down_v01
    )
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
