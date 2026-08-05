from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR
    / "attack_sword_twohand_overhead_directional_correction_v21_pass02.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass02.py"
)
WORKFLOW_PATH = (
    ROOT
    / ".github/workflows/validate-human-warrior-twohand-overhead-directional-v21.yml"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_twohand_overhead_directional_correction_v21_pass02",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("directional overhead pass02 correction could not load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_directional_overhead_pass02_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_directional_overhead_pass02_search_is_bounded() -> None:
    correction = _load_correction()
    assert correction.PROJECTION_SEARCH_STEP == 0.04
    assert correction.MINIMUM_SCREEN_PROJECTION == 0.44
    assert correction.REQUIRE_ZERO_EDGE_ALPHA is True
    assert correction.PRESERVE_ACTION_CURVES is True
    assert correction.PRESERVE_CHARACTER_LOCAL_ARC_ANGLE is True
    assert correction.PRESERVE_DOWN_PASS04_PIXELS is True


def test_directional_overhead_pass02_changes_projection_only_on_clipping() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required = (
        "_projection_candidates",
        "canonical_projection",
        "projection_adjusted_for_containment",
        "projection_candidate_diagnostics",
        "if not touched:",
        "base_adapter.PROJECTION_BY_FRAME[frame_number] = canonical_projection",
        "directional overhead pass02 found no contained projection",
        "attempted to change approved down pixels",
        '"action_curves_preserved": PRESERVE_ACTION_CURVES',
        '"mirroring_used": False',
        '"weapon_geometry_changed": False',
    )
    for marker in required:
        assert marker in source


def test_directional_overhead_workflow_targets_pass02() -> None:
    source = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert (
        "blender_sprite_factory_attack_sword_twohand_overhead_directional_v21_pass02.py"
        in source
    )
    assert "twohand_overhead_directional_v21_pass02_32_frames" in source
