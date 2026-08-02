from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_attack_sword_onehand_up_depth_aware_diagnostic_v21 as pass22_adapter
from attack_sword_directional_cycle_correction_v21_pass23 import (
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    FULLY_OCCLUDED_CLEARANCE_PIXELS,
    MIN_VISIBLE_BLADE_SAMPLES,
    ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_TECHNICAL_ARTIFACT_ID,
    SOURCE_TECHNICAL_RUN_ID,
)


ORIGINAL_PASS22_CLEARANCE = pass22_adapter._depth_aware_visible_blade_head_clearance
ORIGINAL_PASS22_WRITE_MANIFEST = pass22_adapter._write_manifest_pass22
ORIGINAL_PASS22_SCENE_KEY = pass22_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS22_CONTACT_SHEET = pass22_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS22_REVISION = pass22_adapter.ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION
ORIGINAL_PASS22_REQUIRE_ZERO_EDGE_ALPHA = pass22_adapter.REQUIRE_ZERO_EDGE_ALPHA


def _depth_search_visible_blade_head_clearance(
    objects: tuple[object, ...],
) -> float:
    scene = factory.bpy.context.scene
    scene["attack_sword_onehand_up_pass23_fully_occluded"] = False
    scene["attack_sword_onehand_up_pass23_insufficient_visible_samples"] = False
    try:
        clearance = float(ORIGINAL_PASS22_CLEARANCE(objects))
    except RuntimeError as error:
        if (
            str(error)
            != "one-hand up depth-aware diagnostic could not evaluate blade clearance"
        ):
            raise
        scene["attack_sword_onehand_up_pass22_clearance"] = float(
            FULLY_OCCLUDED_CLEARANCE_PIXELS
        )
        scene["attack_sword_onehand_up_pass22_visible_samples"] = 0
        scene["attack_sword_onehand_up_pass23_fully_occluded"] = True
        return float(FULLY_OCCLUDED_CLEARANCE_PIXELS)

    visible_samples = int(
        scene.get("attack_sword_onehand_up_pass22_visible_samples", 0)
    )
    if visible_samples < MIN_VISIBLE_BLADE_SAMPLES:
        scene["attack_sword_onehand_up_pass22_clearance"] = float(
            FULLY_OCCLUDED_CLEARANCE_PIXELS
        )
        scene["attack_sword_onehand_up_pass23_insufficient_visible_samples"] = True
        return float(FULLY_OCCLUDED_CLEARANCE_PIXELS)
    return clearance


def _write_manifest_pass23(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS22_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    scene = factory.bpy.context.scene
    payload["attack_sword_directional_cycle_v21_pass23"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION,
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "minimum_visible_blade_samples": MIN_VISIBLE_BLADE_SAMPLES,
        "fully_occluded_clearance_pixels": FULLY_OCCLUDED_CLEARANCE_PIXELS,
        "require_zero_edge_alpha": REQUIRE_ZERO_EDGE_ALPHA,
        "source_technical_run_id": SOURCE_TECHNICAL_RUN_ID,
        "source_technical_artifact_id": SOURCE_TECHNICAL_ARTIFACT_ID,
        "selected_fully_occluded": bool(
            scene.get("attack_sword_onehand_up_pass23_fully_occluded", False)
        ),
        "selected_insufficient_visible_samples": bool(
            scene.get(
                "attack_sword_onehand_up_pass23_insufficient_visible_samples",
                False,
            )
        ),
        "selected_visible_samples": int(
            scene.get("attack_sword_onehand_up_pass22_visible_samples", 0)
        ),
        "selected_occluded_samples": int(
            scene.get("attack_sword_onehand_up_pass22_occluded_samples", 0)
        ),
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
    pass22_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass22_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass22_adapter.ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION = (
        ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION
    )
    pass22_adapter.REQUIRE_ZERO_EDGE_ALPHA = REQUIRE_ZERO_EDGE_ALPHA
    pass22_adapter._depth_aware_visible_blade_head_clearance = (
        _depth_search_visible_blade_head_clearance
    )
    pass22_adapter._write_manifest_pass22 = _write_manifest_pass23
    try:
        return pass22_adapter.main()
    finally:
        pass22_adapter._depth_aware_visible_blade_head_clearance = (
            ORIGINAL_PASS22_CLEARANCE
        )
        pass22_adapter._write_manifest_pass22 = ORIGINAL_PASS22_WRITE_MANIFEST
        pass22_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS22_SCENE_KEY
        pass22_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS22_CONTACT_SHEET
        pass22_adapter.ONEHAND_UP_DEPTH_AWARE_DIAGNOSTIC_REVISION = (
            ORIGINAL_PASS22_REVISION
        )
        pass22_adapter.REQUIRE_ZERO_EDGE_ALPHA = (
            ORIGINAL_PASS22_REQUIRE_ZERO_EDGE_ALPHA
        )


if __name__ == "__main__":
    raise SystemExit(main())
