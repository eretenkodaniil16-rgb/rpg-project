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
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19 as v19_base
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_combat_idle_directional_v11 as directional_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from attack_sword_down_cycle_builder_v20 import (
    create_attack_sword_down_cycle_actions_v20,
)
from attack_sword_down_cycle_profile_v20 import (
    FULL_CYCLE_PHASE_ORDER,
    SOURCE_KEYPOSE_REVISION,
    load_attack_sword_down_cycle_profile_v20,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


PROFILE_PATH = SCRIPT_DIR / "attack_sword_down_cycle_profile_v20.py"
BUILDER_PATH = SCRIPT_DIR / "attack_sword_down_cycle_builder_v20.py"
SOURCE_ADAPTER_PATH = (
    SCRIPT_DIR / "blender_sprite_factory_attack_sword_down_keyposes_v19_pass07.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_down_cycle_v20.png"
MAX_APPROVED_GUARD_EDGE_PIXELS = 12
ONEHAND_GUARD_FAMILY_FRAMES = (1, 7, 8)
TWOHAND_PLANNED_CLEARANCE_FRAMES = (2, 3)
TWOHAND_CLEARANCE_FRAMES = (2, 3, 4)
MIN_TWOHAND_HEAD_CLEARANCE_PIXELS = 4.0
BASE_RENDER_FRAME = factory._render_frame
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _find_frames(
    artifacts: list[factory.FrameArtifact],
    *,
    animation_id: str,
) -> tuple[factory.FrameArtifact, ...]:
    frames = tuple(
        sorted(
            (
                artifact
                for artifact in artifacts
                if artifact.animation_id == animation_id
                and artifact.direction == "down"
            ),
            key=lambda artifact: artifact.frame_number,
        )
    )
    if tuple(artifact.frame_number for artifact in frames) != tuple(range(1, 9)):
        raise RuntimeError(f"attack sword down v20 missing frames: {animation_id}")
    return frames


def _assert_boundary_contract(
    artifact: factory.FrameArtifact,
    *,
    grip_id: str,
) -> None:
    counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
    label = f"{grip_id}/down/f{artifact.frame_number:02d}"
    if grip_id == "onehand_ready" and artifact.frame_number in ONEHAND_GUARD_FAMILY_FRAMES:
        forbidden = {
            edge: count
            for edge, count in counts.items()
            if edge != "left" and count > 0
        }
        if forbidden:
            raise RuntimeError(
                f"attack sword down v20 {label} touches forbidden boundaries: {forbidden}"
            )
        if counts["left"] > MAX_APPROVED_GUARD_EDGE_PIXELS:
            raise RuntimeError(
                f"attack sword down v20 {label} exceeds approved left-edge budget: "
                f"{counts['left']}"
            )
        return
    touched = {edge: count for edge, count in counts.items() if count > 0}
    if touched:
        raise RuntimeError(
            f"attack sword down v20 {label} touches canvas boundary: {touched}"
        )


def _assert_frame_contract(
    frames: tuple[factory.FrameArtifact, ...],
    *,
    label: str,
) -> None:
    if {artifact.baseline_y for artifact in frames} != {91}:
        raise RuntimeError(
            f"attack sword down v20 {label} baseline drifted: "
            f"{sorted({artifact.baseline_y for artifact in frames})}"
        )
    for artifact in frames:
        if artifact.sprite_width <= 0 or artifact.sprite_height <= 0:
            raise RuntimeError(
                f"attack sword down v20 {label} produced an empty frame: "
                f"f{artifact.frame_number:02d}"
            )
        if artifact.sprite_width > 96 or artifact.sprite_height > 96:
            raise RuntimeError(
                f"attack sword down v20 {label} exceeds 96x96 canvas: "
                f"f{artifact.frame_number:02d}="
                f"{artifact.sprite_width}x{artifact.sprite_height}"
            )


def _record_planner_metrics(
    scene: object,
    *,
    frame_number: int,
    projection_before: float,
    projection_after: float,
) -> None:
    prefix = f"attack_sword_down_cycle_v20_f{frame_number:02d}"
    scene[f"{prefix}_projection_before"] = float(projection_before)
    scene[f"{prefix}_projection_after"] = float(projection_after)
    scene[f"{prefix}_angle_offset_degrees"] = float(
        scene["attack_sword_down_v19_pass07_angle_offset_degrees"]
    )
    scene[f"{prefix}_planned_clearance_pixels"] = float(
        scene["attack_sword_down_v19_pass07_planned_clearance"]
    )
    scene[f"{prefix}_camera_margin_pixels"] = float(
        scene["attack_sword_down_v19_pass07_camera_margin"]
    )


def _render_frame_v20(
    context: factory.BuildContext,
    *,
    animation_id: str,
    direction: str,
    frame_number: int,
    raw_dir: Path,
    frame_dir: Path,
    output_name: str,
    fixed_scale: float | None,
    fixed_center_x: float | None,
    use_clearance_planner: bool,
) -> tuple[factory.FrameArtifact, factory.FramingCalibration]:
    if not use_clearance_planner:
        return BASE_RENDER_FRAME(
            context,
            animation_id,
            direction,
            frame_number,
            raw_dir,
            frame_dir,
            output_name,
            fixed_scale,
            fixed_center_x,
        )

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    saved_basis, projection_before, projection_after = (
        pass07_adapter._apply_clearance_planned_weapon_projection()
    )
    try:
        raw_path = raw_dir / output_name.replace(".png", "_raw.png")
        output_path = frame_dir / output_name
        scene.render.filepath = str(raw_path)
        factory.bpy.ops.render.render(write_still=True)
        width, height, calibration = factory._normalize_render(
            raw_path,
            output_path,
            context.config,
            fixed_scale=fixed_scale,
            fixed_center_x=fixed_center_x,
        )
        _record_planner_metrics(
            scene,
            frame_number=frame_number,
            projection_before=projection_before,
            projection_after=projection_after,
        )
        return (
            factory.FrameArtifact(
                animation_id=animation_id,
                direction=direction,
                frame_number=frame_number,
                output_path=output_path,
                sprite_width=width,
                sprite_height=height,
                baseline_y=context.config.technical.baseline_y,
            ),
            calibration,
        )
    finally:
        pass06_adapter._restore_weapon(saved_basis)


def _validate_twohand_clearance(
    context: factory.BuildContext,
    *,
    action_id: str,
    weapon_cycle_id: str,
) -> dict[int, float]:
    config = context.config
    action = factory.bpy.data.actions.get(f"{config.character_id}_{action_id}")
    if action is None:
        raise RuntimeError("attack sword down v20 two-hand action is missing")
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    clearances: dict[int, float] = {}
    try:
        weapon_adapter._set_v12_weapon(weapon_cycle_id, "down")
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        for frame_number in TWOHAND_CLEARANCE_FRAMES:
            factory.bpy.context.scene.frame_set(frame_number)
            factory.bpy.context.view_layer.update()
            saved_basis = None
            if frame_number in TWOHAND_PLANNED_CLEARANCE_FRAMES:
                saved_basis, projection_before, projection_after = (
                    pass07_adapter._apply_clearance_planned_weapon_projection()
                )
                _record_planner_metrics(
                    factory.bpy.context.scene,
                    frame_number=frame_number,
                    projection_before=projection_before,
                    projection_after=projection_after,
                )
            try:
                clearance = v19_base._twohand_head_clearance_pixels(context)
            finally:
                if saved_basis is not None:
                    pass06_adapter._restore_weapon(saved_basis)
            clearances[frame_number] = clearance
            factory.bpy.context.scene[
                f"attack_sword_down_cycle_v20_actual_clearance_f{frame_number:02d}"
            ] = clearance
            print(
                "ATTACK_SWORD_DOWN_CYCLE_V20_HEAD_CLEARANCE="
                f"f{frame_number:02d}:{clearance:.3f}px"
            )
            if clearance < MIN_TWOHAND_HEAD_CLEARANCE_PIXELS:
                raise RuntimeError(
                    "attack sword down v20 two-hand blade enters the projected "
                    f"head clearance zone: f{frame_number:02d}={clearance:.3f}px, "
                    f"required={MIN_TWOHAND_HEAD_CLEARANCE_PIXELS:.3f}px"
                )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
    return clearances


def render_attack_sword_down_cycle_v20(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    revision = context.proxy_revision
    profile = load_attack_sword_down_cycle_profile_v20(config.character_id)
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
            if action is None or action.get("profile_revision") != "v20":
                raise RuntimeError(
                    f"attack sword down v20 action is missing: {grip.action_id}"
                )
            factory._assign_action(context.rig, action)
            weapon_adapter._set_v12_weapon(grip.weapon_cycle_id, "down")
            context.rig.rotation_euler[2] = math.radians(config.directions["down"])

            for frame_number in profile.frame_order:
                artifact, _calibration = _render_frame_v20(
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
                    use_clearance_planner=(
                        grip.grip_id == "twohand_center_high"
                        and frame_number in TWOHAND_PLANNED_CLEARANCE_FRAMES
                    ),
                )
                artifacts.append(artifact)
                _assert_boundary_contract(artifact, grip_id=grip.grip_id)

            _assert_frame_contract(
                _find_frames(artifacts, animation_id=grip.action_id),
                label=grip.grip_id,
            )

        twohand = profile.grips[1]
        clearances = _validate_twohand_clearance(
            context,
            action_id=twohand.action_id,
            weapon_cycle_id=twohand.weapon_cycle_id,
        )
        factory.bpy.context.scene["attack_sword_down_cycle_v20_clearance_passed"] = True
        factory.bpy.context.scene["attack_sword_down_cycle_v20_clearance_frames"] = (
            ",".join(str(frame_number) for frame_number in sorted(clearances))
        )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    rendered_count = sum(
        1
        for artifact in artifacts
        if artifact.animation_id in {grip.action_id for grip in profile.grips}
    )
    if rendered_count != 16:
        raise RuntimeError(
            f"attack sword down v20 requires 16 rendered frames, got {rendered_count}"
        )
    return artifacts


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_attack_sword_down_cycle_profile_v20(config.character_id)
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
        "human_warrior_m01_attack_sword_down_cycle_v20",
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


def _write_contact_sheet_v20(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = _write_cycle_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_cycle_sheet(config, artifacts, named_path)
    return result


def _planner_payload(scene: object, frame_number: int) -> dict[str, float]:
    prefix = f"attack_sword_down_cycle_v20_f{frame_number:02d}"
    return {
        "angle_offset_degrees": float(scene[f"{prefix}_angle_offset_degrees"]),
        "projection_before": float(scene[f"{prefix}_projection_before"]),
        "projection_after": float(scene[f"{prefix}_projection_after"]),
        "planned_head_clearance_pixels": float(
            scene[f"{prefix}_planned_clearance_pixels"]
        ),
        "camera_margin_pixels": float(scene[f"{prefix}_camera_margin_pixels"]),
    }


def _write_manifest_v20(
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
    profile = load_attack_sword_down_cycle_profile_v20(context.config.character_id)
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("attack sword down v20 contact sheet is missing")
    scene = factory.bpy.context.scene

    grip_payloads: list[dict[str, object]] = []
    for grip in profile.grips:
        frames = _find_frames(artifacts, animation_id=grip.action_id)
        grip_payloads.append(
            {
                "grip_id": grip.grip_id,
                "display_name": grip.display_name,
                "action_id": grip.action_id,
                "weapon_cycle_id": grip.weapon_cycle_id,
                "trajectory_id": grip.trajectory_id,
                "frames": [
                    {
                        "frame": artifact.frame_number,
                        "phase": grip.poses[index].phase,
                        "width": artifact.sprite_width,
                        "height": artifact.sprite_height,
                        "baseline_y": artifact.baseline_y,
                    }
                    for index, artifact in enumerate(frames)
                ],
            }
        )

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": [grip.grip_id for grip in profile.grips],
        "columns_left_to_right": list(FULL_CYCLE_PHASE_ORDER),
    }
    payload["attack_sword_down_cycle_v20"] = {
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
        "source_adapter_path": context.config.relative_to_repo(SOURCE_ADAPTER_PATH),
        "source_adapter_sha256": hashlib.sha256(
            SOURCE_ADAPTER_PATH.read_bytes()
        ).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "total_rendered_frames": 16,
        "source_keypose_revision": SOURCE_KEYPOSE_REVISION,
        "approved_anchor_frames": [1, 3, 4, 5, 7, 8],
        "interpolated_frames": [2, 6],
        "twohand_clearance_frames": {
            f"f{frame_number:02d}": float(
                scene[
                    f"attack_sword_down_cycle_v20_actual_clearance_f{frame_number:02d}"
                ]
            )
            for frame_number in TWOHAND_CLEARANCE_FRAMES
        },
        "twohand_planned_frames": {
            f"f{frame_number:02d}": _planner_payload(scene, frame_number)
            for frame_number in TWOHAND_PLANNED_CLEARANCE_FRAMES
        },
        "grips": grip_payloads,
        "locked_contract": {
            "approved_v19_anchor_values_preserved": True,
            "direction_down_only": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "weapon_geometry_deformed": False,
            "materials_changed": False,
            "baseline_y_91_required": True,
            "manual_full_cycle_review_required": True,
            "runtime_connected": False,
        },
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_full_cycle_v20",
            "attack_sword_01_direction": "down",
            "attack_sword_01_frame_count_per_grip": 8,
            "attack_sword_01_total_rendered_frames": 16,
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
        create_attack_sword_down_cycle_actions_v20
    )
    base_adapter.render_pilot_combat_idle_down_v01 = (
        render_attack_sword_down_cycle_v20
    )
    base_adapter._write_contact_sheet_combat_idle_down_v01 = (
        _write_contact_sheet_v20
    )
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v20
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
