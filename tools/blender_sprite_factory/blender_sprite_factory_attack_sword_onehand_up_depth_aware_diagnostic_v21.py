from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from bpy_extras.object_utils import world_to_camera_view

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_down_keyposes_v19 as v19_base
import blender_sprite_factory_attack_sword_onehand_up_visible_blade_diagnostic_v21 as pass21_adapter
from attack_sword_directional_cycle_correction_v21_pass22 import (
    ALLOW_BLADE_OCCLUSION_BEHIND_HEAD,
    BLADE_CLEARANCE_PART_IDS,
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DEPTH_EPSILON_WORLD,
    DEPTH_MAP_SUPERSAMPLE,
    DIAGNOSTIC_SCENE_KEY,
    HEAD_MODULE_IDS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    WEAPON_EDGE_SAMPLE_STEP_PIXELS,
)


ORIGINAL_PASS21_CLEARANCE = pass21_adapter._visible_blade_head_clearance
ORIGINAL_PASS21_WRITE_MANIFEST = pass21_adapter._write_manifest_pass21
ORIGINAL_PASS21_SCENE_KEY = pass21_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS21_CONTACT_SHEET = pass21_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS21_REVISION = pass21_adapter.ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION
ORIGINAL_PASS21_MIN_CLEARANCE = pass21_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
ORIGINAL_PASS21_REQUIRE_ZERO_EDGE_ALPHA = pass21_adapter.REQUIRE_ZERO_EDGE_ALPHA

_HEAD_DEPTH_CACHE: dict[tuple[object, ...], dict[str, object]] = {}


def _head_objects() -> tuple[object, ...]:
    objects = tuple(
        obj
        for obj in factory.bpy.data.objects
        if getattr(obj, "type", "") == "MESH"
        and obj.get(factory.MODULE_PROPERTY) in HEAD_MODULE_IDS
    )
    if not objects:
        raise RuntimeError("one-hand up depth-aware diagnostic has no head/hair meshes")
    return objects


def _head_cache_key(objects: tuple[object, ...]) -> tuple[object, ...]:
    scene = factory.bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("one-hand up depth-aware diagnostic camera is missing")
    matrices: list[float] = []
    for obj in objects:
        matrices.extend(round(float(value), 6) for row in obj.matrix_world for value in row)
    return (
        int(scene.frame_current),
        int(camera.as_pointer()),
        tuple(obj.name for obj in objects),
        tuple(matrices),
    )


def _barycentric_weights(
    point_x: float,
    point_y: float,
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    third: tuple[float, float, float],
) -> tuple[float, float, float] | None:
    denominator = (
        (second[1] - third[1]) * (first[0] - third[0])
        + (third[0] - second[0]) * (first[1] - third[1])
    )
    if abs(denominator) <= 1.0e-10:
        return None
    first_weight = (
        (second[1] - third[1]) * (point_x - third[0])
        + (third[0] - second[0]) * (point_y - third[1])
    ) / denominator
    second_weight = (
        (third[1] - first[1]) * (point_x - third[0])
        + (first[0] - third[0]) * (point_y - third[1])
    ) / denominator
    third_weight = 1.0 - first_weight - second_weight
    epsilon = 1.0e-7
    if (
        first_weight < -epsilon
        or second_weight < -epsilon
        or third_weight < -epsilon
    ):
        return None
    return first_weight, second_weight, third_weight


def _build_head_depth_field() -> dict[str, object]:
    scene = factory.bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("one-hand up depth-aware diagnostic camera is missing")
    objects = _head_objects()
    cache_key = _head_cache_key(objects)
    cached = _HEAD_DEPTH_CACHE.get(cache_key)
    if cached is not None:
        return cached

    width = 96
    height = 96
    supersample = int(DEPTH_MAP_SUPERSAMPLE)
    raster_width = width * supersample
    raster_height = height * supersample
    camera_inverse = camera.matrix_world.inverted()
    depsgraph = factory.bpy.context.evaluated_depsgraph_get()
    depth_by_cell: dict[tuple[int, int], float] = {}
    projected_points: list[tuple[float, float]] = []
    triangle_count = 0

    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices: list[tuple[float, float, float]] = []
            for vertex in mesh.vertices:
                world_point = evaluated.matrix_world @ vertex.co
                projected = world_to_camera_view(scene, camera, world_point)
                screen_x = float(projected.x) * width
                screen_y = (1.0 - float(projected.y)) * height
                camera_z = float((camera_inverse @ world_point).z)
                vertices.append((screen_x, screen_y, camera_z))
                projected_points.append((screen_x, screen_y))

            for triangle in mesh.loop_triangles:
                first = vertices[int(triangle.vertices[0])]
                second = vertices[int(triangle.vertices[1])]
                third = vertices[int(triangle.vertices[2])]
                scaled = tuple(
                    (
                        point[0] * supersample,
                        point[1] * supersample,
                        point[2],
                    )
                    for point in (first, second, third)
                )
                minimum_x = max(
                    0,
                    int(math.floor(min(point[0] for point in scaled))),
                )
                maximum_x = min(
                    raster_width - 1,
                    int(math.ceil(max(point[0] for point in scaled))),
                )
                minimum_y = max(
                    0,
                    int(math.floor(min(point[1] for point in scaled))),
                )
                maximum_y = min(
                    raster_height - 1,
                    int(math.ceil(max(point[1] for point in scaled))),
                )
                if minimum_x > maximum_x or minimum_y > maximum_y:
                    continue
                triangle_count += 1
                for cell_y in range(minimum_y, maximum_y + 1):
                    sample_y = float(cell_y) + 0.5
                    for cell_x in range(minimum_x, maximum_x + 1):
                        sample_x = float(cell_x) + 0.5
                        weights = _barycentric_weights(
                            sample_x,
                            sample_y,
                            scaled[0],
                            scaled[1],
                            scaled[2],
                        )
                        if weights is None:
                            continue
                        camera_z = (
                            weights[0] * scaled[0][2]
                            + weights[1] * scaled[1][2]
                            + weights[2] * scaled[2][2]
                        )
                        key = (cell_x, cell_y)
                        previous = depth_by_cell.get(key)
                        if previous is None or camera_z > previous:
                            depth_by_cell[key] = camera_z
        finally:
            evaluated.to_mesh_clear()

    if not projected_points or not depth_by_cell:
        raise RuntimeError(
            "one-hand up depth-aware diagnostic could not rasterize head depth"
        )
    xs = [point[0] for point in projected_points]
    ys = [point[1] for point in projected_points]
    result: dict[str, object] = {
        "bbox": (min(xs), min(ys), max(xs), max(ys)),
        "depth_by_cell": depth_by_cell,
        "supersample": supersample,
        "triangle_count": triangle_count,
        "covered_cells": len(depth_by_cell),
    }
    _HEAD_DEPTH_CACHE[cache_key] = result
    return result


def _point_rect_distance(
    point_x: float,
    point_y: float,
    rect: tuple[float, float, float, float],
) -> float:
    left, top, right, bottom = rect
    horizontal = max(left - point_x, 0.0, point_x - right)
    vertical = max(top - point_y, 0.0, point_y - bottom)
    return math.hypot(horizontal, vertical)


def _head_depth_at(
    field: dict[str, object],
    screen_x: float,
    screen_y: float,
) -> float | None:
    supersample = int(field["supersample"])
    cell_x = int(math.floor(screen_x * supersample))
    cell_y = int(math.floor(screen_y * supersample))
    depth_by_cell = field["depth_by_cell"]
    if not isinstance(depth_by_cell, dict):
        raise RuntimeError("one-hand up depth-aware diagnostic depth field is invalid")
    value = depth_by_cell.get((cell_x, cell_y))
    return None if value is None else float(value)


def _record_depth_metrics(
    *,
    clearance: float,
    occluded_samples: int,
    visible_samples: int,
    minimum_occluded_depth_gap: float | None,
    field: dict[str, object],
) -> None:
    scene = factory.bpy.context.scene
    scene["attack_sword_onehand_up_pass22_clearance"] = float(clearance)
    scene["attack_sword_onehand_up_pass22_occluded_samples"] = int(
        occluded_samples
    )
    scene["attack_sword_onehand_up_pass22_visible_samples"] = int(visible_samples)
    scene["attack_sword_onehand_up_pass22_minimum_occluded_depth_gap"] = (
        -1.0
        if minimum_occluded_depth_gap is None
        else float(minimum_occluded_depth_gap)
    )
    scene["attack_sword_onehand_up_pass22_head_triangles"] = int(
        field["triangle_count"]
    )
    scene["attack_sword_onehand_up_pass22_head_depth_cells"] = int(
        field["covered_cells"]
    )


def _depth_aware_visible_blade_head_clearance(
    objects: tuple[object, ...],
) -> float:
    by_part = pass21_adapter._objects_by_weapon_part(objects)
    blade_objects = tuple(by_part[part] for part in BLADE_CLEARANCE_PART_IDS)
    field = _build_head_depth_field()
    head_bbox = field["bbox"]
    if not isinstance(head_bbox, tuple) or len(head_bbox) != 4:
        raise RuntimeError("one-hand up depth-aware diagnostic head bbox is invalid")

    scene = factory.bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("one-hand up depth-aware diagnostic camera is missing")
    camera_inverse = camera.matrix_world.inverted()
    depsgraph = factory.bpy.context.evaluated_depsgraph_get()
    minimum_clearance = float("inf")
    occluded_samples = 0
    visible_samples = 0
    minimum_occluded_depth_gap: float | None = None
    found = False

    for obj in blade_objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points: list[tuple[float, float, float]] = []
            for vertex in mesh.vertices:
                world_point = evaluated.matrix_world @ vertex.co
                projected = world_to_camera_view(scene, camera, world_point)
                points.append(
                    (
                        float(projected.x) * 96.0,
                        (1.0 - float(projected.y)) * 96.0,
                        float((camera_inverse @ world_point).z),
                    )
                )

            for edge in mesh.edges:
                first = points[int(edge.vertices[0])]
                second = points[int(edge.vertices[1])]
                projected_length = math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                sample_segments = max(
                    1,
                    int(
                        math.ceil(
                            projected_length / WEAPON_EDGE_SAMPLE_STEP_PIXELS
                        )
                    ),
                )
                for sample_index in range(sample_segments + 1):
                    found = True
                    blend = float(sample_index) / float(sample_segments)
                    screen_x = first[0] + (second[0] - first[0]) * blend
                    screen_y = first[1] + (second[1] - first[1]) * blend
                    camera_z = first[2] + (second[2] - first[2]) * blend
                    clearance = _point_rect_distance(
                        screen_x,
                        screen_y,
                        head_bbox,
                    )
                    if clearance <= 1.0e-7:
                        head_depth = _head_depth_at(field, screen_x, screen_y)
                        if (
                            head_depth is not None
                            and camera_z <= head_depth - DEPTH_EPSILON_WORLD
                        ):
                            occluded_samples += 1
                            depth_gap = head_depth - camera_z
                            minimum_occluded_depth_gap = (
                                depth_gap
                                if minimum_occluded_depth_gap is None
                                else min(minimum_occluded_depth_gap, depth_gap)
                            )
                            continue
                    visible_samples += 1
                    minimum_clearance = min(minimum_clearance, clearance)
                    if minimum_clearance <= 1.0e-7:
                        _record_depth_metrics(
                            clearance=0.0,
                            occluded_samples=occluded_samples,
                            visible_samples=visible_samples,
                            minimum_occluded_depth_gap=minimum_occluded_depth_gap,
                            field=field,
                        )
                        return 0.0
        finally:
            evaluated.to_mesh_clear()

    if not found or not math.isfinite(minimum_clearance):
        raise RuntimeError(
            "one-hand up depth-aware diagnostic could not evaluate blade clearance"
        )
    _record_depth_metrics(
        clearance=minimum_clearance,
        occluded_samples=occluded_samples,
        visible_samples=visible_samples,
        minimum_occluded_depth_gap=minimum_occluded_depth_gap,
        field=field,
    )
    return float(minimum_clearance)


def _write_manifest_pass22(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS21_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    payload["attack_sword_directional_cycle_v21_pass22"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION,
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "head_module_ids": list(HEAD_MODULE_IDS),
        "collision_weapon_part_ids": list(BLADE_CLEARANCE_PART_IDS),
        "minimum_visible_blade_head_clearance_pixels": (
            MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
        ),
        "depth_map_supersample": DEPTH_MAP_SUPERSAMPLE,
        "weapon_edge_sample_step_pixels": WEAPON_EDGE_SAMPLE_STEP_PIXELS,
        "depth_epsilon_world": DEPTH_EPSILON_WORLD,
        "allow_blade_occlusion_behind_head": (
            ALLOW_BLADE_OCCLUSION_BEHIND_HEAD
        ),
        "require_zero_edge_alpha": REQUIRE_ZERO_EDGE_ALPHA,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "selected_clearance_pixels": float(
            scene.get("attack_sword_onehand_up_pass22_clearance", -1.0)
        ),
        "selected_occluded_samples": int(
            scene.get("attack_sword_onehand_up_pass22_occluded_samples", 0)
        ),
        "selected_visible_samples": int(
            scene.get("attack_sword_onehand_up_pass22_visible_samples", 0)
        ),
        "minimum_occluded_depth_gap": float(
            scene.get(
                "attack_sword_onehand_up_pass22_minimum_occluded_depth_gap",
                -1.0,
            )
        ),
        "head_triangle_count": int(
            scene.get("attack_sword_onehand_up_pass22_head_triangles", 0)
        ),
        "head_depth_cell_count": int(
            scene.get("attack_sword_onehand_up_pass22_head_depth_cells", 0)
        ),
        "weapon_parts_removed_from_render": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "weapon_scale_changed": False,
        "materials_changed": False,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    pass21_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass21_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass21_adapter.ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION = (
        ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION
    )
    pass21_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
        MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
    )
    pass21_adapter.REQUIRE_ZERO_EDGE_ALPHA = REQUIRE_ZERO_EDGE_ALPHA
    pass21_adapter._visible_blade_head_clearance = (
        _depth_aware_visible_blade_head_clearance
    )
    pass21_adapter._write_manifest_pass21 = _write_manifest_pass22
    try:
        return pass21_adapter.main()
    finally:
        pass21_adapter._visible_blade_head_clearance = ORIGINAL_PASS21_CLEARANCE
        pass21_adapter._write_manifest_pass21 = ORIGINAL_PASS21_WRITE_MANIFEST
        pass21_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS21_SCENE_KEY
        pass21_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS21_CONTACT_SHEET
        pass21_adapter.ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION = (
            ORIGINAL_PASS21_REVISION
        )
        pass21_adapter.MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS = (
            ORIGINAL_PASS21_MIN_CLEARANCE
        )
        pass21_adapter.REQUIRE_ZERO_EDGE_ALPHA = (
            ORIGINAL_PASS21_REQUIRE_ZERO_EDGE_ALPHA
        )


if __name__ == "__main__":
    raise SystemExit(main())
