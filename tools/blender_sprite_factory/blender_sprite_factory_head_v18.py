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
import blender_sprite_factory_head_v17 as previous_adapter
from hair_mass_builder_v18 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    REMOVED_BACK_OVERLAY_NAMES,
    RETAINED_PROFILE_LOCK_NAMES,
    apply_localized_organic_tone_pass,
)
from hair_organic_tone_profile_v18 import load_hair_organic_tone_profile_v18
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v18 import load_head_profile_v18


BASE_WRITE_RUN_MANIFEST = previous_adapter.BASE_WRITE_RUN_MANIFEST
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v17.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v18.py"
HAIR_ORGANIC_TONE_PROFILE_PATH = SCRIPT_DIR / "hair_organic_tone_profile_v18.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_ORGANIC_TONE_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v18.py"


def _build_head_and_hair_v18(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v17(context)
    apply_localized_organic_tone_pass(context)


def _tone_region_payload(region: object) -> dict[str, object]:
    return {
        "role": region.role,
        "center_xyz": list(region.center_xyz),
        "radius_xyz": list(region.radius_xyz),
    }


def _write_run_manifest_v18(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
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

    profile = load_hair_organic_tone_profile_v18()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v17",
        "proxy_revision": "v20",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_organic_tone_profile"] = {
        "path": context.config.relative_to_repo(HAIR_ORGANIC_TONE_PROFILE_PATH),
        "revision": profile.revision,
        "proxy_revision": profile.proxy_revision,
        "sha256": hashlib.sha256(
            HAIR_ORGANIC_TONE_PROFILE_PATH.read_bytes()
        ).hexdigest(),
        "lower_shadow": {
            "base_z": profile.lower_shadow_base_z,
            "x_slope": profile.lower_shadow_x_slope,
            "y_slope": profile.lower_shadow_y_slope,
        },
        "rear_shadow": {
            "min_y": profile.rear_shadow_min_y,
            "base_z": profile.rear_shadow_base_z,
            "x_slope": profile.rear_shadow_x_slope,
        },
        "highlight_region": _tone_region_payload(profile.highlight_region),
        "main_mid_region": _tone_region_payload(profile.main_mid_region),
        "rear_mid_region": _tone_region_payload(profile.rear_mid_region),
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_organic_tone_builder"] = {
        "path": context.config.relative_to_repo(HAIR_ORGANIC_TONE_BUILDER_PATH),
        "sha256": hashlib.sha256(
            HAIR_ORGANIC_TONE_BUILDER_PATH.read_bytes()
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
    crown = factory.bpy.data.objects.get("hair_reference_crown_mesh")
    if crown is None:
        raise RuntimeError("Proxy v21 manifest cannot find the organic crown")
    material_counts = {
        role: sum(
            1
            for polygon in crown.data.polygons
            if polygon.material_index == index
        )
        for index, role in enumerate(("shadow", "base", "mid", "highlight"))
    }

    retained_stats: dict[str, dict[str, object]] = {}
    for name in sorted(RETAINED_PROFILE_LOCK_NAMES):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Proxy v21 manifest cannot find retained lock: {name}")
        retained_stats[name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "physical_side": obj.get("hair_physical_side"),
        }

    payload.setdefault("head_geometry", {})
    payload["head_geometry"].update(
        {
            "separate_hair_parts": len(actual_hair_names),
            "active_hair_names": actual_hair_names,
            "organic_crown_back_vertices": len(crown.data.vertices),
            "organic_crown_back_faces": len(crown.data.polygons),
            "localized_material_face_counts": material_counts,
            "retained_profile_locks": retained_stats,
        }
    )

    payload["hair_structure"] = {
        "strategy": "natural_organic_crown_with_localized_tone_support",
        "zones": ["top", "front", "sides", "organic_back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "organic_geometry_locked_to_revision": "v17",
        "localized_tone_revision": "v18",
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "dominant_dark_base_with_small_local_ellipsoid_highlight",
        "art_direction": {
            "primary_goal": "natural_readable_hair_mass",
            "forced_angularity": False,
            "large_flat_highlight_cap_allowed": False,
            "pixel_steps_expected_from_normalization": True,
        },
        "geometry_strategy": {
            "organic_crown_back": "unchanged_226_vertex_256_face_mesh_from_proxy_v20",
            "removed_overlays": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_locks": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "new_hair_part_count": 0,
        },
        "tone_strategy": {
            "base": "dominant_default_mass",
            "mid": "two_broad_support_ellipsoids",
            "highlight": "one_small_front_top_ellipsoid",
            "shadow": "lower_and_rear_boundaries",
            "material_face_counts": material_counts,
        },
        "localized_tone_contract": {
            "vertices": len(crown.data.vertices),
            "faces": len(crown.data.polygons),
            "removed_overlay_names": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_lock_names": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "physical_sides_preserved": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "palette_changed": False,
            "geometry_changed": False,
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
    factory.load_head_profile = load_head_profile_v18
    factory._build_head_and_hair = _build_head_and_hair_v18
    factory._write_run_manifest = _write_run_manifest_v18
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
