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
from hair_dense_crown_back_profile_v20 import load_hair_dense_crown_back_profile_v20
from hair_mass_builder_v20 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    REMOVED_BACK_OVERLAY_NAMES,
    RETAINED_PROFILE_LOCK_NAMES,
    apply_dense_crown_restoration_pass,
)
from hair_organic_crown_back_profile_v17 import (
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17,
)
from hair_organic_tone_profile_v18 import load_hair_organic_tone_profile_v18
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v20 import load_head_profile_v20


BASE_WRITE_RUN_MANIFEST = previous_adapter.BASE_WRITE_RUN_MANIFEST
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v18.py"
REJECTED_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v19.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v20.py"
HAIR_DENSE_PROFILE_PATH = SCRIPT_DIR / "hair_dense_crown_back_profile_v20.py"
HAIR_TONE_PROFILE_PATH = SCRIPT_DIR / "hair_organic_tone_profile_v18.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_DENSE_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v20.py"


def _build_head_and_hair_v20(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v18(context)
    apply_dense_crown_restoration_pass(context)


def _slice_width(profile_slice: object) -> float:
    x_values = [point[0] for point in profile_slice.points_xz]
    return max(x_values) - min(x_values)


def _slice_top(profile_slice: object) -> float:
    return max(point[1] for point in profile_slice.points_xz)


def _write_run_manifest_v20(
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

    profile = load_hair_dense_crown_back_profile_v20()
    previous_geometry = HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17
    tone = load_hair_organic_tone_profile_v18()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v18",
        "proxy_revision": "v21",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["rejected_candidate"] = {
        "path": context.config.relative_to_repo(REJECTED_HEAD_PROFILE_PATH),
        "revision": "v19",
        "proxy_revision": "v22",
        "reason": "rear_width_taper_reduced_visible_hair_density",
        "used_as_build_parent": False,
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_dense_profile"] = {
        "path": context.config.relative_to_repo(HAIR_DENSE_PROFILE_PATH),
        "revision": profile.revision,
        "proxy_revision": profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_DENSE_PROFILE_PATH.read_bytes()).hexdigest(),
        "sampled_widths": [_slice_width(item) for item in profile.slices],
        "proxy_v21_sampled_widths": [
            _slice_width(item) for item in previous_geometry.slices
        ],
        "sampled_tops": [_slice_top(item) for item in profile.slices],
        "proxy_v21_sampled_tops": [
            _slice_top(item) for item in previous_geometry.slices
        ],
        "width_status": "restored_exactly_to_proxy_v21",
        "top_status": "restrained_broad_lift_only",
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
    payload["hair_dense_builder"] = {
        "path": context.config.relative_to_repo(HAIR_DENSE_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_DENSE_BUILDER_PATH.read_bytes()).hexdigest(),
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
        raise RuntimeError("Proxy v23 manifest cannot find the dense organic crown")

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
            raise RuntimeError(f"Proxy v23 manifest cannot find retained lock: {name}")
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
            "dense_crown_back_vertices": len(crown.data.vertices),
            "dense_crown_back_faces": len(crown.data.polygons),
            "localized_material_face_counts": material_counts,
            "retained_profile_locks": retained_stats,
        }
    )

    payload["hair_structure"] = {
        "strategy": "restore_full_proxy_v21_density_with_restrained_top_lift",
        "zones": ["top", "front", "sides", "dense_organic_back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "dense_geometry_revision": profile.revision,
        "localized_tone_revision": tone.revision,
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "art_direction": {
            "primary_goal": "full_dense_wavy_hair_mass",
            "forced_angularity": False,
            "rear_taper_allowed": False,
            "visible_density_reduction_allowed": False,
            "pixel_steps_expected_from_normalization": True,
        },
        "geometry_strategy": {
            "organic_crown_back": (
                "exact_proxy_v21_x_envelope_with_only_three_broad_top_controls_lifted"
            ),
            "removed_overlays": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_locks": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "new_hair_part_count": 0,
        },
        "density_contract": {
            "vertices": len(crown.data.vertices),
            "faces": len(crown.data.polygons),
            "sampled_widths": [_slice_width(item) for item in profile.slices],
            "proxy_v21_sampled_widths": [
                _slice_width(item) for item in previous_geometry.slices
            ],
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
            "rejected_proxy_v22_used": False,
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
    factory.load_head_profile = load_head_profile_v20
    factory._build_head_and_hair = _build_head_and_hair_v20
    factory._write_run_manifest = _write_run_manifest_v20
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
