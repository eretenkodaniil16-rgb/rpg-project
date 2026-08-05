from __future__ import annotations

import json
import math
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_onehand_up_depth_search_diagnostic_v21 as pass23_adapter
import blender_sprite_factory_attack_sword_onehand_up_tail_diagnostic_v21 as pass20_adapter
from attack_sword_directional_cycle_correction_v21_pass24 import (
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    FLIP_CAMERA_DEPTH_BRANCH,
    ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
)


ORIGINAL_PROJECTION_TARGET = pass20_adapter._projection_target_direction
ORIGINAL_PASS23_WRITE_MANIFEST = pass23_adapter._write_manifest_pass23
ORIGINAL_PASS23_SCENE_KEY = pass23_adapter.DIAGNOSTIC_SCENE_KEY
ORIGINAL_PASS23_CONTACT_SHEET = pass23_adapter.CONTACT_SHEET_NAME
ORIGINAL_PASS23_REVISION = pass23_adapter.ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION
ORIGINAL_PASS23_REQUIRE_ZERO_EDGE_ALPHA = pass23_adapter.REQUIRE_ZERO_EDGE_ALPHA


def _front_depth_projection_target_direction(
    current_direction: object,
    *,
    offset_degrees: float,
    requested_projection: float,
) -> tuple[object, float, float]:
    screen_x, screen_y, camera_forward = pass20_adapter.pass06_adapter._camera_axes()
    current_x = float(current_direction.dot(screen_x))
    current_y = float(current_direction.dot(screen_y))
    current_depth = float(current_direction.dot(camera_forward))
    source_projection = math.hypot(current_x, current_y)
    if source_projection <= 1.0e-6:
        raise RuntimeError(
            "one-hand up front-depth diagnostic source projection is degenerate"
        )
    target_projection = min(source_projection, float(requested_projection))
    angle = math.atan2(current_y, current_x) + math.radians(offset_degrees)
    source_depth_sign = 1.0 if current_depth >= 0.0 else -1.0
    target_depth_sign = -source_depth_sign
    depth_magnitude = math.sqrt(max(0.0, 1.0 - target_projection**2))
    target_direction = (
        screen_x * (math.cos(angle) * target_projection)
        + screen_y * (math.sin(angle) * target_projection)
        + camera_forward * (target_depth_sign * depth_magnitude)
    ).normalized()
    return target_direction, source_projection, target_projection


def _write_manifest_pass24(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_PASS23_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["attack_sword_directional_cycle_v21_pass24"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION,
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "flip_camera_depth_branch": FLIP_CAMERA_DEPTH_BRANCH,
        "require_zero_edge_alpha": REQUIRE_ZERO_EDGE_ALPHA,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
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
    pass20_adapter._projection_target_direction = (
        _front_depth_projection_target_direction
    )
    pass23_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass23_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass23_adapter.ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION = (
        ONEHAND_UP_FRONT_DEPTH_DIAGNOSTIC_REVISION
    )
    pass23_adapter.REQUIRE_ZERO_EDGE_ALPHA = REQUIRE_ZERO_EDGE_ALPHA
    pass23_adapter._write_manifest_pass23 = _write_manifest_pass24
    try:
        return pass23_adapter.main()
    finally:
        pass20_adapter._projection_target_direction = ORIGINAL_PROJECTION_TARGET
        pass23_adapter._write_manifest_pass23 = ORIGINAL_PASS23_WRITE_MANIFEST
        pass23_adapter.DIAGNOSTIC_SCENE_KEY = ORIGINAL_PASS23_SCENE_KEY
        pass23_adapter.CONTACT_SHEET_NAME = ORIGINAL_PASS23_CONTACT_SHEET
        pass23_adapter.ONEHAND_UP_DEPTH_AWARE_SEARCH_REVISION = (
            ORIGINAL_PASS23_REVISION
        )
        pass23_adapter.REQUIRE_ZERO_EDGE_ALPHA = (
            ORIGINAL_PASS23_REQUIRE_ZERO_EDGE_ALPHA
        )


if __name__ == "__main__":
    raise SystemExit(main())
