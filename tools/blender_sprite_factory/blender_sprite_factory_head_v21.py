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
import blender_sprite_factory_head_v20 as previous_adapter
from hair_dense_crown_back_profile_v20 import load_hair_dense_crown_back_profile_v20
from hair_mass_builder_v21 import (
    ACTIVE_HAIR_PART_NAMES,
    DARK_REFERENCE_HAIR_FACET_COLORS,
    DARK_REFERENCE_HAIR_PALETTE,
    REMOVED_BACK_OVERLAY_NAMES,
    RETAINED_PROFILE_LOCK_NAMES,
    apply_side_nape_volume_pass,
)
from hair_organic_tone_profile_v18 import load_hair_organic_tone_profile_v18
from hair_palette_v10 import load_hair_palette_v10
from hair_side_nape_volume_profile_v21 import load_hair_side_nape_volume_profile_v21
from head_profile_v21 import load_head_profile_v21


BASE_WRITE_RUN_MANIFEST = previous_adapter.BASE_WRITE_RUN_MANIFEST
PREVIOUS_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v20.py"
ACTIVE_HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v21.py"
HAIR_DENSE_PROFILE_PATH = SCRIPT_DIR / "hair_dense_crown_back_profile_v20.py"
HAIR_TRANSITION_PROFILE_PATH = SCRIPT_DIR / "hair_side_nape_volume_profile_v21.py"
HAIR_TONE_PROFILE_PATH = SCRIPT_DIR / "hair_organic_tone_profile_v18.py"
HAIR_PALETTE_PROFILE_PATH = SCRIPT_DIR / "hair_palette_v10.py"
HAIR_TRANSITION_BUILDER_PATH = SCRIPT_DIR / "hair_mass_builder_v21.py"


def _build_head_and_hair_v21(context: factory.BuildContext) -> None:
    previous_adapter._build_head_and_hair_v20(context)
    apply_side_nape_volume_pass(context)


def _transform_payload(transform: object) -> dict[str, object]:
    return {
        "name": transform.name,
        "zone": transform.zone,
        "physical_side": transform.physical_side,
        "scale_multiplier": list(transform.scale_multiplier),
        "world_offset": list(transform.world_offset),
        "rotation_delta_degrees": list(transform.rotation_delta_degrees),
    }


def _vector_payload(values: object) -> list[float]:
    return [float(value) for value in values]


def _write_run_manifest_v21(
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

    dense = load_hair_dense_crown_back_profile_v20()
    transition = load_hair_side_nape_volume_profile_v21()
    tone = load_hair_organic_tone_profile_v18()
    palette = load_hair_palette_v10()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    payload["previous_head_profile"] = {
        "path": context.config.relative_to_repo(PREVIOUS_HEAD_PROFILE_PATH),
        "revision": "v20",
        "proxy_revision": "v23",
        "sha256": hashlib.sha256(PREVIOUS_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(ACTIVE_HEAD_PROFILE_PATH),
        "revision": context.head.revision,
        "proxy_revision": context.head.proxy_revision,
        "sha256": hashlib.sha256(ACTIVE_HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
    }
    payload["hair_dense_profile"] = {
        "path": context.config.relative_to_repo(HAIR_DENSE_PROFILE_PATH),
        "revision": dense.revision,
        "proxy_revision": dense.proxy_revision,
        "sha256": hashlib.sha256(HAIR_DENSE_PROFILE_PATH.read_bytes()).hexdigest(),
        "status": "reused_without_crown_geometry_change",
    }
    payload["hair_side_nape_volume_profile"] = {
        "path": context.config.relative_to_repo(HAIR_TRANSITION_PROFILE_PATH),
        "revision": transition.revision,
        "proxy_revision": transition.proxy_revision,
        "sha256": hashlib.sha256(HAIR_TRANSITION_PROFILE_PATH.read_bytes()).hexdigest(),
        "transforms": [_transform_payload(item) for item in transition.transforms],
        "target_names": sorted(item.name for item in transition.transforms),
        "density_reduction_allowed": False,
        "long_hair_extension_allowed": False,
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
    payload["hair_side_nape_volume_builder"] = {
        "path": context.config.relative_to_repo(HAIR_TRANSITION_BUILDER_PATH),
        "sha256": hashlib.sha256(HAIR_TRANSITION_BUILDER_PATH.read_bytes()).hexdigest(),
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
        raise RuntimeError("Proxy v24 manifest cannot find the proxy v23 dense crown")
    if len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Proxy v24 manifest found changed crown topology")

    retained_stats: dict[str, dict[str, object]] = {}
    for transform in transition.transforms:
        obj = factory.bpy.data.objects.get(transform.name)
        if obj is None:
            raise RuntimeError(f"Proxy v24 manifest cannot find retained mass: {transform.name}")
        retained_stats[transform.name] = {
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
            "zone": transform.zone,
            "physical_side": obj.get("hair_physical_side"),
            "scale": _vector_payload(obj.scale),
            "world_translation": _vector_payload(obj.matrix_world.translation),
            "scale_multiplier": list(transform.scale_multiplier),
            "world_offset": list(transform.world_offset),
            "rotation_delta_degrees": list(transform.rotation_delta_degrees),
        }

    payload.setdefault("head_geometry", {})
    payload["head_geometry"].update(
        {
            "separate_hair_parts": len(actual_hair_names),
            "active_hair_names": actual_hair_names,
            "dense_crown_back_vertices": len(crown.data.vertices),
            "dense_crown_back_faces": len(crown.data.polygons),
            "crown_geometry_status": "unchanged_from_proxy_v23",
            "retained_side_nape_masses": retained_stats,
        }
    )

    payload["hair_structure"] = {
        "strategy": "dense_proxy_v23_crown_with_local_temple_side_nape_volume",
        "zones": ["top", "front", "side_transition", "dense_organic_back", "nape"],
        "active_parts": sorted(ACTIVE_HAIR_PART_NAMES),
        "face_geometry_locked_to_revision": "v07",
        "crown_geometry_locked_to_revision": dense.revision,
        "side_nape_volume_revision": transition.revision,
        "localized_tone_revision": tone.revision,
        "palette_source_revision": palette.revision,
        "palette_source_proxy_revision": palette.proxy_revision,
        "material_palette": list(DARK_REFERENCE_HAIR_PALETTE),
        "material_roles": dict(DARK_REFERENCE_HAIR_FACET_COLORS),
        "art_direction": {
            "primary_goal": "continuous_medium_length_wavy_hair_mass",
            "forced_angularity": False,
            "rear_taper_allowed": False,
            "visible_density_reduction_allowed": False,
            "long_hanging_locks_allowed": False,
            "pixel_steps_expected_from_normalization": True,
        },
        "geometry_strategy": {
            "crown_back": "unchanged_proxy_v23_dense_mesh",
            "side_nape": "restrained_positive_scale_depth_and_descent_on_five_existing_masses",
            "removed_overlays": sorted(REMOVED_BACK_OVERLAY_NAMES),
            "retained_profile_locks": sorted(RETAINED_PROFILE_LOCK_NAMES),
            "forelock": "unchanged_from_v11",
            "separators": "unchanged_six_short_local_depressions_from_v11",
            "new_hair_part_count": 0,
        },
        "transition_contract": {
            "target_count": len(transition.transforms),
            "target_names": sorted(item.name for item in transition.transforms),
            "retained_topology": "38_vertices_42_faces_each",
            "crown_vertices": len(crown.data.vertices),
            "crown_faces": len(crown.data.polygons),
            "physical_sides_preserved": True,
            "mirroring_used": False,
            "negative_scale_used": False,
            "palette_changed": False,
            "tone_regions_changed": False,
            "crown_geometry_changed": False,
            "target_topology_changed": False,
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
    factory.load_head_profile = load_head_profile_v21
    factory._build_head_and_hair = _build_head_and_hair_v21
    factory._write_run_manifest = _write_run_manifest_v21
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
