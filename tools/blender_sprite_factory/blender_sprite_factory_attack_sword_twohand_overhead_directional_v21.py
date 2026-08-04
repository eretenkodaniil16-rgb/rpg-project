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
import blender_sprite_factory_attack_sword_directional_cycle_v21 as directional_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass03 as export_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass05 as down_pass05
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass06 as pass06_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v19_pass07 as pass07_adapter
import blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass02 as arc_adapter
from attack_sword_twohand_down_overhead_correction_v21_pass02 import (
    SCREEN_OFFSET_DEGREES_BY_FRAME,
    SCREEN_PROJECTION_BY_FRAME,
    TARGET_FRAMES,
)
from attack_sword_twohand_down_overhead_correction_v21_pass04 import (
    F03_SCREEN_PROJECTION,
)
from attack_sword_twohand_overhead_directional_builder_v21 import (
    create_attack_sword_twohand_overhead_directional_actions_v21,
)
from attack_sword_twohand_overhead_directional_profile_v21 import (
    DIRECTIONAL_OVERHEAD_REVISION,
    DIRECTION_ORDER,
    DOWN_FRAME_SHA256,
    GRIP_ID,
    TOTAL_RENDERED_FRAME_COUNT,
    load_attack_sword_twohand_overhead_directional_profile_v21,
)


PROFILE_PATH = (
    SCRIPT_DIR / "attack_sword_twohand_overhead_directional_profile_v21.py"
)
BUILDER_PATH = (
    SCRIPT_DIR / "attack_sword_twohand_overhead_directional_builder_v21.py"
)
DOWN_SOURCE_PATH = (
    SCRIPT_DIR / "blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass04.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_twohand_overhead_directional_v21.png"
MANIFEST_KEY = "attack_sword_twohand_overhead_directional_v21"
METRICS_SCENE_KEY = "twohand_overhead_dir_v21_metrics"

ACTION_ID_BY_DIRECTION = {
    "down": "attack_sword_01_twohand_down_overhead_v21",
    "left": "attack_sword_01_twohand_left_overhead_v21",
    "right": "attack_sword_01_twohand_right_overhead_v21",
    "up": "attack_sword_01_twohand_up_overhead_v21",
}
PROJECTION_BY_FRAME = dict(SCREEN_PROJECTION_BY_FRAME)
PROJECTION_BY_FRAME[3] = F03_SCREEN_PROJECTION

ORIGINAL_RENDER_FRAME = down_pass05._render_frame_v20_pass05
ORIGINAL_PROFILE_LOADER = directional_adapter.load_attack_sword_directional_cycle_profile_v21
ORIGINAL_ACTION_BUILDER = directional_adapter.create_attack_sword_directional_cycle_actions_v21
ORIGINAL_TOTAL_RENDERED_FRAME_COUNT = directional_adapter.TOTAL_RENDERED_FRAME_COUNT
ORIGINAL_GRIP_ORDER = directional_adapter.GRIP_ORDER
ORIGINAL_PROFILE_PATH = directional_adapter.PROFILE_PATH
ORIGINAL_BUILDER_PATH = directional_adapter.BUILDER_PATH
ORIGINAL_DOWN_SOURCE_PATH = directional_adapter.DOWN_SOURCE_PATH
ORIGINAL_CONTACT_SHEET_NAME = directional_adapter.CONTACT_SHEET_NAME
ORIGINAL_VALIDATE_CLEARANCE = directional_adapter._validate_directional_clearance
ORIGINAL_WRITE_MANIFEST = directional_adapter._write_manifest_v21


def _is_target(
    animation_id: str,
    direction: str,
    frame_number: int,
) -> bool:
    return (
        direction in ACTION_ID_BY_DIRECTION
        and animation_id == ACTION_ID_BY_DIRECTION[direction]
        and frame_number in TARGET_FRAMES
    )


def _local_overhead_target_direction(
    context: factory.BuildContext,
    *,
    frame_number: int,
) -> tuple[object, dict[str, float]]:
    scene = factory.bpy.context.scene
    saved_frame = int(scene.frame_current)
    saved_rotation = context.rig.rotation_euler.copy()
    try:
        context.rig.rotation_euler[2] = math.radians(
            context.config.directions["down"]
        )
        scene.frame_set(1)
        factory.bpy.context.view_layer.update()
        reference_direction = arc_adapter._blade_direction().copy()
        target_world, reference_projection, reference_depth, target_depth = (
            arc_adapter._target_direction(
                reference_direction,
                offset_degrees=float(
                    SCREEN_OFFSET_DEGREES_BY_FRAME[frame_number]
                ),
                requested_projection=float(PROJECTION_BY_FRAME[frame_number]),
            )
        )
        target_local = (
            context.rig.matrix_world.to_3x3().inverted() @ target_world
        ).normalized()
    finally:
        context.rig.rotation_euler = saved_rotation
        scene.frame_set(saved_frame)
        factory.bpy.context.view_layer.update()

    return target_local, {
        "down_reference_screen_projection": float(reference_projection),
        "down_reference_camera_depth": float(reference_depth),
        "down_target_camera_depth": float(target_depth),
    }


def _render_frame_directional_overhead_v21(
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
    if not _is_target(animation_id, direction, frame_number):
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
        raise RuntimeError("directional overhead v21 requires fixed framing")

    scene = factory.bpy.context.scene
    scene.frame_set(frame_number)
    factory.bpy.context.view_layer.update()
    objects = directional_adapter._visible_weapon_objects(GRIP_ID, direction)
    saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
    current_direction = arc_adapter._blade_direction()
    grip = factory.bpy.data.objects.get(arc_adapter.GRIP_OBJECT_NAME)
    if grip is None:
        raise RuntimeError("directional overhead v21 grip object is missing")
    pivot = grip.matrix_world.translation.copy()
    target_local, source_metrics = _local_overhead_target_direction(
        context,
        frame_number=frame_number,
    )
    target_world = (
        context.rig.matrix_world.to_3x3() @ target_local
    ).normalized()

    pass07_adapter._apply_world_rotation(
        objects,
        pivot=pivot,
        current_direction=current_direction,
        target_direction=target_world,
    )
    try:
        factory.bpy.context.view_layer.update()
        head_clearance = float(export_adapter._weapon_head_clearance(objects))
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
        touched = {
            edge: int(count)
            for edge, count in edge_counts.items()
            if count > 0
        }
        if touched:
            raise RuntimeError(
                "directional overhead v21 touched canvas edge at "
                f"{direction}/f{frame_number:02d}: {touched}"
            )
    finally:
        pass06_adapter._restore_weapon(saved_basis)
        factory.bpy.context.view_layer.update()

    key = f"{direction}/f{frame_number:02d}"
    metrics = json.loads(str(scene.get(METRICS_SCENE_KEY, "{}")))
    metrics[key] = {
        "screen_offset_degrees_from_guard": float(
            SCREEN_OFFSET_DEGREES_BY_FRAME[frame_number]
        ),
        "screen_projection_in_down_reference": float(
            PROJECTION_BY_FRAME[frame_number]
        ),
        "character_local_target_direction": [
            float(value) for value in target_local
        ],
        "world_target_direction": [float(value) for value in target_world],
        "head_clearance_pixels": head_clearance,
        "edge_counts": {
            edge: int(count) for edge, count in edge_counts.items()
        },
        "rigid_weapon_transform": True,
        "local_action_curves_changed": False,
        **source_metrics,
    }
    scene[METRICS_SCENE_KEY] = json.dumps(metrics, sort_keys=True)
    print(
        "ATTACK_SWORD_TWOHAND_OVERHEAD_DIRECTIONAL_V21="
        f"{key};offset:{float(SCREEN_OFFSET_DEGREES_BY_FRAME[frame_number]):.1f};"
        f"projection:{float(PROJECTION_BY_FRAME[frame_number]):.3f};"
        f"clearance:{head_clearance:.3f};edges:{edge_counts}"
    )
    return artifact, calibration


def _validate_directional_overhead_clearance(
    context: factory.BuildContext,
    *,
    action_id: str,
    grip_id: str,
    weapon_cycle_id: str,
    direction: str,
) -> dict[int, float]:
    del context, action_id, weapon_cycle_id
    if grip_id != GRIP_ID or direction not in DIRECTION_ORDER:
        raise RuntimeError(
            f"directional overhead v21 received unsupported clearance target: "
            f"{grip_id}/{direction}"
        )
    metrics = json.loads(
        str(factory.bpy.context.scene.get(METRICS_SCENE_KEY, "{}"))
    )
    result: dict[int, float] = {}
    for frame_number in directional_adapter.CLEARANCE_FRAMES:
        key = f"{direction}/f{frame_number:02d}"
        if key not in metrics:
            raise RuntimeError(
                f"directional overhead v21 clearance metrics missing: {key}"
            )
        value = float(metrics[key]["head_clearance_pixels"])
        if not math.isfinite(value) or value < 0.0:
            raise RuntimeError(
                f"directional overhead v21 invalid head clearance: {key}={value}"
            )
        result[frame_number] = value
    return result


def _write_manifest_directional_overhead_v21(
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
    profile = load_attack_sword_twohand_overhead_directional_profile_v21(
        context.config.character_id
    )
    metrics = json.loads(
        str(factory.bpy.context.scene.get(METRICS_SCENE_KEY, "{}"))
    )
    expected_metrics = {
        f"{direction}/f{frame_number:02d}"
        for direction in DIRECTION_ORDER
        for frame_number in TARGET_FRAMES
    }
    if set(metrics) != expected_metrics:
        raise RuntimeError(
            "directional overhead v21 metrics are incomplete: "
            f"actual={sorted(metrics)}, expected={sorted(expected_metrics)}"
        )

    direction_payload: dict[str, object] = {}
    for action_spec in profile.actions:
        frames = directional_adapter._action_frames(
            artifacts,
            animation_id=action_spec.action_id,
            direction=action_spec.direction,
        )
        guard_sha = hashlib.sha256(frames[0].output_path.read_bytes()).hexdigest()
        settle_sha = hashlib.sha256(frames[-1].output_path.read_bytes()).hexdigest()
        if guard_sha != settle_sha:
            raise RuntimeError(
                "directional overhead v21 did not return to guard: "
                f"{action_spec.direction}"
            )
        frame_hashes = {
            frame.frame_number: hashlib.sha256(
                frame.output_path.read_bytes()
            ).hexdigest()
            for frame in frames
        }
        if action_spec.direction == "down" and frame_hashes != DOWN_FRAME_SHA256:
            raise RuntimeError(
                "directional overhead v21 changed approved pass04 down pixels: "
                f"actual={frame_hashes}"
            )
        action = factory.bpy.data.actions.get(
            f"{context.config.character_id}_{action_spec.action_id}"
        )
        if action is None:
            raise RuntimeError(
                f"directional overhead v21 source blend action missing: "
                f"{action_spec.action_id}"
            )
        if action_spec.direction != "down" and not bool(
            action.get("directional_copy_of_overhead_local_motion", False)
        ):
            raise RuntimeError(
                "directional overhead v21 action copy contract missing: "
                f"{action_spec.action_id}"
            )
        direction_payload[action_spec.direction] = {
            "action_id": action_spec.action_id,
            "trajectory_id": action_spec.trajectory_id,
            "frame_sha256": {
                f"f{frame:02d}": digest
                for frame, digest in sorted(frame_hashes.items())
            },
            "guard_settle_pixel_identical": True,
            "local_action_curves_changed": False,
        }

    payload[MANIFEST_KEY] = {
        "revision": DIRECTIONAL_OVERHEAD_REVISION,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "source_down_adapter_path": context.config.relative_to_repo(
            DOWN_SOURCE_PATH
        ),
        "source_down_adapter_sha256": hashlib.sha256(
            DOWN_SOURCE_PATH.read_bytes()
        ).hexdigest(),
        "source_down_workflow_run": 30957411611,
        "source_down_artifact_id": 8911848479,
        "source_down_artifact_sha256": (
            "620e24dccef0194deaf3dcbb3b56d917def3bde994ef73b1d9561288eba981a9"
        ),
        "directions": list(DIRECTION_ORDER),
        "total_actions": len(profile.actions),
        "total_rendered_frames": len(artifacts),
        "target_frames_with_rigid_weapon_arc": list(TARGET_FRAMES),
        "projection_by_frame": {
            str(frame): float(value)
            for frame, value in sorted(PROJECTION_BY_FRAME.items())
        },
        "screen_offset_degrees_by_frame": {
            str(frame): float(value)
            for frame, value in sorted(
                SCREEN_OFFSET_DEGREES_BY_FRAME.items()
            )
        },
        "render_metrics": metrics,
        "direction_results": direction_payload,
        "approved_down_pass04_pixels_preserved": True,
        "same_local_action_curves_for_all_directions": True,
        "character_local_weapon_trajectory_shared": True,
        "directional_idle_calibration_used": True,
        "real_directional_rig_rotation_used": True,
        "physical_equipment_sides_preserved": True,
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
            "attack_sword_01_twohand_overhead_current_stage": (
                "directional_review_v21"
            ),
            "attack_sword_01_twohand_overhead_directions": list(
                DIRECTION_ORDER
            ),
            "attack_sword_01_twohand_overhead_total_actions": len(
                profile.actions
            ),
            "attack_sword_01_twohand_overhead_total_frames": len(artifacts),
            "attack_sword_01_twohand_overhead_same_local_motion": True,
            "attack_sword_01_twohand_overhead_manual_review_required": True,
            "attack_sword_01_twohand_overhead_runtime_connected": False,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_contract() -> None:
    down_pass05._render_frame_v20_pass05 = (
        _render_frame_directional_overhead_v21
    )
    directional_adapter.load_attack_sword_directional_cycle_profile_v21 = (
        load_attack_sword_twohand_overhead_directional_profile_v21
    )
    directional_adapter.create_attack_sword_directional_cycle_actions_v21 = (
        create_attack_sword_twohand_overhead_directional_actions_v21
    )
    directional_adapter.TOTAL_RENDERED_FRAME_COUNT = TOTAL_RENDERED_FRAME_COUNT
    directional_adapter.GRIP_ORDER = (GRIP_ID,)
    directional_adapter.PROFILE_PATH = PROFILE_PATH
    directional_adapter.BUILDER_PATH = BUILDER_PATH
    directional_adapter.DOWN_SOURCE_PATH = DOWN_SOURCE_PATH
    directional_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    directional_adapter._validate_directional_clearance = (
        _validate_directional_overhead_clearance
    )
    directional_adapter._write_manifest_v21 = (
        _write_manifest_directional_overhead_v21
    )


def _restore_contract() -> None:
    down_pass05._render_frame_v20_pass05 = ORIGINAL_RENDER_FRAME
    directional_adapter.load_attack_sword_directional_cycle_profile_v21 = (
        ORIGINAL_PROFILE_LOADER
    )
    directional_adapter.create_attack_sword_directional_cycle_actions_v21 = (
        ORIGINAL_ACTION_BUILDER
    )
    directional_adapter.TOTAL_RENDERED_FRAME_COUNT = (
        ORIGINAL_TOTAL_RENDERED_FRAME_COUNT
    )
    directional_adapter.GRIP_ORDER = ORIGINAL_GRIP_ORDER
    directional_adapter.PROFILE_PATH = ORIGINAL_PROFILE_PATH
    directional_adapter.BUILDER_PATH = ORIGINAL_BUILDER_PATH
    directional_adapter.DOWN_SOURCE_PATH = ORIGINAL_DOWN_SOURCE_PATH
    directional_adapter.CONTACT_SHEET_NAME = ORIGINAL_CONTACT_SHEET_NAME
    directional_adapter._validate_directional_clearance = (
        ORIGINAL_VALIDATE_CLEARANCE
    )
    directional_adapter._write_manifest_v21 = ORIGINAL_WRITE_MANIFEST


def main() -> int:
    _apply_contract()
    try:
        return directional_adapter.main()
    finally:
        _restore_contract()


if __name__ == "__main__":
    raise SystemExit(main())
