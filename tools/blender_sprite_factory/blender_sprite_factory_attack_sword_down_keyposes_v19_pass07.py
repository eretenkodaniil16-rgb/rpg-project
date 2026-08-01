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
import blender_sprite_factory_attack_sword_down_keyposes_v19 as v19_base
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as previous_adapter
from attack_sword_down_keyposes_correction_v19_pass07 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    MIN_CAMERA_MARGIN_PIXELS,
    TARGET_HEAD_CLEARANCE_PIXELS,
    TWOHAND_ANTICIPATION_REVISION,
    WEAPON_SCREEN_PROJECTION_MAGNITUDE,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_correction_v19_pass07.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"
CANVAS_WIDTH = 96
CANVAS_HEIGHT = 96
BASE_WRITE_MANIFEST_PASS06 = previous_adapter._write_manifest_v19_pass06


def _apply_world_rotation(
    objects: tuple[object, ...],
    *,
    pivot: Vector,
    current_direction: Vector,
    target_direction: Vector,
) -> None:
    rotation = current_direction.rotation_difference(target_direction)
    transform = (
        Matrix.Translation(pivot)
        @ rotation.to_matrix().to_4x4()
        @ Matrix.Translation(-pivot)
    )
    for obj in objects:
        obj.matrix_world = transform @ obj.matrix_world
    factory.bpy.context.view_layer.update()


def _actual_weapon_head_clearance() -> float:
    head_bbox = v19_base._head_screen_bbox(
        width=CANVAS_WIDTH,
        height=CANVAS_HEIGHT,
    )
    clearance = float("inf")
    found = False
    for object_name in v19_base.TWOHAND_WEAPON_OBJECT_NAMES:
        obj = factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(
                f"attack sword down v19 pass07 weapon object is missing: {object_name}"
            )
        points, edges = v19_base._object_screen_geometry(
            obj,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
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
        raise RuntimeError("attack sword down v19 pass07 could not evaluate clearance")
    return clearance


def _weapon_camera_margin(objects: tuple[object, ...]) -> float:
    points: list[tuple[float, float]] = []
    for obj in objects:
        object_points, _edges = v19_base._object_screen_geometry(
            obj,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
        )
        points.extend(object_points)
    if not points:
        raise RuntimeError("attack sword down v19 pass07 weapon geometry is empty")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(
        min(xs),
        min(ys),
        CANVAS_WIDTH - max(xs),
        CANVAS_HEIGHT - max(ys),
    )


def _apply_clearance_planned_weapon_projection(
) -> tuple[dict[str, Matrix], float, float]:
    objects = previous_adapter._weapon_objects()
    grip = factory.bpy.data.objects.get("combat_twohand_high_v06_grip")
    if grip is None:
        raise RuntimeError("attack sword down v19 pass07 grip object is missing")

    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = previous_adapter._weapon_world_direction()
    screen_x, screen_y, camera_forward = previous_adapter._camera_axes()
    current_x = current_direction.dot(screen_x)
    current_y = current_direction.dot(screen_y)
    current_projection = math.hypot(current_x, current_y)
    if current_projection <= 1.0e-6:
        raise RuntimeError("attack sword down v19 pass07 source projection is degenerate")
    current_angle = math.atan2(current_y, current_x)
    depth_magnitude = math.sqrt(
        max(0.0, 1.0 - WEAPON_SCREEN_PROJECTION_MAGNITUDE ** 2)
    )
    pivot = grip.matrix_world.translation.copy()

    candidates: list[dict[str, float | Vector]] = []
    for offset_degrees in range(
        -ANGLE_SEARCH_LIMIT_DEGREES,
        ANGLE_SEARCH_LIMIT_DEGREES + 1,
        ANGLE_SEARCH_STEP_DEGREES,
    ):
        candidate_angle = current_angle + math.radians(offset_degrees)
        candidate_x = math.cos(candidate_angle)
        candidate_y = math.sin(candidate_angle)
        if candidate_x >= -0.05:
            continue
        if candidate_y <= -0.35:
            continue
        target_direction = (
            screen_x * (candidate_x * WEAPON_SCREEN_PROJECTION_MAGNITUDE)
            + screen_y * (candidate_y * WEAPON_SCREEN_PROJECTION_MAGNITUDE)
            + camera_forward * depth_magnitude
        ).normalized()
        _apply_world_rotation(
            objects,
            pivot=pivot,
            current_direction=current_direction,
            target_direction=target_direction,
        )
        try:
            clearance = _actual_weapon_head_clearance()
            margin = _weapon_camera_margin(objects)
        finally:
            previous_adapter._restore_weapon(saved_basis)
        score = (
            clearance * 3.0
            + margin
            - abs(float(offset_degrees)) * 0.03
            + candidate_y * 1.5
        )
        candidates.append(
            {
                "angle": candidate_angle,
                "offset_degrees": float(offset_degrees),
                "clearance": clearance,
                "margin": margin,
                "score": score,
                "target_direction": target_direction,
            }
        )

    valid = [
        candidate
        for candidate in candidates
        if float(candidate["clearance"]) >= TARGET_HEAD_CLEARANCE_PIXELS
        and float(candidate["margin"]) >= MIN_CAMERA_MARGIN_PIXELS
    ]
    if not valid:
        best = max(candidates, key=lambda item: float(item["score"]), default=None)
        if best is None:
            raise RuntimeError("attack sword down v19 pass07 generated no arc candidates")
        raise RuntimeError(
            "attack sword down v19 pass07 found no valid head-safe arc; "
            f"best clearance={float(best['clearance']):.3f}px, "
            f"margin={float(best['margin']):.3f}px, "
            f"offset={float(best['offset_degrees']):.1f}deg"
        )

    chosen = max(valid, key=lambda item: float(item["score"]))
    _apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=chosen["target_direction"],
    )
    transformed_projection = previous_adapter._screen_projection_magnitude(
        previous_adapter._weapon_world_direction()
    )
    scene = factory.bpy.context.scene
    scene["attack_sword_down_v19_pass07_angle_offset_degrees"] = float(
        chosen["offset_degrees"]
    )
    scene["attack_sword_down_v19_pass07_planned_clearance"] = float(
        chosen["clearance"]
    )
    scene["attack_sword_down_v19_pass07_camera_margin"] = float(
        chosen["margin"]
    )
    print(
        "ATTACK_SWORD_DOWN_V19_PASS07_ARC="
        f"offset:{float(chosen['offset_degrees']):.1f}deg;"
        f"clearance:{float(chosen['clearance']):.3f}px;"
        f"margin:{float(chosen['margin']):.3f}px;"
        f"projection:{transformed_projection:.3f}"
    )
    return saved_basis, current_projection, transformed_projection


def _write_manifest_v19_pass07(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS06(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    payload["attack_sword_down_keyposes_v19_pass07"] = {
        "correction_pass": CORRECTION_PASS,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(run_dir / CONTACT_SHEET_NAME),
        "twohand_anticipation_revision": TWOHAND_ANTICIPATION_REVISION,
        "projection_magnitude": WEAPON_SCREEN_PROJECTION_MAGNITUDE,
        "selected_angle_offset_degrees": float(
            scene["attack_sword_down_v19_pass07_angle_offset_degrees"]
        ),
        "planned_head_clearance_pixels": float(
            scene["attack_sword_down_v19_pass07_planned_clearance"]
        ),
        "planned_camera_margin_pixels": float(
            scene["attack_sword_down_v19_pass07_camera_margin"]
        ),
        "angle_search_limit_degrees": ANGLE_SEARCH_LIMIT_DEGREES,
        "angle_search_step_degrees": ANGLE_SEARCH_STEP_DEGREES,
        "target_head_clearance_pixels": TARGET_HEAD_CLEARANCE_PIXELS,
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
            "attack_sword_01_current_stage": "down_keyposes_v19_pass07",
            "attack_sword_01_manual_review_required": True,
            "attack_sword_01_head_safe_arc_planned": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter.WEAPON_SCREEN_PROJECTION_MAGNITUDE = (
        WEAPON_SCREEN_PROJECTION_MAGNITUDE
    )
    previous_adapter._apply_rigid_weapon_depth_projection = (
        _apply_clearance_planned_weapon_projection
    )
    previous_adapter._write_manifest_v19_pass06 = _write_manifest_v19_pass07
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
