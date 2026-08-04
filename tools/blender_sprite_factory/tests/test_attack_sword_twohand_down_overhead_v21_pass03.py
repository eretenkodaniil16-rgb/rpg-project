from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR / "attack_sword_twohand_down_overhead_correction_v21_pass03.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass03.py"
)
WORKFLOW_PATH = (
    ROOT / ".github/workflows/validate-human-warrior-attack-twohand-overhead-v21.yml"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_down_overhead_correction_v21_pass03",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("overhead pass03 correction could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_overhead_pass03_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_overhead_pass03_changes_only_f03_projection() -> None:
    correction = _load_correction()
    assert correction.TARGET_FRAME == 3
    assert correction.F03_SCREEN_PROJECTION == 0.88
    assert correction.PRESERVE_F02 is True
    assert correction.PRESERVE_F04_F07_PROFILE is True
    assert correction.PRESERVE_BODY_ACTION is True
    assert correction.PRESERVE_WEAPON_GEOMETRY is True
    assert correction.REQUIRE_ZERO_EDGE_ALPHA is True


def test_overhead_pass03_restores_pass02_globals() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "ORIGINAL_PROJECTION_BY_FRAME",
        "ORIGINAL_REVISION",
        "ORIGINAL_WRITE_MANIFEST",
        "SCREEN_PROJECTION_BY_FRAME[TARGET_FRAME]",
        "_apply_pass03_contract",
        "_restore_pass03_contract",
        "f03 projection drifted",
        "f03 still touches canvas edge",
        '"weapon_geometry_changed": False',
        '"root_translation_used": False',
        '"mirroring_used": False',
        '"negative_scale_used": False',
    )
    for marker in required:
        assert marker in source


def test_overhead_workflow_retains_pass03_history() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass03.py"
        in source
    )
    assert "pass03" in source
