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
import blender_sprite_factory_attack_sword_directional_cycle_v21 as base_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass05 as down_pass05
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19 as v19_base
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
from attack_sword_directional_cycle_correction_v21_pass02 import (
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CLEARANCE_FRAMES,
    CORRECTION_PASS,
    DIRECTIONAL_CLEARANCE_REVISION,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_HEAD_CLEARANCE_BY_GRIP,
    MIN_NONKEY_HEAD_CLEARANCE_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_DIRECTIONS,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass02.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
BASE_RENDER_FRAME = down_pass05._render_frame_v20_pass05
BASE_VALIDATE_CLEARANCE = base_adapter._validate_directional_clearance
BASE_WRITE_MANIFEST = base_adapter._write_manifest_v21


def _grip_id_from_animation(animation_id: str) -> str:
    if "_onehand_" in animation_id:
        return "onehand_ready"
    if "_twohand_" in animation_id:
        return "twohand_center_high"
    raise KeyError(
        f"attack sword directional v21 pass02 cannot infer grip: {animation_id}"
    )


def _weapon_world_direction(objects: tuple[object, ...]) -> Vector:
    blade = next(
        (obj for obj in objects if str(obj.name).endswith("_blade")),
        None,
    )
    if blade is None:
        raise RuntimeError(
            "attack sword directional v21 pass02 active blade is missing"
        )
    return (
        blade.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))
    ).normalized()


def _weapon_pivot(objects: tuple[object, ...]) -> Vector:
    grip = next(
        (obj for obj in objects if str(obj.name).endswith("_grip")),
        None,
    )
    if grip is None:
        raise RuntimeError(
            "attack sword directional v21 pass02 active grip is missing"
        )
    return grip.matrix_world.translation.copy()


def _camera_margin(objects: tuple[object, ...]) -> float:
    points: list[tuple[float, float]] = []
    for obj in objects:
        object_points, _edges = v19_base._object_screen_geometry(
            obj,
            width=96,
            height=96,
        )
        points.extend(object_points)
    if not points:
        raise RuntimeError(
            "attack sword directional v21 pass02 weapon projection is empty"
        )
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return min(
        min(xs),
        min(ys),
        96.0 - max(xs),
        96.0 - max(ys),
    )


def _candidate_offsets(
    objects: tuple[object, ...],
    *,
    saved_basis: dict[str, Matrix],
    pivot: Vector,
    current_direction: Vector,
    minimum_clearance: float,
) -> tuple[dict[str, float], ...]:
    offsets: list[float] = [0.0]
    for magnitude in range(
        ANGLE_SEARCH_STEP_DEGREES,
        ANGLE_SEARCH_LIMIT_DEGREES + 1,
        ANGLE_SEARCH_STEP_DEGREES,
    ):
        offsets.extend((float(magnitude), -float(magnitude)))

    candidates: list[dict[str, float]] = []
    for offset_degrees in offsets:
        pass07_adapter._apply_world_rotation(
            objects,
            pivot=pivot,
            current_direction=current_direction,
            target_direction=export_adapter._target_direction(
                current_direction,
                offset_degrees=offset_degrees,
            ),
        )
        try:
            clearance = export_adapter._weapon_head_clearance(objects)
            margin = _camera_margin(objects)
        finally:
            pass06_adapter._restore_weapon(saved_basis)
        if clearance < minimum_clearance:
            continue
        if margin < MIN_CAMERA_MARGIN_PIXELS:
            continue
        candidates.append(
            {
                "offset_degrees": offset_degrees,
                "head_clearance_pixels": clearance,
                "camera_margin_pixels": margin,
            }
        )

    candidates.sort(
        key=lambda item: (
            abs(float(item["offset_degrees"])),
            -float(item["head_clearance_pixels"]),
            -float(item["camera_margin_pixels"]),
            float(item["offset_degrees"]),
        )
    )
    return tuple(candidates)


def _render_frame_v21_pass02(
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
    if direction not in TARGET_DIRECTIONS:
        return BASE_RENDER_FRAME(
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

    grip_id = _grip_id_from_animation(animation_id)
    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    objects = base_adapter._visible_weapon_objects(grip_id, direction)
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = _weapon_world_direction(objects)
    pivot = _weapon_pivot(objects)
    minimum_clearance = (
        MIN_HEAD_CLEARANCE_BY_GRIP[grip_id]
        if frame_number in CLEARANCE_FRAMES
        else MIN_NONKEY_HEAD_CLEARANCE_PIXELS
    )
    candidates = _candidate_offsets(
        objects,
        saved_basis=saved_basis,
        pivot=pivot,
        current_direction=current_direction,
        minimum_clearance=minimum_clearance,
    )
    if not candidates:
        raise RuntimeError(
            f"attack sword directional v21 pass02 found no geometry-safe "
            f"candidate for {grip_id}/{direction}/f{frame_number:02d}"
        )

    diagnostics: list[dict[str, object]] = []
    accepted: tuple[factory.FrameArtifact, factory.FramingCalibration] | None = None
    selected: dict[str, float] | None = None
    selected_edges: dict[str, int] = {}

    for attempt_number, candidate in enumerate(candidates, start=1):
        offset_degrees = float(candidate["offset_degrees"])
        pass07_adapter._apply_world_rotation(
            objects,
            pivot=pivot,
            current_direction=current_direction,
            target_direction=export_adapter._target_direction(
                current_direction,
                offset_degrees=offset_degrees,
            ),
        )
        try:
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
            edge_counts = keypose_adapter._edge_alpha_counts(
                artifact.output_path
            )
            touched = {
                edge: count
                for edge, count in edge_counts.items()
                if count > 0
            }
            diagnostics.append(
                {
                    "attempt": attempt_number,
                    **candidate,
                    "edge_counts": edge_counts,
                    "accepted": not touched,
                }
            )
            print(
                "ATTACK_SWORD_DIRECTIONAL_V21_PASS02_ATTEMPT="
                f"{grip_id}/{direction}/f{frame_number:02d};"
                f"attempt:{attempt_number};"
                f"offset:{offset_degrees:.1f}deg;"
                f"clearance:{float(candidate['head_clearance_pixels']):.3f}px;"
                f"margin:{float(candidate['camera_margin_pixels']):.3f}px;"
                f"edges:{touched}"
            )
            if not touched:
                accepted = (artifact, calibration)
                selected = candidate
                selected_edges = edge_counts
                break
        finally:
            pass06_adapter._restore_weapon(saved_basis)

    if accepted is None or selected is None:
        raise RuntimeError(
            f"attack sword directional v21 pass02 found no export-contained "
            f"candidate for {grip_id}/{direction}/f{frame_number:02d}: "
            f"{diagnostics}"
        )

    key = f"{grip_id}/{direction}/f{frame_number:02d}"
    metrics_raw = str(
        scene.get("attack_sword_directional_cycle_v21_pass02_metrics", "{}")
    )
    metrics = json.loads(metrics_raw)
    metrics[key] = {
        **selected,
        "edge_counts": selected_edges,
        "render_attempts": len(diagnostics),
        "candidate_diagnostics": diagnostics,
    }
    scene["attack_sword_directional_cycle_v21_pass02_metrics"] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_DIRECTIONAL_V21_PASS02_SELECTED="
        f"{key};"
        f"offset:{float(selected['offset_degrees']):.1f}deg;"
        f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
        f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
        f"attempts:{len(diagnostics)}"
    )
    return accepted


def _validate_directional_clearance_v21_pass02(
    context: factory.BuildContext,
    *,
    action_id: str,
    grip_id: str,
    weapon_cycle_id: str,
    direction: str,
) -> dict[int, float]:
    if direction not in TARGET_DIRECTIONS:
        return BASE_VALIDATE_CLEARANCE(
            context,
            action_id=action_id,
            grip_id=grip_id,
            weapon_cycle_id=weapon_cycle_id,
            direction=direction,
        )
    metrics = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_directional_cycle_v21_pass02_metrics"
            ]
        )
    )
    clearances: dict[int, float] = {}
    for frame_number in CLEARANCE_FRAMES:
        key = f"{grip_id}/{direction}/f{frame_number:02d}"
        if key not in metrics:
            raise RuntimeError(
                f"attack sword directional v21 pass02 missing metrics: {key}"
            )
        clearance = float(metrics[key]["head_clearance_pixels"])
        minimum = MIN_HEAD_CLEARANCE_BY_GRIP[grip_id]
        if clearance < minimum:
            raise RuntimeError(
                f"attack sword directional v21 pass02 clearance drifted: "
                f"{key}={clearance:.3f}px"
            )
        clearances[frame_number] = clearance
    return clearances


def _write_manifest_v21_pass02(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    metrics = json.loads(
        str(scene["attack_sword_directional_cycle_v21_pass02_metrics"])
    )
    payload["attack_sword_directional_cycle_v21_pass02"] = {
        "correction_pass": CORRECTION_PASS,
        "directional_clearance_revision": DIRECTIONAL_CLEARANCE_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(
            run_dir / CONTACT_SHEET_NAME
        ),
        "target_directions": list(TARGET_DIRECTIONS),
        "clearance_frames": list(CLEARANCE_FRAMES),
        "angle_search_limit_degrees": ANGLE_SEARCH_LIMIT_DEGREES,
        "angle_search_step_degrees": ANGLE_SEARCH_STEP_DEGREES,
        "minimum_camera_margin_pixels": MIN_CAMERA_MARGIN_PIXELS,
        "minimum_head_clearance_by_grip": MIN_HEAD_CLEARANCE_BY_GRIP,
        "minimum_nonkey_head_clearance_pixels": (
            MIN_NONKEY_HEAD_CLEARANCE_PIXELS
        ),
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "selected_metrics": metrics,
        "rigid_weapon_transform_only": True,
        "body_pose_changed": False,
        "approved_down_v20_changed": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_directional_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": (
                "directional_full_cycle_v21_pass02"
            ),
            "attack_sword_01_directional_export_planner_enabled": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    down_pass05._render_frame_v20_pass05 = _render_frame_v21_pass02
    base_adapter._validate_directional_clearance = (
        _validate_directional_clearance_v21_pass02
    )
    base_adapter._write_manifest_v21 = _write_manifest_v21_pass02
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
