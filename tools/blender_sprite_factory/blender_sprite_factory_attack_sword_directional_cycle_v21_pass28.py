from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_directional_cycle_v21_pass27 as pass27_adapter
import blender_sprite_factory_attack_sword_onehand_up_depth_search_diagnostic_v21 as pass23_adapter
from attack_sword_directional_cycle_correction_v21_pass28 import (
    CORRECTION_PASS,
    FALLBACK_ERROR_PREFIXES,
    FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAMES,
    TARGET_GRIP_ID,
    TWOHAND_UP_FALLBACK_REVISION,
    USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_directional_cycle_correction_v21_pass28.py"
)
CONTACT_SHEET_NAME = "attack_sword_01_directional_cycle_v21.png"
ORIGINAL_PASS27_RENDER = pass27_adapter._render_frame_v21_pass27
ORIGINAL_PASS27_WRITE_MANIFEST = pass27_adapter._write_manifest_v21_pass27
ORIGINAL_PASS27_CLEARANCE = (
    pass27_adapter.depth_aware_adapter._depth_aware_visible_blade_head_clearance
)


def _is_twohand_up_frame(
    animation_id: str,
    direction: str,
    frame_number: int,
) -> bool:
    return (
        animation_id == TARGET_ACTION_ID
        and direction == TARGET_DIRECTION
        and frame_number in TARGET_FRAMES
    )


def _is_fallback_error(error: RuntimeError, frame_number: int) -> bool:
    message = str(error)
    frame_key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{frame_number:02d}"
    return frame_key in message and any(
        message.startswith(prefix) for prefix in FALLBACK_ERROR_PREFIXES
    )


def _record_fallback_frame(frame_number: int) -> None:
    scene = factory.bpy.context.scene
    raw = str(scene.get("attack_sword_directional_cycle_v21_pass28_frames", "[]"))
    frames = [int(value) for value in json.loads(raw)]
    if frame_number not in frames:
        frames.append(frame_number)
        frames.sort()
    scene["attack_sword_directional_cycle_v21_pass28_frames"] = json.dumps(frames)


def _render_frame_v21_pass28(
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
    if not _is_twohand_up_frame(animation_id, direction, frame_number):
        return ORIGINAL_PASS27_RENDER(
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

    try:
        return pass27_adapter.BASE_RENDER_FRAME_PASS26(
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
    except RuntimeError as error:
        if not _is_fallback_error(error, frame_number):
            raise

    original_target_frames = pass27_adapter.TARGET_FRAMES
    pass27_adapter.TARGET_FRAMES = (frame_number,)
    try:
        result = ORIGINAL_PASS27_RENDER(
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
    finally:
        pass27_adapter.TARGET_FRAMES = original_target_frames

    _record_fallback_frame(frame_number)
    scene = factory.bpy.context.scene
    metrics = json.loads(
        str(scene.get("attack_sword_directional_cycle_v21_pass02_metrics", "{}"))
    )
    key = f"{TARGET_GRIP_ID}/{direction}/f{frame_number:02d}"
    if key not in metrics:
        raise RuntimeError(
            "attack sword directional v21 pass28 fallback metrics missing: "
            f"{key}"
        )
    metrics[key]["pass28_on_demand_fallback"] = True
    metrics[key]["pass28_fully_occluded_candidates_rejected"] = True
    scene["attack_sword_directional_cycle_v21_pass02_metrics"] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_DIRECTIONAL_V21_PASS28_FALLBACK="
        f"{key};solver:pass27;fully_occluded:rejected"
    )
    return result


def _write_manifest_v21_pass28(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_PASS27_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    fallback_frames = [
        int(value)
        for value in json.loads(
            str(scene.get("attack_sword_directional_cycle_v21_pass28_frames", "[]"))
        )
    ]
    metrics = json.loads(
        str(scene["attack_sword_directional_cycle_v21_pass02_metrics"])
    )
    fallback_metrics: dict[str, object] = {}
    for frame_number in fallback_frames:
        key = f"{TARGET_GRIP_ID}/{TARGET_DIRECTION}/f{frame_number:02d}"
        if key not in metrics:
            raise RuntimeError(
                "attack sword directional v21 pass28 manifest metrics missing: "
                f"{key}"
            )
        fallback_metrics[f"f{frame_number:02d}"] = metrics[key]

    payload["attack_sword_directional_cycle_v21_pass28"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": TWOHAND_UP_FALLBACK_REVISION,
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
        "fallback_frames": fallback_frames,
        "fallback_metrics": fallback_metrics,
        "fallback_error_prefixes": list(FALLBACK_ERROR_PREFIXES),
        "fully_occluded_candidates_are_rejected": (
            FULLY_OCCLUDED_CANDIDATES_ARE_REJECTED
        ),
        "minimum_visible_blade_sample_guard_used": (
            USE_MINIMUM_VISIBLE_BLADE_SAMPLE_GUARD
        ),
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "source_failed_artifact_sha256": SOURCE_FAILED_ARTIFACT_SHA256,
        "source_failure": SOURCE_FAILURE,
        "action_data_changed": False,
        "rigid_weapon_transform_used_only_on_fallback": True,
        "approved_down_v20_changed": False,
        "left_direction_changed": False,
        "right_direction_changed": False,
        "onehand_up_changed": False,
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
                "directional_full_cycle_v21_pass28"
            ),
            "attack_sword_01_twohand_up_fallback_revision": (
                TWOHAND_UP_FALLBACK_REVISION
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
    pass27_adapter.depth_aware_adapter._depth_aware_visible_blade_head_clearance = (
        pass23_adapter._depth_search_visible_blade_head_clearance
    )
    pass27_adapter._render_frame_v21_pass27 = _render_frame_v21_pass28
    pass27_adapter._write_manifest_v21_pass27 = _write_manifest_v21_pass28
    try:
        return pass27_adapter.main()
    finally:
        pass27_adapter.depth_aware_adapter._depth_aware_visible_blade_head_clearance = (
            ORIGINAL_PASS27_CLEARANCE
        )
        pass27_adapter._render_frame_v21_pass27 = ORIGINAL_PASS27_RENDER
        pass27_adapter._write_manifest_v21_pass27 = ORIGINAL_PASS27_WRITE_MANIFEST


if __name__ == "__main__":
    raise SystemExit(main())
