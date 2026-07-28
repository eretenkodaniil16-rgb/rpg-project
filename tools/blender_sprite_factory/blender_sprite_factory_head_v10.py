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
import blender_sprite_factory_head_v09 as previous_adapter
from hair_lock_profile_v10 import load_hair_lock_profile_v10
from hair_mass_builder_v10 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    HAIR_ROTATION_OVERRIDES_DEGREES,
    HAIR_SCALE_MULTIPLIERS,
    HAIR_WORLD_OFFSETS,
    apply_dark_reference_hair_pass,
)
from hair_palette_v10 import load_hair_palette_v10
from head_profile_v10 import load_head_profile_v10


PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v09.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v10.py"
PREVIOUS_HAIR_LOCK_PROFILE_PATH = SCRIPT_DIR / "hair_lock_profile_v09.py"
HAIR_LOCK_PROFILE_PATH = SCRIPT_DIR / "hair_lock_profile_v10.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_LOCK_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v10.py"


def _build_head_and_hair_v10(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v09(context)
    apply_dark_reference_hair_pass(context)


def _write_run_manifest_v10(
    context: factory.BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[factory.FrameArtifact],
    contact_sheet: Path | None,
) -> Path:
    manifest_path = previous_adapter._write_run_manifest_v09(
        context,
        run_dir,
        run_id,
        blend_path,
        artifacts,
        contact_sheet,
    )
    lock_profile = load_hair_lock_profile_v10()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v09",
        "proxy_revision": "v12",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["previous_hair_lock_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HAIR_LOCK_PROFILE_PATH),
        "revision": "v09",
        "proxy_revision": "v12",
        "sha256": hashlib.sha256(PREVIOUS_HAIR_LOCK_PROFILE_PATH.read_bytes()).hexdigest(),
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
        raise RuntimeError("Proxy v13 manifest cannot find the curved lock separator mesh")

    payload["head_geometry"]["separate_hair_parts"] = len(actual_hair_names)
    payload["head_geometry"]["active_hair_names"] = actual_hair_names
    payload["head_geometry"]["lock_separator_vertices"] = len(separator.data.vertices)
    payload["head_geometry"]["lock_separator_faces"] = len(separator.data.polygons)
    payload["hair_structure"] = {
        "strategy": "approved_reference_dark_hair_with_curved_large_lock_grooves",
        "zones": ["top", "front", "sides", "back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "crown_and_forelock_geometry_source": "v08",
        "previous_lock_geometry_revision": "v09",
        "palette_revision": palette.revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "material_strategy": "quantization_exact_srgb_to_linear_emission_with_restrained_highlight",
        "skin_contrast_contract": {
            "hair_highlight": palette.highlight,
            "separator": palette.separator,
            "intent": "hair remains visibly darker than pale skin in normalized 96x96 frames",
        },
        "lock_separator_mesh": {
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
    factory.load_head_profile = load_head_profile_v10
    factory._build_head_and_hair = _build_head_and_hair_v10
    factory._write_run_manifest = _write_run_manifest_v10
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
