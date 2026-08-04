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
import blender_sprite_factory_attack_sword_twohand_overhead_directional_v21 as base_adapter
from attack_sword_twohand_overhead_directional_correction_v21_pass02 import (
    CORRECTION_PASS,
    DIRECTIONAL_CONTAINMENT_REVISION,
    MINIMUM_SCREEN_PROJECTION,
    PRESERVE_ACTION_CURVES,
    PRESERVE_CHARACTER_LOCAL_ARC_ANGLE,
    PRESERVE_DOWN_PASS04_PIXELS,
    PROJECTION_SEARCH_STEP,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
)


CORRECTION_PATH = (
    SCRIPT_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass02.py"
)
PASS02_MANIFEST_KEY = "attack_sword_twohand_overhead_directional_v21_pass02"
ORIGINAL_RENDER_FRAME = base_adapter._render_frame_directional_overhead_v21
ORIGINAL_WRITE_MANIFEST = base_adapter._write_manifest_directional_overhead_v21


def _projection_candidates(canonical: float) -> tuple[float, ...]:
    values: list[float] = [float(canonical)]
    candidate = canonical - PROJECTION_SEARCH_STEP
    while candidate >= MINIMUM_SCREEN_PROJECTION - 1.0e-9:
        values.append(round(candidate, 6))
        candidate -= PROJECTION_SEARCH_STEP
    if values[-1] > MINIMUM_SCREEN_PROJECTION + 1.0e-9:
        values.append(float(MINIMUM_SCREEN_PROJECTION))
    return tuple(values)


def _render_frame_directional_overhead_v21_pass02(
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
    if not base_adapter._is_target(animation_id, direction, frame_number):
        return ORIGINAL_RENDER_FRAME(
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
        raise RuntimeError("directional overhead pass02 requires fixed framing")

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    objects = base_adapter.directional_adapter._visible_weapon_objects(
        base_adapter.GRIP_ID,
        direction,
    )
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = base_adapter.arc_adapter._blade_direction()
    grip = factory.bpy.data.objects.get(base_adapter.arc_adapter.GRIP_OBJECT_NAME)
    if grip is None:
        raise RuntimeError("directional overhead pass02 grip object is missing")
    pivot = grip.matrix_world.translation.copy()
    canonical_projection = float(base_adapter.PROJECTION_BY_FRAME[frame_number])

    diagnostics: list[dict[str, object]] = []
    accepted: tuple[factory.FrameArtifact, factory.FramingCalibration] | None = None
    selected_projection: float | None = None
    selected_target_local: object | None = None
    selected_target_world: object | None = None
    selected_source_metrics: dict[str, float] | None = None
    selected_clearance = 0.0
    selected_edges: dict[str, int] = {}

    try:
        for attempt, projection in enumerate(
            _projection_candidates(canonical_projection),
            start=1,
        ):
            base_adapter.PROJECTION_BY_FRAME[frame_number] = projection
            target_local, source_metrics = (
                base_adapter._local_overhead_target_direction(
                    context,
                    frame_number=frame_number,
                )
            )
            target_world = (
                context.rig.matrix_world.to_3x3() @ target_local
            ).normalized()
            base_adapter.pass07_adapter._apply_world_rotation(
                objects,
                pivot=pivot,
                current_direction=current_direction,
                target_direction=target_world,
            )
            try:
                factory.bpy.context.view_layer.update()
                head_clearance = float(
                    base_adapter.export_adapter._weapon_head_clearance(objects)
                )
                artifact, calibration = (
                    base_adapter.export_adapter._render_candidate(
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
                )
                edge_counts = base_adapter.keypose_adapter._edge_alpha_counts(
                    artifact.output_path
                )
                touched = {
                    edge: int(count)
                    for edge, count in edge_counts.items()
                    if count > 0
                }
            finally:
                base_adapter.pass06_adapter._restore_weapon(saved_basis)
                factory.bpy.context.view_layer.update()

            diagnostics.append(
                {
                    "attempt": attempt,
                    "screen_projection": projection,
                    "head_clearance_pixels": head_clearance,
                    "edge_counts": {
                        edge: int(count) for edge, count in edge_counts.items()
                    },
                    "accepted": not touched,
                }
            )
            print(
                "ATTACK_SWORD_TWOHAND_OVERHEAD_DIRECTIONAL_V21_PASS02_ATTEMPT="
                f"{direction}/f{frame_number:02d};attempt:{attempt};"
                f"projection:{projection:.3f};"
                f"clearance:{head_clearance:.3f};edges:{touched}"
            )
            if not touched:
                accepted = (artifact, calibration)
                selected_projection = projection
                selected_target_local = target_local
                selected_target_world = target_world
                selected_source_metrics = source_metrics
                selected_clearance = head_clearance
                selected_edges = {
                    edge: int(count) for edge, count in edge_counts.items()
                }
                break
    finally:
        base_adapter.PROJECTION_BY_FRAME[frame_number] = canonical_projection

    if (
        accepted is None
        or selected_projection is None
        or selected_target_local is None
        or selected_target_world is None
        or selected_source_metrics is None
    ):
        raise RuntimeError(
            "directional overhead pass02 found no contained projection for "
            f"{direction}/f{frame_number:02d}: {diagnostics}"
        )
    if REQUIRE_ZERO_EDGE_ALPHA and any(selected_edges.values()):
        raise RuntimeError(
            "directional overhead pass02 selected an edge-touching frame: "
            f"{direction}/f{frame_number:02d}={selected_edges}"
        )

    key = f"{direction}/f{frame_number:02d}"
    metrics = json.loads(
        str(scene.get(base_adapter.METRICS_SCENE_KEY, "{}"))
    )
    metrics[key] = {
        "screen_offset_degrees_from_guard": float(
            base_adapter.SCREEN_OFFSET_DEGREES_BY_FRAME[frame_number]
        ),
        "canonical_screen_projection": canonical_projection,
        "screen_projection_in_down_reference": selected_projection,
        "projection_adjusted_for_containment": (
            not math.isclose(
                selected_projection,
                canonical_projection,
                rel_tol=0.0,
                abs_tol=1.0e-9,
            )
        ),
        "projection_render_attempts": len(diagnostics),
        "projection_candidate_diagnostics": diagnostics,
        "character_local_target_direction": [
            float(value) for value in selected_target_local
        ],
        "world_target_direction": [
            float(value) for value in selected_target_world
        ],
        "head_clearance_pixels": selected_clearance,
        "edge_counts": selected_edges,
        "rigid_weapon_transform": True,
        "local_action_curves_changed": False,
        **selected_source_metrics,
    }
    scene[base_adapter.METRICS_SCENE_KEY] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_TWOHAND_OVERHEAD_DIRECTIONAL_V21_PASS02_SELECTED="
        f"{key};projection:{selected_projection:.3f};"
        f"attempts:{len(diagnostics)};edges:{selected_edges}"
    )
    return accepted


def _write_manifest_directional_overhead_v21_pass02(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = json.loads(
        str(factory.bpy.context.scene.get(base_adapter.METRICS_SCENE_KEY, "{}"))
    )
    adjusted = {
        key: value
        for key, value in metrics.items()
        if bool(value.get("projection_adjusted_for_containment", False))
    }
    if any(key.startswith("down/") for key in adjusted):
        raise RuntimeError(
            "directional overhead pass02 attempted to change approved down pixels"
        )

    payload[PASS02_MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": DIRECTIONAL_CONTAINMENT_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "projection_search_step": PROJECTION_SEARCH_STEP,
        "minimum_screen_projection": MINIMUM_SCREEN_PROJECTION,
        "adjusted_frames": adjusted,
        "adjusted_frame_count": len(adjusted),
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "action_curves_preserved": PRESERVE_ACTION_CURVES,
        "character_local_arc_angle_preserved": (
            PRESERVE_CHARACTER_LOCAL_ARC_ANGLE
        ),
        "approved_down_pass04_pixels_preserved": PRESERVE_DOWN_PASS04_PIXELS,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "runtime_connected": False,
        "manual_directional_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_twohand_overhead_directional_containment": (
                DIRECTIONAL_CONTAINMENT_REVISION
            ),
            "attack_sword_01_twohand_overhead_action_curves_preserved": True,
            "attack_sword_01_twohand_overhead_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter._render_frame_directional_overhead_v21 = (
        _render_frame_directional_overhead_v21_pass02
    )
    base_adapter._write_manifest_directional_overhead_v21 = (
        _write_manifest_directional_overhead_v21_pass02
    )
    try:
        return base_adapter.main()
    finally:
        base_adapter._render_frame_directional_overhead_v21 = ORIGINAL_RENDER_FRAME
        base_adapter._write_manifest_directional_overhead_v21 = (
            ORIGINAL_WRITE_MANIFEST
        )


if __name__ == "__main__":
    raise SystemExit(main())
