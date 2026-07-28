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
import blender_sprite_factory_head_v12 as previous_adapter
from hair_crown_profile_v13 import load_hair_crown_profile_v13
from hair_mass_builder_v13 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    apply_side_back_silhouette_pass,
)
from hair_palette_v10 import load_hair_palette_v10
from hair_side_back_profile_v13 import load_hair_side_back_profile_v13
from head_profile_v13 import load_head_profile_v13


PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v12.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v13.py"
PREVIOUS_HAIR_CROWN_PROFILE_PATH = SCRIPT_DIR / "hair_crown_profile_v12.py"
HAIR_CROWN_PROFILE_PATH = SCRIPT_DIR / "hair_crown_profile_v13.py"
HAIR_SIDE_BACK_PROFILE_PATH = SCRIPT_DIR / "hair_side_back_profile_v13.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_SIDE_BACK_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v13.py"


def _build_head_and_hair_v13(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v12(context)
    apply_side_back_silhouette_pass(context)


def _profile_slices_payload(profile: object) -> list[dict[str, object]]:
    return [
        {
            "y": profile_slice.y,
            "points_xz": [list(point) for point in profile_slice.points_xz],
        }
        for profile_slice in profile.slices
    ]


def _write_run_manifest_v13(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_run_manifest_v12(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )

    crown_profile = load_hair_crown_profile_v13()
    side_back_profile = load_hair_side_back_profile_v13()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v12",
        "proxy_revision": "v15",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["previous_hair_crown_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HAIR_CROWN_PROFILE_PATH),
        "revision": "v12",
        "proxy_revision": "v15",
        "sha256": hashlib.sha256(
            PREVIOUS_HAIR_CROWN_PROFILE_PATH.read_bytes()
        ).hexdigest(),
    }
    payload["hair_crown_profile"] = {
        "path": context.config.relative_to_repo(HAIR_CROWN_PROFILE_PATH),
        "revision": crown_profile.revision,
        "proxy_revision": crown_profile.proxy_revision,
        "sha256": hashlib.sha256(HAIR_CROWN_PROFILE_PATH.read_bytes()).hexdigest(),
        "mesh_name": crown_profile.mesh_name,
        "slices": _profile_slices_payload(crown_profile),
    }
    payload["hair_side_back_profile"] = {
        "path": context.config.relative_to_repo(HAIR_SIDE_BACK_PROFILE_PATH),
        "revision": side_back_profile.revision,
        "proxy_revision": side_back_profile.proxy_revision,
        "sha256": hashlib.sha256(
            HAIR_SIDE_BACK_PROFILE_PATH.read_bytes()
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
            for item in side_back_profile.transforms
        ],
    }
    payload["hair_palette_profile"] = {
        "path": context.config.relative_to_repo(HAIR_PALETTE_PROFILE_PATH),
        "revision": palette.revision,
        "proxy_revision": palette.proxy_revision,
        "sha256": hashlib.sha256(HAIR_PALETTE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_color_change",
    }
    payload["hair_side_back_builder"] = {
        "path": context.config.relative_to_repo(HAIR_SIDE_BACK_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_SIDE_BACK_BUILDER_PATH.read_bytes()).hexdigest(),
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
    if crown is None:
        raise RuntimeError("Proxy v16 manifest cannot find the crown mesh")

    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["crown_vertices"] = len(crown.data.vertices)
    payload["head_geometry"]["crown_faces"] = len(crown.data.polygons)

    payload["hair_structure"] = {
        "strategy": "approved_reference_wavy_side_and_rear_medium_hair_silhouette",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "previous_scalp_coverage_revision": "v12",
        "side_back_silhouette_revision": "v13",
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "reuse_dark_v10_ramp_without_color_change",
        "geometry_strategy": {
            "front_crown": "unchanged_from_proxy_v15",
            "middle_crown": "subtle_side_edge_descent_without_width_increase",
            "rear_crown": "deeper_rear_slice_with_three_broad_hanging_edge_masses",
            "side_masses": "existing_physical_left_and_right_masses_elongated_asymmetrically",
            "back_masses": "existing_shell_and_sweeps_reshaped_without_new_objects",
            "nape": "existing_three_masses_form_an_uneven_hanging_lower_edge",
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "scalp_coverage": "preserved_from_v12",
            "new_hair_part_count": 0,
        },
        "side_back_contract": {
            "targeted_existing_objects": [
                item.name for item in side_back_profile.transforms
            ],
            "physical_sides_preserved": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "palette_changed": False,
            "forelock_changed": False,
            "animation_keys_changed": False,
        },
    }

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_head_profile = load_head_profile_v13
    factory._build_head_and_hair = _build_head_and_hair_v13
    factory._write_run_manifest = _write_run_manifest_v13
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
