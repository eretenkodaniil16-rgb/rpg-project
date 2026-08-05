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

from mathutils import Matrix, Vector

import attack_sword_down_keyposes_builder_v17 as action_builder
import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_down_keyposes_v19 as v19_base
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass04 as previous_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
from attack_sword_down_keyposes_correction_v19_pass04 import (
    load_attack_sword_down_keyposes_profile_v19_pass04,
)
from attack_sword_down_keyposes_correction_v19_pass06 import (
    CORRECTION_PASS,
    TWOHAND_ANTICIPATION_REVISION,
    WEAPON_SCREEN_PROJECTION_MAGNITUDE,
)
from combat_idle_down_weapon_variants_builder_v06 import (
    TWO_HAND_HIGH_V06_OBJECT_NAMES,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_correction_v19_pass06.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"
TARGET_ANIMATION_ID = "attack_sword_01_twohand_down_keyposes_v17"
TARGET_FRAME = 2
BASE_RENDER_FRAME = factory._render_frame
BASE_WRITE_MANIFEST_PASS04 = previous_adapter._write_manifest_v19_pass04


def _weapon_objects() -> tuple[object, ...]:
    objects: list[object] = []
    for object_name in TWO_HAND_HIGH_V06_OBJECT_NAMES:
        obj = factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(
                f"attack sword down v19 pass06 weapon object is missing: {object_name}"
            )
        objects.append(obj)
    return tuple(objects)


def _camera_axes() -> tuple[Vector, Vector, Vector]:
    camera = factory.bpy.context.scene.camera
    if camera is None:
        raise RuntimeError("attack sword down v19 pass06 camera is missing")
    rotation = camera.matrix_world.to_3x3()
    screen_x = (rotation @ Vector((1.0, 0.0, 0.0))).normalized()
    screen_y = (rotation @ Vector((0.0, 1.0, 0.0))).normalized()
    camera_forward = (rotation @ Vector((0.0, 0.0, -1.0))).normalized()
    return screen_x, screen_y, camera_forward


def _weapon_world_direction() -> Vector:
    blade = factory.bpy.data.objects.get("combat_twohand_high_v06_blade")
    if blade is None:
        raise RuntimeError("attack sword down v19 pass06 blade object is missing")
    return (blade.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def _screen_projection_magnitude(direction: Vector) -> float:
    screen_x, screen_y, _camera_forward = _camera_axes()
    return math.hypot(direction.dot(screen_x), direction.dot(screen_y))


def _apply_rigid_weapon_depth_projection() -> tuple[dict[str, Matrix], float, float]:
    objects = _weapon_objects()
    grip = factory.bpy.data.objects.get("combat_twohand_high_v06_grip")
    if grip is None:
        raise RuntimeError("attack sword down v19 pass06 grip object is missing")

    current_direction = _weapon_world_direction()
    screen_x, screen_y, camera_forward = _camera_axes()
    projected_x = current_direction.dot(screen_x)
    projected_y = current_direction.dot(screen_y)
    current_projection = math.hypot(projected_x, projected_y)
    if current_projection <= 1.0e-6:
        raise RuntimeError("attack sword down v19 pass06 weapon projection is degenerate")

    screen_direction = (
        screen_x * (projected_x / current_projection)
        + screen_y * (projected_y / current_projection)
    ).normalized()
    depth_magnitude = math.sqrt(
        max(0.0, 1.0 - WEAPON_SCREEN_PROJECTION_MAGNITUDE ** 2)
    )
    target_direction = (
        screen_direction * WEAPON_SCREEN_PROJECTION_MAGNITUDE
        + camera_forward * depth_magnitude
    ).normalized()
    rotation = current_direction.rotation_difference(target_direction)
    pivot = grip.matrix_world.translation.copy()
    transform = (
        Matrix.Translation(pivot)
        @ rotation.to_matrix().to_4x4()
        @ Matrix.Translation(-pivot)
    )

    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    for obj in objects:
        obj.matrix_world = transform @ obj.matrix_world
    factory.bpy.context.view_layer.update()

    transformed_projection = _screen_projection_magnitude(_weapon_world_direction())
    return saved_basis, current_projection, transformed_projection


def _restore_weapon(saved_basis: dict[str, Matrix]) -> None:
    for object_name, matrix_basis in saved_basis.items():
        obj = factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(
                f"attack sword down v19 pass06 cannot restore object: {object_name}"
            )
        obj.matrix_basis = matrix_basis
    factory.bpy.context.view_layer.update()


def _render_frame_pass06(
    context: factory.BuildContext,
    animation_id: str,
    direction: str,
    frame_number: int,
    raw_dir: Path,
    frame_dir: Path,
    output_name: str,
    fixed_scale: float | None,
    fixed_center_x: float | None,
) -> tuple[factory.FrameArtifact, factory.FramingCalibration]:
    if animation_id != TARGET_ANIMATION_ID or frame_number != TARGET_FRAME:
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
        _apply_rigid_weapon_depth_projection()
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
        scene["attack_sword_down_v19_pass06_projection_before"] = projection_before
        scene["attack_sword_down_v19_pass06_projection_after"] = projection_after
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
        _restore_weapon(saved_basis)


def _validate_twohand_head_clearance_pass06(
    context: factory.BuildContext,
) -> dict[int, float]:
    config = context.config
    profile = load_attack_sword_down_keyposes_profile_v19_pass04(
        config.character_id
    )
    twohand = profile.grips[1]
    action = factory.bpy.data.actions.get(
        f"{config.character_id}_{twohand.action_id}"
    )
    if action is None:
        raise RuntimeError("attack sword down v19 pass06 two-hand action is missing")
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    clearances: dict[int, float] = {}
    try:
        weapon_adapter._set_v12_weapon(twohand.weapon_cycle_id, "down")
        factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        for frame_number in v19_base.CLEARANCE_FRAMES:
            factory.bpy.context.scene.frame_set(frame_number)
            factory.bpy.context.view_layer.update()
            saved_basis: dict[str, Matrix] | None = None
            if frame_number == TARGET_FRAME:
                saved_basis, _before, _after = _apply_rigid_weapon_depth_projection()
            try:
                clearance = v19_base._twohand_head_clearance_pixels(context)
            finally:
                if saved_basis is not None:
                    _restore_weapon(saved_basis)
            clearances[frame_number] = clearance
            print(
                "ATTACK_SWORD_DOWN_V19_PASS06_HEAD_CLEARANCE="
                f"f{frame_number:02d}:{clearance:.3f}px"
            )
            if clearance < v19_base.MIN_TWOHAND_HEAD_CLEARANCE_PIXELS:
                raise RuntimeError(
                    "attack sword down v19 pass06 two-hand blade enters the "
                    f"projected head clearance zone: f{frame_number:02d}="
                    f"{clearance:.3f}px, required="
                    f"{v19_base.MIN_TWOHAND_HEAD_CLEARANCE_PIXELS:.3f}px"
                )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
    return clearances


def _write_manifest_v19_pass06(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS04(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    payload["attack_sword_down_keyposes_v19_pass06"] = {
        "correction_pass": CORRECTION_PASS,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(run_dir / CONTACT_SHEET_NAME),
        "twohand_anticipation_revision": TWOHAND_ANTICIPATION_REVISION,
        "weapon_screen_projection_target": WEAPON_SCREEN_PROJECTION_MAGNITUDE,
        "weapon_screen_projection_before": float(
            scene["attack_sword_down_v19_pass06_projection_before"]
        ),
        "weapon_screen_projection_after": float(
            scene["attack_sword_down_v19_pass06_projection_after"]
        ),
        "rigid_weapon_parts": list(TWO_HAND_HIGH_V06_OBJECT_NAMES),
        "pivot_object": "combat_twohand_high_v06_grip",
        "onehand_v19_pass03_unchanged": True,
        "twohand_pose_source": "v19_pass04",
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "approved_guard_frames_changed": False,
        "manual_keypose_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_keyposes_v19_pass06",
            "attack_sword_01_manual_review_required": True,
            "attack_sword_01_rigid_weapon_depth_projection": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory._render_frame = _render_frame_pass06
    v19_base._validate_twohand_head_clearance = (
        _validate_twohand_head_clearance_pass06
    )
    previous_adapter._write_manifest_v19_pass04 = _write_manifest_v19_pass06
    action_builder.load_attack_sword_down_keyposes_profile_v17 = (
        load_attack_sword_down_keyposes_profile_v19_pass04
    )
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
