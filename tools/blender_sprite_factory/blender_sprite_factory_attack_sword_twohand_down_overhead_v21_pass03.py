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
import blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass02 as pass02_adapter
from attack_sword_twohand_down_overhead_correction_v21_pass03 import (
    CORRECTION_PASS,
    F03_SCREEN_PROJECTION,
    OVERHEAD_WEAPON_ARC_REVISION,
    PRESERVE_BODY_ACTION,
    PRESERVE_F02,
    PRESERVE_F04_F07_PROFILE,
    PRESERVE_WEAPON_GEOMETRY,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_ARTIFACT_SHA256,
    SOURCE_FAILED_RUN_ID,
    SOURCE_FAILURE,
    TARGET_FRAME,
)


CORRECTION_PATH = (
    SCRIPT_DIR / "attack_sword_twohand_down_overhead_correction_v21_pass03.py"
)
PASS03_MANIFEST_KEY = "attack_sword_twohand_down_overhead_v21_pass03"
ORIGINAL_PROJECTION_BY_FRAME = dict(pass02_adapter.SCREEN_PROJECTION_BY_FRAME)
ORIGINAL_REVISION = pass02_adapter.OVERHEAD_WEAPON_ARC_REVISION
ORIGINAL_WRITE_MANIFEST = pass02_adapter._write_manifest_overhead_v21_pass02


def _write_manifest_overhead_v21_pass03(
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
    pass02_payload = payload.get(
        pass02_adapter.PASS02_MANIFEST_KEY,
        {},
    )
    metrics = dict(pass02_payload.get("render_metrics", {}))
    f03 = dict(metrics.get("f03", {}))
    if not f03:
        raise RuntimeError("two-hand overhead pass03 f03 metrics are missing")
    actual_projection = float(f03["requested_screen_projection"])
    if not math.isclose(
        actual_projection,
        F03_SCREEN_PROJECTION,
        rel_tol=0.0,
        abs_tol=1.0e-9,
    ):
        raise RuntimeError(
            "two-hand overhead pass03 f03 projection drifted: "
            f"{actual_projection}, expected={F03_SCREEN_PROJECTION}"
        )
    edge_counts = {
        str(edge): int(count)
        for edge, count in dict(f03["edge_counts"]).items()
    }
    if REQUIRE_ZERO_EDGE_ALPHA and any(edge_counts.values()):
        raise RuntimeError(
            "two-hand overhead pass03 f03 still touches canvas edge: "
            f"{edge_counts}"
        )

    payload[PASS03_MANIFEST_KEY] = {
        "correction_pass": CORRECTION_PASS,
        "revision": OVERHEAD_WEAPON_ARC_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(
            CORRECTION_PATH.read_bytes()
        ).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "target_frame": TARGET_FRAME,
        "f03_screen_projection": F03_SCREEN_PROJECTION,
        "f03_edge_counts": edge_counts,
        "f02_preserved": PRESERVE_F02,
        "f04_f07_profile_preserved": PRESERVE_F04_F07_PROFILE,
        "body_action_preserved": PRESERVE_BODY_ACTION,
        "weapon_geometry_preserved": PRESERVE_WEAPON_GEOMETRY,
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
        "manual_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_twohand_down_overhead_weapon_arc_revision": (
                OVERHEAD_WEAPON_ARC_REVISION
            ),
            "attack_sword_01_twohand_down_overhead_f03_contained": True,
            "attack_sword_01_twohand_down_overhead_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _apply_pass03_contract() -> None:
    pass02_adapter.SCREEN_PROJECTION_BY_FRAME[TARGET_FRAME] = (
        F03_SCREEN_PROJECTION
    )
    pass02_adapter.OVERHEAD_WEAPON_ARC_REVISION = (
        OVERHEAD_WEAPON_ARC_REVISION
    )
    pass02_adapter._write_manifest_overhead_v21_pass02 = (
        _write_manifest_overhead_v21_pass03
    )


def _restore_pass03_contract() -> None:
    pass02_adapter.SCREEN_PROJECTION_BY_FRAME.clear()
    pass02_adapter.SCREEN_PROJECTION_BY_FRAME.update(
        ORIGINAL_PROJECTION_BY_FRAME
    )
    pass02_adapter.OVERHEAD_WEAPON_ARC_REVISION = ORIGINAL_REVISION
    pass02_adapter._write_manifest_overhead_v21_pass02 = (
        ORIGINAL_WRITE_MANIFEST
    )


def main() -> int:
    _apply_pass03_contract()
    try:
        return pass02_adapter.main()
    finally:
        _restore_pass03_contract()


if __name__ == "__main__":
    raise SystemExit(main())
