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
import blender_sprite_factory_head_v10 as previous_adapter
from hair_crown_profile_v11 import load_hair_crown_profile_v11
from hair_forelock_profile_v11 import load_hair_forelock_profile_v11
from hair_lock_profile_v11 import load_hair_lock_profile_v11
from hair_mass_builder_v11 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    HAIR_ROTATION_OVERRIDES_DEGREES,
    HAIR_SCALE_MULTIPLIERS,
    HAIR_WORLD_OFFSETS,
    apply_physical_lock_shape_pass,
)
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v11 import load_head_profile_v11


PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v10.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v11.py"
HAIR_CROWN_PROFILE_PATH = SCRIPT_DIR / "hair_crown_profile_v11.py"
HAIR_FORELOCK_PROFILE_PATH = SCRIPT_DIR / "hair_forelock_profile_v11.py"
HAIR_LOCK_PROFILE_PATH = SCRIPT_DIR / "hair_lock_profile_v11.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_SHAPE_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v11.py"


def _build_head_and_hair_v11(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v10(context)
    apply_physical_lock_shape_pass(context)


def _profile_slices_payload(profile: object) -> list[dict[str, object]]:
    return [
        {
            "y": profile_slice.y,
            "points_xz": [list(point) for point in profile_slice.points_xz],
        }
        for profile_slice in profile.slices
    ]


def _write_run_manifest_v11(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_run_manifest_v10(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )

    crown_profile = load_hair_crown_profile_v11()
    forelock_profile = load_hair_forelock_profile_v11()
    lock_profile = load_hair_lock_profile_v11()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v10",
        "proxy_revision": "v13",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_crown_profile"] = {
        "path": context.config.relative_to_repo(HAIR_CROWN_PROFILE_PATH),
        "revision": crown_profile.revision,
        "proxy_revision": crown_profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_CROWN_PROFILE_PATH.read_bytes()).hexdigest(),
        "mesh_name": crown_profile.mesh_name,
        "slices": _profile_slices_payload(crown_profile),
    }
    payload["hair_forelock_profile"] = {
        "path": context.config.relative_to_repo(HAIR_FORELOCK_PROFILE_PATH),
        "revision": forelock_profile.revision,
        "proxy_revision": forelock_profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_FORELOCK_PROFILE_PATH.read_bytes()).hexdigest(),
        "mesh_name": forelock_profile.mesh_name,
        "slices": _profile_slices_payload(forelock_profile),
    }
    payload["hair_lock_profile"] = {
        "path": context.config.relative_to_repo(HAIR_LOCK_PROFILE_PATH),
        "revision": lock_profile.revision,
        "proxy_revision": lock_profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_LOCK_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_shape_builder"] = {
        "path": context.config.relative_to_repo(HAIR_SHAPE_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_SHAPE_BUILDER_PATH.read_bytes()).hexdigest(),
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
    crown = factory.bpy.data.objects.get(crown_profile.mesh_name)
    forelock = factory.bpy.data.objects.get(forelock_profile.mesh_name)
    separator = factory.bpy.data.objects.get(lock_profile.mesh_name)
    if crown is None or forelock is None or separator is None:
        raise RuntimeError("Proxy v14 manifest cannot find the physical hair meshes")

    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["crown_vertices"] = len(crown.data.vertices)
    payload["head_geometry"]["crown_faces"] = len(crown.data.polygons)
    payload["head_geometry"]["forelock_vertices"] = len(forelock.data.vertices)
    payload["head_geometry"]["forelock_faces"] = len(forelock.data.polygons)
    payload["head_geometry"]["lock_separator_vertices"] = len(separator.data.vertices)
    payload["head_geometry"]["lock_separator_faces"] = len(separator.data.polygons)

    payload["hair_structure"] = {
        "strategy": "approved_reference_physical_large_waves_and_single_forelock",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "previous_shape_revision": "v10",
        "physical_shape_revision": "v11",
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "reuse_dark_v10_ramp_with_contiguous_tonal_masses",
        "geometry_strategy": {
            "crown": "three_or_four_large_asymmetric_silhouette_waves",
            "forelock": "single_physical_left_root_bend_tip_mesh",
            "separators": "six_short_local_depressions_supporting_physical_shape",
            "new_hair_part_count": 0,
        },
        "localized_lock_separator_mesh": {
            "name": lock_profile.mesh_name,
            "material_role": lock_profile.material_role,
            "groove_count": len(lock_profile.grooves),
            "control_points_per_groove": 4,
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
            name: list(values)
            for name, values in sorted(HAIR_SCALE_MULTIPLIERS.items())
        },
        "world_offsets": {
            name: list(values)
            for name, values in sorted(HAIR_WORLD_OFFSETS.items())
        },
    }

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v11
    factory._build_head_and_hair = _build_head_and_hair_v11
    factory._write_run_manifest = _write_run_manifest_v11
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
