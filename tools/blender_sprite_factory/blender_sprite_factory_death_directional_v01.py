from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

from mathutils import Matrix


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_combat_idle_directional_v11 as directional_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
import blender_sprite_factory_death_down_cycle_v01 as down_adapter
import blender_sprite_factory_death_down_keyposes_v01 as keypose_adapter
from death_directional_cycles_builder_v01 import (
    create_death_directional_cycle_actions_v01,
)
from death_directional_cycles_profile_v01 import (
    load_death_directional_cycles_profile_v01,
)
from death_down_cycle_profile_v01 import (
    CORPSE_HOLD_FRAME,
    DEATH_DOWN_CYCLE_FRAME_ORDER,
    load_death_down_cycle_profiles_v01,
)
from death_down_keyposes_builder_v01 import _GORE_UPPER_BODY_BONES
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


PROFILE_PATH = SCRIPT_DIR / "death_directional_cycles_profile_v01.py"
BUILDER_PATH = SCRIPT_DIR / "death_directional_cycles_builder_v01.py"
DOWN_ADAPTER_PATH = SCRIPT_DIR / "blender_sprite_factory_death_down_cycle_v01.py"
CONTACT_SHEET_NAME = "human_warrior_m01_death_directional_cycles_v01.png"
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest
MIN_MAJOR_COMPONENT_PIXELS = 120
MIN_SECONDARY_COMPONENT_RATIO = 0.20
DIRECTIONAL_PACKING_MARGIN_PIXELS = 1
DIRECTIONAL_SPLIT_LATERAL_FACTOR_BY_DIRECTION = {
    "left": 2.90,
    "right": 2.60,
    "up": 0.80,
}
DIRECTIONAL_SPLIT_SCREEN_UP_FACTOR_BY_DIRECTION = {
    "left": 5.00,
    "right": 5.00,
    "up": 4.50,
}
SPLIT_SCREEN_UP_REFERENCE_FRAME = 6
UP_SPLIT_TUMBLE_BY_FRAME = {
    6: {
        "degrees": 40.0,
        "screen_right_raw_pixels": 5.5,
        "screen_down_raw_pixels": 14.5,
    },
    7: {
        "degrees": 32.0,
        "screen_right_raw_pixels": 15.0,
        "screen_down_raw_pixels": 2.0,
    },
    8: {
        "degrees": 32.0,
        "screen_right_raw_pixels": 15.0,
        "screen_down_raw_pixels": 2.0,
    },
}
FAIL_FAST_RENDER_VARIANT_ORDER = (
    "death_03_base",
    "death_01_base",
    "death_02_base",
)
_LAST_DIRECTIONAL_FRAMING: dict[str, object] = {}
_LAST_DIRECTIONAL_SPLIT_OFFSETS: dict[str, dict[str, list[float]]] = {}
_LAST_DIRECTIONAL_SPLIT_TUMBLES: dict[
    str,
    dict[str, dict[str, float]],
] = {}


def _profiles(character_id: str) -> tuple[object, ...]:
    return load_death_down_cycle_profiles_v01(character_id)


def _find_frames(
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
    if tuple(item.frame_number for item in matches) != (
        DEATH_DOWN_CYCLE_FRAME_ORDER
    ):
        raise RuntimeError(
            "death directional v01 missing frames: "
            f"{animation_id}/{direction}"
        )
    return matches


def _rgba_sha256(path: Path) -> str:
    width, height, rows, _ = keypose_adapter._decode_rgba8_png(path)
    payload = width.to_bytes(4, "big") + height.to_bytes(4, "big")
    payload += b"".join(bytes(row) for row in rows)
    return hashlib.sha256(payload).hexdigest()


def _frame_rgba_hashes(
    artifacts: list[factory.FrameArtifact],
    profiles: tuple[object, ...],
    direction: str,
) -> dict[tuple[str, int], str]:
    return {
        (profile.animation_id, item.frame_number): _rgba_sha256(item.output_path)
        for profile in profiles
        for item in _find_frames(
            artifacts,
            animation_id=profile.animation_id,
            direction=direction,
        )
    }


def _assert_binary_rgba_canvas(path: Path, *, label: str) -> None:
    width, height, rows, _ = keypose_adapter._decode_rgba8_png(path)
    if (width, height) != (96, 96):
        raise RuntimeError(
            f"death directional v01 {label} canvas drifted: {width}x{height}"
        )
    alpha_values = {
        row[offset + 3]
        for row in rows
        for offset in range(0, len(row), 4)
    }
    if not alpha_values.issubset({0, 255}):
        raise RuntimeError(
            f"death directional v01 {label} alpha is not binary: "
            f"{sorted(alpha_values)}"
        )


def _assert_no_boundary_touch(
    artifact: factory.FrameArtifact,
    *,
    label: str,
) -> None:
    counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
    active = {edge: count for edge, count in counts.items() if count > 0}
    if active:
        raise RuntimeError(
            f"death directional v01 {label} touches boundaries: {active}"
        )


def _major_component_sizes(path: Path) -> tuple[int, ...]:
    return tuple(
        size
        for size in keypose_adapter._opaque_component_sizes(path)
        if size >= MIN_MAJOR_COMPONENT_PIXELS
    )


def _assert_split_components(
    artifact: factory.FrameArtifact,
    *,
    label: str,
) -> None:
    major = _major_component_sizes(artifact.output_path)
    if len(major) < 2 or major[1] < major[0] * MIN_SECONDARY_COMPONENT_RATIO:
        all_sizes = keypose_adapter._opaque_component_sizes(artifact.output_path)
        raise RuntimeError(
            "death directional v01 torso and legs are not visually separated: "
            f"{label}={all_sizes}"
        )


def _assert_direction_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    profile: object,
    direction: str,
) -> None:
    label = f"{profile.death_variant_id}/{direction}"
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            f"death directional v01 {label} baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )
    for item in frames:
        frame_label = f"{label}/f{item.frame_number:02d}"
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"death directional v01 {frame_label} is empty"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                f"death directional v01 {frame_label} exceeds 96x96: "
                f"{item.sprite_width}x{item.sprite_height}"
            )
        _assert_binary_rgba_canvas(item.output_path, label=frame_label)
        _assert_no_boundary_touch(item, label=frame_label)
        if (
            profile.gore_mode == "waist_torso_legs_separation"
            and profile.detachment_frame is not None
            and item.frame_number >= profile.detachment_frame
        ):
            _assert_split_components(item, label=frame_label)

    final_frame = next(item for item in frames if item.frame_number == 7)
    hold_frame = next(
        item for item in frames if item.frame_number == CORPSE_HOLD_FRAME
    )
    if _rgba_sha256(final_frame.output_path) != _rgba_sha256(
        hold_frame.output_path
    ):
        raise RuntimeError(
            f"death directional v01 {label} corpse hold differs from final"
        )


def _rotated_upper_body_offset(
    frame_number: int,
    direction_degrees: float,
) -> tuple[float, float, float]:
    local_x, local_y, local_z = down_adapter._cycle_upper_body_offset(
        frame_number
    )
    radians = math.radians(direction_degrees)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        cosine * local_x - sine * local_y,
        sine * local_x + cosine * local_y,
        local_z,
    )


def _projection_aware_upper_body_offset(
    context: factory.BuildContext,
    frame_number: int,
    direction: str,
) -> tuple[float, float, float]:
    rotated = factory.Vector(
        _rotated_upper_body_offset(
            frame_number,
            context.config.directions[direction],
        )
    )
    camera = factory.bpy.context.scene.camera
    if camera is None:
        raise RuntimeError("death directional v01 camera is missing")
    camera_right = camera.matrix_world.to_quaternion() @ factory.Vector(
        (1.0, 0.0, 0.0)
    )
    camera_right.normalize()
    approved_down = factory.Vector(
        down_adapter._cycle_upper_body_offset(frame_number)
    )
    minimum_lateral = abs(approved_down.dot(camera_right)) * (
        DIRECTIONAL_SPLIT_LATERAL_FACTOR_BY_DIRECTION[direction]
    )
    current_lateral = rotated.dot(camera_right)
    lateral_sign = -1.0 if direction in {"left", "up"} else 1.0
    if current_lateral * lateral_sign < minimum_lateral:
        rotated += camera_right * (
            lateral_sign * minimum_lateral - current_lateral
        )

    camera_up = camera.matrix_world.to_quaternion() @ factory.Vector(
        (0.0, 1.0, 0.0)
    )
    camera_up.normalize()
    approved_screen_up = factory.Vector(
        down_adapter._cycle_upper_body_offset(
            SPLIT_SCREEN_UP_REFERENCE_FRAME
        )
    ).dot(camera_up)
    target_screen_up = (
        abs(approved_screen_up)
        * DIRECTIONAL_SPLIT_SCREEN_UP_FACTOR_BY_DIRECTION[direction]
    )
    if approved_screen_up < 0.0:
        target_screen_up *= -1.0
    current_screen_up = rotated.dot(camera_up)
    ground_screen_up = factory.Vector(
        (camera_up[0], camera_up[1], 0.0)
    )
    ground_length = ground_screen_up.length
    if ground_length <= 1e-8:
        raise RuntimeError(
            "death directional v01 camera-up has no ground-plane projection"
        )
    ground_screen_up.normalize()
    ground_projection = ground_screen_up.dot(camera_up)
    if (
        target_screen_up >= 0.0
        and current_screen_up < target_screen_up
    ) or (
        target_screen_up < 0.0
        and current_screen_up > target_screen_up
    ):
        rotated += ground_screen_up * (
            (target_screen_up - current_screen_up) / ground_projection
        )
    return tuple(float(value) for value in rotated)


def _apply_up_split_tumble(
    context: factory.BuildContext,
    frame_number: int,
    states: tuple[tuple[object, object, str, str, object], ...],
) -> None:
    if not states:
        return
    profile = UP_SPLIT_TUMBLE_BY_FRAME[frame_number]
    objects = tuple(state[0] for state in states)
    points = [
        obj.matrix_world @ factory.Vector(corner)
        for obj in objects
        for corner in obj.bound_box
    ]
    pivot = factory.Vector(
        tuple(
            (
                min(point[axis] for point in points)
                + max(point[axis] for point in points)
            )
            * 0.5
            for axis in range(3)
        )
    )

    camera = factory.bpy.context.scene.camera
    if camera is None:
        raise RuntimeError("death directional v01 camera is missing")
    camera_rotation = camera.matrix_world.to_quaternion()
    camera_right = camera_rotation @ factory.Vector((1.0, 0.0, 0.0))
    camera_right.normalize()
    camera_up = camera_rotation @ factory.Vector((0.0, 1.0, 0.0))
    camera_up.normalize()
    camera_back = camera_rotation @ factory.Vector((0.0, 0.0, 1.0))
    camera_back.normalize()
    ground_screen_up = factory.Vector((camera_up[0], camera_up[1], 0.0))
    ground_screen_up.normalize()
    ground_projection = ground_screen_up.dot(camera_up)
    pixels_per_world = (
        context.config.camera["render_width"] / camera.data.ortho_scale
    )
    correction = camera_right * (
        profile["screen_right_raw_pixels"] / pixels_per_world
    )
    correction -= ground_screen_up * (
        (profile["screen_down_raw_pixels"] / pixels_per_world)
        / ground_projection
    )
    transform = (
        Matrix.Translation(pivot + correction)
        @ Matrix.Rotation(
            math.radians(profile["degrees"]),
            4,
            camera_back,
        )
        @ Matrix.Translation(-pivot)
    )
    for obj in objects:
        obj.matrix_world = transform @ obj.matrix_world
    factory.bpy.context.view_layer.update()
    _LAST_DIRECTIONAL_SPLIT_TUMBLES.setdefault("up", {})[
        str(frame_number)
    ] = dict(profile)


def _detach_upper_body_directional(
    context: factory.BuildContext,
    frame_number: int,
    direction: str,
) -> tuple[tuple[object, object, str, str, object], ...]:
    offset_values = _projection_aware_upper_body_offset(
        context,
        frame_number,
        direction,
    )
    offset = factory.Vector(offset_values)
    if offset.length == 0.0:
        return ()
    _LAST_DIRECTIONAL_SPLIT_OFFSETS.setdefault(direction, {})[
        str(frame_number)
    ] = [round(value, 6) for value in offset_values]

    states: list[tuple[object, object, str, str, object]] = []
    for obj in tuple(factory.bpy.data.objects):
        if obj.parent != context.rig or obj.parent_type != "BONE":
            continue
        if obj.parent_bone not in _GORE_UPPER_BODY_BONES:
            continue
        if obj.hide_render:
            continue
        parent = obj.parent
        parent_type = obj.parent_type
        parent_bone = obj.parent_bone
        world_matrix = obj.matrix_world.copy()
        states.append((obj, parent, parent_type, parent_bone, world_matrix))
        moved_matrix = world_matrix.copy()
        moved_matrix.translation += offset
        obj.parent = None
        obj.parent_type = "OBJECT"
        obj.parent_bone = ""
        obj.matrix_world = moved_matrix
    if not states:
        raise RuntimeError("death directional v01 upper-body object set is empty")
    factory.bpy.context.view_layer.update()
    state_tuple = tuple(states)
    if direction == "up":
        _apply_up_split_tumble(context, frame_number, state_tuple)
    return state_tuple


def _restore_upper_body(
    states: tuple[tuple[object, object, str, str, object], ...],
) -> None:
    for obj, parent, parent_type, parent_bone, world_matrix in states:
        obj.parent = parent
        obj.parent_type = parent_type
        obj.parent_bone = parent_bone
        obj.matrix_world = world_matrix
    if states:
        factory.bpy.context.view_layer.update()


def _raw_alpha_bbox(
    path: Path,
    *,
    alpha_threshold: float,
) -> tuple[int, int, int, int]:
    image = factory.bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = (int(value) for value in image.size)
        bbox = factory.alpha_bbox(
            tuple(image.pixels[:]),
            width,
            height,
            alpha_threshold,
        )
        if bbox is None:
            raise RuntimeError(f"directional raw render is empty: {path}")
        return bbox
    finally:
        factory.bpy.data.images.remove(image)


def _raw_path_for_artifact(
    raw_dir: Path,
    artifact: factory.FrameArtifact,
) -> Path:
    return raw_dir / artifact.output_path.name.replace(".png", "_raw.png")


def _normalize_direction_artifacts(
    context: factory.BuildContext,
    raw_dir: Path,
    artifacts: list[factory.FrameArtifact],
    *,
    direction: str,
    fixed_scale: float,
    idle_source_center_x: float,
) -> tuple[list[factory.FrameArtifact], dict[str, object]]:
    if not artifacts:
        raise RuntimeError(
            f"death directional v01 has no raw artifacts for {direction}"
        )
    config = context.config
    alpha_threshold = max(
        0.08,
        config.technical.alpha_threshold / 255.0,
    )
    source_half_span = (
        config.technical.canvas_width * 0.5
        - DIRECTIONAL_PACKING_MARGIN_PIXELS
        - 0.5
    ) / fixed_scale
    normalized: list[factory.FrameArtifact] = []
    framing_by_animation: dict[str, dict[str, float | int | str]] = {}
    animation_ids = tuple(
        dict.fromkeys(artifact.animation_id for artifact in artifacts)
    )
    for animation_id in animation_ids:
        cycle_artifacts = tuple(
            artifact
            for artifact in artifacts
            if artifact.animation_id == animation_id
        )
        bboxes = [
            _raw_alpha_bbox(
                _raw_path_for_artifact(raw_dir, artifact),
                alpha_threshold=alpha_threshold,
            )
            for artifact in cycle_artifacts
        ]
        union_min_x = min(bbox[0] for bbox in bboxes)
        union_max_x = max(bbox[2] for bbox in bboxes)
        minimum_center_x = union_max_x - source_half_span
        maximum_center_x = union_min_x + source_half_span
        if minimum_center_x > maximum_center_x:
            required_width = (union_max_x - union_min_x + 1) * fixed_scale
            raise RuntimeError(
                "death directional v01 cannot pack one full cycle into a "
                f"stable {direction} center at approved scale: "
                f"animation={animation_id},"
                f"required_width={required_width:.3f}px"
            )
        packed_center_x = min(
            max(idle_source_center_x, minimum_center_x),
            maximum_center_x,
        )

        for artifact in cycle_artifacts:
            width, height, _ = factory._normalize_render(
                _raw_path_for_artifact(raw_dir, artifact),
                artifact.output_path,
                config,
                fixed_scale=fixed_scale,
                fixed_center_x=packed_center_x,
            )
            normalized.append(
                factory.FrameArtifact(
                    animation_id=artifact.animation_id,
                    direction=artifact.direction,
                    frame_number=artifact.frame_number,
                    output_path=artifact.output_path,
                    sprite_width=width,
                    sprite_height=height,
                    baseline_y=artifact.baseline_y,
                )
            )
        framing_by_animation[animation_id] = {
            "mode": "shared_cycle_motion_envelope",
            "raw_union_min_x": union_min_x,
            "raw_union_max_x": union_max_x,
            "raw_union_width": union_max_x - union_min_x + 1,
            "fixed_scale": fixed_scale,
            "idle_source_center_x": idle_source_center_x,
            "packed_source_center_x": packed_center_x,
            "runtime_anchor_compensation_x_pixels": (
                packed_center_x - idle_source_center_x
            )
            * fixed_scale,
            "packing_margin_pixels": DIRECTIONAL_PACKING_MARGIN_PIXELS,
        }

    for artifact in normalized:
        _assert_no_boundary_touch(
            artifact,
            label=(
                f"packing/{artifact.animation_id}/{direction}/"
                f"f{artifact.frame_number:02d}"
            ),
        )
    return normalized, {
        "mode": "shared_cycle_motion_envelope",
        "cycles": framing_by_animation,
    }


def render_death_directional_cycles_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = down_adapter.render_death_down_cycles_v01(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    directional = load_death_directional_cycles_profile_v01(
        config.character_id
    )
    profiles = _profiles(config.character_id)
    profile_by_variant = {
        profile.death_variant_id: profile for profile in profiles
    }
    render_profiles = tuple(
        profile_by_variant[variant_id]
        for variant_id in FAIL_FAST_RENDER_VARIANT_ORDER
    )
    approved_down_hashes = _frame_rgba_hashes(artifacts, profiles, "down")
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    fixed_scale = calibrations["down"].scale
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    _LAST_DIRECTIONAL_FRAMING.clear()
    _LAST_DIRECTIONAL_SPLIT_OFFSETS.clear()
    _LAST_DIRECTIONAL_SPLIT_TUMBLES.clear()
    _LAST_DIRECTIONAL_SPLIT_OFFSETS["down"] = {
        str(frame_number): [
            round(value, 6)
            for value in down_adapter._cycle_upper_body_offset(frame_number)
        ]
        for frame_number in (6, 7, 8)
    }
    _LAST_DIRECTIONAL_FRAMING["down"] = {
        "mode": "approved_down_renderer",
        "cycles": {
            profile.animation_id: {
                "mode": "approved_down_renderer",
                "fixed_scale": fixed_scale,
                "idle_source_center_x": calibrations["down"].source_center_x,
                "packed_source_center_x": (
                    calibrations["down"].source_center_x
                ),
                "runtime_anchor_compensation_x_pixels": 0.0,
                "packing_margin_pixels": DIRECTIONAL_PACKING_MARGIN_PIXELS,
            }
            for profile in profiles
        },
    }

    try:
        for direction in directional.review_directions:
            direction_artifacts: list[factory.FrameArtifact] = []
            for profile in render_profiles:
                action = factory.bpy.data.actions.get(
                    f"{config.character_id}_{profile.animation_id}"
                )
                if (
                    action is None
                    or action.get("profile_revision") != profile.revision
                ):
                    raise RuntimeError(
                        "death directional v01 action is missing: "
                        f"{profile.animation_id}"
                    )
                factory._assign_action(context.rig, action)
                weapon_adapter._set_v12_weapon(None, None)
                context.rig.rotation_euler[2] = math.radians(
                    config.directions[direction]
                )
                factory.bpy.context.view_layer.update()

                for frame_number in directional.frame_order:
                    factory.bpy.context.scene.frame_set(frame_number)
                    factory.bpy.context.view_layer.update()
                    keypose_adapter._apply_gore_state(profile, frame_number)
                    split_states: tuple[
                        tuple[object, object, str, str, object], ...
                    ] = ()
                    if (
                        profile.gore_mode == "waist_torso_legs_separation"
                        and profile.detachment_frame is not None
                        and frame_number >= profile.detachment_frame
                    ):
                        split_states = _detach_upper_body_directional(
                            context,
                            frame_number,
                            direction,
                        )
                    try:
                        artifact, _ = factory._render_frame(
                            context,
                            animation_id=profile.animation_id,
                            direction=direction,
                            frame_number=frame_number,
                            raw_dir=raw_dir,
                            frame_dir=frame_dir,
                            output_name=(
                                f"{config.character_id}_{profile.animation_id}_"
                                f"{direction}_f{frame_number:02d}_"
                                f"proxy_{revision}.png"
                            ),
                            fixed_scale=fixed_scale,
                            fixed_center_x=(
                                None
                                if split_states
                                else calibrations[direction].source_center_x
                            ),
                        )
                        direction_artifacts.append(artifact)
                        if split_states:
                            _assert_split_components(
                                artifact,
                                label=(
                                    f"preflight/{profile.death_variant_id}/"
                                    f"{direction}/f{frame_number:02d}"
                                ),
                            )
                    finally:
                        _restore_upper_body(split_states)

            normalized, framing = _normalize_direction_artifacts(
                context,
                raw_dir,
                direction_artifacts,
                direction=direction,
                fixed_scale=fixed_scale,
                idle_source_center_x=calibrations[
                    direction
                ].source_center_x,
            )
            artifacts.extend(normalized)
            _LAST_DIRECTIONAL_FRAMING[direction] = framing
            for profile in profiles:
                frames = _find_frames(
                    artifacts,
                    animation_id=profile.animation_id,
                    direction=direction,
                )
                _assert_direction_contract(
                    frames,
                    profile=profile,
                    direction=direction,
                )
    finally:
        keypose_adapter._reset_gore_state()
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    expected_count = (
        len(directional.variants)
        * len(directional.directions)
        * len(directional.frame_order)
    )
    if len(artifacts) != expected_count:
        raise RuntimeError(
            f"death directional v01 requires {expected_count} frames, "
            f"got {len(artifacts)}"
        )

    for profile in profiles:
        for direction in directional.directions:
            _assert_direction_contract(
                _find_frames(
                    artifacts,
                    animation_id=profile.animation_id,
                    direction=direction,
                ),
                profile=profile,
                direction=direction,
            )
    if _frame_rgba_hashes(artifacts, profiles, "down") != approved_down_hashes:
        raise RuntimeError(
            "death directional v01 changed approved down RGBA pixels"
        )
    return artifacts


def _row_specs(character_id: str) -> tuple[tuple[object, str], ...]:
    directional = load_death_directional_cycles_profile_v01(character_id)
    return tuple(
        (profile, direction)
        for profile in _profiles(character_id)
        for direction in directional.directions
    )


def _write_directional_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    rows = _row_specs(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(DEATH_DOWN_CYCLE_FRAME_ORDER)
    height = tile_height * len(rows)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, (profile, direction) in enumerate(rows):
        frames = _find_frames(
            artifacts,
            animation_id=profile.animation_id,
            direction=direction,
        )
        row_y = (len(rows) - 1 - row_index) * tile_height
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
                    row_y,
                )
            finally:
                factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_death_directional_cycles_v01",
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
    result = _write_directional_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_directional_sheet(config, artifacts, named_path)
    return result


def _direction_payload(
    artifacts: list[factory.FrameArtifact],
    profile: object,
    direction: str,
) -> dict[str, object]:
    frames = _find_frames(
        artifacts,
        animation_id=profile.animation_id,
        direction=direction,
    )
    return {
        "direction": direction,
        "frame_count": len(frames),
        "corpse_hold_matches_final": (
            _rgba_sha256(frames[6].output_path)
            == _rgba_sha256(frames[7].output_path)
        ),
        "frames": [
            {
                "frame": item.frame_number,
                "phase": profile.poses[index].phase,
                "width": item.sprite_width,
                "height": item.sprite_height,
                "baseline_y": item.baseline_y,
                "edge_alpha": keypose_adapter._edge_alpha_counts(
                    item.output_path
                ),
                "rgba_sha256": _rgba_sha256(item.output_path),
                "major_component_sizes": (
                    list(_major_component_sizes(item.output_path))
                    if profile.gore_mode == "waist_torso_legs_separation"
                    and profile.detachment_frame is not None
                    and item.frame_number >= profile.detachment_frame
                    else []
                ),
            }
            for index, item in enumerate(frames)
        ],
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
    directional = load_death_directional_cycles_profile_v01(
        context.config.character_id
    )
    profiles = _profiles(context.config.character_id)
    named_sheet = run_dir / CONTACT_SHEET_NAME
    rendered = bool(artifacts)
    if rendered and not named_sheet.is_file():
        raise RuntimeError("death directional v01 contact sheet is missing")

    if rendered:
        payload["contact_sheet_review"] = {
            "background_color": CONTACT_SHEET_BACKGROUND_HEX,
            "rows_top_to_bottom": [
                f"{profile.death_variant_id}_{direction}"
                for profile, direction in _row_specs(
                    context.config.character_id
                )
            ],
            "columns_left_to_right": list(directional.phase_order),
        }
    payload["death_directional_cycles_v01"] = {
        "profile_revision": directional.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "down_adapter_path": context.config.relative_to_repo(DOWN_ADAPTER_PATH),
        "down_adapter_sha256": hashlib.sha256(
            DOWN_ADAPTER_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": (
            context.config.relative_to_repo(named_sheet) if rendered else None
        ),
        "directions": list(directional.directions),
        "review_directions": list(directional.review_directions),
        "framing_by_direction": (
            dict(_LAST_DIRECTIONAL_FRAMING) if rendered else {}
        ),
        "split_offsets_by_direction": (
            dict(_LAST_DIRECTIONAL_SPLIT_OFFSETS) if rendered else {}
        ),
        "split_tumbles_by_direction": (
            dict(_LAST_DIRECTIONAL_SPLIT_TUMBLES) if rendered else {}
        ),
        "frame_order": list(directional.frame_order),
        "phase_order": list(directional.phase_order),
        "fps": directional.fps,
        "duration_seconds": directional.duration_seconds,
        "variant_count": len(directional.variants),
        "direction_count": len(directional.directions),
        "frames_per_direction": len(directional.frame_order),
        "expected_new_directional_frames": (
            len(directional.variants)
            * len(directional.review_directions)
            * len(directional.frame_order)
        ),
        "expected_total_rendered_frames": (
            len(directional.variants)
            * len(directional.directions)
            * len(directional.frame_order)
        ),
        "total_rendered_frames": len(artifacts),
        "variants": {
            profile.death_variant_id: {
                "animation_id": profile.animation_id,
                "source_profile_revision": profile.revision,
                "gore_mode": profile.gore_mode,
                "detached_part_id": profile.detached_part_id,
                "detachment_frame": profile.detachment_frame,
                "directions": (
                    {
                        direction: _direction_payload(
                            artifacts,
                            profile,
                            direction,
                        )
                        for direction in directional.directions
                    }
                    if rendered
                    else {}
                ),
            }
            for profile in profiles
        },
        "locked_contract": {
            "approved_down_renderer_reused": True,
            "approved_down_rgba_unchanged_during_directional_render": True,
            "approved_down_motion_unchanged": True,
            "left_right_up_rendered_independently": True,
            "real_rig_rotation_per_direction": True,
            "stable_motion_envelope_center_per_cycle_and_direction": True,
            "runtime_anchor_compensation_per_cycle_recorded": True,
            "detachment_offset_rotates_with_rig": True,
            "projection_aware_detachment_readability": True,
            "up_detached_upper_body_camera_plane_tumble": True,
            "directional_split_lateral_factor_by_direction": (
                DIRECTIONAL_SPLIT_LATERAL_FACTOR_BY_DIRECTION
            ),
            "directional_split_screen_up_factor_by_direction": (
                DIRECTIONAL_SPLIT_SCREEN_UP_FACTOR_BY_DIRECTION
            ),
            "up_split_tumble_by_frame": UP_SPLIT_TUMBLE_BY_FRAME,
            "weapon_agnostic": True,
            "weapon_visible": False,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "binary_alpha_required": True,
            "zero_edge_alpha_required": True,
            "baseline_y_91_required": True,
            "corpse_hold_matches_final_per_direction": True,
            "death_03_two_major_components_per_direction": True,
            "manual_directional_review_required": True,
            "random_runtime_selection_not_started": True,
            "runtime_connected": False,
        },
        "status": (
            "directional_render_requires_manual_review"
            if rendered
            else "actions_built_render_not_started"
        ),
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "death_current_stage": "directional_cycles_v01",
            "death_variant_count": len(directional.variants),
            "death_direction_count": len(directional.directions),
            "death_frame_count_per_direction": len(directional.frame_order),
            "death_expected_new_directional_frame_count": (
                len(directional.variants)
                * len(directional.review_directions)
                * len(directional.frame_order)
            ),
            "death_total_directional_frame_count": len(artifacts),
            "death_weapon_agnostic": True,
            "death_weapon_visible": False,
            "death_corpse_hold_matches_final_per_direction": True,
            "death_directional_render_complete": rendered,
            "death_manual_directional_review_required": rendered,
            "death_directional_variants_not_yet_approved": True,
            "death_random_runtime_selection_not_started": True,
            "death_runtime_connected": False,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_death_directional_cycle_actions_v01
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_death_directional_cycles_v01
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_v01
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v01
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
