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
import blender_sprite_factory_head_v13 as previous_adapter
from hair_major_lock_profile_v14 import load_hair_major_lock_profile_v14
from hair_mass_builder_v14 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    MAJOR_LOCK_NAMES,
    apply_major_profile_lock_pass,
)
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v14 import load_head_profile_v14


PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v13.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v14.py"
HAIR_MAJOR_LOCK_PROFILE_PATH = SCRIPT_DIR / "hair_major_lock_profile_v14.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_MAJOR_LOCK_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v14.py"


def _build_head_and_hair_v14(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v13(context)
    apply_major_profile_lock_pass(context)


def _write_run_manifest_v14(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_run_manifest_v13(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )

    profile = load_hair_major_lock_profile_v14()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v13",
        "proxy_revision": "v16",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_major_lock_profile"] = {
        "path": context.config.relative_to_repo(HAIR_MAJOR_LOCK_PROFILE_PATH),
        "revision": profile.revision,
        "proxy_revision": profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_MAJOR_LOCK_PROFILE_PATH.read_bytes()).hexdigest(),
        "locks": [
            {
                "name": lock.name,
                "zone": lock.zone,
                "physical_side": lock.physical_side,
                "material_role": lock.material_role,
                "half_extent": list(lock.half_extent),
                "ring_sides": lock.ring_sides,
                "rings": [
                    {
                        "z_ratio": ring.z_ratio,
                        "center_x_ratio": ring.center_x_ratio,
                        "center_y_ratio": ring.center_y_ratio,
                        "radius_x_ratio": ring.radius_x_ratio,
                        "radius_y_ratio": ring.radius_y_ratio,
                    }
                    for ring in lock.rings
                ],
            }
            for lock in profile.locks
        ],
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_major_lock_builder"] = {
        "path": context.config.relative_to_repo(HAIR_MAJOR_LOCK_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_MAJOR_LOCK_BUILDER_PATH.read_bytes()).hexdigest(),
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
    mesh_stats: dict[str, dict[str, object]] = {}
    for lock in profile.locks:
        obj = factory.bpy.data.objects.get(lock.name)
        if obj is None:
            raise RuntimeError(f"Proxy v17 manifest cannot find major lock: {lock.name}")
        mesh_stats[lock.name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "physical_side": obj.get("hair_physical_side"),
            "material_role": obj.get("hair_material_role"),
            "mesh_strategy": obj.get("hair_mesh_strategy"),
        }

    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["major_profile_lock_count"] = len(mesh_stats)
    payload["head_geometry"]["major_profile_lock_meshes"] = mesh_stats

    payload["hair_structure"] = {
        "strategy": "approved_reference_large_profile_locks_for_sides_back_and_nape",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "previous_side_back_revision": "v13",
        "major_profile_lock_revision": "v14",
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "reuse_dark_v10_ramp_without_color_change",
        "geometry_strategy": {
            "crown": "unchanged_from_proxy_v16_with_scalp_coverage_preserved",
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "side_back_nape": "replace_eight_uv_ellipsoids_with_six_ring_pointed_profile_meshes",
            "object_names": "preserved",
            "object_transforms": "preserved_from_proxy_v16",
            "new_hair_part_count": 0,
        },
        "major_lock_contract": {
            "replaced_objects": sorted(MAJOR_LOCK_NAMES),
            "profile_ring_count": 6,
            "cross_section_sides": 6,
            "vertices_per_lock": 38,
            "faces_per_lock": 42,
            "physical_sides_preserved": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "palette_changed": False,
            "crown_changed": False,
            "forelock_changed": False,
            "separator_geometry_changed": False,
            "animation_keys_changed": False,
        },
    }

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v14
    factory._build_head_and_hair = _build_head_and_hair_v14
    factory._write_run_manifest = _write_run_manifest_v14
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
