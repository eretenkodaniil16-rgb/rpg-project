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
import blender_sprite_factory_appearance_v01 as previous_adapter
from appearance_readability_correction_v02 import (
    CORRECTION_REVISION,
    load_appearance_readability_corrected_v02,
)
from head_profile_v22 import load_head_profile_v22
from walk_animation_builder import create_walk_down_actions_v02


CORRECTION_PATH = SCRIPT_DIR / "appearance_readability_correction_v02.py"
BASE_WRITE_RUN_MANIFEST = previous_adapter._write_run_manifest_appearance_v01


def _write_run_manifest_appearance_v02(
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
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["appearance_readability_correction"] = {
        "path": context.config.relative_to_repo(CORRECTION_PATH),
        "sha256": hashlib.sha256(CORRECTION_PATH.read_bytes()).hexdigest(),
        "revision": CORRECTION_REVISION,
        "reason": "fix_linear_color_conversion_and_increase_visible_temple_coverage",
        "rejected_render_run": "30439634828_1_pre_correction",
        "rejected_reason": "constant_srgb_values_were_used_as_linear_and_temple_fill_was_too_restrained",
    }
    payload.setdefault("appearance_candidate", {})
    payload["appearance_candidate"]["correction_revision"] = CORRECTION_REVISION
    payload["appearance_candidate"]["linear_color_conversion"] = True
    payload["appearance_candidate"]["temple_fill_strengthened"] = True
    payload["appearance_candidate"]["status"] = (
        "corrected_technical_candidate_requires_manual_appearance_review"
    )
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    corrected_profile = load_appearance_readability_corrected_v02("human_warrior_m01")

    appearance_builder._PROFILE = corrected_profile
    appearance_builder._rgb = factory._hex_to_linear_rgb
    appearance_builder.load_appearance_readability_profile_v01 = (
        lambda character_id: load_appearance_readability_corrected_v02(character_id)
    )
    previous_adapter.load_appearance_readability_profile_v01 = (
        lambda character_id: load_appearance_readability_corrected_v02(character_id)
    )

    factory.load_factory_config = appearance_builder.load_factory_config_appearance_v01
    factory.load_head_profile = load_head_profile_v22
    factory._create_material = appearance_builder.create_material_appearance_v01
    factory._build_head_and_hair = appearance_builder.build_head_and_hair_appearance_v01
    factory._build_armor = appearance_builder.build_armor_appearance_v01
    factory._build_arms = appearance_builder.build_arms_appearance_v01
    factory._build_legs = appearance_builder.build_legs_appearance_v01
    factory._build_accessories = appearance_builder.build_accessories_appearance_v01
    factory._create_actions = create_walk_down_actions_v02
    factory._write_run_manifest = _write_run_manifest_appearance_v02
    return factory.main()


if __name__ == "__main__":
    raise SystemExit(main())
