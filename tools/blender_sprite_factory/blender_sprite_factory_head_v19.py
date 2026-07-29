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
import blender_sprite_factory_head_v18 as previous_adapter
from hair_mass_builder_v19 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    REMOVED_BACK_OVERLAY_NAMES,
    RETAINED_PROFILE_LOCK_NAMES,
    apply_centered_volume_taper_pass,
)
from hair_organic_tone_profile_v18 import load_hair_organic_tone_profile_v18
from hair_palette_v10 import load_hair_palette_v10
from hair_volume_crown_back_profile_v19 import (
    load_hair_volume_crown_back_profile_v19,
)
from head_profile_v19 import load_head_profile_v19


BASE_WRITE_RUN_MANIFEST = previous_adapter.BASE_WRITE_RUN_MANIFEST
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v18.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v19.py"
HAIR_VOLUME_PROFILE_PATH = SCRIPT_DIR / "hair_volume_crown_back_profile_v19.py"
HAIR_TONE_PROFILE_PATH = SCRIPT_DIR / "hair_organic_tone_profile_v18.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_VOLUME_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v19.py"


def _build_head_and_hair_v19(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v18(context)
    apply_centered_volume_taper_pass(context)


def _slice_width(profile_slice: object) -> float:
    x_values = [point[0] for point in profile_slice.points_xz]
    return max(x_values) - min(x_values)


def _central_rise(profile_slice: object) -> float:
    central = [
        profile_slice.control_points_xz[index][1]
        for index in (5, 6, 7)
    ]
    shoulders = [
        profile_slice.control_points_xz[index][1]
        for index in (3, 4, 8)
    ]
    return sum(central) / len(central) - sum(shoulders) / len(shoulders)


def _write_run_manifest_v19(
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

    profile = load_hair_volume_crown_back_profile_v19()
    tone = load_hair_organic_tone_profile_v18()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v18",
        "proxy_revision": "v21",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_volume_profile"] = {
        "path": context.config.relative_to_repo(HAIR_VOLUME_PROFILE_PATH),
        "revision": profile.revision,
        "proxy_revision": profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_VOLUME_PROFILE_PATH.read_bytes()).hexdigest(),
        "slice_y": [item.y for item in profile.slices],
        "sampled_widths": [_slice_width(item) for item in profile.slices],
        "central_rise": [_central_rise(item) for item in profile.slices],
        "front_top": max(point[1] for point in profile.slices[0].points_xz),
        "rear_top": max(point[1] for point in profile.slices[-1].points_xz),
    }
    payload["hair_organic_tone_profile"] = {
        "path": context.config.relative_to_repo(HAIR_TONE_PROFILE_PATH),
        "revision": tone.revision,
        "proxy_revision": tone.proxy_revision,
        "sha256": hashlib.sha256(HAIR_TONE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_tone_region_change",
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_volume_builder"] = {
        "path": context.config.relative_to_repo(HAIR_VOLUME_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_VOLUME_BUILDER_PATH.read_bytes()).hexdigest(),
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
    crown = factory.bpy.data.objects.get(profile.mesh_name)
    if crown is None:
        raise RuntimeError("Proxy v22 manifest cannot find the tapered organic crown")

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
            raise RuntimeError(f"Proxy v22 manifest cannot find retained lock: {name}")
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
            "volume_crown_back_vertices": len(crown.data.vertices),
            "volume_crown_back_faces": len(crown.data.polygons),
            "localized_material_face_counts": material_counts,
            "retained_profile_locks": retained_stats,
        }
    )

    payload["hair_structure"] = {
        "strategy": "centered_natural_volume_with_smooth_rear_taper",
        "zones": ["top", "front", "sides", "tapered_organic_back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "volume_geometry_revision": profile.revision,
        "localized_tone_revision": tone.revision,
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "dominant_dark_base_with_reused_localized_v18_tones",
        "art_direction": {
            "primary_goal": "natural_readable_hair_mass",
            "forced_angularity": False,
            "monolithic_cap_allowed": False,
            "large_flat_highlight_cap_allowed": False,
            "pixel_steps_expected_from_normalization": True,
        },
        "geometry_strategy": {
            "organic_crown_back": (
                "same_226_vertex_256_face_topology_with_broad_center_rise_"
                "and_gradual_rear_width_taper"
            ),
            "removed_overlays": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_locks": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "new_hair_part_count": 0,
        },
        "volume_contract": {
            "vertices": len(crown.data.vertices),
            "faces": len(crown.data.polygons),
            "sampled_widths": [_slice_width(item) for item in profile.slices],
            "central_rise": [_central_rise(item) for item in profile.slices],
            "removed_overlay_names": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_lock_names": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "physical_sides_preserved": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "palette_changed": False,
            "tone_regions_changed": False,
            "geometry_changed": True,
            "topology_changed": False,
            "forelock_changed": False,
            "separator_geometry_changed": False,
            "animation_keys_changed": False,
        },
        "tone_strategy": {
            "source_revision": tone.revision,
            "material_face_counts": material_counts,
        },
    }

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v19
    factory._build_head_and_hair = _build_head_and_hair_v19
    factory._write_run_manifest = _write_run_manifest_v19
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
