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

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_down_cycle_v20 as base_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19 as v19_base
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
from attack_sword_down_cycle_correction_v20_pass02 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_PIXELS,
    ONEHAND_CONTAINMENT_REVISION,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)
from combat_idle_down_weapon_variants_builder_v06 import (
    ONE_HAND_V06_OBJECT_NAMES,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_cycle_correction_v20_pass02.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_cycle_v20.png"
BASE_RENDER_FRAME_V20 = base_adapter._render_frame_v20
BASE_WRITE_MANIFEST_V20 = base_adapter._write_manifest_v20


def _onehand_objects() -> tuple[object, ...]:
    objects: list[object] = []
    for object_name in ONE_HAND_V06_OBJECT_NAMES:
        obj = factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(
                f"attack sword down v20 pass02 weapon object is missing: {object_name}"
            )
        objects.append(obj)
    return tuple(objects)


def _onehand_world_direction() -> Vector:
    blade = factory.bpy.data.objects.get("combat_onehand_v06_blade")
    if blade is None:
        raise RuntimeError("attack sword down v20 pass02 blade object is missing")
    return (blade.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def _weapon_head_clearance(objects: tuple[object, ...]) -> float:
    head_bbox = v19_base._head_screen_bbox(
        width=base_adapter.CANVAS_WIDTH if hasattr(base_adapter, "CANVAS_WIDTH") else 96,
        height=base_adapter.CANVAS_HEIGHT if hasattr(base_adapter, "CANVAS_HEIGHT") else 96,
    )
    clearance = float("inf")
    found = False
    for obj in objects:
        points, edges = v19_base._object_screen_geometry(
            obj,
            width=96,
            height=96,
        )
        for first_index, second_index in edges:
            found = True
            clearance = min(
                clearance,
                v19_base._segment_rect_distance(
                    points[first_index],
                    points[second_index],
                    head_bbox,
                ),
            )
    if not found or not math.isfinite(clearance):
        raise RuntimeError("attack sword down v20 pass02 could not evaluate clearance")
    return clearance


def _apply_containment_planned_onehand_rotation(
) -> tuple[dict[str, Matrix], float, float, float]:
    objects = _onehand_objects()
    grip = factory.bpy.data.objects.get("combat_onehand_v06_grip")
    if grip is None:
        raise RuntimeError("attack sword down v20 pass02 grip object is missing")

    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = _onehand_world_direction()
    screen_x, screen_y, camera_forward = pass06_adapter._camera_axes()
    current_x = current_direction.dot(screen_x)
    current_y = current_direction.dot(screen_y)
    current_depth = current_direction.dot(camera_forward)
    current_projection = math.hypot(current_x, current_y)
    if current_projection <= 1.0e-6:
        raise RuntimeError("attack sword down v20 pass02 source projection is degenerate")
    current_angle = math.atan2(current_y, current_x)
    pivot = grip.matrix_world.translation.copy()

    candidates: list[dict[str, float | Vector]] = []
    offsets = sorted(
        range(
            -ANGLE_SEARCH_LIMIT_DEGREES,
            ANGLE_SEARCH_LIMIT_DEGREES + 1,
            ANGLE_SEARCH_STEP_DEGREES,
        ),
        key=lambda value: (abs(value), value),
    )
    for offset_degrees in offsets:
        candidate_angle = current_angle + math.radians(offset_degrees)
        target_direction = (
            screen_x * (math.cos(candidate_angle) * current_projection)
            + screen_y * (math.sin(candidate_angle) * current_projection)
            + camera_forward * current_depth
        ).normalized()
        pass07_adapter._apply_world_rotation(
            objects,
            pivot=pivot,
            current_direction=current_direction,
            target_direction=target_direction,
        )
        try:
            margin = pass07_adapter._weapon_camera_margin(objects)
            clearance = _weapon_head_clearance(objects)
        finally:
            pass06_adapter._restore_weapon(saved_basis)
        candidates.append(
            {
                "offset_degrees": float(offset_degrees),
                "margin": float(margin),
                "clearance": float(clearance),
                "target_direction": target_direction,
            }
        )

    valid = [
        candidate
        for candidate in candidates
        if float(candidate["margin"]) >= MIN_CAMERA_MARGIN_PIXELS
        and float(candidate["clearance"]) >= MIN_HEAD_CLEARANCE_PIXELS
    ]
    if not valid:
        best = max(
            candidates,
            key=lambda item: (
                float(item["margin"]),
                float(item["clearance"]),
                -abs(float(item["offset_degrees"])),
            ),
            default=None,
        )
        if best is None:
            raise RuntimeError("attack sword down v20 pass02 generated no candidates")
        raise RuntimeError(
            "attack sword down v20 pass02 found no contained rebound arc; "
            f"best margin={float(best['margin']):.3f}px, "
            f"clearance={float(best['clearance']):.3f}px, "
            f"offset={float(best['offset_degrees']):.1f}deg"
        )

    chosen = min(
        valid,
        key=lambda item: (
            abs(float(item["offset_degrees"])),
            -float(item["margin"]),
            -float(item["clearance"]),
        ),
    )
    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=chosen["target_direction"],
    )
    transformed_projection = pass06_adapter._screen_projection_magnitude(
        _onehand_world_direction()
    )
    scene = factory.bpy.context.scene
    scene["attack_sword_down_cycle_v20_pass02_angle_offset_degrees"] = float(
        chosen["offset_degrees"]
    )
    scene["attack_sword_down_cycle_v20_pass02_camera_margin"] = float(
        chosen["margin"]
    )
    scene["attack_sword_down_cycle_v20_pass02_head_clearance"] = float(
        chosen["clearance"]
    )
    scene["attack_sword_down_cycle_v20_pass02_projection_before"] = float(
        current_projection
    )
    scene["attack_sword_down_cycle_v20_pass02_projection_after"] = float(
        transformed_projection
    )
    print(
        "ATTACK_SWORD_DOWN_CYCLE_V20_PASS02_CONTAINMENT="
        f"offset:{float(chosen['offset_degrees']):.1f}deg;"
        f"margin:{float(chosen['margin']):.3f}px;"
        f"clearance:{float(chosen['clearance']):.3f}px;"
        f"projection:{transformed_projection:.3f}"
    )
    return (
        saved_basis,
        current_projection,
        transformed_projection,
        float(chosen["margin"]),
    )


def _render_frame_v20_pass02(
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
    if animation_id != TARGET_ANIMATION_ID or frame_number != TARGET_FRAME:
        return BASE_RENDER_FRAME_V20(
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

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    saved_basis, _projection_before, _projection_after, _margin = (
        _apply_containment_planned_onehand_rotation()
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


def _write_manifest_v20_pass02(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_V20(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    payload["attack_sword_down_cycle_v20_pass02"] = {
        "correction_pass": CORRECTION_PASS,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(run_dir / CONTACT_SHEET_NAME),
        "onehand_containment_revision": ONEHAND_CONTAINMENT_REVISION,
        "target_animation_id": TARGET_ANIMATION_ID,
        "target_frame": TARGET_FRAME,
        "selected_angle_offset_degrees": float(
            scene["attack_sword_down_cycle_v20_pass02_angle_offset_degrees"]
        ),
        "camera_margin_pixels": float(
            scene["attack_sword_down_cycle_v20_pass02_camera_margin"]
        ),
        "head_clearance_pixels": float(
            scene["attack_sword_down_cycle_v20_pass02_head_clearance"]
        ),
        "projection_before": float(
            scene["attack_sword_down_cycle_v20_pass02_projection_before"]
        ),
        "projection_after": float(
            scene["attack_sword_down_cycle_v20_pass02_projection_after"]
        ),
        "angle_search_limit_degrees": ANGLE_SEARCH_LIMIT_DEGREES,
        "angle_search_step_degrees": ANGLE_SEARCH_STEP_DEGREES,
        "minimum_camera_margin_pixels": MIN_CAMERA_MARGIN_PIXELS,
        "minimum_head_clearance_pixels": MIN_HEAD_CLEARANCE_PIXELS,
        "body_pose_changed": False,
        "approved_v19_anchor_frames_changed": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_full_cycle_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_full_cycle_v20_pass02",
            "attack_sword_01_onehand_rebound_contained": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter._render_frame_v20 = _render_frame_v20_pass02
    base_adapter._write_manifest_v20 = _write_manifest_v20_pass02
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
