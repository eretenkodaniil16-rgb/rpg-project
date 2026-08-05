from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("heart_cycle_build.py").read_text(encoding="utf-8")


def test_anatomy_v02_source_parses() -> None:
    ast.parse(SOURCE)


def test_revision_and_required_anatomy_are_locked() -> None:
    required_tokens = (
        'ANATOMY_REVISION = "heart_cutaway_v02"',
        '"LeftAuricle"',
        '"RightAuricle"',
        'f"{prefix}_Lobe_{index}"',
        '"RV_ModeratorBand"',
        '"LVOT_SeptalRidge"',
        '"RVOT_InfundibularRidge"',
        '"RightPapillary_Septal"',
        '"PulmonaryArtery_LeftBranch"',
        '"PulmonaryArtery_RightBranch"',
    )
    for token in required_tokens:
        assert token in SOURCE


def test_anatomy_remains_bound_to_phase_controls() -> None:
    assert '("LV", left_paths, 0.030, build.controls["left_ventricle"])' in SOURCE
    assert '("RV", right_paths, 0.042, build.controls["right_ventricle"])' in SOURCE
    assert '_parent_preserve_world(ridge, parent)' in SOURCE
    assert '_parent_preserve_world(moderator, build.controls["right_ventricle"])' in SOURCE
    assert 'build.controls["left_atrium"]' in SOURCE
    assert 'build.controls["right_atrium"]' in SOURCE
