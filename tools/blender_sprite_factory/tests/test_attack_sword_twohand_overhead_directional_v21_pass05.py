from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass05.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass05.py"
)
WORKFLOW_PATH = (
    ROOT
    / ".github/workflows/validate-human-warrior-twohand-overhead-directional-v21.yml"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_overhead_directional_correction_v21_pass05",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("directional overhead pass05 correction could not load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_overhead_pass05_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_directional_overhead_pass05_uses_measured_rear_scale() -> None:
    correction = _load_correction()
    assert correction.UP_SCALE_MULTIPLIER == 0.88
    assert correction.SOURCE_RAW_F03_ALPHA_HEIGHT == 154
    assert correction.TARGET_NORMALIZED_ALPHA_HEIGHT == 88
    assert correction.PRESERVE_ACTION_CURVES is True
    assert correction.PRESERVE_CHARACTER_LOCAL_WEAPON_ARC is True
    assert correction.PRESERVE_DOWN_PASS04_PIXELS is True
    assert correction.PRESERVE_SIDE_PASS03_FRAMING is True


def test_directional_overhead_pass05_patches_pass04_scale_only() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "ORIGINAL_UP_SCALE_MULTIPLIER",
        'pass04_adapter.UP_SCALE_MULTIPLIER = UP_SCALE_MULTIPLIER',
        "pass04_adapter.main()",
        "measured rear scale drifted",
        '"action_curves_preserved": PRESERVE_ACTION_CURVES',
        '"side_pass03_framing_preserved": PRESERVE_SIDE_PASS03_FRAMING',
        '"mirroring_used": False',
        '"negative_scale_used": False',
        '"weapon_geometry_changed": False',
    )
    for marker in required:
        assert marker in source


def test_directional_overhead_pass05_restores_pass04_contract() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    assert (
        "pass04_adapter.UP_SCALE_MULTIPLIER = ORIGINAL_UP_SCALE_MULTIPLIER"
        in source
    )
    assert "ORIGINAL_WRITE_MANIFEST" in source
    assert "_restore_contract()" in source


def test_directional_overhead_workflow_targets_pass05() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass05.py"
        in source
    )
    assert "twohand_overhead_directional_v21_pass05_32_frames" in source
