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
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
from attack_sword_down_cycle_correction_v20_pass05 import (
    ACTIVE_BLADE_OBJECT_NAME,
    ACTIVE_GRIP_OBJECT_NAME,
    ACTIVE_WEAPON_SOURCE_REVISION,
    ACTIVE_WEAPON_VARIANT_ID,
    ANGLE_SEARCH_LIMIT_DEGREES,
    ANGLE_SEARCH_STEP_DEGREES,
    CORRECTION_PASS,
    DIAGNOSTIC_ARTIFACT_IDS,
    DIAGNOSTIC_RUN_IDS,
    MIN_HEAD_CLEARANCE_PIXELS,
    MISIDENTIFIED_WEAPON_SOURCE_REVISION,
    ONEHAND_CONTAINMENT_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    TARGET_ANIMATION_ID,
    TARGET_FRAME,
)
from combat_idle_down_weapon_variants_builder_v09 import (
    ONE_HAND_READY_V09_OBJECT_NAMES,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_cycle_correction_v20_pass05.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_cycle_v20.png"
BASE_RENDER_FRAME_V20 = base_adapter._render_frame_v20
BASE_WRITE_MANIFEST_V20 = base_adapter._write_manifest_v20


def _active_onehand_objects() -> tuple[object, ...]:
    objects: list[object] = []
    for object_name in ONE_HAND_READY_V09_OBJECT_NAMES:
        obj = factory.bpy.data.objects.get(object_name)
        if obj is None:
            raise RuntimeError(
                f"attack sword down v20 pass05 active weapon object is missing: {object_name}"
            )
        if obj.hide_render:
            raise RuntimeError(
                f"attack sword down v20 pass05 active weapon object is hidden: {object_name}"
            )
        objects.append(obj)
    return tuple(objects)


def _active_onehand_world_direction() -> Vector:
    blade = factory.bpy.data.objects.get(ACTIVE_BLADE_OBJECT_NAME)
    if blade is None:
        raise RuntimeError("attack sword down v20 pass05 active blade is missing")
    return (blade.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def _candidate_offsets(
    objects: tuple[object, ...],
    *,
    saved_basis: dict[str, Matrix],
    pivot: Vector,
    current_direction: Vector,
) -> tuple[float, ...]:
    ordered: list[float] = [0.0]
    for magnitude in range(
        ANGLE_SEARCH_STEP_DEGREES,
        ANGLE_SEARCH_LIMIT_DEGREES + 1,
        ANGLE_SEARCH_STEP_DEGREES,
    ):
        scored: list[tuple[float, float]] = []
        for offset in (-float(magnitude), float(magnitude)):
            pass07_adapter._apply_world_rotation(
                objects,
                pivot=pivot,
                current_direction=current_direction,
                target_direction=export_adapter._target_direction(
                    current_direction,
                    offset_degrees=offset,
                ),
            )
            try:
                scored.append((export_adapter._projected_min_x(objects), offset))
            finally:
                pass06_adapter._restore_weapon(saved_basis)
        scored.sort(key=lambda item: (-item[0], item[1]))
        ordered.extend(offset for _minimum_x, offset in scored)
    return tuple(ordered)


def _render_frame_v20_pass05(
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
    objects = _active_onehand_objects()
    grip = factory.bpy.data.objects.get(ACTIVE_GRIP_OBJECT_NAME)
    if grip is None:
        raise RuntimeError("attack sword down v20 pass05 active grip is missing")
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = _active_onehand_world_direction()
    pivot = grip.matrix_world.translation.copy()
    projection_before = pass06_adapter._screen_projection_magnitude(current_direction)
    offsets = _candidate_offsets(
        objects,
        saved_basis=saved_basis,
        pivot=pivot,
        current_direction=current_direction,
    )

    diagnostics: list[dict[str, object]] = []
    accepted: tuple[factory.FrameArtifact, factory.FramingCalibration] | None = None
    selected_offset = 0.0
    selected_clearance = 0.0
    selected_projected_min_x = 0.0
    selected_projection = 0.0
    selected_edge_counts: dict[str, int] = {}

    for attempt_number, offset_degrees in enumerate(offsets, start=1):
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
            projected_min_x = export_adapter._projected_min_x(objects)
            if clearance < MIN_HEAD_CLEARANCE_PIXELS:
                diagnostics.append(
                    {
                        "attempt": attempt_number,
                        "offset_degrees": offset_degrees,
                        "head_clearance_pixels": clearance,
                        "projected_min_x": projected_min_x,
                        "rendered": False,
                        "reason": "head_clearance",
                    }
                )
                continue
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
            touched = {edge: count for edge, count in edge_counts.items() if count > 0}
            projection_after = pass06_adapter._screen_projection_magnitude(
                _active_onehand_world_direction()
            )
            diagnostics.append(
                {
                    "attempt": attempt_number,
                    "offset_degrees": offset_degrees,
                    "head_clearance_pixels": clearance,
                    "projected_min_x": projected_min_x,
                    "projection_after": projection_after,
                    "rendered": True,
                    "edge_counts": edge_counts,
                    "accepted": not touched,
                }
            )
            print(
                "ATTACK_SWORD_DOWN_CYCLE_V20_PASS05_ATTEMPT="
                f"attempt:{attempt_number};"
                f"offset:{offset_degrees:.1f}deg;"
                f"clearance:{clearance:.3f}px;"
                f"projected_min_x:{projected_min_x:.3f}px;"
                f"edges:{touched}"
            )
            if not touched:
                accepted = (artifact, calibration)
                selected_offset = offset_degrees
                selected_clearance = clearance
                selected_projected_min_x = projected_min_x
                selected_projection = projection_after
                selected_edge_counts = edge_counts
                break
        finally:
            pass06_adapter._restore_weapon(saved_basis)

    if accepted is None:
        raise RuntimeError(
            "attack sword down v20 pass05 found no export-contained active v09 "
            f"one-hand rebound candidate after {len(offsets)} offsets: {diagnostics}"
        )

    scene["attack_sword_down_cycle_v20_pass05_angle_offset_degrees"] = selected_offset
    scene["attack_sword_down_cycle_v20_pass05_head_clearance"] = selected_clearance
    scene["attack_sword_down_cycle_v20_pass05_projected_min_x"] = selected_projected_min_x
    scene["attack_sword_down_cycle_v20_pass05_projection_before"] = projection_before
    scene["attack_sword_down_cycle_v20_pass05_projection_after"] = selected_projection
    scene["attack_sword_down_cycle_v20_pass05_render_attempts"] = len(diagnostics)
    scene["attack_sword_down_cycle_v20_pass05_edge_counts"] = json.dumps(
        selected_edge_counts,
        sort_keys=True,
    )
    scene["attack_sword_down_cycle_v20_pass05_diagnostics"] = json.dumps(
        diagnostics,
        sort_keys=True,
    )
    scene["attack_sword_down_cycle_v20_pass05_export_contained"] = True
    scene["attack_sword_down_cycle_v20_pass05_active_weapon_revision"] = (
        ACTIVE_WEAPON_SOURCE_REVISION
    )
    print(
        "ATTACK_SWORD_DOWN_CYCLE_V20_PASS05_SELECTED="
        f"offset:{selected_offset:.1f}deg;"
        f"clearance:{selected_clearance:.3f}px;"
        f"attempts:{len(diagnostics)};"
        f"edges:{selected_edge_counts}"
    )
    return accepted


def _write_manifest_v20_pass05(
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
    payload["attack_sword_down_cycle_v20_pass05"] = {
        "correction_pass": CORRECTION_PASS,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(run_dir / CONTACT_SHEET_NAME),
        "onehand_containment_revision": ONEHAND_CONTAINMENT_REVISION,
        "target_animation_id": TARGET_ANIMATION_ID,
        "target_frame": TARGET_FRAME,
        "active_weapon_variant_id": ACTIVE_WEAPON_VARIANT_ID,
        "active_weapon_source_revision": ACTIVE_WEAPON_SOURCE_REVISION,
        "active_weapon_object_names": list(ONE_HAND_READY_V09_OBJECT_NAMES),
        "active_blade_object_name": ACTIVE_BLADE_OBJECT_NAME,
        "active_grip_object_name": ACTIVE_GRIP_OBJECT_NAME,
        "misidentified_weapon_source_revision": MISIDENTIFIED_WEAPON_SOURCE_REVISION,
        "diagnostic_run_ids": list(DIAGNOSTIC_RUN_IDS),
        "diagnostic_artifact_ids": list(DIAGNOSTIC_ARTIFACT_IDS),
        "selected_angle_offset_degrees": float(
            scene["attack_sword_down_cycle_v20_pass05_angle_offset_degrees"]
        ),
        "head_clearance_pixels": float(
            scene["attack_sword_down_cycle_v20_pass05_head_clearance"]
        ),
        "projected_min_x": float(
            scene["attack_sword_down_cycle_v20_pass05_projected_min_x"]
        ),
        "projection_before": float(
            scene["attack_sword_down_cycle_v20_pass05_projection_before"]
        ),
        "projection_after": float(
            scene["attack_sword_down_cycle_v20_pass05_projection_after"]
        ),
        "render_attempts": int(
            scene["attack_sword_down_cycle_v20_pass05_render_attempts"]
        ),
        "edge_counts": json.loads(
            str(scene["attack_sword_down_cycle_v20_pass05_edge_counts"])
        ),
        "candidate_diagnostics": json.loads(
            str(scene["attack_sword_down_cycle_v20_pass05_diagnostics"])
        ),
        "angle_search_limit_degrees": ANGLE_SEARCH_LIMIT_DEGREES,
        "angle_search_step_degrees": ANGLE_SEARCH_STEP_DEGREES,
        "minimum_head_clearance_pixels": MIN_HEAD_CLEARANCE_PIXELS,
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "export_space_validated": True,
        "body_pose_changed": False,
        "approved_v19_anchor_frames_changed": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "manual_full_cycle_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_full_cycle_v20_pass05",
            "attack_sword_01_onehand_active_v09_rebound_export_contained": True,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter._render_frame_v20 = _render_frame_v20_pass05
    base_adapter._write_manifest_v20 = _write_manifest_v20_pass05
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
