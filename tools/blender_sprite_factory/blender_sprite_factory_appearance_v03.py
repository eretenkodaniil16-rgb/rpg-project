from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import appearance_builder_v01 as appearance_builder
import blender_sprite_factory as factory
import blender_sprite_factory_appearance_v01 as appearance_adapter_v01
import blender_sprite_factory_appearance_v02 as previous_adapter
from appearance_readability_correction_v03 import (
    CORRECTION_REVISION,
    load_appearance_readability_corrected_v03,
)
from head_profile_v22 import load_head_profile_v22
from walk_animation_builder import create_walk_down_actions_v02


CORRECTION_PATH = SCRIPT_DIR / "appearance_readability_correction_v03.py"
BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_appearance_v02


def _force_full_scarf_palette(context: factory.BuildContext) -> dict[str, int]:
    profile = load_appearance_readability_corrected_v03(context.config.character_id)
    base_material = appearance_builder._constant_material(
        "MAT_scarf_base_v03",
        profile.material_override_map()["scarf"],
        roughness=0.92,
    )
    highlight_material = appearance_builder._constant_material(
        "MAT_scarf_highlight_v03",
        profile.scarf_highlight_hex,
        roughness=0.88,
    )
    assigned: dict[str, int] = {}
    for name in ("scarf_wrap", "scarf_front"):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Appearance v03 cannot find scarf object: {name}")
        obj.data.materials.clear()
        obj.data.materials.append(base_material)
        for polygon in obj.data.polygons:
            polygon.material_index = 0
        highlight_count = appearance_builder._assign_scarf_highlight(obj, highlight_material)
        if any(polygon.material_index not in {0, 1} for polygon in obj.data.polygons):
            raise RuntimeError(f"Appearance v03 found an unexpected scarf material slot: {name}")
        obj["appearance_correction_revision"] = CORRECTION_REVISION
        obj["scarf_full_base_assignment"] = True
        assigned[name] = highlight_count
    return assigned


def _build_armor_appearance_v03(context: factory.BuildContext) -> None:
    appearance_builder.build_armor_appearance_v01(context)
    assigned = _force_full_scarf_palette(context)
    if any(count <= 0 for count in assigned.values()):
        raise RuntimeError("Appearance v03 must preserve local scarf highlights")
    factory.bpy.context.view_layer.update()


def _write_run_manifest_appearance_v03(
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
    profile = load_appearance_readability_corrected_v03(context.config.character_id)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    scarf_contract: dict[str, dict[str, object]] = {}
    for name in ("scarf_wrap", "scarf_front"):
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Appearance v03 manifest cannot find scarf object: {name}")
        if not bool(obj.get("scarf_full_base_assignment")):
            raise RuntimeError(f"Appearance v03 scarf base assignment was not stamped: {name}")
        material_names = [material.name for material in obj.data.materials]
        if material_names != ["MAT_scarf_base_v03", "MAT_scarf_highlight_v03"]:
            raise RuntimeError(f"Appearance v03 scarf material slots drifted: {name}={material_names}")
        scarf_contract[name] = {
            "material_names": material_names,
            "polygon_count": len(obj.data.polygons),
            "highlight_faces": int(obj.get("scarf_highlight_face_count", 0)),
            "full_base_assignment": True,
        }

    payload["appearance_readability_correction_v03"] = {
        "path": context.config.relative_to_repo(CORRECTION_PATH),
        "sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "revision": CORRECTION_REVISION,
        "reason": (
            "restore_original_dark_clothing_materials_force_full_red_scarf_assignment_"
            "and_strengthen_temple_coverage"
        ),
        "rejected_predecessor": {
            "revision": "v02",
            "reason": "non_scarf_clothing_became_too_light_and_scarf_center_was_not_reliably_red",
        },
        "hair": {
            "temple_fill_count": len(profile.temple_fills),
            "retained_side_nape_transform_count": len(profile.hair_transforms),
            "crown_geometry_changed": False,
            "visible_density_reduction_allowed": False,
            "new_hair_object_count": 0,
        },
        "scarf": {
            "base_hex": profile.material_override_map()["scarf"],
            "highlight_hex": profile.scarf_highlight_hex,
            "objects": scarf_contract,
        },
        "clothing": {
            "material_overrides": dict(profile.material_overrides),
            "original_non_scarf_materials_restored": True,
            "readability_details_retained": [
                item.name for item in profile.clothing_details
            ],
            "equipment_sides_changed": False,
        },
        "animation_keys_changed": False,
        "status": "technical_candidate_requires_manual_appearance_review",
    }
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["correction_revision"] = CORRECTION_REVISION
    payload["appearance_candidate"]["full_scarf_material_assignment"] = True
    payload["appearance_candidate"]["original_non_scarf_materials_restored"] = True
    payload["appearance_candidate"]["status"] = (
        "v03_technical_candidate_requires_manual_appearance_review"
    )

    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    corrected_profile = load_appearance_readability_corrected_v03("human_warrior_m01")

    appearance_builder._PROFILE = corrected_profile
    appearance_builder._rgb = factory._hex_to_linear_rgb
    appearance_builder.load_appearance_readability_profile_v01 = (
        lambda character_id: load_appearance_readability_corrected_v03(character_id)
    )
    appearance_adapter_v01.load_appearance_readability_profile_v01 = (
        lambda character_id: load_appearance_readability_corrected_v03(character_id)
    )

    factory.load_factory_config = appearance_builder.load_factory_config_appearance_v01
    factory.load_head_profile = load_head_profile_v22
    factory._create_material = appearance_builder.create_material_appearance_v01
    factory._build_head_and_hair = appearance_builder.build_head_and_hair_appearance_v01
    factory._build_armor = _build_armor_appearance_v03
    factory._build_arms = appearance_builder.build_arms_appearance_v01
    factory._build_legs = appearance_builder.build_legs_appearance_v01
    factory._build_accessories = appearance_builder.build_accessories_appearance_v01
    factory._create_actions = create_walk_down_actions_v02
    factory._write_run_manifest = _write_run_manifest_appearance_v03
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
