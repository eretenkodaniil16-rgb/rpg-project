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
import blender_sprite_factory_walk_down_v04 as previous_adapter
from factory_config import CONTACT_SHEET_BACKGROUND_HEX
from walk_left_animation_builder_v01 import create_walk_left_actions_v01
from walk_left_profile_v01 import WalkLeftProfileV01, load_walk_left_profile_v01


BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_walk_down_v04
WALK_LEFT_PROFILE_PATH = SCRIPT_DIR / "walk_left_profile_v01.py"
WALK_LEFT_BUILDER_PATH = SCRIPT_DIR / "walk_left_animation_builder_v01.py"


def _pose_payload(pose: object) -> dict[str, object]:
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
            "shin_left_x_degrees": pose.shin_left_x_degrees,
            "shin_right_x_degrees": pose.shin_right_x_degrees,
            "foot_left_x_degrees": pose.foot_left_x_degrees,
            "foot_right_x_degrees": pose.foot_right_x_degrees,
        },
        "arms": {
            "upper_arm_left_x_degrees": pose.upper_arm_left_x_degrees,
            "upper_arm_right_x_degrees": pose.upper_arm_right_x_degrees,
            "forearm_left_x_degrees": pose.forearm_left_x_degrees,
            "forearm_right_x_degrees": pose.forearm_right_x_degrees,
        },
        "cloth": {
            "left_x_degrees": pose.cloth_left_x_degrees,
            "center_x_degrees": pose.cloth_center_x_degrees,
            "right_x_degrees": pose.cloth_right_x_degrees,
        },
    }


def _pelvis_height_range(profile: WalkLeftProfileV01) -> float:
    values = [pose.pelvis_z for pose in profile.poses]
    return max(values) - min(values)


def _maximum_loop_wrap(profile: WalkLeftProfileV01) -> float:
    first = profile.poses[0].numeric_channels()
    last = profile.poses[-1].numeric_channels()
    return max(abs(end - start) for start, end in zip(first, last))


def render_pilot_walk_left_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_walk_left_profile_v01(config.character_id)
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    raw_dir.mkdir()
    frame_dir.mkdir()
    artifacts: list[factory.FrameArtifact] = []

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

    if down_calibration is None or "left" not in direction_calibrations:
        raise RuntimeError("walk_left v01 could not calibrate down and left idle directions")

    walk_down_action = factory.bpy.data.actions[f"{config.character_id}_walk_down"]
    factory._assign_action(context.rig, walk_down_action)
    context.rig.rotation_euler[2] = math.radians(config.directions["down"])
    for frame_number in config.animations["walk_down"]["frames"]:
        artifact, _ = factory._render_frame(
            context,
            animation_id="walk_down",
            direction="down",
            frame_number=int(frame_number),
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=(
                f"{config.character_id}_walk_down_f{int(frame_number):02d}"
                f"_proxy_{revision}.png"
            ),
            fixed_scale=down_calibration.scale,
            fixed_center_x=down_calibration.source_center_x,
        )
        artifacts.append(artifact)

    walk_left_action = factory.bpy.data.actions.get(f"{config.character_id}_walk_left")
    if walk_left_action is None:
        raise RuntimeError("walk_left v01 render cannot find the generated action")
    factory._assign_action(context.rig, walk_left_action)
    context.rig.rotation_euler[2] = math.radians(config.directions[profile.direction])
    left_calibration = direction_calibrations[profile.direction]
    for pose in profile.poses:
        artifact, _ = factory._render_frame(
            context,
            animation_id=profile.animation_id,
            direction=profile.direction,
            frame_number=pose.frame,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=(
                f"{config.character_id}_walk_left_f{pose.frame:02d}"
                f"_proxy_{revision}.png"
            ),
            fixed_scale=down_calibration.scale,
            fixed_center_x=left_calibration.source_center_x,
        )
        artifacts.append(artifact)

    return artifacts


def _write_contact_sheet_walk_left_v01(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    columns = 6
    rows = 4
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
        raise RuntimeError(f"walk_left contact sheet is missing idle directions: {missing_idle}")

    proxy_idle_paths = tuple(
        idle_by_direction[direction].output_path for direction in idle_directions
    )
    approved_idle_paths = tuple(
        config.idle_reference_root / f"{config.character_id}_idle_{direction}.png"
        for direction in idle_directions
    )

    def animation_paths(animation_id: str) -> tuple[Path, ...]:
        paths = tuple(
            item.output_path
            for item in sorted(
                (artifact for artifact in artifacts if artifact.animation_id == animation_id),
                key=lambda artifact: artifact.frame_number,
            )
        )
        if len(paths) != 6:
            raise RuntimeError(
                f"walk_left contact sheet requires six {animation_id} frames, got {len(paths)}"
            )
        return paths

    rows_data = (
        proxy_idle_paths,
        approved_idle_paths,
        animation_paths("walk_down"),
        animation_paths("walk_left"),
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
        "human_warrior_m01_walk_left_v01_contact_sheet",
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


def _write_run_manifest_walk_left_v01(
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
    profile = load_walk_left_profile_v01(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    action = factory.bpy.data.actions.get(f"{context.config.character_id}_walk_left")
    if action is None:
        raise RuntimeError("walk_left v01 manifest cannot find the generated action")
    if action.get("animation_revision") != profile.animation_revision:
        raise RuntimeError("walk_left v01 action revision drifted")
    if action.get("direction") != "left" or bool(action.get("mirroring_used")):
        raise RuntimeError("walk_left v01 must use the real left rotation without mirroring")
    if action.get("foreground_physical_side") != "left":
        raise RuntimeError("walk_left v01 foreground physical side drifted")

    left_artifacts = sorted(
        (item for item in artifacts if item.animation_id == "walk_left"),
        key=lambda item: item.frame_number,
    )
    if [item.frame_number for item in left_artifacts] != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("walk_left v01 manifest requires all six rendered frames")
    if any(item.direction != "left" for item in left_artifacts):
        raise RuntimeError("walk_left v01 rendered an incorrect direction")
    if any(item.baseline_y != context.config.technical.baseline_y for item in left_artifacts):
        raise RuntimeError("walk_left v01 baseline drifted")

    payload["contact_sheet_review"]["rows_top_to_bottom"] = [
        "proxy_idle",
        "approved_idle_reference",
        "proxy_walk_down",
        "proxy_walk_left",
    ]
    payload["walk_left_candidate_v01"] = {
        "profile_path": context.config.relative_to_repo(WALK_LEFT_PROFILE_PATH),
        "profile_sha256": hashlib.sha256(WALK_LEFT_PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(WALK_LEFT_BUILDER_PATH),
        "builder_sha256": hashlib.sha256(WALK_LEFT_BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "profile_revision": profile.revision,
        "animation_revision": profile.animation_revision,
        "direction": profile.direction,
        "direction_rotation_degrees": context.config.directions[profile.direction],
        "fps": profile.fps,
        "loop": profile.loop,
        "poses": [_pose_payload(item) for item in profile.poses],
        "pelvis_height_range": _pelvis_height_range(profile),
        "maximum_loop_wrap": _maximum_loop_wrap(profile),
        "rendered_frames": [
            {
                "frame": item.frame_number,
                "width": item.sprite_width,
                "height": item.sprite_height,
                "baseline_y": item.baseline_y,
            }
            for item in left_artifacts
        ],
        "physical_view_contract": {
            "foreground_side": "physical_left",
            "large_silver_pauldron_foreground": True,
            "scabbard_foreground": True,
            "pouch_background": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "equipment_sides_changed": False,
        },
        "locked_appearance": {
            "head_revision": context.head.revision,
            "proxy_revision": context.proxy_revision,
            "appearance_revision": "v03",
            "geometry_changed": False,
            "materials_changed": False,
            "hair_changed": False,
            "scarf_changed": False,
        },
        "status": "technical_candidate_requires_manual_motion_review",
    }

    payload.setdefault("walk_down_candidate", {})
    payload["walk_down_candidate"]["artist_approved"] = True
    payload["walk_down_candidate"]["status"] = "artist_approved_walk_down_v04"
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "walk_down_artist_approved": True,
            "walk_down_approved_revision": "v04",
            "walk_left_revision": profile.animation_revision,
            "walk_left_profile_revision": profile.revision,
            "walk_left_direction": profile.direction,
            "walk_left_direction_rotation_degrees": context.config.directions[profile.direction],
            "walk_left_fps": profile.fps,
            "walk_left_frames": [item.frame for item in profile.poses],
            "walk_left_loop": profile.loop,
            "walk_left_real_rotation_without_mirroring": True,
            "approved_appearance_v03_locked": True,
            "idle_unchanged": True,
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["artist_approved"] = True
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_v03_with_approved_walk_down_v04_and_walk_left_v01_candidate"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter.create_walk_down_actions_v04 = create_walk_left_actions_v01
    previous_adapter._write_run_manifest_walk_down_v04 = _write_run_manifest_walk_left_v01
    factory.render_pilot = render_pilot_walk_left_v01
    factory._write_contact_sheet = _write_contact_sheet_walk_left_v01
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
