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

from mathutils import Vector

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21 as base_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass02 as pass02_adapter
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass26 as pass26_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_attack_sword_onehand_up_depth_aware_diagnostic_v21 as depth_aware_adapter
from attack_sword_directional_cycle_correction_v21_pass27 import (
    ALLOW_BLADE_OCCLUSION_BEHIND_HEAD,
    CORRECTION_PASS,
    MAX_RENDER_ATTEMPTS,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    PREFER_HIGH_SCREEN_PROJECTION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SEARCH_DEPTH_BRANCHES,
    SEARCH_OFFSET_LIMIT_DEGREES,
    SEARCH_OFFSET_STEP_DEGREES,
    SEARCH_SCREEN_PROJECTIONS,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_SOLVER_REVISION,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass27.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
BASE_RENDER_FRAME_PASS26 = pass26_adapter._render_frame_v21_pass26
BASE_WRITE_MANIFEST_PASS26 = pass26_adapter._write_manifest_v21_pass26


def _is_target_frame(
    animation_id: str,
    direction: str,
    frame_number: int,
) -> bool:
    return (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number in TARGET_FRAMES
    )


def _candidate_offsets() -> tuple[float, ...]:
    offsets: list[float] = [0.0]
    for magnitude in range(
        SEARCH_OFFSET_STEP_DEGREES,
        SEARCH_OFFSET_LIMIT_DEGREES + 1,
        SEARCH_OFFSET_STEP_DEGREES,
    ):
        offsets.extend((float(magnitude), -float(magnitude)))
    return tuple(offsets)


def _target_direction_v21_pass27(
    current_direction: Vector,
    *,
    requested_projection: float,
    offset_degrees: float,
    depth_branch: str,
) -> tuple[Vector, float, float]:
    screen_x, screen_y, camera_forward = pass06_adapter._camera_axes()
    current_x = float(current_direction.dot(screen_x))
    current_y = float(current_direction.dot(screen_y))
    current_depth = float(current_direction.dot(camera_forward))
    source_projection = math.hypot(current_x, current_y)
    if source_projection <= 1.0e-6:
        raise RuntimeError(
            "attack sword directional v21 pass27 source projection is degenerate"
        )

    applied_projection = min(source_projection, float(requested_projection))
    if applied_projection <= 1.0e-6 or applied_projection >= 1.0:
        raise RuntimeError(
            "attack sword directional v21 pass27 projection is invalid: "
            f"{applied_projection:.6f}"
        )

    angle = math.atan2(current_y, current_x) + math.radians(offset_degrees)
    source_depth_sign = 1.0 if current_depth >= 0.0 else -1.0
    if depth_branch == "source":
        target_depth_sign = source_depth_sign
    elif depth_branch == "flipped":
        target_depth_sign = -source_depth_sign
    else:
        raise KeyError(
            "attack sword directional v21 pass27 unknown depth branch: "
            f"{depth_branch}"
        )

    depth_magnitude = math.sqrt(max(0.0, 1.0 - applied_projection**2))
    target_direction = (
        screen_x * (math.cos(angle) * applied_projection)
        + screen_y * (math.sin(angle) * applied_projection)
        + camera_forward * (target_depth_sign * depth_magnitude)
    ).normalized()
    return target_direction, source_projection, applied_projection


def _geometry_candidates(
    objects: tuple[object, ...],
    *,
    saved_basis: dict[str, object],
    pivot: Vector,
    current_direction: Vector,
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    candidates: list[dict[str, object]] = []
    evaluated: list[dict[str, object]] = []
    applied_projection_keys: set[float] = set()
    screen_x, screen_y, _camera_forward = pass06_adapter._camera_axes()
    source_projection = math.hypot(
        float(current_direction.dot(screen_x)),
        float(current_direction.dot(screen_y)),
    )

    for requested_projection in SEARCH_SCREEN_PROJECTIONS:
        applied_projection = min(source_projection, float(requested_projection))
        projection_key = round(float(applied_projection), 6)
        if projection_key in applied_projection_keys:
            continue
        applied_projection_keys.add(projection_key)

        for depth_branch in SEARCH_DEPTH_BRANCHES:
            for offset_degrees in _candidate_offsets():
                target_direction, resolved_source_projection, resolved_projection = (
                    _target_direction_v21_pass27(
                        current_direction,
                        requested_projection=float(requested_projection),
                        offset_degrees=float(offset_degrees),
                        depth_branch=depth_branch,
                    )
                )
                pass07_adapter._apply_world_rotation(
                    objects,
                    pivot=pivot,
                    current_direction=current_direction,
                    target_direction=target_direction,
                )
                try:
                    clearance = float(
                        depth_aware_adapter
                        ._depth_aware_visible_blade_head_clearance(objects)
                    )
                    margin = float(pass02_adapter._camera_margin(objects))
                finally:
                    pass06_adapter._restore_weapon(saved_basis)

                metric: dict[str, object] = {
                    "depth_branch": depth_branch,
                    "offset_degrees": float(offset_degrees),
                    "source_projection": float(resolved_source_projection),
                    "requested_screen_projection": float(requested_projection),
                    "screen_projection": float(resolved_projection),
                    "head_clearance_pixels": float(clearance),
                    "camera_margin_pixels": float(margin),
                }
                evaluated.append(metric)
                if clearance < MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS:
                    continue
                if margin < MIN_CAMERA_MARGIN_PIXELS:
                    continue
                candidates.append(metric)

    candidates.sort(
        key=lambda item: (
            -float(item["screen_projection"]),
            abs(float(item["offset_degrees"])),
            0 if item["depth_branch"] == "source" else 1,
            -float(item["head_clearance_pixels"]),
            -float(item["camera_margin_pixels"]),
            float(item["offset_degrees"]),
        )
    )
    evaluated.sort(
        key=lambda item: (
            -float(item["head_clearance_pixels"]),
            -float(item["camera_margin_pixels"]),
            -float(item["screen_projection"]),
            abs(float(item["offset_degrees"])),
        )
    )
    return tuple(candidates), tuple(evaluated[:16])


def _render_frame_v21_pass27(
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
    if not _is_target_frame(animation_id, direction, frame_number):
        return BASE_RENDER_FRAME_PASS26(
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
    objects = base_adapter._visible_weapon_objects(TARGET_GRIP_ID, direction)
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = pass02_adapter._weapon_world_direction(objects)
    pivot = pass02_adapter._weapon_pivot(objects)
    candidates, best_rejected = _geometry_candidates(
        objects,
        saved_basis=saved_basis,
        pivot=pivot,
        current_direction=current_direction,
    )
    if not candidates:
        raise RuntimeError(
            "attack sword directional v21 pass27 found no depth-aware "
            f"geometry-safe candidate for {TARGET_GRIP_ID}/{direction}/"
            f"f{frame_number:02d}; best={best_rejected}"
        )

    diagnostics: list[dict[str, object]] = []
    accepted: tuple[factory.FrameArtifact, factory.FramingCalibration] | None = None
    selected: dict[str, object] | None = None
    selected_edges: dict[str, int] = {}

    for attempt_number, candidate in enumerate(
        candidates[:MAX_RENDER_ATTEMPTS],
        start=1,
    ):
        target_direction, _source_projection, _applied_projection = (
            _target_direction_v21_pass27(
                current_direction,
                requested_projection=float(
                    candidate["requested_screen_projection"]
                ),
                offset_degrees=float(candidate["offset_degrees"]),
                depth_branch=str(candidate["depth_branch"]),
            )
        )
        pass07_adapter._apply_world_rotation(
            objects,
            pivot=pivot,
            current_direction=current_direction,
            target_direction=target_direction,
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
            attempt = {
                "attempt": attempt_number,
                **candidate,
                "edge_counts": edge_counts,
                "accepted": not touched,
            }
            diagnostics.append(attempt)
            print(
                "ATTACK_SWORD_DIRECTIONAL_V21_PASS27_ATTEMPT="
                f"{TARGET_GRIP_ID}/{direction}/f{frame_number:02d};"
                f"attempt:{attempt_number};"
                f"branch:{candidate['depth_branch']};"
                f"projection:{float(candidate['screen_projection']):.6f};"
                f"offset:{float(candidate['offset_degrees']):.1f}deg;"
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
            "attack sword directional v21 pass27 found no export-contained "
            f"candidate for {TARGET_GRIP_ID}/{direction}/f{frame_number:02d}: "
            f"{diagnostics}"
        )

    key = f"{TARGET_GRIP_ID}/{direction}/f{frame_number:02d}"
    metrics = json.loads(
        str(scene.get("attack_sword_directional_cycle_v21_pass02_metrics", "{}"))
    )
    metrics[key] = {
        **selected,
        "edge_counts": selected_edges,
        "render_attempts": len(diagnostics),
        "candidate_diagnostics": diagnostics,
        "pass27_depth_aware_solver": True,
        "allow_blade_occlusion_behind_head": (
            ALLOW_BLADE_OCCLUSION_BEHIND_HEAD
        ),
    }
    scene["attack_sword_directional_cycle_v21_pass02_metrics"] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_DIRECTIONAL_V21_PASS27_SELECTED="
        f"{key};"
        f"branch:{selected['depth_branch']};"
        f"projection:{float(selected['screen_projection']):.6f};"
        f"offset:{float(selected['offset_degrees']):.1f}deg;"
        f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
        f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
        f"attempts:{len(diagnostics)}"
    )
    return accepted


def _write_manifest_v21_pass27(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS26(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = json.loads(
        str(
            factory.bpy.context.scene[
                "attack_sword_directional_cycle_v21_pass02_metrics"
            ]
        )
    )
    target_key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f01"
    if target_key not in metrics:
        raise RuntimeError(
            "attack sword directional v21 pass27 target metrics missing: "
            f"{target_key}"
        )

    payload["attack_sword_directional_cycle_v21_pass27"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": TWOHAND_UP_F01_SOLVER_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(
            run_dir / CONTACT_SHEET_NAME
        ),
        "target_action_id": TARGET_ACTION_ID,
        "target_grip_id": TARGET_GRIP_ID,
        "target_direction": TARGET_DIRECTION,
        "target_frames": list(TARGET_FRAMES),
        "search_screen_projections": list(SEARCH_SCREEN_PROJECTIONS),
        "search_offset_limit_degrees": SEARCH_OFFSET_LIMIT_DEGREES,
        "search_offset_step_degrees": SEARCH_OFFSET_STEP_DEGREES,
        "search_depth_branches": list(SEARCH_DEPTH_BRANCHES),
        "maximum_render_attempts": MAX_RENDER_ATTEMPTS,
        "minimum_visible_blade_head_clearance_pixels": (
            MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
        ),
        "minimum_camera_margin_pixels": MIN_CAMERA_MARGIN_PIXELS,
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "allow_blade_occlusion_behind_head": (
            ALLOW_BLADE_OCCLUSION_BEHIND_HEAD
        ),
        "prefer_high_screen_projection": PREFER_HIGH_SCREEN_PROJECTION,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "selected_metrics": metrics[target_key],
        "action_data_changed": False,
        "rigid_weapon_transform_used": True,
        "approved_down_v20_changed": False,
        "left_direction_changed": False,
        "right_direction_changed": False,
        "onehand_up_changed": False,
        "twohand_up_other_frames_changed": False,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_directional_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": (
                "directional_full_cycle_v21_pass27"
            ),
            "attack_sword_01_twohand_up_f01_solver_revision": (
                TWOHAND_UP_F01_SOLVER_REVISION
            ),
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    pass26_adapter._render_frame_v21_pass26 = _render_frame_v21_pass27
    pass26_adapter._write_manifest_v21_pass26 = _write_manifest_v21_pass27
    try:
        depth_aware_adapter._HEAD_DEPTH_CACHE.clear()
        return pass26_adapter.main()
    finally:
        pass26_adapter._render_frame_v21_pass26 = BASE_RENDER_FRAME_PASS26
        pass26_adapter._write_manifest_v21_pass26 = BASE_WRITE_MANIFEST_PASS26


if __name__ == "__main__":
    raise SystemExit(main())
