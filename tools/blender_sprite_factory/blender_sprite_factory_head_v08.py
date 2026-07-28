from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import blender_sprite_factory as factory
import blender_sprite_factory_head_v07 as previous_adapter
from head_profile_v08 import (
    load_head_detail_profile_v08,
    load_head_profile_v08,
)


BASE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile.py"
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v07.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v08.py"
_ORIGINAL_WRITE_RUN_MANIFEST = factory._write_run_manifest


def _build_head_and_hair_v08(context: factory.BuildContext) -> None:
    previous_adapter.load_head_detail_profile_v07 = load_head_detail_profile_v08
    previous_adapter._build_head_and_hair_v07(context)


def _write_run_manifest_v08(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = _ORIGINAL_WRITE_RUN_MANIFEST(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    detail = load_head_detail_profile_v08(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["base_head_profile"] = {
        "path": context.config.relative_to_repo(BASE_HEAD_PROFILE_PATH),
        "sha256": hashlib.sha256(BASE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v07",
        "proxy_revision": "v10",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_builder_adapter"] = {
        "path": context.config.relative_to_repo(SCRIPT_PATH),
        "sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
    }
    payload["head_geometry"] = {
        "cranium_segments": detail.cranium_density.segments,
        "cranium_rings": detail.cranium_density.rings,
        "jaw_segments": detail.jaw_density.segments,
        "jaw_rings": detail.jaw_density.rings,
        "hair_cap_segments": detail.hair_cap_density.segments,
        "hair_cap_rings": detail.hair_cap_density.rings,
        "hair_primary_segments": detail.hair_primary_density.segments,
        "hair_primary_rings": detail.hair_primary_density.rings,
        "hair_secondary_segments": detail.hair_secondary_density.segments,
        "hair_secondary_rings": detail.hair_secondary_density.rings,
        "hair_tertiary_segments": detail.hair_tertiary_density.segments,
        "hair_tertiary_rings": detail.hair_tertiary_density.rings,
        "nose_vertices": detail.nose_vertices,
        "separate_face_skin_parts": len(detail.face_skin_masses),
        "separate_face_dark_parts": (
            len(context.head.brows)
            + len(context.head.eyes)
            + 1
            + len(detail.face_dark_details)
        ),
        "separate_hair_parts": (
            1
            + len(context.head.hair_back_masses)
            + len(context.head.hair_front_locks)
            + len(context.head.hair_side_locks)
            + len(detail.hair_detail_masses)
        ),
    }
    payload["hair_structure"] = {
        "strategy": "approved_reference_consolidated_five_zone",
        "zones": ["top", "front", "sides", "back", "nape"],
        "profile_hair_parts": (
            1
            + len(context.head.hair_back_masses)
            + len(context.head.hair_front_locks)
            + len(context.head.hair_side_locks)
        ),
        "detail_hair_parts": len(detail.hair_detail_masses),
        "face_geometry_locked_to_revision": "v07",
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v08
    factory._build_head_and_hair = _build_head_and_hair_v08
    factory._write_run_manifest = _write_run_manifest_v08
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
