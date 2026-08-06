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
from death_down_keyposes_builder_v01 import (
    _GORE_LOWER_CUT_CAP,
    _GORE_UPPER_BODY_BONES,
    _GORE_UPPER_CUT_CAP,
    create_death_down_keypose_actions_v01,
)
from death_down_keyposes_profile_v01 import (
    load_death_down_keyposes_profiles_v01,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


PROFILE_PATH = SCRIPT_DIR / "death_down_keyposes_profile_v01.py"
BUILDER_PATH = SCRIPT_DIR / "death_down_keyposes_builder_v01.py"
CONTACT_SHEET_NAME = "human_warrior_m01_death_base_down_keyposes_v01.png"
EXPECTED_FRAME_NUMBERS = (1, 2, 3, 4, 5)
MAX_ALLOWED_EDGE_PIXELS = 18
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _profiles(character_id: str) -> tuple[object, ...]:
    return load_death_down_keyposes_profiles_v01(character_id)


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
        raise RuntimeError(f"death down keyposes v01 incomplete set: {animation_id}")
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


def _opaque_component_sizes(path: Path) -> tuple[int, ...]:
    image = factory.bpy.data.images.load(str(path), check_existing=False)
    try:
        width, height = (int(value) for value in image.size)
        pixels = tuple(image.pixels[:])
        opaque = {
            (x, y)
            for y in range(height)
            for x in range(width)
            if pixels[(y * width + x) * 4 + 3] >= 0.5
        }
        sizes: list[int] = []
        while opaque:
            seed = opaque.pop()
            stack = [seed]
            size = 0
            while stack:
                x, y = stack.pop()
                size += 1
                for neighbor in (
                    (x + 1, y),
                    (x - 1, y),
                    (x, y + 1),
                    (x, y - 1),
                ):
                    if neighbor in opaque:
                        opaque.remove(neighbor)
                        stack.append(neighbor)
            sizes.append(size)
        return tuple(sorted(sizes, reverse=True))
    finally:
        factory.bpy.data.images.remove(image)


def _assert_frame_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    death_variant_id: str,
) -> None:
    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError(
            f"{death_variant_id} baseline drifted: "
            f"{sorted({item.baseline_y for item in frames})}"
        )
    for item in frames:
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"{death_variant_id} produced empty f{item.frame_number:02d}"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                f"{death_variant_id} exceeds 96x96: "
                f"f{item.frame_number:02d}={item.sprite_width}x{item.sprite_height}"
            )
        edge_counts = _edge_alpha_counts(item.output_path)
        clipped = {
            edge: count
            for edge, count in edge_counts.items()
            if count > MAX_ALLOWED_EDGE_PIXELS
        }
        if clipped:
            raise RuntimeError(
                f"{death_variant_id} exceeds review edge budget: "
                f"f{item.frame_number:02d}={clipped}"
            )


def _set_hidden(obj: factory.bpy.types.Object, hidden: bool) -> None:
    obj.hide_render = hidden
    obj.hide_viewport = hidden


def _required_object(name: str) -> factory.bpy.types.Object:
    obj = factory.bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"death gore object is missing: {name}")
    return obj


def _reset_gore_state() -> None:
    for name in (_GORE_UPPER_CUT_CAP, _GORE_LOWER_CUT_CAP):
        _set_hidden(_required_object(name), True)


def _apply_gore_state(profile: object, frame_number: int) -> None:
    _reset_gore_state()
    if profile.gore_mode != "waist_torso_legs_separation":
        return
    if profile.detachment_frame is None or frame_number < profile.detachment_frame:
        return
    _set_hidden(_required_object(_GORE_UPPER_CUT_CAP), False)
    _set_hidden(_required_object(_GORE_LOWER_CUT_CAP), False)


def _upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 4:
        return (0.78, -0.38, 0.18)
    if frame_number == 5:
        return (1.05, -0.52, 0.10)
    return (0.0, 0.0, 0.0)


def _detach_upper_body(
    context: factory.BuildContext,
    frame_number: int,
) -> tuple[tuple[object, object, str, str, object], ...]:
    offset = factory.Vector(_upper_body_offset(frame_number))
    if offset.length == 0.0:
        return ()

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
        raise RuntimeError("death_03 upper-body object set is empty")
    factory.bpy.context.view_layer.update()
    return tuple(states)


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



def render_death_down_keyposes_v01(
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

    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    weapon_adapter._set_v12_weapon(None, None)
    calibrations = directional_adapter._direction_calibrations(context, run_dir)
    down_calibration = calibrations["down"]
    artifacts: list[factory.FrameArtifact] = []

    try:
        for profile in profiles:
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{profile.animation_id}"
            )
            if action is None or action.get("profile_revision") != profile.revision:
                raise RuntimeError(
                    f"death down keyposes action is missing: {profile.animation_id}"
                )
            factory._assign_action(context.rig, action)
            weapon_adapter._set_v12_weapon(None, None)
            context.rig.rotation_euler[2] = math.radians(config.directions["down"])

            for frame_number in profile.frame_order:
                factory.bpy.context.scene.frame_set(frame_number)
                factory.bpy.context.view_layer.update()
                _apply_gore_state(profile, frame_number)
                split_states: tuple[tuple[object, object, str, str, object], ...] = ()
                if (
                    profile.gore_mode == "waist_torso_legs_separation"
                    and profile.detachment_frame is not None
                    and frame_number >= profile.detachment_frame
                ):
                    split_states = _detach_upper_body(context, frame_number)
                try:
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
                        fixed_center_x=(
                            None
                            if split_states
                            else down_calibration.source_center_x
                        ),
                    )
                    artifacts.append(artifact)
                finally:
                    _restore_upper_body(split_states)

            frames = _find_frames(artifacts, animation_id=profile.animation_id)
            _assert_frame_contract(frames, death_variant_id=profile.death_variant_id)
            if profile.gore_mode == "waist_torso_legs_separation":
                for item in frames:
                    if item.frame_number < int(profile.detachment_frame):
                        continue
                    component_sizes = _opaque_component_sizes(item.output_path)
                    major_components = [
                        size for size in component_sizes if size >= 120
                    ]
                    if (
                        len(major_components) < 2
                        or major_components[1] < major_components[0] * 0.20
                    ):
                        raise RuntimeError(
                            "death_03 torso and legs are not visually separated: "
                            f"f{item.frame_number:02d}={component_sizes}"
                        )
    finally:
        _reset_gore_state()
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    expected_count = len(profiles) * len(EXPECTED_FRAME_NUMBERS)
    if len(artifacts) != expected_count:
        raise RuntimeError(
            f"death down keyposes v01 requires {expected_count} frames, "
            f"got {len(artifacts)}"
        )
    return artifacts


def _write_keypose_sheet(
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
                    (len(profiles) - 1 - row_index) * tile_height,
                )
            finally:
                factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_death_base_down_keyposes_v01",
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
    result = _write_keypose_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_keypose_sheet(config, artifacts, named_path)
    return result


def _profile_payload(
    context: factory.BuildContext,
    profile: object,
    artifacts: list[factory.FrameArtifact],
    named_sheet: Path,
) -> dict[str, object]:
    frames = _find_frames(artifacts, animation_id=profile.animation_id)
    return {
        "profile_revision": profile.revision,
        "death_variant_id": profile.death_variant_id,
        "animation_id": profile.animation_id,
        "direction": profile.direction,
        "fps": profile.fps,
        "loop": profile.loop,
        "source_stance_variant_id": profile.source_stance_variant_id,
        "source_stance_revision": profile.source_stance_revision,
        "weapon_visible": profile.weapon_visible,
        "weapon_agnostic": True,
        "fall_side": profile.fall_side,
        "final_pose_persistent": profile.final_pose_persistent,
        "gore_mode": profile.gore_mode,
        "detached_part_id": profile.detached_part_id,
        "detachment_frame": profile.detachment_frame,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
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
                "edge_alpha": _edge_alpha_counts(item.output_path),
            }
            for index, item in enumerate(frames)
        ],
        "locked_contract": {
            "down_keyposes_only": True,
            "base_weapon_agnostic": True,
            "weapon_visible": False,
            "final_pose_persistent": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "manual_keypose_review_required": True,
            "full_cycle_not_yet_approved": True,
            "random_runtime_selection_not_started": True,
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
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("death base down keyposes contact sheet is missing")

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": [profile.death_variant_id for profile in profiles],
        "columns_left_to_right": list(profiles[0].phase_order),
    }
    payload["death_base_down_keyposes_v01"] = {
        profile.death_variant_id: _profile_payload(
            context,
            profile,
            artifacts,
            named_sheet,
        )
        for profile in profiles
    }
    payload["death_base_down_keyposes_v01_shared"] = {
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "variant_count": len(profiles),
        "frames_per_variant": len(EXPECTED_FRAME_NUMBERS),
        "total_rendered_frames": len(artifacts),
        "weapon_agnostic": True,
        "weapon_visible": False,
        "detachment_variant_count": sum(
            profile.detached_part_id is not None for profile in profiles
        ),
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "death_current_stage": "base_down_keyposes_v01",
            "death_variant_ids": [profile.death_variant_id for profile in profiles],
            "death_variant_count": len(profiles),
            "death_keypose_count_per_variant": len(EXPECTED_FRAME_NUMBERS),
            "death_total_frame_count": len(artifacts),
            "death_fps": profiles[0].fps,
            "death_weapon_agnostic": True,
            "death_weapon_visible": False,
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
    base_adapter.create_combat_idle_down_actions_v01 = create_death_down_keypose_actions_v01
    base_adapter.render_pilot_combat_idle_down_v01 = render_death_down_keyposes_v01
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v01
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v01
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
