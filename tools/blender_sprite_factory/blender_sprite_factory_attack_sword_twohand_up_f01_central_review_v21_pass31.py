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
import blender_sprite_factory_attack_sword_twohand_up_f01_arm_diagnostic_v21_pass29 as pass29_adapter
import blender_sprite_factory_attack_sword_twohand_up_f01_review_v21_pass30 as pass30_adapter
import blender_sprite_factory_combat_idle_directional_v11 as calibration_adapter
import blender_sprite_factory_combat_idle_directional_weapon_v12 as weapon_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_entry
from attack_sword_directional_cycle_builder_v21_pass26 import (
    create_attack_sword_directional_cycle_actions_v21_pass26,
)
from attack_sword_directional_cycle_correction_v21_pass31 import (
    ARM_BLEND_CANDIDATES,
    CORRECTION_PASS,
    MAX_ABS_WEAPON_OFFSET_DEGREES,
    MIN_CAMERA_MARGIN_PIXELS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    PREFERRED_ABS_WEAPON_OFFSET_DEGREES,
    REJECTED_REVIEW_ARTIFACT_ID,
    REJECTED_REVIEW_ARTIFACT_SHA256,
    REJECTED_REVIEW_RUN_ID,
    REJECTION_REASON,
    REQUIRE_ZERO_EDGE_ALPHA,
    REVIEW_VARIANT_COUNT,
    SOURCE_FRAME_CANDIDATES,
    TARGET_ACTION_ID,
    TARGET_DIRECTION,
    TARGET_FRAME,
    TARGET_GRIP_ID,
    TWOHAND_UP_F01_CENTRAL_REVIEW_REVISION,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_WRITE_MANIFEST = factory._write_run_manifest
DIAGNOSTIC_SCENE_KEY = "attack_sword_twohand_up_f01_central_review_v21_pass31"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_up_f01_central_review_v21_pass31.png"


def _central_sort_key(candidate: dict[str, object]) -> tuple[object, ...]:
    offset = abs(float(candidate["offset_degrees"]))
    return (
        0 if offset <= PREFERRED_ABS_WEAPON_OFFSET_DEGREES else 1,
        offset,
        int(candidate["source_frame_order"]),
        -float(candidate["screen_projection"]),
        -float(candidate["head_clearance_pixels"]),
        -int(candidate["visible_blade_samples"]),
        -float(candidate["camera_margin_pixels"]),
        0 if candidate["depth_branch"] == "source" else 1,
    )


def _select_review_candidates(
    candidates: list[dict[str, object]],
) -> tuple[dict[str, object], ...]:
    selected: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()
    for candidate in sorted(candidates, key=_central_sort_key):
        identity = (
            int(candidate["source_frame"]),
            round(float(candidate["arm_blend"]), 4),
            str(candidate["depth_branch"]),
            round(float(candidate["screen_projection"]), 6),
            round(float(candidate["offset_degrees"]), 3),
        )
        if identity in seen:
            continue
        seen.add(identity)
        selected.append(candidate)
        if len(selected) == REVIEW_VARIANT_COUNT:
            break
    return tuple(selected)


def _render_review(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    config = context.config
    calibrations = calibration_adapter._direction_calibrations(context, run_dir)
    up_action = factory.bpy.data.actions.get(
        f"{config.character_id}_{TARGET_ACTION_ID}"
    )
    if up_action is None:
        raise RuntimeError(
            "two-hand up f01 central review action is missing: "
            f"{TARGET_ACTION_ID}"
        )
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    artifacts: list[factory.FrameArtifact] = []
    columns: list[dict[str, object]] = []
    target_rotations: dict[str, object] = {}

    try:
        reference_artifact, reference_metadata = pass30_adapter._render_reference(
            context,
            run_dir,
            calibration=calibrations["down"],
        )
        artifacts.append(reference_artifact)
        columns.append(reference_metadata)

        weapon_adapter._set_v12_weapon(TARGET_GRIP_ID, TARGET_DIRECTION)
        factory._assign_action(context.rig, up_action)
        context.rig.rotation_euler[2] = math.radians(
            config.directions[TARGET_DIRECTION]
        )
        target_rotations = pass29_adapter._capture_arm(context, TARGET_FRAME)
        source_rotations_by_frame = {
            int(source_frame): pass29_adapter._capture_arm(
                context,
                int(source_frame),
            )
            for source_frame in SOURCE_FRAME_CANDIDATES
        }

        selected_blend: float | None = None
        geometry_safe_counts: dict[str, int] = {}
        selected_candidates: tuple[dict[str, object], ...] = ()
        for arm_blend in ARM_BLEND_CANDIDATES:
            blend_candidates: list[dict[str, object]] = []
            for source_order, source_frame in enumerate(
                SOURCE_FRAME_CANDIDATES
            ):
                candidates, _ = pass29_adapter._evaluate_arm_pose(
                    context,
                    target_rotations=target_rotations,
                    source_rotations=source_rotations_by_frame[int(source_frame)],
                    source_frame=int(source_frame),
                    source_frame_order=source_order,
                    arm_blend=float(arm_blend),
                )
                central_candidates = [
                    candidate
                    for candidate in candidates
                    if abs(float(candidate["offset_degrees"]))
                    <= MAX_ABS_WEAPON_OFFSET_DEGREES
                    and float(candidate["head_clearance_pixels"])
                    >= MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
                    and int(candidate["visible_blade_samples"])
                    >= MIN_VISIBLE_BLADE_SAMPLES
                    and float(candidate["camera_margin_pixels"])
                    >= MIN_CAMERA_MARGIN_PIXELS
                ]
                geometry_safe_counts[
                    f"source_{int(source_frame)}_blend_{float(arm_blend):.2f}"
                ] = len(central_candidates)
                blend_candidates.extend(central_candidates)

            selected_candidates = _select_review_candidates(blend_candidates)
            if selected_candidates:
                selected_blend = float(arm_blend)
                break

        if selected_blend is None or not selected_candidates:
            raise RuntimeError(
                "two-hand up f01 central review found no candidate within "
                f"{MAX_ABS_WEAPON_OFFSET_DEGREES:.1f} degrees; "
                f"geometry_safe_counts={geometry_safe_counts}"
            )

        for variant_index, candidate in enumerate(
            selected_candidates,
            start=1,
        ):
            selection = f"central_{variant_index:02d}"
            artifact, metadata = pass30_adapter._render_up_candidate(
                context,
                run_dir,
                calibration=calibrations[TARGET_DIRECTION],
                action=up_action,
                target_rotations=target_rotations,
                source_rotations=source_rotations_by_frame[
                    int(candidate["source_frame"])
                ],
                selection=selection,
                candidate=candidate,
                column_index=len(artifacts) + 1,
            )
            if REQUIRE_ZERO_EDGE_ALPHA and any(
                int(value) > 0 for value in metadata["edge_counts"].values()
            ):
                raise RuntimeError(
                    "two-hand up f01 central review accepted edge pixels: "
                    f"{metadata}"
                )
            artifacts.append(artifact)
            columns.append(metadata)

        payload = {
            "correction_pass": CORRECTION_PASS,
            "revision": TWOHAND_UP_F01_CENTRAL_REVIEW_REVISION,
            "selected_arm_blend": selected_blend,
            "maximum_abs_weapon_offset_degrees": (
                MAX_ABS_WEAPON_OFFSET_DEGREES
            ),
            "preferred_abs_weapon_offset_degrees": (
                PREFERRED_ABS_WEAPON_OFFSET_DEGREES
            ),
            "geometry_safe_counts": geometry_safe_counts,
            "columns": columns,
            "manual_selection_required": True,
        }
        factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY] = json.dumps(
            payload,
            sort_keys=True,
        )
        print(
            "ATTACK_SWORD_TWOHAND_UP_F01_CENTRAL_REVIEW_V21_PASS31="
            f"blend:{selected_blend:.2f};"
            f"variants:{len(selected_candidates)};"
            f"offsets:{[float(item['offset_degrees']) for item in selected_candidates]}"
        )
        return artifacts
    finally:
        if target_rotations:
            pass29_adapter._restore_arm(context, target_rotations)
        weapon_adapter._set_v12_weapon(None, None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()


def _write_review_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    expected_count = 1 + REVIEW_VARIANT_COUNT
    if len(artifacts) != expected_count:
        raise RuntimeError(
            "two-hand up f01 central review sheet count drifted: "
            f"expected {expected_count}, got {len(artifacts)}"
        )
    tile_width = int(config.technical.canvas_width)
    tile_height = int(config.technical.canvas_height)
    width = tile_width * len(artifacts)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * tile_height)
        for component in (*background, 1.0)
    ]
    for column_index, artifact in enumerate(artifacts):
        image = factory.bpy.data.images.load(
            str(artifact.output_path),
            check_existing=False,
        )
        try:
            factory._copy_tile(
                pixels,
                width,
                tuple(image.pixels[:]),
                tile_width,
                tile_height,
                column_index * tile_width,
                0,
            )
        finally:
            factory.bpy.data.images.remove(image)
    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_attack_sword_twohand_up_f01_central_review_v21_pass31",
        width=width,
        height=tile_height,
        alpha=True,
        float_buffer=False,
    )
    try:
        sheet.pixels[:] = pixels
        sheet.file_format = "PNG"
        sheet.filepath_raw = str(output_path)
        sheet.save()
    finally:
        factory.bpy.data.images.remove(sheet)
    return output_path


def _write_manifest(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    path = BASE_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload[DIAGNOSTIC_SCENE_KEY] = json.loads(
        str(factory.bpy.context.scene[DIAGNOSTIC_SCENE_KEY])
    )
    payload.update(
        {
            "diagnostic_only": True,
            "rejected_review_run_id": REJECTED_REVIEW_RUN_ID,
            "rejected_review_artifact_id": REJECTED_REVIEW_ARTIFACT_ID,
            "rejected_review_artifact_sha256": (
                REJECTED_REVIEW_ARTIFACT_SHA256
            ),
            "rejection_reason": REJECTION_REASON,
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "contact_sheet_name": CONTACT_SHEET_NAME,
            "approved_down_v20_changed": False,
            "left_direction_changed": False,
            "right_direction_changed": False,
            "onehand_up_changed": False,
            "twohand_up_action_data_changed": False,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "weapon_geometry_deformed": False,
            "materials_changed": False,
            "manual_review_required": True,
        }
    )
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    base_entry.create_combat_idle_down_actions_v01 = (
        create_attack_sword_directional_cycle_actions_v21_pass26
    )
    base_entry.render_pilot_combat_idle_down_v01 = _render_review
    base_entry._write_contact_sheet_combat_idle_down_v01 = _write_review_sheet
    base_entry._write_run_manifest_combat_idle_down_v01 = _write_manifest
    pass29_adapter.depth_search_adapter.pass22_adapter._HEAD_DEPTH_CACHE.clear()
    return base_entry.main()


if __name__ == "__main__":
    raise SystemExit(main())
