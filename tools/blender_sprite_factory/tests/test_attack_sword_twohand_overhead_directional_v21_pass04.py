from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass04.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass04.py"
)
WORKFLOW_PATH = (
    ROOT
    / ".github/workflows/validate-human-warrior-twohand-overhead-directional-v21.yml"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_overhead_directional_correction_v21_pass04",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("directional overhead pass04 correction could not load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_overhead_pass04_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_directional_overhead_pass04_uses_same_rear_margin() -> None:
    correction = _load_correction()
    assert correction.UP_SCALE_MULTIPLIER == 0.93
    assert correction.PRESERVE_ACTION_CURVES is True
    assert correction.PRESERVE_CHARACTER_LOCAL_WEAPON_ARC is True
    assert correction.PRESERVE_DOWN_PASS04_PIXELS is True
    assert correction.PRESERVE_SIDE_PASS03_FRAMING is True
    assert correction.PRESERVE_DIRECTIONAL_ASYMMETRY is True


def test_directional_overhead_pass04_patches_only_up_scale_and_manifest() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        'pass03_adapter.DIRECTION_SCALE_MULTIPLIER["up"] = UP_SCALE_MULTIPLIER',
        "ORIGINAL_DIRECTION_SCALE_MULTIPLIER",
        "ORIGINAL_WRITE_MANIFEST",
        "rear framing drifted",
        "changed pass03 side framing",
        "changed approved down framing",
        '"action_curves_preserved": PRESERVE_ACTION_CURVES',
        '"side_pass03_framing_preserved": PRESERVE_SIDE_PASS03_FRAMING',
        '"mirroring_used": False',
        '"negative_scale_used": False',
        '"weapon_geometry_changed": False',
    )
    for marker in required:
        assert marker in source


def test_directional_overhead_pass04_restores_pass03_contract() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    assert "DIRECTION_SCALE_MULTIPLIER.clear()" in source
    assert "DIRECTION_SCALE_MULTIPLIER.update(" in source
    assert "pass03_adapter.main()" in source
    assert "_restore_contract()" in source


def test_directional_overhead_workflow_targets_pass04() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass04.py"
        in source
    )
    assert "twohand_overhead_directional_v21_pass04_32_frames" in source
