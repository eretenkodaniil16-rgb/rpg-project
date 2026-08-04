from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR / "attack_sword_directional_cycle_correction_v21_pass56.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass56.py"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_directional_cycle_correction_v21_pass56",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("pass56 correction module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pass56_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_pass56_scene_key_respects_blender_limit() -> None:
    correction = _load_correction()
    assert len(correction.SHORT_CLEARANCE_SCENE_KEY) <= 63
    assert correction.MAX_BLENDER_IDPROPERTY_NAME_LENGTH == 63
    assert correction.VISUAL_OUTPUT_CHANGED_FROM_PASS55 is False
    assert correction.FRONT_DEPTH_SELECTION_PRESERVED is True
    assert correction.BOUNDARY_FIX_PRESERVED is True


def test_pass56_replaces_only_clearance_validator_and_manifest() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    markers = (
        "_validate_directional_clearance_v21_pass56",
        "SHORT_CLEARANCE_SCENE_KEY",
        "_write_manifest_v21_pass56",
        "_apply_pass56_contract",
        "_restore_pass56_contract",
        "pass55_adapter.main()",
    )
    for marker in markers:
        assert marker in source
    assert '"visual_output_changed_from_pass55": VISUAL_OUTPUT_CHANGED_FROM_PASS55' in source
    assert '"approved_down_v20_changed": False' in source
    assert '"root_translation_used": False' in source
    assert '"mirroring_used": False' in source
    assert '"weapon_geometry_changed": False' in source
