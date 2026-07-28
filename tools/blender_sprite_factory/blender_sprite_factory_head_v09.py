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
import blender_sprite_factory_head_v07 as base_adapter
import blender_sprite_factory_head_v08 as previous_adapter
from hair_lock_profile_v09 import load_hair_lock_profile_v09
from hair_mass_builder_v09 import (
    ACTIVE_HAIR_PART_NAMES,
    HAIR_ROTATION_OVERRIDES_DEGREES,
    HAIR_SCALE_MULTIPLIERS,
    HAIR_WORLD_OFFSETS,
    REFERENCE_HAIR_FACET_COLORS,
    REFERENCE_HAIR_PALETTE,
    refine_reference_hair_locks,
)
from head_profile_v08 import load_head_detail_profile_v08
from head_profile_v09 import load_head_profile_v09


PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v08.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v09.py"
HAIR_LOCK_PROFILE_PATH = SCRIPT_DIR / "hair_lock_profile_v09.py"
HAIR_LOCK_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v09.py"


def _build_head_and_hair_v09(context: factory.BuildContext) -> None:
    base_adapter.load_head_detail_profile_v07 = load_head_detail_profile_v08
    base_adapter._build_head_and_hair_v07(context)
    refine_reference_hair_locks(context)


def _write_run_manifest_v09(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_run_manifest_v08(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    lock_profile = load_hair_lock_profile_v09()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v08",
        "proxy_revision": "v11",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_lock_profile"] = {
        "path": context.config.relative_to_repo(HAIR_LOCK_PROFILE_PATH),
        "revision": lock_profile.revision,
        "proxy_revision": lock_profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_LOCK_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_lock_builder"] = {
        "path": context.config.relative_to_repo(HAIR_LOCK_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_LOCK_BUILDER_PATH.read_bytes()).hexdigest(),
    }
    payload["head_builder_adapter"] = {
        "path": context.config.relative_to_repo(SCRIPT_PATH),
        "sha256": hashlib.sha256(SCRIPT_PATH.read_bytes()).hexdigest(),
    }

    actual_hair_names = sorted(
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    )
    separator = factory.bpy.data.objects.get(lock_profile.mesh_name)
    if separator is None:
        raise RuntimeError("Proxy v12 manifest cannot find the lock separator mesh")

    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["lock_separator_vertices"] = len(separator.data.vertices)
    payload["head_geometry"]["lock_separator_faces"] = len(separator.data.polygons)
    payload["hair_structure"] = {
        "strategy": "approved_reference_large_lock_grooves_over_single_crown_and_forelock",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "crown_and_forelock_geometry_source": "v08",
        "material_palette": list(REFERENCE_HAIR_PALETTE),
        "facet_colors": dict(REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "broad_mid_tones_with_dark_geometric_separators",
        "lock_separator_mesh": {
            "name": lock_profile.mesh_name,
            "material_role": lock_profile.material_role,
            "groove_count": len(lock_profile.grooves),
            "grooves": [
                {
                    "name": item.name,
                    "zone": item.zone,
                    "plane": item.plane,
                    "fixed_coordinate": item.fixed_coordinate,
                    "points_uv": [list(point) for point in item.points_uv],
                    "half_width": item.half_width,
                }
                for item in lock_profile.grooves
            ],
        },
        "actual_rotations_degrees": {
            name: list(values)
            for name, values in sorted(HAIR_ROTATION_OVERRIDES_DEGREES.items())
        },
        "positive_scale_multipliers": {
            name: list(values) for name, values in sorted(HAIR_SCALE_MULTIPLIERS.items())
        },
        "world_offsets": {
            name: list(values) for name, values in sorted(HAIR_WORLD_OFFSETS.items())
        },
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v09
    factory._build_head_and_hair = _build_head_and_hair_v09
    factory._write_run_manifest = _write_run_manifest_v09
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
