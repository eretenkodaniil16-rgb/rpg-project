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
import blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass02 as pass02_adapter
from attack_sword_twohand_overhead_directional_correction_v21_pass03 import (
    CORRECTION_PASS,
    DIRECTION_SCALE_MULTIPLIER,
    DIRECTIONAL_FRAMING_REVISION,
    PRESERVE_ACTION_CURVES,
    PRESERVE_CHARACTER_LOCAL_WEAPON_ARC,
    PRESERVE_DIRECTIONAL_ASYMMETRY,
    PRESERVE_DOWN_PASS04_PIXELS,
    REQUIRE_ZERO_EDGE_ALPHA,
    SIDE_DIRECTIONS,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
)


CORRECTION_PATH = (
    SCRIPT_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass03.py"
)
PASS03_MANIFEST_KEY = "attack_sword_twohand_overhead_directional_v21_pass03"
ORIGINAL_RENDER_FRAME = (
    pass02_adapter._render_frame_directional_overhead_v21_pass02
)
ORIGINAL_WRITE_MANIFEST = (
    pass02_adapter._write_manifest_directional_overhead_v21_pass02
)


def _render_frame_directional_overhead_v21_pass03(
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
    try:
        scale_multiplier = float(DIRECTION_SCALE_MULTIPLIER[direction])
    except KeyError as exc:
        raise KeyError(
            f"directional overhead pass03 unknown direction: {direction}"
        ) from exc
    if not math.isfinite(scale_multiplier) or scale_multiplier <= 0.0:
        raise RuntimeError(
            "directional overhead pass03 invalid framing multiplier: "
            f"{direction}={scale_multiplier}"
        )
    effective_scale = (
        None if fixed_scale is None else float(fixed_scale) * scale_multiplier
    )
    result = ORIGINAL_RENDER_FRAME(
        context,
        animation_id=animation_id,
        direction=direction,
        frame_number=frame_number,
        raw_dir=raw_dir,
        frame_dir=frame_dir,
        output_name=output_name,
        fixed_scale=effective_scale,
        fixed_center_x=fixed_center_x,
        use_clearance_planner=use_clearance_planner,
    )
    if not pass02_adapter.base_adapter._is_target(
        animation_id,
        direction,
        frame_number,
    ):
        return result

    artifact, calibration = result
    edge_counts = pass02_adapter.base_adapter.keypose_adapter._edge_alpha_counts(
        artifact.output_path
    )
    if REQUIRE_ZERO_EDGE_ALPHA and any(int(value) for value in edge_counts.values()):
        raise RuntimeError(
            "directional overhead pass03 frame still touches canvas edge: "
            f"{direction}/f{frame_number:02d}={edge_counts}"
        )

    scene = factory.bpy.context.scene
    key = f"{direction}/f{frame_number:02d}"
    metrics = json.loads(
        str(
            scene.get(
                pass02_adapter.base_adapter.METRICS_SCENE_KEY,
                "{}",
            )
        )
    )
    if key not in metrics:
        raise RuntimeError(
            f"directional overhead pass03 metrics missing: {key}"
        )
    metrics[key]["direction_scale_multiplier"] = scale_multiplier
    metrics[key]["directional_framing_only"] = True
    metrics[key]["action_curves_changed"] = False
    scene[pass02_adapter.base_adapter.METRICS_SCENE_KEY] = json.dumps(
        metrics,
        sort_keys=True,
    )
    print(
        "ATTACK_SWORD_TWOHAND_OVERHEAD_DIRECTIONAL_V21_PASS03="
        f"{key};scale_multiplier:{scale_multiplier:.3f};"
        f"effective_scale:{float(effective_scale):.6f};edges:{edge_counts}"
    )
    return artifact, calibration


def _write_manifest_directional_overhead_v21_pass03(
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
                pass02_adapter.base_adapter.METRICS_SCENE_KEY,
                "{}",
            )
        )
    )

    if not math.isclose(
        float(DIRECTION_SCALE_MULTIPLIER["down"]),
        1.0,
        rel_tol=0.0,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "directional overhead pass03 down framing must remain unchanged"
        )
    if not math.isclose(
        float(DIRECTION_SCALE_MULTIPLIER["left"]),
        float(DIRECTION_SCALE_MULTIPLIER["right"]),
        rel_tol=0.0,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "directional overhead pass03 side framing multipliers diverged"
        )

    expected_metrics = {
        f"{direction}/f{frame_number:02d}"
        for direction in pass02_adapter.base_adapter.DIRECTION_ORDER
        for frame_number in pass02_adapter.base_adapter.TARGET_FRAMES
    }
    if set(metrics) != expected_metrics:
        raise RuntimeError(
            "directional overhead pass03 metrics are incomplete: "
            f"actual={sorted(metrics)}, expected={sorted(expected_metrics)}"
        )
    for key, metric in metrics.items():
        direction = key.split("/", 1)[0]
        actual_multiplier = float(metric.get("direction_scale_multiplier", -1.0))
        expected_multiplier = float(DIRECTION_SCALE_MULTIPLIER[direction])
        if not math.isclose(
            actual_multiplier,
            expected_multiplier,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        ):
            raise RuntimeError(
                "directional overhead pass03 framing metric drifted: "
                f"{key}={actual_multiplier}, expected={expected_multiplier}"
            )
        edge_counts = {
            str(edge): int(count)
            for edge, count in dict(metric.get("edge_counts", {})).items()
        }
        if REQUIRE_ZERO_EDGE_ALPHA and any(edge_counts.values()):
            raise RuntimeError(
                "directional overhead pass03 manifest found edge alpha: "
                f"{key}={edge_counts}"
            )

    payload[PASS03_MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": DIRECTIONAL_FRAMING_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "direction_scale_multiplier": {
            direction: float(value)
            for direction, value in DIRECTION_SCALE_MULTIPLIER.items()
        },
        "side_directions": list(SIDE_DIRECTIONS),
        "zero_edge_alpha_required": REQUIRE_ZERO_EDGE_ALPHA,
        "action_curves_preserved": PRESERVE_ACTION_CURVES,
        "character_local_weapon_arc_preserved": (
            PRESERVE_CHARACTER_LOCAL_WEAPON_ARC
        ),
        "approved_down_pass04_pixels_preserved": PRESERVE_DOWN_PASS04_PIXELS,
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
            "attack_sword_01_twohand_overhead_directional_framing": (
                DIRECTIONAL_FRAMING_REVISION
            ),
            "attack_sword_01_twohand_overhead_action_curves_preserved": True,
            "attack_sword_01_twohand_overhead_down_pixels_preserved": True,
            "attack_sword_01_twohand_overhead_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    pass02_adapter._render_frame_directional_overhead_v21_pass02 = (
        _render_frame_directional_overhead_v21_pass03
    )
    pass02_adapter._write_manifest_directional_overhead_v21_pass02 = (
        _write_manifest_directional_overhead_v21_pass03
    )
    try:
        return pass02_adapter.main()
    finally:
        pass02_adapter._render_frame_directional_overhead_v21_pass02 = (
            ORIGINAL_RENDER_FRAME
        )
        pass02_adapter._write_manifest_directional_overhead_v21_pass02 = (
            ORIGINAL_WRITE_MANIFEST
        )


if __name__ == "__main__":
    raise SystemExit(main())
