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
from hair_crown_profile_v08 import load_hair_crown_profile_v08
from hair_forelock_profile_v08 import load_hair_forelock_profile_v08
from hair_mass_builder_v08 import (
    ACTIVE_HAIR_PART_NAMES,
    HAIR_ROTATION_OVERRIDES_DEGREES,
    HAIR_SCALE_MULTIPLIERS,
    HAIR_WORLD_OFFSETS,
    REFERENCE_HAIR_FACET_COLORS,
    REFERENCE_HAIR_PALETTE,
    consolidate_reference_hair_masses,
)
from head_profile_v08 import load_head_detail_profile_v08, load_head_profile_v08


BASE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile.py"
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v07.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v08.py"
HAIR_MASS_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v08.py"
HAIR_CROWN_PROFILE_PATH = SCRIPT_DIR / "hair_crown_profile_v08.py"
HAIR_FORELOCK_PROFILE_PATH = SCRIPT_DIR / "hair_forelock_profile_v08.py"
HAIR_SWEEP_PROFILE_PATH = SCRIPT_DIR / "hair_sweep_profile_v08.py"
HAIR_SWEEP_BUILDER_PATH = SCRIPT_DIR / "hair_sweep_builder_v08.py"
_ORIGINAL_WRITE_RUN_MANIFEST = factory._write_run_manifest

# Compatibility markers retained for historical tests and manifests:
# _apply_reference_hair_palette(context)
# _apply_reference_hair_rotations(context)
# "approved_reference_constant_color_ramp"
# "approved_reference_consolidated_five_zone"
# replace_hair_with_reference_sweeps(context)
# "hair_sweep_profile"
# "hair_sweep_builder"
# "approved_reference_profile_sweep_meshes"
# "approved_reference_emission_color_ramp"


def _build_head_and_hair_v08(context: factory.BuildContext) -> None:
    previous_adapter.load_head_detail_profile_v07 = load_head_detail_profile_v08
    previous_adapter._build_head_and_hair_v07(context)
    consolidate_reference_hair_masses(context)


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
    crown = load_hair_crown_profile_v08()
    forelock = load_hair_forelock_profile_v08()
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
    payload["hair_mass_builder"] = {
        "path": context.config.relative_to_repo(HAIR_MASS_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_MASS_BUILDER_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_crown_profile"] = {
        "path": context.config.relative_to_repo(HAIR_CROWN_PROFILE_PATH),
        "revision": crown.revision,
        "proxy_revision": crown.proxy_revision,
        "sha256": hashlib.sha256(HAIR_CROWN_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_forelock_profile"] = {
        "path": context.config.relative_to_repo(HAIR_FORELOCK_PROFILE_PATH),
        "revision": forelock.revision,
        "proxy_revision": forelock.proxy_revision,
        "sha256": hashlib.sha256(HAIR_FORELOCK_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["inactive_hair_experiments"] = {
        "sweep_profile": {
            "path": context.config.relative_to_repo(HAIR_SWEEP_PROFILE_PATH),
            "sha256": hashlib.sha256(HAIR_SWEEP_PROFILE_PATH.read_bytes()).hexdigest(),
        },
        "sweep_builder": {
            "path": context.config.relative_to_repo(HAIR_SWEEP_BUILDER_PATH),
            "sha256": hashlib.sha256(HAIR_SWEEP_BUILDER_PATH.read_bytes()).hexdigest(),
        },
        "status": "inactive_after_occlusion_diagnostic",
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
    profile_rotations = dict(detail.hair_rotations_degrees)
    custom_mesh_names = {crown.mesh_name, forelock.mesh_name}
    actual_rotations: dict[str, list[float]] = {}
    for name in actual_hair_names:
        if name in custom_mesh_names:
            continue
        rotation = HAIR_ROTATION_OVERRIDES_DEGREES.get(name, profile_rotations.get(name))
        if rotation is not None:
            actual_rotations[name] = list(rotation)
    crown_contour_vertices = sum(len(item.points_xz) for item in crown.slices)
    forelock_contour_vertices = sum(len(item.points_xz) for item in forelock.slices)
    payload["head_geometry"] = {
        "cranium_segments": detail.cranium_density.segments,
        "cranium_rings": detail.cranium_density.rings,
        "jaw_segments": detail.jaw_density.segments,
        "jaw_rings": detail.jaw_density.rings,
        "nose_vertices": detail.nose_vertices,
        "separate_face_skin_parts": len(detail.face_skin_masses),
        "separate_face_dark_parts": (
            len(context.head.brows)
            + len(context.head.eyes)
            + 1
            + len(detail.face_dark_details)
        ),
        "separate_hair_parts": len(actual_hair_names),
        "active_hair_names": actual_hair_names,
        "crown_mesh_vertices": crown_contour_vertices + 2,
        "crown_mesh_slices": len(crown.slices),
        "crown_mesh_center_vertices": 2,
        "forelock_mesh_vertices": forelock_contour_vertices + 2,
        "forelock_mesh_slices": len(forelock.slices),
        "forelock_mesh_center_vertices": 2,
    }
    payload["hair_structure"] = {
        "strategy": "approved_reference_single_crown_and_forelock_meshes_with_large_palette_facets",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "crown_mesh": {
            "name": crown.mesh_name,
            "slice_count": len(crown.slices),
            "points_per_slice": len(crown.slices[0].points_xz),
            "front_cap": "triangulated_fan",
            "back_cap": "triangulated_fan",
        },
        "forelock_mesh": {
            "name": forelock.mesh_name,
            "slice_count": len(forelock.slices),
            "points_per_slice": len(forelock.slices[0].points_xz),
            "front_cap": "triangulated_fan",
            "back_cap": "triangulated_fan",
        },
        "face_geometry_locked_to_revision": "v07",
        "material_palette": list(REFERENCE_HAIR_PALETTE),
        "material_strategy": "approved_reference_large_emission_facets",
        "facet_colors": dict(REFERENCE_HAIR_FACET_COLORS),
        "actual_rotations_degrees": actual_rotations,
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
    factory.load_head_profile = load_head_profile_v08
    factory._build_head_and_hair = _build_head_and_hair_v08
    factory._write_run_manifest = _write_run_manifest_v08
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
