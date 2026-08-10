from __future__ import annotations

import hashlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_combat_idle_down_v01 as base_adapter
import blender_sprite_factory_death_down_keyposes_v01 as keypose_adapter
from death_down_cycle_builder_v01 import create_death_down_cycle_actions_v01
from death_down_cycle_profile_v01 import (
    APPROVED_ANCHOR_FRAMES,
    CORPSE_HOLD_FRAME,
    DEATH_DOWN_CYCLE_DURATION_SECONDS,
    DEATH_DOWN_CYCLE_FRAME_ORDER,
    INTERPOLATED_FRAMES,
    SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME,
    SOURCE_KEYPOSE_REVISIONS,
    load_death_down_cycle_profiles_v01,
)
from factory_config import CONTACT_SHEET_BACKGROUND_HEX


PROFILE_PATH = SCRIPT_DIR / "death_down_cycle_profile_v01.py"
BUILDER_PATH = SCRIPT_DIR / "death_down_cycle_builder_v01.py"
CONTACT_SHEET_NAME = "human_warrior_m01_death_base_down_cycles_v01.png"
BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest

_BASE_PROFILES = keypose_adapter._profiles
_BASE_EXPECTED_FRAME_NUMBERS = keypose_adapter.EXPECTED_FRAME_NUMBERS
_BASE_CONTACT_SHEET_NAME = keypose_adapter.CONTACT_SHEET_NAME
_BASE_WAIST_PIXEL_SEAM = keypose_adapter._waist_pixel_seam_top_down
_BASE_UPPER_BODY_OFFSET = keypose_adapter._upper_body_offset


def _profiles(character_id: str) -> tuple[object, ...]:
    return load_death_down_cycle_profiles_v01(character_id)


def _cycle_waist_pixel_seam_top_down(
    frame_number: int,
) -> tuple[tuple[int, int], ...]:
    if frame_number == 6:
        return _BASE_WAIST_PIXEL_SEAM(4)
    if frame_number in (7, 8):
        return _BASE_WAIST_PIXEL_SEAM(5)
    return ()


def _cycle_upper_body_offset(frame_number: int) -> tuple[float, float, float]:
    if frame_number == 6:
        return _BASE_UPPER_BODY_OFFSET(4)
    if frame_number in (7, 8):
        return _BASE_UPPER_BODY_OFFSET(5)
    return (0.0, 0.0, 0.0)


@contextmanager
def _cycle_adapter_contract():
    keypose_adapter._profiles = _profiles
    keypose_adapter.EXPECTED_FRAME_NUMBERS = DEATH_DOWN_CYCLE_FRAME_ORDER
    keypose_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    keypose_adapter._waist_pixel_seam_top_down = _cycle_waist_pixel_seam_top_down
    keypose_adapter._upper_body_offset = _cycle_upper_body_offset
    try:
        yield
    finally:
        keypose_adapter._profiles = _BASE_PROFILES
        keypose_adapter.EXPECTED_FRAME_NUMBERS = _BASE_EXPECTED_FRAME_NUMBERS
        keypose_adapter.CONTACT_SHEET_NAME = _BASE_CONTACT_SHEET_NAME
        keypose_adapter._waist_pixel_seam_top_down = _BASE_WAIST_PIXEL_SEAM
        keypose_adapter._upper_body_offset = _BASE_UPPER_BODY_OFFSET


def _find_frames(
    artifacts: list[factory.FrameArtifact],
    *,
    animation_id: str,
) -> tuple[factory.FrameArtifact, ...]:
    matches = tuple(
        sorted(
            (
                item
                for item in artifacts
                if item.animation_id == animation_id and item.direction == "down"
            ),
            key=lambda item: item.frame_number,
        )
    )
    if tuple(item.frame_number for item in matches) != DEATH_DOWN_CYCLE_FRAME_ORDER:
        raise RuntimeError(f"death down cycle v01 incomplete set: {animation_id}")
    return matches


def _rgba_sha256(path: Path) -> str:
    width, height, rows, _ = keypose_adapter._decode_rgba8_png(path)
    payload = width.to_bytes(4, "big") + height.to_bytes(4, "big")
    payload += b"".join(bytes(row) for row in rows)
    return hashlib.sha256(payload).hexdigest()


def _assert_corpse_hold(
    profiles: tuple[object, ...],
    artifacts: list[factory.FrameArtifact],
) -> None:
    for profile in profiles:
        frames = _find_frames(artifacts, animation_id=profile.animation_id)
        final_frame = next(item for item in frames if item.frame_number == 7)
        hold_frame = next(
            item for item in frames if item.frame_number == CORPSE_HOLD_FRAME
        )
        if _rgba_sha256(final_frame.output_path) != _rgba_sha256(hold_frame.output_path):
            raise RuntimeError(
                f"{profile.death_variant_id} corpse hold differs from final frame"
            )


def render_death_down_cycles_v01(
    context: factory.BuildContext,
    run_dir: Path,
) -> list[factory.FrameArtifact]:
    with _cycle_adapter_contract():
        artifacts = keypose_adapter.render_death_down_keyposes_v01(
            context,
            run_dir,
        )
    profiles = _profiles(context.config.character_id)
    _assert_corpse_hold(profiles, artifacts)
    return artifacts


def _write_cycle_sheet(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    with _cycle_adapter_contract():
        return keypose_adapter._write_keypose_sheet(
            config,
            artifacts,
            output_path,
        )


def _write_contact_sheet_v01(
    config: object,
    artifacts: list[factory.FrameArtifact],
    output_path: Path,
) -> Path:
    result = _write_cycle_sheet(config, artifacts, output_path)
    named_path = output_path.parent / CONTACT_SHEET_NAME
    if named_path != output_path:
        _write_cycle_sheet(config, artifacts, named_path)
    return result


def _profile_payload(
    context: factory.BuildContext,
    profile: object,
    artifacts: list[factory.FrameArtifact],
    named_sheet: Path,
) -> dict[str, object]:
    frames = _find_frames(artifacts, animation_id=profile.animation_id)
    return {
        "profile_revision": profile.revision,
        "source_keypose_revision": SOURCE_KEYPOSE_REVISIONS[
            profile.death_variant_id
        ],
        "death_variant_id": profile.death_variant_id,
        "animation_id": profile.animation_id,
        "direction": profile.direction,
        "fps": profile.fps,
        "duration_seconds": DEATH_DOWN_CYCLE_DURATION_SECONDS,
        "loop": profile.loop,
        "source_stance_variant_id": profile.source_stance_variant_id,
        "source_stance_revision": profile.source_stance_revision,
        "weapon_visible": profile.weapon_visible,
        "weapon_agnostic": True,
        "fall_side": profile.fall_side,
        "final_pose_persistent": profile.final_pose_persistent,
        "gore_mode": profile.gore_mode,
        "detached_part_id": profile.detached_part_id,
        "detachment_frame": profile.detachment_frame,
        "approved_anchor_frames": list(APPROVED_ANCHOR_FRAMES),
        "source_keypose_frame_by_cycle_frame": {
            str(cycle_frame): source_frame
            for cycle_frame, source_frame in SOURCE_KEYPOSE_FRAME_BY_CYCLE_FRAME.items()
        },
        "interpolated_frames": list(INTERPOLATED_FRAMES),
        "corpse_hold_frame": CORPSE_HOLD_FRAME,
        "pixel_seam_frames": (
            [6, 7, 8]
            if profile.gore_mode == "waist_torso_legs_separation"
            else []
        ),
        "pixel_seam_preserves_existing_rgb": True,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "total_rendered_frames": len(frames),
        "appearance_revision": profile.appearance_revision,
        "head_revision": profile.head_revision,
        "proxy_revision": profile.proxy_revision,
        "frames": [
            {
                "frame": item.frame_number,
                "phase": profile.poses[index].phase,
                "width": item.sprite_width,
                "height": item.sprite_height,
                "baseline_y": item.baseline_y,
                "edge_alpha": keypose_adapter._edge_alpha_counts(item.output_path),
                "rgba_sha256": _rgba_sha256(item.output_path),
            }
            for index, item in enumerate(frames)
        ],
        "locked_contract": {
            "down_cycle_only": True,
            "base_weapon_agnostic": True,
            "weapon_visible": False,
            "source_keypose_anchors_preserved": True,
            "corpse_hold_matches_final": True,
            "final_pose_persistent": True,
            "root_translation_used": False,
            "mirroring_used": False,
            "negative_scale_used": False,
            "weapon_geometry_changed": False,
            "materials_changed": False,
            "manual_full_cycle_review_required": True,
            "directional_variants_not_started": True,
            "random_runtime_selection_not_started": True,
            "runtime_connected": False,
        },
    }


def _write_manifest_v01(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_RUN_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    profiles = _profiles(context.config.character_id)
    named_sheet = run_dir / CONTACT_SHEET_NAME
    if not named_sheet.is_file():
        raise RuntimeError("death base down cycles contact sheet is missing")

    payload["contact_sheet_review"] = {
        "background_color": CONTACT_SHEET_BACKGROUND_HEX,
        "rows_top_to_bottom": [profile.death_variant_id for profile in profiles],
        "columns_left_to_right": list(profiles[0].phase_order),
    }
    payload["death_base_down_cycles_v01"] = {
        profile.death_variant_id: _profile_payload(
            context,
            profile,
            artifacts,
            named_sheet,
        )
        for profile in profiles
    }
    payload["death_base_down_cycles_v01_shared"] = {
        "builder_path": context.config.relative_to_repo(BUILDER_PATH),
        "builder_sha256": hashlib.sha256(BUILDER_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(named_sheet),
        "variant_count": len(profiles),
        "frames_per_variant": len(DEATH_DOWN_CYCLE_FRAME_ORDER),
        "total_rendered_frames": len(artifacts),
        "fps": profiles[0].fps,
        "duration_seconds": DEATH_DOWN_CYCLE_DURATION_SECONDS,
        "approved_anchor_frames": list(APPROVED_ANCHOR_FRAMES),
        "interpolated_frames": list(INTERPOLATED_FRAMES),
        "corpse_hold_frame": CORPSE_HOLD_FRAME,
        "weapon_agnostic": True,
        "weapon_visible": False,
        "detachment_variant_count": sum(
            profile.detached_part_id is not None for profile in profiles
        ),
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "death_current_stage": "base_down_cycles_v01",
            "death_variant_ids": [
                profile.death_variant_id for profile in profiles
            ],
            "death_variant_count": len(profiles),
            "death_frame_count_per_variant": len(DEATH_DOWN_CYCLE_FRAME_ORDER),
            "death_total_frame_count": len(artifacts),
            "death_fps": profiles[0].fps,
            "death_duration_seconds": DEATH_DOWN_CYCLE_DURATION_SECONDS,
            "death_weapon_agnostic": True,
            "death_weapon_visible": False,
            "death_source_keypose_anchors_preserved": True,
            "death_corpse_hold_matches_final": True,
            "death_directional_variants_not_started": True,
            "death_random_runtime_selection_not_started": True,
            "death_runtime_connected": False,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    base_adapter.create_combat_idle_down_actions_v01 = (
        create_death_down_cycle_actions_v01
    )
    base_adapter.render_pilot_combat_idle_down_v01 = render_death_down_cycles_v01
    base_adapter._write_contact_sheet_combat_idle_down_v01 = _write_contact_sheet_v01
    base_adapter._write_run_manifest_combat_idle_down_v01 = _write_manifest_v01
    return base_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
