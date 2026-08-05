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
import blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass04 as pass04_adapter
from attack_sword_twohand_overhead_directional_correction_v21_pass05 import (
    CORRECTION_PASS,
    DIRECTIONAL_FRAMING_REVISION,
    PRESERVE_ACTION_CURVES,
    PRESERVE_CHARACTER_LOCAL_WEAPON_ARC,
    PRESERVE_DIRECTIONAL_ASYMMETRY,
    PRESERVE_DOWN_PASS04_PIXELS,
    PRESERVE_SIDE_PASS03_FRAMING,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    SOURCE_FIXED_SCALE,
    SOURCE_RAW_F03_ALPHA_HEIGHT,
    TARGET_NORMALIZED_ALPHA_HEIGHT,
    UP_SCALE_MULTIPLIER,
)


CORRECTION_PATH = (
    SCRIPT_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass05.py"
)
PASS05_MANIFEST_KEY = "attack_sword_twohand_overhead_directional_v21_pass05"
ORIGINAL_UP_SCALE_MULTIPLIER = float(pass04_adapter.UP_SCALE_MULTIPLIER)
ORIGINAL_WRITE_MANIFEST = (
    pass04_adapter._write_manifest_directional_overhead_v21_pass04
)


def _write_manifest_directional_overhead_v21_pass05(
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
        str(
            factory.bpy.context.scene.get(
                pass04_adapter.pass03_adapter.pass02_adapter.base_adapter.METRICS_SCENE_KEY,
                "{}",
            )
        )
    )
    actual_scale = float(
        pass04_adapter.pass03_adapter.DIRECTION_SCALE_MULTIPLIER["up"]
    )
    if not math.isclose(
        actual_scale,
        UP_SCALE_MULTIPLIER,
        rel_tol=0.0,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "directional overhead pass05 measured rear scale drifted: "
            f"actual={actual_scale}, expected={UP_SCALE_MULTIPLIER}"
        )
    up_metrics = {
        key: value for key, value in metrics.items() if key.startswith("up/")
    }
    expected_up_keys = {
        f"up/f{frame_number:02d}"
        for frame_number in (
            pass04_adapter.pass03_adapter.pass02_adapter.base_adapter.TARGET_FRAMES
        )
    }
    if set(up_metrics) != expected_up_keys:
        raise RuntimeError(
            "directional overhead pass05 rear metrics are incomplete: "
            f"actual={sorted(up_metrics)}, expected={sorted(expected_up_keys)}"
        )
    for key, metric in up_metrics.items():
        edge_counts = {
            str(edge): int(count)
            for edge, count in dict(metric.get("edge_counts", {})).items()
        }
        if REQUIRE_ZERO_EDGE_ALPHA and any(edge_counts.values()):
            raise RuntimeError(
                f"directional overhead pass05 rear frame touched edge: {key}={edge_counts}"
            )
        if not math.isclose(
            float(metric.get("direction_scale_multiplier", -1.0)),
            UP_SCALE_MULTIPLIER,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        ):
            raise RuntimeError(
                f"directional overhead pass05 rear metric scale drifted: {key}"
            )

    payload[PASS05_MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": DIRECTIONAL_FRAMING_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "up_scale_multiplier": UP_SCALE_MULTIPLIER,
        "source_raw_f03_alpha_height": SOURCE_RAW_F03_ALPHA_HEIGHT,
        "source_fixed_scale": SOURCE_FIXED_SCALE,
        "target_normalized_alpha_height": TARGET_NORMALIZED_ALPHA_HEIGHT,
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "action_curves_preserved": PRESERVE_ACTION_CURVES,
        "character_local_weapon_arc_preserved": (
            PRESERVE_CHARACTER_LOCAL_WEAPON_ARC
        ),
        "approved_down_pass04_pixels_preserved": PRESERVE_DOWN_PASS04_PIXELS,
        "side_pass03_framing_preserved": PRESERVE_SIDE_PASS03_FRAMING,
        "directional_asymmetry_preserved": PRESERVE_DIRECTIONAL_ASYMMETRY,
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
            "attack_sword_01_twohand_overhead_rear_framing": (
                DIRECTIONAL_FRAMING_REVISION
            ),
            "attack_sword_01_twohand_overhead_all_direction_action_curves_preserved": True,
            "attack_sword_01_twohand_overhead_down_pixels_preserved": True,
            "attack_sword_01_twohand_overhead_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_contract() -> None:
    pass04_adapter.UP_SCALE_MULTIPLIER = UP_SCALE_MULTIPLIER
    pass04_adapter._write_manifest_directional_overhead_v21_pass04 = (
        _write_manifest_directional_overhead_v21_pass05
    )


def _restore_contract() -> None:
    pass04_adapter.UP_SCALE_MULTIPLIER = ORIGINAL_UP_SCALE_MULTIPLIER
    pass04_adapter._write_manifest_directional_overhead_v21_pass04 = (
        ORIGINAL_WRITE_MANIFEST
    )


def main() -> int:
    _apply_contract()
    try:
        return pass04_adapter.main()
    finally:
        _restore_contract()


if __name__ == "__main__":
    raise SystemExit(main())
