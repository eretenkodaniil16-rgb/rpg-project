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
import blender_sprite_factory_head_v14 as previous_adapter
from hair_lock_exposure_profile_v15 import load_hair_lock_exposure_profile_v15
from hair_mass_builder_v15 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    MAJOR_LOCK_NAMES,
    apply_major_lock_exposure_pass,
)
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v15 import load_head_profile_v15


PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v14.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v15.py"
HAIR_LOCK_EXPOSURE_PROFILE_PATH = SCRIPT_DIR / "hair_lock_exposure_profile_v15.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_LOCK_EXPOSURE_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v15.py"


def _build_head_and_hair_v15(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v14(context)
    apply_major_lock_exposure_pass(context)


def _write_run_manifest_v15(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_run_manifest_v14(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )

    profile = load_hair_lock_exposure_profile_v15()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v14",
        "proxy_revision": "v17",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_lock_exposure_profile"] = {
        "path": context.config.relative_to_repo(HAIR_LOCK_EXPOSURE_PROFILE_PATH),
        "revision": profile.revision,
        "proxy_revision": profile.proxy_revision,
        "sha256": hashlib.sha256(
            HAIR_LOCK_EXPOSURE_PROFILE_PATH.read_bytes()
        ).hexdigest(),
        "transforms": [
            {
                "name": item.name,
                "zone": item.zone,
                "physical_side": item.physical_side,
                "scale_multiplier": list(item.scale_multiplier),
                "world_offset": list(item.world_offset),
                "rotation_delta_degrees": list(item.rotation_delta_degrees),
            }
            for item in profile.transforms
        ],
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_lock_exposure_builder"] = {
        "path": context.config.relative_to_repo(HAIR_LOCK_EXPOSURE_BUILDER_PATH),
        "sha256": hashlib.sha256(
            HAIR_LOCK_EXPOSURE_BUILDER_PATH.read_bytes()
        ).hexdigest(),
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
    exposure_stats: dict[str, dict[str, object]] = {}
    for item in profile.transforms:
        obj = factory.bpy.data.objects.get(item.name)
        if obj is None:
            raise RuntimeError(f"Proxy v18 manifest cannot find exposed lock: {item.name}")
        exposure_stats[item.name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "physical_side": obj.get("hair_physical_side"),
            "scale_multiplier": list(item.scale_multiplier),
            "world_offset": list(item.world_offset),
            "rotation_delta_degrees": list(item.rotation_delta_degrees),
        }

    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["exposed_profile_lock_count"] = len(exposure_stats)
    payload["head_geometry"]["exposed_profile_locks"] = exposure_stats

    payload["hair_structure"] = {
        "strategy": "approved_reference_exposed_large_profile_locks",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "previous_profile_lock_revision": "v14",
        "lock_exposure_revision": "v15",
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "reuse_dark_v10_ramp_without_color_change",
        "geometry_strategy": {
            "crown": "unchanged_from_proxy_v17",
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "profile_lock_meshes": "unchanged_38_vertex_42_face_meshes_from_proxy_v17",
            "central_back_shell": "shrink_and_raise_to_reduce_blanket_overlap",
            "side_back_nape_locks": "move_asymmetrically_outward_rearward_and_downward",
            "new_hair_part_count": 0,
        },
        "lock_exposure_contract": {
            "targeted_objects": sorted(MAJOR_LOCK_NAMES),
            "profile_topology_preserved": True,
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
    factory.load_head_profile = load_head_profile_v15
    factory._build_head_and_hair = _build_head_and_hair_v15
    factory._write_run_manifest = _write_run_manifest_v15
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
