from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR / "attack_sword_twohand_down_overhead_correction_v21_pass02.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass02.py"
)
WORKFLOW_PATH = (
    ROOT / ".github/workflows/validate-human-warrior-attack-twohand-overhead-v21.yml"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_down_overhead_correction_v21_pass02",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("overhead pass02 correction could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_overhead_pass02_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_overhead_pass02_uses_vertical_guard_axis() -> None:
    correction = _load_correction()
    assert correction.TARGET_FRAMES == (2, 3, 4, 5, 6, 7)
    assert correction.SCREEN_OFFSET_DEGREES_BY_FRAME[2] == 0.0
    assert correction.SCREEN_OFFSET_DEGREES_BY_FRAME[3] == 0.0
    assert correction.SCREEN_OFFSET_DEGREES_BY_FRAME[4] == 180.0
    assert correction.SCREEN_OFFSET_DEGREES_BY_FRAME[5] == 180.0
    assert correction.SCREEN_PROJECTION_BY_FRAME[2] >= 0.95
    assert correction.SCREEN_PROJECTION_BY_FRAME[5] >= 0.95


def test_overhead_pass02_preserves_model_contract() -> None:
    correction = _load_correction()
    assert correction.PRESERVE_F01_F08 is True
    assert correction.PRESERVE_BODY_ACTION is True
    assert correction.PRESERVE_WEAPON_GEOMETRY is True
    assert correction.REQUIRE_ZERO_EDGE_ALPHA is True
    assert correction.USE_REFERENCE_DEPTH_SIGN is True


def test_overhead_pass02_adapter_restores_patches() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "_reference_guard_direction",
        "_target_direction",
        "_apply_world_rotation",
        "_render_frame_overhead_v21_pass02",
        "_write_manifest_overhead_v21_pass02",
        "_apply_pass02_contract",
        "_restore_pass02_contract",
        '"body_action_changed": False',
        '"weapon_geometry_changed": False',
        '"root_translation_used": False',
        '"mirroring_used": False',
        '"negative_scale_used": False',
    )
    for marker in required:
        assert marker in source


def test_overhead_workflow_targets_pass02() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_down_overhead_v21_pass02.py"
        in source
    )
    assert "twohand_down_overhead_v21_pass02" in source
