from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import attack_sword_down_keyposes_builder_v17 as action_builder
import blender_sprite_factory_attack_sword_down_keyposes_v17 as previous_adapter
from attack_sword_down_keyposes_correction_v18 import (
    CORRECTION_REVISION,
    ONEHAND_TRAJECTORY_REVISION,
    TWOHAND_ANTICIPATION_REVISION,
    load_attack_sword_down_keyposes_profile_v18,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_correction_v18.py"
BASE_WRITE_MANIFEST_V17 = previous_adapter._write_manifest_v17
CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v18.png"


def _write_manifest_v18(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_V17(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_sheet = run_dir / previous_adapter.CONTACT_SHEET_NAME
    new_sheet = run_dir / CONTACT_SHEET_NAME
    if old_sheet.is_file() and old_sheet != new_sheet:
        new_sheet.write_bytes(old_sheet.read_bytes())
    if not new_sheet.is_file():
        raise RuntimeError("attack sword down v18 contact sheet is missing")

    payload["attack_sword_down_keyposes_correction_v18"] = {
        "correction_revision": CORRECTION_REVISION,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(new_sheet),
        "onehand_trajectory_revision": ONEHAND_TRAJECTORY_REVISION,
        "twohand_anticipation_revision": TWOHAND_ANTICIPATION_REVISION,
        "onehand_phase_order_corrected": True,
        "twohand_top_boundary_correction": True,
        "source_v17_preserved": True,
        "animation_action_ids_changed": False,
        "weapon_geometry_changed": False,
        "materials_changed": False,
        "manual_keypose_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_keyposes_correction_v18",
            "attack_sword_01_keypose_count": 10,
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    action_builder.load_attack_sword_down_keyposes_profile_v17 = (
        load_attack_sword_down_keyposes_profile_v18
    )
    previous_adapter.load_attack_sword_down_keyposes_profile_v17 = (
        load_attack_sword_down_keyposes_profile_v18
    )
    previous_adapter.PROFILE_PATH = CORRECTION_PATH
    previous_adapter.SCRIPT_PATH = SCRIPT_PATH
    previous_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    previous_adapter._write_manifest_v17 = _write_manifest_v18
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
