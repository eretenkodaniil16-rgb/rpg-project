from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_attack_sword_down_keyposes_v19_pass02 as previous_adapter
from attack_sword_down_keyposes_correction_v19_pass03 import (
    CORRECTION_PASS,
    ONEHAND_FOLLOW_CONTAINMENT_REVISION,
    load_attack_sword_down_keyposes_profile_v19_pass03,
)


CORRECTION_PATH = SCRIPT_DIR / "attack_sword_down_keyposes_correction_v19_pass03.py"
CONTACT_SHEET_NAME = "attack_sword_01_down_keyposes_v19.png"
BASE_WRITE_MANIFEST_PASS02 = previous_adapter._write_manifest_v19_pass02


def _write_manifest_v19_pass03(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = BASE_WRITE_MANIFEST_PASS02(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["attack_sword_down_keyposes_v19_pass03"] = {
        "correction_pass": CORRECTION_PASS,
        "correction_path": context.config.relative_to_repo(CORRECTION_PATH),
        "correction_sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
        "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
        "contact_sheet": context.config.relative_to_repo(run_dir / CONTACT_SHEET_NAME),
        "onehand_follow_containment_revision": ONEHAND_FOLLOW_CONTAINMENT_REVISION,
        "onehand_frames_01_to_03_unchanged_from_pass02": True,
        "twohand_v19_trajectory_unchanged": True,
        "weapon_geometry_changed": False,
        "materials_changed": False,
        "approved_guard_frames_changed": False,
        "manual_keypose_review_required": True,
    }
    payload.setdefault("animation_contract", {}).update(
        {
            "attack_sword_01_current_stage": "down_keyposes_v19_pass03",
            "attack_sword_01_manual_review_required": True,
        }
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter.load_attack_sword_down_keyposes_profile_v19_pass02 = (
        load_attack_sword_down_keyposes_profile_v19_pass03
    )
    previous_adapter.CORRECTION_PATH = CORRECTION_PATH
    previous_adapter.SCRIPT_PATH = SCRIPT_PATH
    previous_adapter.CONTACT_SHEET_NAME = CONTACT_SHEET_NAME
    previous_adapter._write_manifest_v19_pass02 = _write_manifest_v19_pass03
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
