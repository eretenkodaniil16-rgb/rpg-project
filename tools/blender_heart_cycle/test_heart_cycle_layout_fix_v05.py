from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("heart_cycle_layout_fix_v05.py").read_text(
    encoding="utf-8"
)


def test_layout_fix_v05_source_parses() -> None:
    ast.parse(SOURCE)


def test_reference_chamber_layout_is_locked() -> None:
    required_tokens = (
        'LAYOUT_REVISION = "heart_cycle_layout_fix_v05"',
        '"LeftVentricle_Wall": (0.78, 0.18, 2.55)',
        '"RightVentricle_Wall": (-0.78, 0.23, 2.65)',
        '"LeftAtrium_Wall": (0.97, 0.20, 4.58)',
        '"RightAtrium_Wall": (-0.97, 0.20, 4.58)',
        '"LeftVentricle_Wall": (0.97, 1.00, 1.08)',
        '"RightVentricle_Wall": (1.08, 0.98, 0.92)',
    )
    for token in required_tokens:
        assert token in SOURCE


def test_layout_has_runtime_anatomical_guards() -> None:
    assert "left ventricular center is not sufficiently below left atrium" in SOURCE
    assert "right ventricular center is not sufficiently below right atrium" in SOURCE
    assert "left ventricle does not form the inferior apex" in SOURCE
    assert '"ventricular_centers_below_atria": True' in SOURCE
    assert '"left_ventricle_forms_apex": True' in SOURCE


def test_blender_52_layered_actions_are_supported() -> None:
    assert 'getattr(action, "layers", ())' in SOURCE
    assert 'getattr(layer, "strips", ())' in SOURCE
    assert 'getattr(strip, "channelbags", ())' in SOURCE
    assert "_set_interpolation_blender_52" in SOURCE
    assert "_set_constant_visibility_interpolation_blender_52" in SOURCE
