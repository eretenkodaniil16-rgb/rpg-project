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
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass05 as pass05_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_attack_sword_twohand_down_overhead_v21 as overhead_adapter
from attack_sword_twohand_down_overhead_correction_v21_pass02 import (
    BLADE_OBJECT_NAME,
    CORRECTION_PASS,
    GRIP_OBJECT_NAME,
    OVERHEAD_WEAPON_ARC_REVISION,
    PRESERVE_BODY_ACTION,
    PRESERVE_F01_F08,
    PRESERVE_WEAPON_GEOMETRY,
    REQUIRE_ZERO_EDGE_ALPHA,
    SCREEN_OFFSET_DEGREES_BY_FRAME,
    SCREEN_PROJECTION_BY_FRAME,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TWOHAND_OBJECT_NAMES,
    USE_REFERENCE_DEPTH_SIGN,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_twohand_down_overhead_correction_v21_pass02.py"
)
PASS02_MANIFEST_KEY = "attack_sword_twohand_down_overhead_v21_pass02"
METRICS_SCENE_KEY = "twohand_overhead_v21_p02_metrics"

ORIGINAL_PASS05_RENDER = pass05_adapter._render_frame_v20_pass05
ORIGINAL_OVERHEAD_WRITE_MANIFEST = overhead_adapter._write_manifest_overhead_v21


def _weapon_objects() -> tuple[object, ...]:
    objects: list[object] = []
    for name in TWOHAND_OBJECT_NAMES:
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"two-hand overhead pass02 object is missing: {name}")
        if obj.hide_render:
            raise RuntimeError(f"two-hand overhead pass02 object is hidden: {name}")
        objects.append(obj)
    return tuple(objects)


def _blade_direction() -> object:
    blade = factory.bpy.data.objects.get(BLADE_OBJECT_NAME)
    if blade is None:
        raise RuntimeError("two-hand overhead pass02 blade is missing")
    return (
        blade.matrix_world.to_3x3() @ factory.Vector((0.0, 0.0, 1.0))
    ).normalized()


def _reference_guard_direction(scene: object, frame_number: int) -> object:
    scene.frame_set(1)
    factory.bpy.context.view_layer.update()
    reference = _blade_direction().copy()
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    return reference


def _target_direction(
    reference_direction: object,
    *,
    offset_degrees: float,
    requested_projection: float,
) -> tuple[object, float, float, float]:
    screen_x, screen_y, camera_forward = pass06_adapter._camera_axes()
    reference_x = float(reference_direction.dot(screen_x))
    reference_y = float(reference_direction.dot(screen_y))
    reference_depth = float(reference_direction.dot(camera_forward))
    reference_projection = math.hypot(reference_x, reference_y)
    if reference_projection <= 1.0e-6:
        raise RuntimeError("two-hand overhead pass02 guard projection is degenerate")

    projection = min(0.999, max(0.05, float(requested_projection)))
    angle = math.atan2(reference_y, reference_x) + math.radians(offset_degrees)
    if USE_REFERENCE_DEPTH_SIGN:
        depth_sign = 1.0 if reference_depth >= 0.0 else -1.0
    else:
        depth_sign = 1.0
    depth = depth_sign * math.sqrt(max(0.0, 1.0 - projection**2))
    target = (
        screen_x * (math.cos(angle) * projection)
        + screen_y * (math.sin(angle) * projection)
        + camera_forward * depth
    ).normalized()
    return target, reference_projection, reference_depth, depth


def _render_frame_overhead_v21_pass02(
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
    if not (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number in TARGET_FRAMES
    ):
        return ORIGINAL_PASS05_RENDER(
            context,
            animation_id=animation_id,
            direction=direction,
            frame_number=frame_number,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=output_name,
            fixed_scale=fixed_scale,
            fixed_center_x=fixed_center_x,
            use_clearance_planner=use_clearance_planner,
        )
    if fixed_scale is None or fixed_center_x is None:
        raise RuntimeError("two-hand overhead pass02 requires fixed framing")

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    reference_direction = _reference_guard_direction(scene, frame_number)
    objects = _weapon_objects()
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = _blade_direction()
    grip = factory.bpy.data.objects.get(GRIP_OBJECT_NAME)
    if grip is None:
        raise RuntimeError("two-hand overhead pass02 grip is missing")
    pivot = grip.matrix_world.translation.copy()

    offset_degrees = float(SCREEN_OFFSET_DEGREES_BY_FRAME[frame_number])
    requested_projection = float(SCREEN_PROJECTION_BY_FRAME[frame_number])
    target_direction, reference_projection, reference_depth, target_depth = (
        _target_direction(
            reference_direction,
            offset_degrees=offset_degrees,
            requested_projection=requested_projection,
        )
    )
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=target_direction,
    )
    try:
        factory.bpy.context.view_layer.update()
        artifact, calibration = export_adapter._render_candidate(
            context,
            animation_id=animation_id,
            direction=direction,
            frame_number=frame_number,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=output_name,
            fixed_scale=fixed_scale,
            fixed_center_x=fixed_center_x,
        )
        edge_counts = keypose_adapter._edge_alpha_counts(artifact.output_path)
        touched = {edge: int(count) for edge, count in edge_counts.items() if count > 0}
        if REQUIRE_ZERO_EDGE_ALPHA and touched:
            raise RuntimeError(
                "two-hand overhead pass02 touched canvas edge at "
                f"f{frame_number:02d}: {touched}"
            )
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        factory.bpy.context.view_layer.update()

    metrics = json.loads(str(scene.get(METRICS_SCENE_KEY, "{}")))
    metrics[f"f{frame_number:02d}"] = {
        "screen_offset_degrees_from_guard": offset_degrees,
        "requested_screen_projection": requested_projection,
        "reference_screen_projection": reference_projection,
        "reference_camera_depth": reference_depth,
        "target_camera_depth": target_depth,
        "edge_counts": edge_counts,
        "rigid_weapon_transform": True,
        "body_action_changed": False,
    }
    scene[METRICS_SCENE_KEY] = json.dumps(metrics, sort_keys=True)
    print(
        "ATTACK_SWORD_TWOHAND_DOWN_OVERHEAD_V21_PASS02="
        f"f{frame_number:02d};offset:{offset_degrees:.1f};"
        f"projection:{requested_projection:.3f};depth:{target_depth:.6f};"
        f"edges:{edge_counts}"
    )
    return artifact, calibration


def _write_manifest_overhead_v21_pass02(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_OVERHEAD_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = json.loads(
        str(factory.bpy.context.scene.get(METRICS_SCENE_KEY, "{}"))
    )
    expected = {f"f{frame:02d}" for frame in TARGET_FRAMES}
    if set(metrics) != expected:
        raise RuntimeError(
            "two-hand overhead pass02 metrics are incomplete: "
            f"actual={sorted(metrics)}, expected={sorted(expected)}"
        )

    payload[PASS02_MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": OVERHEAD_WEAPON_ARC_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "target_action_id": TARGET_ACTION_ID,
        "target_direction": TARGET_DIRECTION,
        "target_frames": list(TARGET_FRAMES),
        "screen_offset_degrees_by_frame": {
            str(frame): value
            for frame, value in SCREEN_OFFSET_DEGREES_BY_FRAME.items()
        },
        "screen_projection_by_frame": {
            str(frame): value
            for frame, value in SCREEN_PROJECTION_BY_FRAME.items()
        },
        "render_metrics": metrics,
        "reference_depth_sign_used": USE_REFERENCE_DEPTH_SIGN,
        "f01_f08_preserved": PRESERVE_F01_F08,
        "body_action_preserved": PRESERVE_BODY_ACTION,
        "weapon_geometry_preserved": PRESERVE_WEAPON_GEOMETRY,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_twohand_down_overhead_weapon_arc_revision": (
                OVERHEAD_WEAPON_ARC_REVISION
            ),
            "attack_sword_01_twohand_down_overhead_vertical_arc": True,
            "attack_sword_01_twohand_down_overhead_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_pass02_contract() -> None:
    pass05_adapter._render_frame_v20_pass05 = _render_frame_overhead_v21_pass02
    overhead_adapter._write_manifest_overhead_v21 = (
        _write_manifest_overhead_v21_pass02
    )


def _restore_pass02_contract() -> None:
    pass05_adapter._render_frame_v20_pass05 = ORIGINAL_PASS05_RENDER
    overhead_adapter._write_manifest_overhead_v21 = (
        ORIGINAL_OVERHEAD_WRITE_MANIFEST
    )


def main() -> int:
    _apply_pass02_contract()
    try:
        return overhead_adapter.main()
    finally:
        _restore_pass02_contract()


if __name__ == "__main__":
    raise SystemExit(main())
