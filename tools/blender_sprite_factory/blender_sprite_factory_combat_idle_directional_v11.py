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
import blender_sprite_factory_combat_idle_down_cycles_v10 as previous_adapter
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
from combat_idle_directional_profile_v11 import (
    DIRECTION_ORDER,
    CombatIdleDirectionalCandidateV11,
    load_combat_idle_directional_profile_v11,
)
from combat_idle_down_cycles_builder_v10 import create_combat_idle_cycles_v10
from combat_idle_down_cycles_profile_v10 import load_combat_idle_cycles_profile_v10
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


BASE_RENDER = previous_adapter.render_combat_idle_cycles_v10
BASE_CONTACT_SHEET = previous_adapter._write_contact_sheet_v10
BASE_WRITE_MANIFEST = previous_adapter._write_manifest_v10
PROFILE_PATH = SCRIPT_DIR / "combat_idle_directional_profile_v11.py"
COMPARISON_SHEET_NAME = "combat_idle_directional_v11.png"


def _direction_calibrations(
    context: factory.BuildContext,
    run_dir: Path,
) -> dict[str, factory.FramingCalibration]:
    config = context.config
    revision = context.proxy_revision
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]
    factory._assign_action(context.rig, idle_action)
    previous_adapter._set_cycle_weapon(None)

    calibrations: dict[str, factory.FramingCalibration] = {}
    down_scale: float | None = None
    for direction in DIRECTION_ORDER:
        context.rig.rotation_euler[2] = math.radians(config.directions[direction])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()
        _, calibration = factory._render_frame(
            context,
            animation_id="combat_idle_direction_calibration_v11",
            direction=direction,
            frame_number=1,
            raw_dir=raw_dir,
            frame_dir=frame_dir,
            output_name=(
                f"{config.character_id}_combat_idle_direction_calibration_v11_"
                f"{direction}_proxy_{revision}.png"
            ),
            fixed_scale=down_scale,
            fixed_center_x=None,
        )
        calibrations[direction] = calibration
        if direction == "down":
            down_scale = calibration.scale

    if tuple(calibrations) != DIRECTION_ORDER:
        raise RuntimeError("combat idle directional v11 calibration order drifted")
    return calibrations


def _source_cycle(candidate: CombatIdleDirectionalCandidateV11) -> object:
    cycles = load_combat_idle_cycles_profile_v10("human_warrior_m01")
    matches = [cycle for cycle in cycles.cycles if cycle.cycle_id == candidate.source_cycle_id]
    if len(matches) != 1:
        raise RuntimeError(
            f"combat idle directional v11 cannot resolve source {candidate.source_cycle_id}"
        )
    return matches[0]


def _approved_down_artifact(
    artifacts: list[factory.FrameArtifact],
    source_animation_id: str,
) -> factory.FrameArtifact:
    matches = [
        item
        for item in artifacts
        if item.animation_id == source_animation_id
        and item.direction == "down"
        and item.frame_number == 1
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"combat idle directional v11 requires one approved down source for {source_animation_id}"
        )
    return matches[0]


def render_combat_idle_directional_v11(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    artifacts = BASE_RENDER(context, run_dir)
    config = context.config
    revision = context.proxy_revision
    profile = load_combat_idle_directional_profile_v11(config.character_id)
    cycle_profile = load_combat_idle_cycles_profile_v10(config.character_id)
    cycle_by_id = {cycle.cycle_id: cycle for cycle in cycle_profile.cycles}
    calibrations = _direction_calibrations(context, run_dir)
    down_scale = calibrations["down"].scale
    raw_dir = run_dir / "raw"
    frame_dir = run_dir / "frames"
    idle_action = factory.bpy.data.actions[f"{config.character_id}_idle"]

    try:
        for candidate in profile.candidates:
            cycle = cycle_by_id[candidate.source_cycle_id]
            action = factory.bpy.data.actions.get(
                f"{config.character_id}_{candidate.source_animation_id}"
            )
            if action is None or action.get("profile_revision") != "v10":
                raise RuntimeError(
                    f"combat idle directional v11 cannot find v10 action "
                    f"{candidate.source_animation_id}"
                )
            factory._assign_action(context.rig, action)
            previous_adapter._set_cycle_weapon(cycle)
            factory.bpy.context.scene.frame_set(1)

            rendered: dict[str, factory.FrameArtifact] = {}
            for direction in candidate.directions:
                context.rig.rotation_euler[2] = math.radians(config.directions[direction])
                factory.bpy.context.view_layer.update()
                artifact, _ = factory._render_frame(
                    context,
                    animation_id=candidate.render_animation_id,
                    direction=direction,
                    frame_number=1,
                    raw_dir=raw_dir,
                    frame_dir=frame_dir,
                    output_name=(
                        f"{config.character_id}_{candidate.render_animation_id}_"
                        f"{direction}_f01_proxy_{revision}.png"
                    ),
                    fixed_scale=down_scale,
                    fixed_center_x=calibrations[direction].source_center_x,
                )
                artifacts.append(artifact)
                rendered[direction] = artifact

            approved = _approved_down_artifact(artifacts, candidate.source_animation_id)
            if rendered["down"].output_path.read_bytes() != approved.output_path.read_bytes():
                raise RuntimeError(
                    f"combat idle directional v11 changed approved down pixels for "
                    f"{candidate.candidate_id}"
                )
    finally:
        previous_adapter._set_cycle_weapon(None)
        factory._assign_action(context.rig, idle_action)
        context.rig.rotation_euler[2] = math.radians(config.directions["down"])
        factory.bpy.context.scene.frame_set(1)
        factory.bpy.context.view_layer.update()

    return artifacts


def _candidate_artifacts(
    artifacts: list[factory.FrameArtifact],
    candidate: CombatIdleDirectionalCandidateV11,
) -> tuple[factory.FrameArtifact, ...]:
    by_direction = {
        item.direction: item
        for item in artifacts
        if item.animation_id == candidate.render_animation_id
    }
    if tuple(direction for direction in DIRECTION_ORDER if direction in by_direction) != DIRECTION_ORDER:
        raise RuntimeError(
            f"combat idle directional v11 is missing directions for {candidate.candidate_id}"
        )
    return tuple(by_direction[direction] for direction in DIRECTION_ORDER)


def _write_directional_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    profile = load_combat_idle_directional_profile_v11(config.character_id)
    tile_width = config.technical.canvas_width
    tile_height = config.technical.canvas_height
    width = tile_width * len(DIRECTION_ORDER)
    height = tile_height * len(profile.candidates)
    background = factory._hex_to_linear_rgb(CONTACT_SHEET_BACKGROUND_HEX)
    pixels = [
        component
        for _ in range(width * height)
        for component in (*background, 1.0)
    ]

    for row_index, candidate in enumerate(profile.candidates):
        row_y = (len(profile.candidates) - 1 - row_index) * tile_height
        for column_index, artifact in enumerate(
            _candidate_artifacts(artifacts, candidate)
        ):
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
                    row_y,
                )
            finally:
                factory.bpy.data.images.remove(image)

    sheet = factory.bpy.data.images.new(
        "human_warrior_m01_combat_idle_directional_v11",
        width=width,
        height=height,
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


def _write_contact_sheet_v11(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = BASE_CONTACT_SHEET(config, artifacts, output_path)
    _write_directional_sheet(
        config,
        artifacts,
        output_path.parent / COMPARISON_SHEET_NAME,
    )
    return result


def _write_manifest_v11(
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
    profile = load_combat_idle_directional_profile_v11(context.config.character_id)
    comparison_path = run_dir / COMPARISON_SHEET_NAME
    if not comparison_path.is_file():
        raise RuntimeError("combat idle directional v11 comparison sheet is missing")

    rendered_candidates: list[dict[str, object]] = []
    for candidate in profile.candidates:
        direction_frames = _candidate_artifacts(artifacts, candidate)
        rendered_candidates.append(
            {
                "candidate_id": candidate.candidate_id,
                "display_name": candidate.display_name,
                "render_animation_id": candidate.render_animation_id,
                "source_cycle_id": candidate.source_cycle_id,
                "source_animation_id": candidate.source_animation_id,
                "source_revision": candidate.source_revision,
                "grip_mode": candidate.grip_mode,
                "weapon_variant_id": candidate.weapon_variant_id,
                "directions": [
                    {
                        "direction": artifact.direction,
                        "width": artifact.sprite_width,
                        "height": artifact.sprite_height,
                        "baseline_y": artifact.baseline_y,
                        "approved_control": artifact.direction == "down",
                    }
                    for artifact in direction_frames
                ],
            }
        )

    payload["combat_idle_directional_v11"] = {
        "profile_revision": profile.revision,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "comparison_sheet": context.config.relative_to_repo(comparison_path),
        "comparison_sheet_layout": {
            "columns_left_to_right": list(DIRECTION_ORDER),
            "rows_top_to_bottom": [
                "onehand_ready_v10_from_v09",
                "twohand_center_high_v10_from_v06",
            ],
        },
        "approved_direction_control": "down",
        "manual_review_directions": list(profile.review_directions),
        "candidates": rendered_candidates,
        "locked_contract": {
            "appearance_v03_unchanged": True,
            "approved_idle_walk_and_combat_down_unchanged": True,
            "down_pixels_identical_to_approved_v10": True,
            "source_cycle_frame": 1,
            "weapon_geometry_rebuilt": False,
            "pose_actions_rebuilt": False,
            "real_rig_rotation_per_direction": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "root_translation_used": False,
        },
        "status": "directional_static_candidates_require_manual_review",
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "combat_idle_active_stage": "directional_static_v11",
            "combat_idle_directional_approved_control": "down_v10",
            "combat_idle_directional_review_required": True,
            "combat_idle_directional_cycles_not_started": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = create_combat_idle_cycles_v10
    base_adapter.render_pilot_combat_idle_down_v01 = render_combat_idle_directional_v11
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v11
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v11
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
