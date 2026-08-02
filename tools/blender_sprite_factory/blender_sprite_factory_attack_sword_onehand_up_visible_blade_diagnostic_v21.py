from __future__ import annotations

import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_onehand_up_tail_diagnostic_v21 as pass20_adapter
from attack_sword_directional_cycle_correction_v21_pass21 import (
    ALLOW_HILT_OCCLUSION_BEHIND_HEAD,
    BLADE_CLEARANCE_PART_IDS,
    CONTACT_SHEET_NAME,
    CORRECTION_PASS,
    DIAGNOSTIC_SCENE_KEY,
    HILT_OCCLUSION_PART_IDS,
    MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS,
    ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION,
    REQUIRE_ZERO_EDGE_ALPHA,
    SOURCE_FAILED_ARTIFACT_ID,
    SOURCE_FAILED_RUN_ID,
    TECHNICAL_FAILED_ARTIFACT_ID,
    TECHNICAL_FAILED_RUN_ID,
)


ORIGINAL_HEAD_CLEARANCE = pass20_adapter.export_adapter._weapon_head_clearance
ORIGINAL_WRITE_MANIFEST = pass20_adapter._write_manifest


def _objects_by_weapon_part(
    objects: tuple[object, ...],
) -> dict[str, object]:
    expected = set(BLADE_CLEARANCE_PART_IDS + HILT_OCCLUSION_PART_IDS)
    by_part: dict[str, object] = {}
    for obj in objects:
        part = str(obj.get("weapon_part", ""))
        if part not in expected:
            continue
        if part in by_part:
            raise RuntimeError(
                "one-hand up visible blade diagnostic has duplicate weapon part: "
                f"{part}"
            )
        by_part[part] = obj
    missing = sorted(expected.difference(by_part))
    if missing:
        raise RuntimeError(
            "one-hand up visible blade diagnostic is missing weapon parts: "
            + ", ".join(missing)
        )
    return by_part


def _visible_blade_head_clearance(objects: tuple[object, ...]) -> float:
    by_part = _objects_by_weapon_part(objects)
    blade_objects = tuple(by_part[part] for part in BLADE_CLEARANCE_PART_IDS)
    return float(ORIGINAL_HEAD_CLEARANCE(blade_objects))


def _write_manifest_pass21(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    path = ORIGINAL_WRITE_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["attack_sword_directional_cycle_v21_pass21"] = {
        "correction_pass": CORRECTION_PASS,
        "revision": ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION,
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "collision_weapon_part_ids": list(BLADE_CLEARANCE_PART_IDS),
        "hilt_occlusion_weapon_part_ids": list(HILT_OCCLUSION_PART_IDS),
        "allow_hilt_occlusion_behind_head": ALLOW_HILT_OCCLUSION_BEHIND_HEAD,
        "minimum_visible_blade_head_clearance_pixels": (
            MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
        ),
        "require_zero_edge_alpha": REQUIRE_ZERO_EDGE_ALPHA,
        "source_failed_run_id": SOURCE_FAILED_RUN_ID,
        "source_failed_artifact_id": SOURCE_FAILED_ARTIFACT_ID,
        "technical_failed_run_id": TECHNICAL_FAILED_RUN_ID,
        "technical_failed_artifact_id": TECHNICAL_FAILED_ARTIFACT_ID,
        "weapon_parts_removed_from_render": False,
        "weapon_geometry_changed": False,
        "weapon_geometry_deformed": False,
        "weapon_scale_changed": False,
        "materials_changed": False,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    pass20_adapter.DIAGNOSTIC_SCENE_KEY = DIAGNOSTIC_SCENE_KEY
    pass20_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    pass20_adapter.ONEHAND_UP_TAIL_DIAGNOSTIC_REVISION = (
        ONEHAND_UP_VISIBLE_BLADE_DIAGNOSTIC_REVISION
    )
    pass20_adapter.MIN_HEAD_CLEARANCE_PIXELS = (
        MIN_VISIBLE_BLADE_HEAD_CLEARANCE_PIXELS
    )
    pass20_adapter.REQUIRE_ZERO_EDGE_ALPHA = REQUIRE_ZERO_EDGE_ALPHA
    pass20_adapter.export_adapter._weapon_head_clearance = (
        _visible_blade_head_clearance
    )
    pass20_adapter._write_manifest = _write_manifest_pass21
    try:
        return pass20_adapter.main()
    finally:
        pass20_adapter.export_adapter._weapon_head_clearance = (
            ORIGINAL_HEAD_CLEARANCE
        )
        pass20_adapter._write_manifest = ORIGINAL_WRITE_MANIFEST


if __name__ == "__main__":
    raise SystemExit(main())
