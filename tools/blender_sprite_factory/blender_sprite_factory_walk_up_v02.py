from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory_walk_up_v01 as previous_adapter
from walk_up_animation_builder_v02 import create_walk_up_actions_v02
from walk_up_profile_v02 import load_walk_up_profile_v02


BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_walk_up_v01
WALK_UP_PROFILE_PATH = SCRIPT_DIR / "walk_up_profile_v02.py"
WALK_UP_BUILDER_PATH = SCRIPT_DIR / "walk_up_animation_builder_v02.py"


def _write_run_manifest_walk_up_v02(
    context: object,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[object],
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
    candidate = payload.pop("walk_up_candidate_v01")
    profile = load_walk_up_profile_v02(context.config.character_id)

    candidate.update(
        {
            "profile_path": context.config.relative_to_repo(WALK_UP_PROFILE_PATH),
            "profile_sha256": hashlib.sha256(WALK_UP_PROFILE_PATH.read_bytes()).hexdigest(),
            "builder_path": context.config.relative_to_repo(WALK_UP_BUILDER_PATH),
            "builder_sha256": hashlib.sha256(WALK_UP_BUILDER_PATH.read_bytes()).hexdigest(),
            "adapter_path": context.config.relative_to_repo(SCRIPT_PATH),
            "adapter_sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
            "profile_revision": profile.revision,
            "animation_revision": profile.animation_revision,
            "previous_candidate": "walk_up profile v01 / animation v01",
            "previous_candidate_status": "rejected_rear_passing_silhouette_too_compressed",
            "correction_scope": "physical_right_passing_leg_keys_only",
            "corrected_frame": 6,
            "geometry_changed": False,
            "materials_changed": False,
            "mirroring_used": False,
            "status": "technical_candidate_requires_manual_motion_review",
        }
    )
    payload["walk_up_candidate_v02"] = candidate
    payload.setdefault("animation_contract", {})
    payload["animation_contract"].update(
        {
            "walk_up_revision": "v02",
            "walk_up_profile_revision": "v02",
            "walk_up_v01_rejected": True,
            "walk_up_v02_corrected_phase": "physical_right_passing",
            "walk_up_v02_previous_frames_unchanged_by_profile": [1, 2, 3, 4, 5],
        }
    )
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["status"] = (
        "artist_approved_appearance_v03_with_approved_walk_down_v04_"
        "walk_left_v01_walk_right_v01_and_walk_up_v02_candidate"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    previous_adapter.load_walk_up_profile_v01 = load_walk_up_profile_v02
    previous_adapter.WALK_UP_PROFILE_PATH = WALK_UP_PROFILE_PATH
    previous_adapter.WALK_UP_BUILDER_PATH = WALK_UP_BUILDER_PATH
    previous_adapter.SCRIPT_PATH = SCRIPT_PATH
    previous_adapter.create_walk_up_actions_v01 = create_walk_up_actions_v02
    previous_adapter._write_run_manifest_walk_up_v01 = _write_run_manifest_walk_up_v02
    return previous_adapter.main()


if __name__ == "__main__":
    raise SystemExit(main())
