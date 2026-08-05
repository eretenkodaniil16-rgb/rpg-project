from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_onehand_up_front_depth_diagnostic_v21 as pass24_adapter
import blender_sprite_factory_attack_sword_onehand_up_tail_diagnostic_v21 as pass20_adapter
from attack_sword_directional_cycle_correction_v21_pass25 import (
    ARM_PROFILE_CANDIDATES,
    BASE_BONE_DELTAS_DEGREES,
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    ONEHAND_UP_F05_ARM_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SEARCH_ANGLE_OFFSETS,
    SEARCH_PROJECTIONS,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TARGET_FRAMES,
)


ORIGINAL_DIAGNOSE_FRAME = pass20_adapter._diagnose_frame
ORIGINAL_PASS24_WRITE_MANIFEST = pass24_adapter._write_manifest_pass24
ORIGINAL_PASS24_SCENE_KEY = pass24_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS24_CONTACT_SHEET = pass24_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS24_REVISION = pass24_adapter.ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION
ORIGINAL_PASS24_CORRECTION_PASS = pass24_adapter.CORRECTION_PASS
ORIGINAL_PASS24_REQUIRE_ZERO_EDGE_ALPHA = pass24_adapter.REQUIRE_ZERO_EDGE_ALPHA
PASS25_RESULT_SCENE_KEY = "attack_sword_onehand_up_f05_arm_search_v21"


def _apply_arm_profile(
    context: factory.BuildContext,
    target_rotations: dict[str, object],
    source_rotations: dict[str, object],
    profile: dict[str, float],
) -> dict[str, object]:
    pass20_adapter._set_arm_blend(
        context,
        target_rotations,
        source_rotations,
        float(profile["source_blend"]),
    )
    scale = float(profile["scale"])
    sweep_sign = float(profile["sweep_sign"])
    lift_sign = float(profile["lift_sign"])
    for bone_name, delta_degrees in BASE_BONE_DELTAS_DEGREES.items():
        bone = context.rig.pose.bones[bone_name]
        bone.rotation_euler[0] += math.radians(
            float(delta_degrees[0]) * scale * lift_sign
        )
        bone.rotation_euler[1] += math.radians(
            float(delta_degrees[1]) * scale * sweep_sign
        )
        bone.rotation_euler[2] += math.radians(
            float(delta_degrees[2]) * scale * sweep_sign
        )
    factory.bpy.context.view_layer.update()
    return pass20_adapter._capture_current_arm(context)


def _diagnose_f05_with_arm_search(
    context: factory.BuildContext,
    run_dir: Path,
    *,
    calibration: factory.FramingCalibration,
    target_frame: int,
    selected_pose_by_frame: dict[int, dict[str, object]],
) -> tuple[factory.FrameArtifact, dict[str, object], dict[str, object]]:
    if int(target_frame) not in TARGET_FRAMES:
        return ORIGINAL_DIAGNOSE_FRAME(
            context,
            run_dir,
            calibration=calibration,
            target_frame=target_frame,
            selected_pose_by_frame=selected_pose_by_frame,
        )

    source_frame = int(pass20_adapter.SOURCE_FRAME_BY_TARGET[target_frame])
    target_rotations = pass20_adapter._capture_action_arm(context, target_frame)
    source_rotations = selected_pose_by_frame.get(source_frame)
    source_kind = "selected_previous_frame"
    if source_rotations is None:
        source_rotations = pass20_adapter._capture_action_arm(context, source_frame)
        source_kind = "action_frame"
    factory.bpy.context.scene.frame_set(target_frame)
    factory.bpy.context.view_layer.update()

    objects = pass20_adapter.directional_cycle._visible_weapon_objects(
        pass20_adapter.TARGET_GRIP_ID,
        pass20_adapter.TARGET_DIRECTION,
    )
    selected: dict[str, object] | None = None
    selected_artifact: factory.FrameArtifact | None = None
    selected_pose: dict[str, object] | None = None
    diagnostics: list[dict[str, object]] = []
    attempt_number = 0

    try:
        for profile_index, raw_profile in enumerate(ARM_PROFILE_CANDIDATES):
            profile = {
                key: float(value)
                for key, value in raw_profile.items()
            }
            pass20_adapter._restore_arm(context, target_rotations)
            candidate_pose = _apply_arm_profile(
                context,
                target_rotations,
                source_rotations,
                profile,
            )
            saved_basis = {obj.name: obj.matrix_basis.copy() for obj in objects}
            current_direction = pass20_adapter.pass02._weapon_world_direction(objects)
            pivot = pass20_adapter.pass02._weapon_pivot(objects)

            for requested_projection in SEARCH_PROJECTIONS:
                for offset_degrees in SEARCH_ANGLE_OFFSETS:
                    attempt_number += 1
                    target_direction, source_projection, applied_projection = (
                        pass20_adapter._projection_target_direction(
                            current_direction,
                            offset_degrees=float(offset_degrees),
                            requested_projection=float(requested_projection),
                        )
                    )
                    pass20_adapter.pass07_adapter._apply_world_rotation(
                        objects,
                        pivot=pivot,
                        current_direction=current_direction,
                        target_direction=target_direction,
                    )
                    try:
                        clearance = float(
                            pass20_adapter.export_adapter._weapon_head_clearance(objects)
                        )
                        margin = float(pass20_adapter.pass02._camera_margin(objects))
                        diagnostic: dict[str, object] = {
                            "attempt": attempt_number,
                            "target_frame": int(target_frame),
                            "source_frame": source_frame,
                            "source_kind": source_kind,
                            "arm_profile_index": profile_index,
                            "arm_profile": profile,
                            "offset_degrees": float(offset_degrees),
                            "source_projection": float(source_projection),
                            "requested_projection": float(requested_projection),
                            "applied_projection": float(applied_projection),
                            "head_clearance_pixels": clearance,
                            "camera_margin_pixels": margin,
                            "edge_counts": None,
                            "accepted": False,
                        }
                        diagnostics.append(diagnostic)
                        if (
                            clearance < pass20_adapter.MIN_HEAD_CLEARANCE_PIXELS
                            or margin < pass20_adapter.MIN_CAMERA_MARGIN_PIXELS
                        ):
                            continue

                        artifact, _ = pass20_adapter.export_adapter._render_candidate(
                            context,
                            animation_id=(
                                "attack_sword_01_onehand_up_"
                                "f05_arm_diagnostic_v21"
                            ),
                            direction=pass20_adapter.TARGET_DIRECTION,
                            frame_number=int(target_frame),
                            raw_dir=run_dir / "raw",
                            frame_dir=run_dir / "frames",
                            output_name=(
                                f"{context.config.character_id}_attack_sword_01_"
                                f"onehand_up_f05_arm_diagnostic_v21_"
                                f"f{int(target_frame):02d}_proxy_"
                                f"{context.proxy_revision}.png"
                            ),
                            fixed_scale=calibration.scale,
                            fixed_center_x=calibration.source_center_x,
                        )
                        edge_counts = pass20_adapter.keypose_adapter._edge_alpha_counts(
                            artifact.output_path
                        )
                        touched = {
                            edge: count
                            for edge, count in edge_counts.items()
                            if count > 0
                        }
                        diagnostic["edge_counts"] = edge_counts
                        diagnostic["accepted"] = (
                            not touched if REQUIRE_ZERO_EDGE_ALPHA else True
                        )
                        print(
                            "ATTACK_SWORD_ONEHAND_UP_F05_ARM_"
                            "DIAGNOSTIC_V21_ATTEMPT="
                            f"profile:{profile_index};"
                            f"blend:{profile['source_blend']:.2f};"
                            f"scale:{profile['scale']:.2f};"
                            f"sweep:{profile['sweep_sign']:.1f};"
                            f"lift:{profile['lift_sign']:.1f};"
                            f"projection:{float(applied_projection):.3f};"
                            f"offset:{float(offset_degrees):.1f}deg;"
                            f"clearance:{clearance:.3f}px;"
                            f"margin:{margin:.3f}px;"
                            f"edges:{touched}"
                        )
                        if bool(diagnostic["accepted"]):
                            selected = diagnostic
                            selected_artifact = artifact
                            selected_pose = {
                                key: value.copy()
                                for key, value in candidate_pose.items()
                            }
                            break
                    finally:
                        pass20_adapter.pass06_adapter._restore_weapon(saved_basis)
                if selected is not None:
                    break
            if selected is not None:
                break

        if selected is None or selected_artifact is None or selected_pose is None:
            ranked = sorted(
                diagnostics,
                key=lambda item: (
                    float(item["head_clearance_pixels"]),
                    float(item["camera_margin_pixels"]),
                ),
                reverse=True,
            )[:24]
            raise RuntimeError(
                "one-hand up f05 arm diagnostic found no safe candidate; "
                f"best candidates: {ranked}"
            )

        result = {
            "selected": selected,
            "candidate_count": len(diagnostics),
            "candidate_diagnostics": diagnostics,
        }
        factory.bpy.context.scene[PASS25_RESULT_SCENE_KEY] = json.dumps(
            result,
            sort_keys=True,
        )
        print(
            "ATTACK_SWORD_ONEHAND_UP_F05_ARM_DIAGNOSTIC_V21_SELECTED="
            f"profile:{int(selected['arm_profile_index'])};"
            f"projection:{float(selected['applied_projection']):.3f};"
            f"offset:{float(selected['offset_degrees']):.1f}deg;"
            f"clearance:{float(selected['head_clearance_pixels']):.3f}px;"
            f"margin:{float(selected['camera_margin_pixels']):.3f}px;"
            f"attempts:{len(diagnostics)}"
        )
        return selected_artifact, result, selected_pose
    finally:
        pass20_adapter._restore_arm(context, target_rotations)


def _write_manifest_pass25(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS24_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    selected = json.loads(
        str(factory.bpy.context.scene.get(PASS25_RESULT_SCENE_KEY, "{}"))
    )
    payload["attack_sword_directional_cycle_v21_pass25"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": ONEHAND_UP_F05_ARM_DIAGNOSTIC_REVISION,
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "target_frames": list(TARGET_FRAMES),
        "arm_profile_candidates": [
            {key: float(value) for key, value in profile.items()}
            for profile in ARM_PROFILE_CANDIDATES
        ],
        "base_bone_deltas_degrees": {
            bone_name: list(values)
            for bone_name, values in BASE_BONE_DELTAS_DEGREES.items()
        },
        "search_projections": list(SEARCH_PROJECTIONS),
        "search_angle_offsets": list(SEARCH_ANGLE_OFFSETS),
        "require_zero_edge_alpha": REQUIRE_ZERO_EDGE_ALPHA,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "selected": selected.get("selected"),
        "candidate_count": int(selected.get("candidate_count", 0)),
        "approved_down_v20_changed": False,
        "left_direction_changed": False,
        "right_direction_changed": False,
        "onehand_up_f01_f04_changed": False,
        "twohand_up_changed": False,
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
    pass20_adapter._diagnose_frame = _diagnose_f05_with_arm_search
    pass24_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass24_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass24_adapter.ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION = (
        ONEHAND_UP_F05_ARM_DIAGNOSTIC_REVISION
    )
    pass24_adapter.CORRECTION_PASS = CORRECTION_PASS
    pass24_adapter.REQUIRE_ZERO_EDGE_ALPHA = REQUIRE_ZERO_EDGE_ALPHA
    pass24_adapter._write_manifest_pass24 = _write_manifest_pass25
    try:
        return pass24_adapter.main()
    finally:
        pass20_adapter._diagnose_frame = ORIGINAL_DIAGNOSE_FRAME
        pass24_adapter._write_manifest_pass24 = ORIGINAL_PASS24_WRITE_MANIFEST
        pass24_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS24_SCENE_KEY
        pass24_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS24_CONTACT_SHEET
        pass24_adapter.ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION = (
            ORIGINAL_PASS24_REVISION
        )
        pass24_adapter.CORRECTION_PASS = ORIGINAL_PASS24_CORRECTION_PASS
        pass24_adapter.REQUIRE_ZERO_EDGE_ALPHA = (
            ORIGINAL_PASS24_REQUIRE_ZERO_EDGE_ALPHA
        )


if __name__ == "__main__":
    raise SystemExit(main())
