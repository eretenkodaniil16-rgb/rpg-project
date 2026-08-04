from __future__ import annotations

import ast
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FACTORY_DIR = ROOT / "tools" / "blender_sprite_factory"
CORRECTION_PATH = (
    FACTORY_DIR / "attack_sword_directional_cycle_correction_v21_pass55.py"
)
ADAPTER_PATH = (
    FACTORY_DIR
    / "blender_sprite_factory_attack_sword_directional_cycle_v21_pass55.py"
)


def _load_correction() -> object:
    spec = importlib.util.spec_from_file_location(
        "attack_sword_directional_cycle_correction_v21_pass55",
        CORRECTION_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("pass55 correction module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pass55_sources_parse() -> None:
    ast.parse(CORRECTION_PATH.read_text(encoding="utf-8"))
    ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_pass55_flips_only_f04_f05_to_front_depth() -> None:
    correction = _load_correction()
    assert correction.FRONT_DEPTH_FRAMES == (4, 5)
    assert set(correction.PROJECTED_WEAPON_PROFILE_OVERRIDES_BY_FRAME) == {4, 5}
    for frame_number in correction.FRONT_DEPTH_FRAMES:
        profile = correction.PROJECTED_WEAPON_PROFILE_OVERRIDES_BY_FRAME[
            frame_number
        ]
        assert profile["depth_branch"] == "flipped"
        assert profile["projection"] > 0.0
    assert correction.PRESERVE_SCREEN_SPACE_TRAJECTORY is True
    assert correction.PRESERVE_ACTION_DATA is True


def test_pass55_f08_uses_temporary_horizontal_overscan() -> None:
    correction = _load_correction()
    assert correction.BOUNDARY_FIX_FRAME == 8
    assert correction.CAMERA_SHIFT_X_OVERRIDES_BY_FRAME == {8: -0.05}
    assert correction.REQUIRE_ZERO_EDGE_ALPHA is True


def test_pass55_adapter_restores_mutated_pass54_contract() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    required_markers = (
        "ANGLE_ONLY_WEAPON_OFFSET_DEGREES_BY_FRAME.pop",
        "PROJECTED_WEAPON_PROFILE_BY_FRAME.update",
        "EXPECTED_SOURCE_PROJECTION_BY_FRAME.update",
        "CAMERA_SHIFT_X_BY_FRAME.update",
        "_restore_pass55_contract",
        "ORIGINAL_PROJECTED_PROFILE",
        "ORIGINAL_EXPECTED_SOURCE",
        "ORIGINAL_ANGLE_ONLY",
        "ORIGINAL_CAMERA_SHIFT_X",
        "camera_shift_persistent_change",
    )
    for marker in required_markers:
        assert marker in source


def test_pass55_manifest_requires_front_branch_and_zero_edges() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8")
    assert 'str(metric["depth_branch"]) != "flipped"' in source
    assert "any(edge_counts.values())" in source
    assert '"attack_sword_01_twohand_up_f04_f05_front_depth": True' in source
    assert '"attack_sword_01_twohand_up_f08_boundary_fixed": True' in source
    assert '"approved_down_v20_changed": False' in source
    assert '"root_translation_used": False' in source
    assert '"mirroring_used": False' in source
    assert '"weapon_geometry_changed": False' in source
