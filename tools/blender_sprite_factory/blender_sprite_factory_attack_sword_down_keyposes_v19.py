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

from bpy_extras.object_utils import world_to_camera_view

import attack_sword_down_keyposes_builder_v17 as action_builder
import blender_sprite_factory_attack_sword_down_keyposes_v17 as base_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
from attack_sword_down_keyposes_correction_v19 import (
    CORRECTION_REVISION,
    MIN_TWOHAND_HEAD_CLEARANCE_PIXELS,
    ONEHAND_TRAJECTORY_REVISION,
    TWOHAND_TRAJECTORY_REVISION,
    load_attack_sword_down_keyposes_profile_v19,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_correction_v19.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"
MAX_APPROVED_GUARD_EDGE_PIXELS = 12
TWOHAND_WEAPON_OBJECT_NAMES = (
    "combat_twohand_high_v06_blade",
    "combat_twohand_high_v06_highlight",
    "combat_twohand_high_v06_tip",
)
CLEARANCE_FRAMES = (2, 3)
BASE_RENDER_V17 = base_adapter.render_attack_sword_down_keyposes_v17
BASE_WRITE_MANIFEST_V17 = base_adapter._write_manifest_v17
BASE_ASSERT_BOUNDARY_V17 = base_adapter._assert_boundary_contract


def _assert_boundary_v19(
    artifact: object,
    *,
    grip_id: str,
) -> None:
    if grip_id != "onehand_ready" or artifact.frame_number not in (1, 5):
        BASE_ASSERT_BOUNDARY_V17(artifact, grip_id=grip_id)
        return
    counts = base_adapter._edge_alpha_counts(artifact.output_path)
    forbidden = {
        edge: count
        for edge, count in counts.items()
        if edge != "left" and count > 0
    }
    if forbidden:
        raise RuntimeError(
            "attack sword down v19 one-hand guard-family frame touches "
            f"forbidden boundaries: f{artifact.frame_number:02d}={forbidden}"
        )
    if counts["left"] > MAX_APPROVED_GUARD_EDGE_PIXELS:
        raise RuntimeError(
            "attack sword down v19 one-hand guard-family frame exceeds "
            f"approved left-edge budget: f{artifact.frame_number:02d}="
            f"{counts['left']}"
        )


def _project_point(
    scene: object,
    camera: object,
    world_point: object,
    width: int,
    height: int,
) -> tuple[float, float]:
    projected = world_to_camera_view(scene, camera, world_point)
    return (float(projected.x) * width, (1.0 - float(projected.y)) * height)


def _object_screen_geometry(
    obj: object,
    *,
    width: int,
    height: int,
) -> tuple[list[tuple[float, float]], list[tuple[int, int]]]:
    scene = base_adapter.factory.bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("attack sword down v19 camera is missing")
    depsgraph = base_adapter.factory.bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        points = [
            _project_point(
                scene,
                camera,
                evaluated.matrix_world @ vertex.co,
                width,
                height,
            )
            for vertex in mesh.vertices
        ]
        edges = [(int(edge.vertices[0]), int(edge.vertices[1])) for edge in mesh.edges]
        return points, edges
    finally:
        evaluated.to_mesh_clear()


def _head_screen_bbox(
    *,
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    points: list[tuple[float, float]] = []
    for obj in base_adapter.factory.bpy.data.objects:
        if getattr(obj, "type", "") != "MESH":
            continue
        if obj.get(base_adapter.factory.MODULE_PROPERTY) not in ("head", "hair"):
            continue
        object_points, _object_edges = _object_screen_geometry(
            obj,
            width=width,
            height=height,
        )
        points.extend(object_points)
    if not points:
        raise RuntimeError("attack sword down v19 head/hair geometry is missing")
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    length_squared = dx * dx + dy * dy
    if length_squared <= 1.0e-9:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_squared))
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return math.hypot(px - closest_x, py - closest_y)


def _orientation(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    epsilon = 1.0e-7
    if ((o1 > epsilon and o2 < -epsilon) or (o1 < -epsilon and o2 > epsilon)) and (
        (o3 > epsilon and o4 < -epsilon) or (o3 < -epsilon and o4 > epsilon)
    ):
        return True
    return False


def _segment_distance(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> float:
    if _segments_intersect(a, b, c, d):
        return 0.0
    return min(
        _point_segment_distance(a, c, d),
        _point_segment_distance(b, c, d),
        _point_segment_distance(c, a, b),
        _point_segment_distance(d, a, b),
    )


def _segment_rect_distance(
    start: tuple[float, float],
    end: tuple[float, float],
    rect: tuple[float, float, float, float],
) -> float:
    left, top, right, bottom = rect
    if (
        left <= start[0] <= right
        and top <= start[1] <= bottom
    ) or (
        left <= end[0] <= right
        and top <= end[1] <= bottom
    ):
        return 0.0
    corners = (
        (left, top),
        (right, top),
        (right, bottom),
        (left, bottom),
    )
    edges = tuple(zip(corners, corners[1:] + corners[:1]))
    return min(_segment_distance(start, end, edge_start, edge_end) for edge_start, edge_end in edges)


def _twohand_head_clearance_pixels(context: object) -> float:
    width = int(context.config.technical.canvas_width)
    height = int(context.config.technical.canvas_height)
    head_bbox = _head_screen_bbox(width=width, height=height)
    clearance = float("inf")
    found = False
    for object_name in TWOHAND_WEAPON_OBJECT_NAMES:
        obj = base_adapter.factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(f"attack sword down v19 weapon object is missing: {object_name}")
        points, edges = _object_screen_geometry(obj, width=width, height=height)
        for first_index, second_index in edges:
            found = True
            clearance = min(
                clearance,
                _segment_rect_distance(
                    points[first_index],
                    points[second_index],
                    head_bbox,
                ),
            )
    if not found or not math.isfinite(clearance):
        raise RuntimeError("attack sword down v19 could not evaluate sword/head clearance")
    return clearance


def _validate_twohand_head_clearance(context: object) -> dict[int, float]:
    config = context.config
    profile = load_attack_sword_down_keyposes_profile_v19(config.character_id)
    twohand = profile.grips[1]
    action = base_adapter.factory.bpy.data.actions.get(
        f"{config.character_id}_{twohand.action_id}"
    )
    if action is None:
        raise RuntimeError("attack sword down v19 two-hand action is missing")
    idle_action = base_adapter.factory.bpy.data.actions[f"{config.character_id}_idle"]
    clearances: dict[int, float] = {}
    try:
        weapon_adapter._set_v12_weapon(twohand.weapon_cycle_id, "down")
        base_adapter.factory._assign_action(context.rig, action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        for frame_number in CLEARANCE_FRAMES:
            base_adapter.factory.bpy.context.scene.frame_set(frame_number)
            base_adapter.factory.bpy.context.view_layer.update()
            clearance = _twohand_head_clearance_pixels(context)
            clearances[frame_number] = clearance
            print(
                "ATTACK_SWORD_DOWN_V19_HEAD_CLEARANCE="
                f"f{frame_number:02d}:{clearance:.3f}px"
            )
            if clearance < MIN_TWOHAND_HEAD_CLEARANCE_PIXELS:
                raise RuntimeError(
                    "attack sword down v19 two-hand blade enters the projected head "
                    f"clearance zone: f{frame_number:02d}={clearance:.3f}px, "
                    f"required={MIN_TWOHAND_HEAD_CLEARANCE_PIXELS:.3f}px"
                )
    finally:
        weapon_adapter._set_v12_weapon(None, None)
        base_adapter.factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        base_adapter.factory.bpy.context.scene.frame_set(1)
        base_adapter.factory.bpy.context.view_layer.update()
    return clearances


def _render_keyposes_v19(
    context: object,
    run_dir: Path,
) -> list[object]:
    artifacts = BASE_RENDER_V17(context, run_dir)
    clearances = _validate_twohand_head_clearance(context)
    scene = base_adapter.factory.bpy.context.scene
    for frame_number, clearance in clearances.items():
        scene[f"attack_sword_down_v19_head_clearance_f{frame_number:02d}"] = clearance
    scene["attack_sword_down_v19_head_clearance_passed"] = True
    return artifacts


def _write_manifest_v19(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_V17(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("attack sword down v19 contact sheet is missing")
    clearance_payload = {
        f"f{frame_number:02d}": float(
            base_adapter.factory.bpy.context.scene[
                f"attack_sword_down_v19_head_clearance_f{frame_number:02d}"
            ]
        )
        for frame_number in CLEARANCE_FRAMES
    }
    payload["attack_sword_down_keyposes_correction_v19"] = {
        "correction_revision": CORRECTION_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "onehand_trajectory_revision": ONEHAND_TRAJECTORY_REVISION,
        "twohand_trajectory_revision": TWOHAND_TRAJECTORY_REVISION,
        "twohand_head_clearance_pixels": clearance_payload,
        "twohand_head_clearance_required_pixels": MIN_TWOHAND_HEAD_CLEARANCE_PIXELS,
        "twohand_head_clearance_frames": list(CLEARANCE_FRAMES),
        "onehand_guard_family_left_edge_frames": [1, 5],
        "onehand_guard_family_left_edge_budget_pixels": MAX_APPROVED_GUARD_EDGE_PIXELS,
        "source_v17_and_v18_preserved": True,
        "animation_action_ids_changed": False,
        "weapon_geometry_changed": False,
        "materials_changed": False,
        "approved_guard_frames_changed": False,
        "manual_keypose_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_keyposes_correction_v19",
            "attack_sword_01_keypose_count": 10,
            "attack_sword_01_manual_review_required": True,
            "attack_sword_01_twohand_head_clearance_checked": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    action_builder.load_attack_sword_down_keyposes_profile_v17 = (
        load_attack_sword_down_keyposes_profile_v19
    )
    base_adapter.load_attack_sword_down_keyposes_profile_v17 = (
        load_attack_sword_down_keyposes_profile_v19
    )
    base_adapter.PROFILE_PATH = CORRECTION_PATH
    base_adapter.SCRIPT_PATH = SCRIPT_PATH
    base_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    base_adapter._assert_boundary_contract = _assert_boundary_v19
    base_adapter.render_attack_sword_down_keyposes_v17 = _render_keyposes_v19
    base_adapter._write_manifest_v17 = _write_manifest_v19
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
