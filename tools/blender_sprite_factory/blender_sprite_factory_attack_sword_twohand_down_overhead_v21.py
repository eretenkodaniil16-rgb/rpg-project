from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import attack_sword_down_cycle_builder_v20 as cycle_builder
import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_down_cycle_v20 as cycle_adapter
import blender_sprite_factory_attack_sword_down_cycle_v20_pass05 as pass05_adapter
import blender_sprite_factory_attack_sword_down_keyposes_v17 as keypose_adapter
from attack_sword_twohand_down_overhead_profile_v21 import (
    OVERHEAD_ACTION_ID,
    OVERHEAD_REVIEW_REVISION,
    OVERHEAD_SOURCE_ACTION_ID,
    OVERHEAD_TRAJECTORY_ID,
    TWOHAND_OVERHEAD_POSES,
    load_attack_sword_twohand_down_overhead_profile_v21,
)


PROFILE_PATH = SCRIPT_DIR / "attack_sword_twohand_down_overhead_profile_v21.py"
CONTACT_SHEET_NAME = "attack_sword_01_twohand_down_overhead_review_v21.png"
MANIFEST_KEY = "attack_sword_twohand_down_overhead_v21"

ORIGINAL_BUILDER_PROFILE_LOADER = cycle_builder.load_attack_sword_down_cycle_profile_v20
ORIGINAL_CYCLE_PROFILE_LOADER = cycle_adapter.load_attack_sword_down_cycle_profile_v20
ORIGINAL_CYCLE_CONTACT_SHEET_NAME = cycle_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS05_CONTACT_SHEET_NAME = pass05_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS05_WRITE_MANIFEST = pass05_adapter._write_manifest_v20_pass05


def _target_artifacts(artifacts: list[factory.FrameArtifact]) -> tuple[factory.FrameArtifact, ...]:
    selected = tuple(
        sorted(
            (
                artifact
                for artifact in artifacts
                if artifact.animation_id == OVERHEAD_ACTION_ID
                and artifact.direction == "down"
            ),
            key=lambda artifact: artifact.frame_number,
        )
    )
    if tuple(item.frame_number for item in selected) != tuple(range(1, 9)):
        raise RuntimeError("two-hand overhead v21 did not render f01-f08")
    return selected


def _write_manifest_overhead_v21(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = ORIGINAL_PASS05_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames = _target_artifacts(artifacts)

    if {item.baseline_y for item in frames} != {91}:
        raise RuntimeError("two-hand overhead v21 baseline drifted")
    for item in frames:
        if item.sprite_width <= 0 or item.sprite_height <= 0:
            raise RuntimeError(
                f"two-hand overhead v21 produced empty f{item.frame_number:02d}"
            )
        if item.sprite_width > 96 or item.sprite_height > 96:
            raise RuntimeError(
                "two-hand overhead v21 exceeded 96x96 canvas at "
                f"f{item.frame_number:02d}"
            )

    f01_sha256 = hashlib.sha256(frames[0].output_path.read_bytes()).hexdigest()
    f08_sha256 = hashlib.sha256(frames[7].output_path.read_bytes()).hexdigest()
    if f01_sha256 != f08_sha256:
        raise RuntimeError(
            "two-hand overhead v21 settle does not return exactly to guard"
        )

    edge_counts: dict[str, dict[str, int]] = {}
    for item in frames:
        counts = keypose_adapter._edge_alpha_counts(item.output_path)
        touched = {edge: int(count) for edge, count in counts.items() if count > 0}
        if touched:
            raise RuntimeError(
                "two-hand overhead v21 touched canvas edge at "
                f"f{item.frame_number:02d}: {touched}"
            )
        edge_counts[f"f{item.frame_number:02d}"] = {
            edge: int(count) for edge, count in counts.items()
        }

    action = factory.bpy.data.actions.get(
        f"{context.config.character_id}_{OVERHEAD_ACTION_ID}"
    )
    if action is None:
        raise RuntimeError("two-hand overhead v21 action is missing from source blend")
    action["overhead_review_revision"] = OVERHEAD_REVIEW_REVISION
    action["overhead_centered_vertical_trajectory"] = True
    action["overhead_source_action_id"] = OVERHEAD_SOURCE_ACTION_ID
    action["overhead_manual_review_required"] = True
    action["runtime_connected"] = False

    payload[MANIFEST_KEY] = {
        "revision": OVERHEAD_REVIEW_REVISION,
        "profile_path": context.config.relative_to_repo(PROFILE_PATH),
        "profile_sha256": hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(
            run_dir / CONTACT_SHEET_NAME
        ),
        "target_action_id": OVERHEAD_ACTION_ID,
        "source_action_id": OVERHEAD_SOURCE_ACTION_ID,
        "trajectory_id": OVERHEAD_TRAJECTORY_ID,
        "frame_count": len(frames),
        "frame_order": [item.frame_number for item in frames],
        "phase_order": [pose.phase for pose in TWOHAND_OVERHEAD_POSES],
        "baseline_y": 91,
        "guard_sha256": f01_sha256,
        "settle_sha256": f08_sha256,
        "guard_settle_pixel_identical": True,
        "edge_counts": edge_counts,
        "centered_overhead_motion": True,
        "lateral_pelvis_motion_used": False,
        "torso_yaw_used": False,
        "root_translation_used": False,
        "mirroring_used": False,
        "negative_scale_used": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "materials_changed": False,
        "onehand_cycle_changed": False,
        "approved_down_v20_replaced": False,
        "runtime_connected": False,
        "manual_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_twohand_down_overhead_review_revision": (
                OVERHEAD_REVIEW_REVISION
            ),
            "attack_sword_01_twohand_down_overhead_action_id": OVERHEAD_ACTION_ID,
            "attack_sword_01_twohand_down_overhead_centered": True,
            "attack_sword_01_twohand_down_overhead_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_overhead_contract() -> None:
    cycle_builder.load_attack_sword_down_cycle_profile_v20 = (
        load_attack_sword_twohand_down_overhead_profile_v21
    )
    cycle_adapter.load_attack_sword_down_cycle_profile_v20 = (
        load_attack_sword_twohand_down_overhead_profile_v21
    )
    cycle_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass05_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass05_adapter._write_manifest_v20_pass05 = _write_manifest_overhead_v21


def _restore_overhead_contract() -> None:
    cycle_builder.load_attack_sword_down_cycle_profile_v20 = (
        ORIGINAL_BUILDER_PROFILE_LOADER
    )
    cycle_adapter.load_attack_sword_down_cycle_profile_v20 = (
        ORIGINAL_CYCLE_PROFILE_LOADER
    )
    cycle_adapter.CONTACT_SHEET_NAME = ORIGINAL_CYCLE_CONTACT_SHEET_NAME
    pass05_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS05_CONTACT_SHEET_NAME
    pass05_adapter._write_manifest_v20_pass05 = ORIGINAL_PASS05_WRITE_MANIFEST


def main() -> int:
    _apply_overhead_contract()
    try:
        return pass05_adapter.main()
    finally:
        _restore_overhead_contract()


if __name__ == "__main__":
    raise SystemExit(main())
