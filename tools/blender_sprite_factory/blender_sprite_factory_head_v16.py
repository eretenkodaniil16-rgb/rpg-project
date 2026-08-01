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
import blender_sprite_factory_head_v15 as previous_adapter
from hair_integrated_crown_back_profile_v16 import (
    load_hair_integrated_crown_back_profile_v16,
)
from hair_mass_builder_v16 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    REMOVED_BACK_OVERLAY_NAMES,
    RETAINED_PROFILE_LOCK_NAMES,
    apply_integrated_crown_back_pass,
)
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v16 import load_head_profile_v16


BASE_WRITE_RUN_MANIFEST = factory._write_run_manifest
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v15.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v16.py"
HAIR_INTEGRATED_PROFILE_PATH = SCRIPT_DIR / "hair_integrated_crown_back_profile_v16.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_INTEGRATED_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v16.py"


def _build_head_and_hair_v16(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v15(context)
    apply_integrated_crown_back_pass(context)


def _profile_slices_payload(profile: object) -> list[dict[str, object]]:
    return [
        {
            "y": profile_slice.y,
            "points_xz": [list(point) for point in profile_slice.points_xz],
        }
        for profile_slice in profile.slices
    ]


def _write_run_manifest_v16(
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

    profile = load_hair_integrated_crown_back_profile_v16()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v15",
        "proxy_revision": "v18",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_integrated_crown_back_profile"] = {
        "path": context.config.relative_to_repo(HAIR_INTEGRATED_PROFILE_PATH),
        "revision": profile.revision,
        "proxy_revision": profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_INTEGRATED_PROFILE_PATH.read_bytes()).hexdigest(),
        "mesh_name": profile.mesh_name,
        "slices": _profile_slices_payload(profile),
        "removed_overlay_names": list(profile.removed_overlay_names),
        "retained_profile_lock_names": list(profile.retained_profile_lock_names),
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_integrated_crown_back_builder"] = {
        "path": context.config.relative_to_repo(HAIR_INTEGRATED_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_INTEGRATED_BUILDER_PATH.read_bytes()).hexdigest(),
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
        raise RuntimeError("Proxy v19 manifest cannot find the integrated crown/back mesh")

    retained_stats: dict[str, dict[str, object]] = {}
    for name in sorted(RETAINED_PROFILE_LOCK_NAMES):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Proxy v19 manifest cannot find retained profile lock: {name}")
        retained_stats[name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "physical_side": obj.get("hair_physical_side"),
        }

    payload.setdefault("head_geometry", {})
    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["integrated_crown_back_vertices"] = len(crown.data.vertices)
    payload["head_geometry"]["integrated_crown_back_faces"] = len(crown.data.polygons)
    payload["head_geometry"]["integrated_crown_back_slices"] = len(profile.slices)
    payload["head_geometry"]["removed_back_overlay_count"] = len(REMOVED_BACK_OVERLAY_NAMES)
    payload["head_geometry"]["retained_profile_locks"] = retained_stats

    payload["hair_structure"] = {
        "strategy": "approved_reference_integrated_crown_back_with_retained_side_nape_locks",
        "zones": ["top", "front", "sides", "integrated_back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "previous_lock_exposure_revision": "v15",
        "integrated_crown_back_revision": "v16",
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "reuse_dark_v10_ramp_without_color_change",
        "geometry_strategy": {
            "front_crown": "locked_to_proxy_v18_front_silhouette",
            "crown_back": "single_five_slice_82_vertex_96_face_integrated_mesh",
            "rear_edge": "three_broad_physical_tips_separated_by_two_raised_valleys",
            "removed_overlays": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_locks": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "scalp_coverage": "embedded_in_every_integrated_depth_slice",
            "new_hair_part_count": 0,
            "net_hair_part_change": -len(REMOVED_BACK_OVERLAY_NAMES),
        },
        "integrated_crown_back_contract": {
            "integrated_object_name": profile.mesh_name,
            "slice_count": len(profile.slices),
            "points_per_slice": len(profile.slices[0].points_xz),
            "vertices": len(crown.data.vertices),
            "faces": len(crown.data.polygons),
            "removed_overlay_names": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_lock_names": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "physical_sides_preserved": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "palette_changed": False,
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
    factory.load_head_profile = load_head_profile_v16
    factory._build_head_and_hair = _build_head_and_hair_v16
    factory._write_run_manifest = _write_run_manifest_v16
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
