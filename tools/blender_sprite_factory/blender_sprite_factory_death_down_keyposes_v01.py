from __future__ import annotations

import binascii
import hashlib
import json
import math
import struct
import sys
import zlib
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



_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _waist_pixel_seam_top_down(
    frame_number: int,
) -> tuple[tuple[int, int], ...]:
    if frame_number == 4:
        return (
            ((19, 63),)
            + tuple((x, 64) for x in range(20, 36))
            + (
                (36, 65),
                (36, 66),
                (36, 67),
                (37, 68),
                (38, 69),
                (39, 70),
                (40, 71),
            )
        )
    if frame_number == 5:
        return tuple((x, x + 28) for x in range(21, 42))
    return ()


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", checksum)
    )


def _paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    left_distance = abs(estimate - left)
    up_distance = abs(estimate - up)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= up_distance and left_distance <= upper_left_distance:
        return left
    if up_distance <= upper_left_distance:
        return up
    return upper_left


def _decode_rgba8_png(
    path: Path,
    expected_dimensions: tuple[int, int] | None = (96, 96),
) -> tuple[int, int, list[bytearray], tuple[tuple[bytes, bytes], ...]]:
    data = path.read_bytes()
    if not data.startswith(_PNG_SIGNATURE):
        raise RuntimeError(f"death_03 seam requires PNG: {path}")

    chunks: list[tuple[bytes, bytes]] = []
    idat_parts: list[bytes] = []
    width = 0
    height = 0
    bit_depth = -1
    color_type = -1
    interlace = -1
    offset = len(_PNG_SIGNATURE)
    while offset < len(data):
        if offset + 12 > len(data):
            raise RuntimeError(f"truncated PNG chunk: {path}")
        payload_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + payload_length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise RuntimeError(f"truncated PNG payload: {path}")
        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = binascii.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise RuntimeError(f"PNG CRC mismatch: {path} {chunk_type!r}")
        chunks.append((chunk_type, payload))
        if chunk_type == b"IHDR":
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", payload)
            if compression != 0 or filter_method != 0:
                raise RuntimeError(f"unsupported PNG method: {path}")
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)
        elif chunk_type == b"IEND":
            break
        offset = crc_end

    if (bit_depth, color_type, interlace) != (8, 6, 0) or (
        expected_dimensions is not None
        and (width, height) != expected_dimensions
    ):
        raise RuntimeError(
            "death_03 seam requires expected-size RGBA8 non-interlaced PNG: "
            f"{path}={(width, height, bit_depth, color_type, interlace)}"
        )
    if not idat_parts:
        raise RuntimeError(f"PNG has no IDAT: {path}")

    packed = zlib.decompress(b"".join(idat_parts))
    row_size = width * 4
    expected_size = height * (row_size + 1)
    if len(packed) != expected_size:
        raise RuntimeError(
            f"unexpected PNG scanline size: {path}={len(packed)}/{expected_size}"
        )

    rows: list[bytearray] = []
    previous = bytearray(row_size)
    cursor = 0
    for _ in range(height):
        filter_type = packed[cursor]
        encoded = packed[cursor + 1 : cursor + 1 + row_size]
        cursor += row_size + 1
        decoded = bytearray(row_size)
        for index, value in enumerate(encoded):
            left = decoded[index - 4] if index >= 4 else 0
            up = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            elif filter_type == 4:
                predictor = _paeth_predictor(left, up, upper_left)
            else:
                raise RuntimeError(f"unsupported PNG filter {filter_type}: {path}")
            decoded[index] = (value + predictor) & 0xFF
        rows.append(decoded)
        previous = decoded
    return width, height, rows, tuple(chunks)


def _write_rgba8_png(
    path: Path,
    width: int,
    height: int,
    rows: list[bytearray],
    chunks: tuple[tuple[bytes, bytes], ...],
) -> None:
    if len(rows) != height or any(len(row) != width * 4 for row in rows):
        raise RuntimeError(f"death_03 seam row contract drifted: {path}")
    packed = b"".join(b"\x00" + bytes(row) for row in rows)
    replacement_idat = zlib.compress(packed, level=9)
    output = bytearray(_PNG_SIGNATURE)
    wrote_idat = False
    for chunk_type, payload in chunks:
        if chunk_type == b"IDAT":
            if not wrote_idat:
                output.extend(_png_chunk(b"IDAT", replacement_idat))
                wrote_idat = True
            continue
        output.extend(_png_chunk(chunk_type, payload))
    if not wrote_idat:
        raise RuntimeError(f"death_03 seam could not replace IDAT: {path}")
    path.write_bytes(bytes(output))


def _apply_waist_pixel_seam(path: Path, frame_number: int) -> int:
    seam = _waist_pixel_seam_top_down(frame_number)
    if not seam:
        return 0
    width, height, rows, chunks = _decode_rgba8_png(path)
    removed_opaque = 0
    for x, top_down_y in seam:
        if not (0 <= x < width and 0 <= top_down_y < height):
            raise RuntimeError(
                f"death_03 seam coordinate outside canvas: f{frame_number:02d} "
                f"{(x, top_down_y)}"
            )
        pixel_offset = x * 4
        if rows[top_down_y][pixel_offset + 3] >= 128:
            removed_opaque += 1
        rows[top_down_y][pixel_offset : pixel_offset + 4] = b"\x00\x00\x00\x00"
    if removed_opaque < len(seam) - 2:
        raise RuntimeError(
            "death_03 seam no longer follows the rendered waist: "
            f"f{frame_number:02d}={removed_opaque}/{len(seam)}"
        )
    _write_rgba8_png(path, width, height, rows, chunks)
    return removed_opaque


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
        return (0.35, 0.30, 0.45)
    if frame_number == 5:
        return (0.42, 0.40, 0.55)
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
                    if split_states:
                        _apply_waist_pixel_seam(
                            artifact.output_path,
                            frame_number,
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
        "pixel_seam_frames": (
            [4, 5]
            if profile.gore_mode == "waist_torso_legs_separation"
            else []
        ),
        "pixel_seam_preserves_existing_rgb": True,
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
