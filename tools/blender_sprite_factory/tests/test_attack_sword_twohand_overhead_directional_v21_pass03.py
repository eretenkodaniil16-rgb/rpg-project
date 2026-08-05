from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass03.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass03.py"
)
WORKFLOW_PATH = (
    ROOT
    / ".github/workflows/validate-human-warrior-twohand-overhead-directional-v21.yml"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_overhead_directional_correction_v21_pass03",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("directional overhead pass03 correction could not load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_overhead_pass03_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_directional_overhead_pass03_uses_stable_side_scale() -> None:
    correction = _load_correction()
    assert correction.DIRECTION_SCALE_MULTIPLIER == {
        "down": 1.0,
        "left": 0.93,
        "right": 0.93,
        "up": 1.0,
    }
    assert correction.SIDE_DIRECTIONS == ("left", "right")
    assert correction.PRESERVE_ACTION_CURVES is True
    assert correction.PRESERVE_CHARACTER_LOCAL_WEAPON_ARC is True
    assert correction.PRESERVE_DOWN_PASS04_PIXELS is True
    assert correction.PRESERVE_DIRECTIONAL_ASYMMETRY is True


def test_directional_overhead_pass03_changes_framing_not_action() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "effective_scale =",
        "float(fixed_scale) * scale_multiplier",
        "fixed_scale=effective_scale",
        'metrics[key]["direction_scale_multiplier"] = scale_multiplier',
        'metrics[key]["directional_framing_only"] = True',
        'metrics[key]["action_curves_changed"] = False',
        "down framing must remain unchanged",
        "side framing multipliers diverged",
        '"approved_down_pass04_pixels_preserved": PRESERVE_DOWN_PASS04_PIXELS',
        '"mirroring_used": False',
        '"negative_scale_used": False',
        '"weapon_geometry_changed": False',
    )
    for marker in required:
        assert marker in source


def test_directional_overhead_pass03_restores_pass02_hooks() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    assert "ORIGINAL_RENDER_FRAME" in source
    assert "ORIGINAL_WRITE_MANIFEST" in source
    assert "pass02_adapter.main()" in source
    assert (
        "pass02_adapter._render_frame_directional_overhead_v21_pass02 = ("
        in source
    )
    assert (
        "pass02_adapter._write_manifest_directional_overhead_v21_pass02 = ("
        in source
    )


def test_directional_overhead_workflow_targets_pass03() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass03.py"
        in source
    )
    assert "twohand_overhead_directional_v21_pass03_32_frames" in source
