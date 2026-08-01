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
import blender_sprite_factory_walk_down_v02 as previous_adapter
from appearance_builder_v01 import (
    build_accessories_appearance_v01,
    build_armor_appearance_v01,
    build_arms_appearance_v01,
    build_head_and_hair_appearance_v01,
    build_legs_appearance_v01,
    create_material_appearance_v01,
    load_factory_config_appearance_v01,
)
from appearance_readability_profile_v01 import load_appearance_readability_profile_v01
from head_profile_v22 import load_head_profile_v22
from walk_animation_builder import create_walk_down_actions_v02


BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_walk_down_v02
APPEARANCE_PROFILE_PATH = SCRIPT_DIR / "appearance_readability_profile_v01.py"
APPEARANCE_BUILDER_PATH = SCRIPT_DIR / "appearance_builder_v01.py"
HEAD_PROFILE_PATH = SCRIPT_DIR / "head_profile_v22.py"


def _vector(values: object) -> list[float]:
    return [float(value) for value in values]


def _write_run_manifest_appearance_v01(
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
    profile = load_appearance_readability_profile_v01(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    hair_names = sorted(
        obj.name
        for obj in factory.bpy.data.objects
        if obj.get(factory.MODULE_PROPERTY) == "hair"
    )
    expected_fills = sorted(item.name for item in profile.temple_fills)
    if len(hair_names) != 12 or not set(expected_fills).issubset(hair_names):
        raise RuntimeError("Appearance v01 manifest requires twelve hair objects and two temple fills")

    crown = factory.bpy.data.objects.get("hair_reference_crown_mesh")
    if crown is None or len(crown.data.vertices) != 226 or len(crown.data.polygons) != 256:
        raise RuntimeError("Appearance v01 manifest requires unchanged crown topology 226/256")

    material_contract: dict[str, dict[str, object]] = {}
    for slot_id, expected_hex in profile.material_overrides:
        material = context.materials.get(slot_id)
        if material is None:
            raise RuntimeError(f"Appearance v01 manifest cannot find material: {slot_id}")
        if material.get("appearance_override_hex") != expected_hex:
            raise RuntimeError(f"Appearance v01 material override drifted: {slot_id}")
        material_contract[slot_id] = {
            "hex": expected_hex,
            "texture_link_disabled": bool(material.get("appearance_texture_link_disabled")),
        }

    scarf_stats: dict[str, dict[str, object]] = {}
    for name in ("scarf_wrap", "scarf_front"):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Appearance v01 manifest cannot find scarf object: {name}")
        highlight_faces = int(obj.get("scarf_highlight_face_count", 0))
        if highlight_faces <= 0:
            raise RuntimeError(f"Appearance v01 scarf highlight was not assigned: {name}")
        scarf_stats[name] = {
            "scale": _vector(obj.scale),
            "highlight_faces": highlight_faces,
        }

    clothing_details: dict[str, dict[str, object]] = {}
    for spec in profile.clothing_details:
        obj = factory.bpy.data.objects.get(spec.name)
        if obj is None:
            raise RuntimeError(f"Appearance v01 manifest cannot find clothing detail: {spec.name}")
        clothing_details[spec.name] = {
            "module_id": obj.get(factory.MODULE_PROPERTY),
            "material_slot_id": obj.get(factory.MATERIAL_PROPERTY),
            "dimensions": _vector(obj.dimensions),
        }

    payload["appearance_readability_profile"] = {
        "path": context.config.relative_to_repo(APPEARANCE_PROFILE_PATH),
        "sha256": hashlib.sha256(APPEARANCE_PROFILE_PATH.read_bytes()).hexdigest(),
        "revision": profile.revision,
        "head_revision": profile.head_revision,
        "proxy_revision": profile.proxy_revision,
        "quantization_additions": list(profile.quantization_additions),
        "material_overrides": material_contract,
        "scarf_highlight_hex": profile.scarf_highlight_hex,
    }
    payload["appearance_builder"] = {
        "path": context.config.relative_to_repo(APPEARANCE_BUILDER_PATH),
        "sha256": hashlib.sha256(APPEARANCE_BUILDER_PATH.read_bytes()).hexdigest(),
    }
    payload["head_profile"] = {
        "path": context.config.relative_to_repo(HEAD_PROFILE_PATH),
        "sha256": hashlib.sha256(HEAD_PROFILE_PATH.read_bytes()).hexdigest(),
        "revision": context.head.revision,
        "proxy_revision": context.proxy_revision,
    }
    payload["appearance_candidate"] = {
        "revision": profile.revision,
        "status": "technical_candidate_requires_manual_appearance_review",
        "hair": {
            "object_count": len(hair_names),
            "active_names": hair_names,
            "temple_fill_names": expected_fills,
            "crown_vertices": len(crown.data.vertices),
            "crown_faces": len(crown.data.polygons),
            "crown_geometry_changed": False,
            "visible_density_reduction_allowed": False,
            "mirroring_used": False,
            "negative_scale_used": False,
        },
        "scarf": {
            "base_hex": profile.material_override_map()["scarf"],
            "highlight_hex": profile.scarf_highlight_hex,
            "objects": scarf_stats,
        },
        "clothing": {
            "details": clothing_details,
            "material_overrides": material_contract,
            "equipment_sides_changed": False,
            "rig_changed": False,
            "animation_keys_changed": False,
        },
    }
    payload.setdefault("animation_contract", {})
    payload["animation_contract"]["head_v21_proxy_v24_locked"] = False
    payload["animation_contract"]["head_v22_proxy_v25_locked"] = True
    payload["animation_contract"]["walk_down_v02_reused_without_key_change"] = True

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    factory.load_factory_config = load_factory_config_appearance_v01
    factory.load_head_profile = load_head_profile_v22
    factory._create_material = create_material_appearance_v01
    factory._build_head_and_hair = build_head_and_hair_appearance_v01
    factory._build_armor = build_armor_appearance_v01
    factory._build_arms = build_arms_appearance_v01
    factory._build_legs = build_legs_appearance_v01
    factory._build_accessories = build_accessories_appearance_v01
    factory._create_actions = create_walk_down_actions_v02
    factory._write_run_manifest = _write_run_manifest_appearance_v01
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
