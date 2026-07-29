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
import blender_sprite_factory_walk_right_v01 as previous_adapter
from factory_config import CONTACT_SHEET_BACKGROUND_HEX
from walk_up_animation_builder_v01 import create_walk_up_actions_v01
from walk_up_profile_v01 import WalkUpProfileV01, load_walk_up_profile_v01


BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_walk_right_v01
WALK_UP_PROFILE_PATH = SCRIPT_DIR / "walk_up_profile_v01.py"
WALK_UP_BUILDER_PATH = SCRIPT_DIR / "walk_up_animation_builder_v01.py"


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


def _pelvis_height_range(profile: WalkUpProfileV01) -> float:
    values = [pose.pelvis_z for pose in profile.poses]
    return max(values) - min(values)


def _maximum_loop_wrap(profile: WalkUpProfileV01) -> float:
    first = profile.poses[0].numeric_channels()
    last = profile.poses[-1].numeric_channels()
    return max(abs(end - start) for start, end in zip(first, last))


def render_pilot_walk_up_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_walk_up_profile_v01(config.character_id)
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

    if down_calibration is None:
        raise RuntimeError("walk_up v01 could not calibrate idle_down")
    for direction in ("left", "right", "up"):
        if direction not in direction_calibrations:
            raise RuntimeError(f"walk_up v01 could not calibrate idle_{direction}")

    animation_specs = (
        ("walk_down", "down", config.animations["walk_down"]["frames"]),
        ("walk_left", "left", range(1, 7)),
        ("walk_right", "right", range(1, 7)),
        (profile.animation_id, profile.direction, (pose.frame for pose in profile.poses)),
    )
    for animation_id, direction, frame_numbers in animation_specs:
        action = factory.bpy.data.actions.get(f"{config.character_id}_{animation_id}")
        if action is None:
            raise RuntimeError(f"walk_up v01 render cannot find action {animation_id}")
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

    return artifacts


def _write_contact_sheet_walk_up_v01(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    columns = 6
    rows = 6
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
        raise RuntimeError(f"walk_up contact sheet is missing idle directions: {missing_idle}")

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
                f"walk_up contact sheet requires six {animation_id} frames, got {len(paths)}"
            )
        return paths

    rows_data = (
        proxy_idle_paths,
        approved_idle_paths,
        animation_paths("walk_down"),
        animation_paths("walk_left"),
        animation_paths("walk_right"),
        animation_paths("walk_up"),
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
        "human_warrior_m01_walk_up_v01_contact_sheet",
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


def _write_run_manifest_walk_up_v01(
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
    profile = load_walk_up_profile_v01(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    action = factory.bpy.data.actions.get(f"{context.config.character_id}_walk_up")
    if action is None:
        raise RuntimeError("walk_up v01 manifest cannot find the generated action")
    if action.get("animation_revision") != profile.animation_revision:
        raise RuntimeError("walk_up v01 action revision drifted")
    if action.get("direction") != "up" or bool(action.get("mirroring_used")):
        raise RuntimeError("walk_up v01 must use real rear rotation without mirroring")
    if not bool(action.get("rear_view")):
        raise RuntimeError("walk_up v01 rear-view contract drifted")
    if action.get("screen_left_physical_side") != "left":
        raise RuntimeError("walk_up v01 physical side mapping drifted")

    up_artifacts = sorted(
        (item for item in artifacts if item.animation_id == "walk_up"),
        key=lambda item: item.frame_number,
    )
    if [item.frame_number for item in up_artifacts] != [1, 2, 3, 4, 5, 6]:
        raise RuntimeError("walk_up v01 manifest requires all six rendered frames")
    if any(item.direction != "up" for item in up_artifacts):
        raise RuntimeError("walk_up v01 rendered an incorrect direction")
    if any(
        item.baseline_y != context.config.technical.baseline_y for item in up_artifacts
    ):
        raise RuntimeError("walk_up v01 baseline drifted")

    payload["contact_sheet_review"]["rows_top_to_bottom"] = [
        "proxy_idle",
        "approved_idle_reference",
        "proxy_walk_down",
        "proxy_walk_left",
        "proxy_walk_right",
        "proxy_walk_up",
    ]
    payload.setdefault("walk_right_candidate_v01", {})
    payload["walk_right_candidate_v01"]["artist_approved"] = True
    payload["walk_right_candidate_v01"]["status"] = "artist_approved_walk_right_v01"
    payload["walk_up_candidate_v01"] = {
        "profile_path": context.config.relative_to_repo(WALK_UP_PROFILE_PATH),
        "profile_sha256": hashlib.sha256(WALK_UP_PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(WALK_UP_BUILDER_PATH),
        "builder_sha256": hashlib.sha256(WALK_UP_BUILDER_PATH.read_bytes()).hexdigest(),
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
            for item in up_artifacts
        ],
        "physical_view_contract": {
            "rear_view": True,
            "screen_left_physical_side": "left",
            "large_silver_pauldron_screen_left": True,
            "scabbard_screen_left": True,
            "small_dark_pauldron_screen_right": True,
            "pouch_screen_right": True,
            "face_visible": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "equipment_sides_changed": False,
        },
        "motion_readability": {
            "back_cloth_primary_motion_cue": True,
            "forearm_articulation_enabled": True,
            "root_translation_used": False,
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

    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "walk_right_artist_approved": True,
            "walk_right_approved_revision": "v01",
            "walk_up_revision": profile.animation_revision,
            "walk_up_profile_revision": profile.revision,
            "walk_up_direction": profile.direction,
            "walk_up_direction_rotation_degrees": context.config.directions[
                profile.direction
            ],
            "walk_up_fps": profile.fps,
            "walk_up_frames": [item.frame for item in profile.poses],
            "walk_up_loop": profile.loop,
            "walk_up_real_rotation_without_mirroring": True,
            "approved_appearance_v03_locked": True,
            "idle_unchanged": True,
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["artist_approved"] = True
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_v03_with_approved_walk_down_v04_"
        "walk_left_v01_walk_right_v01_and_walk_up_v01_candidate"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter.create_walk_right_actions_v01 = create_walk_up_actions_v01
    previous_adapter._write_run_manifest_walk_right_v01 = _write_run_manifest_walk_up_v01
    previous_adapter.render_pilot_walk_right_v01 = render_pilot_walk_up_v01
    previous_adapter._write_contact_sheet_walk_right_v01 = _write_contact_sheet_walk_up_v01
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
