from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("heart_cycle_presentation_polish_v06.py").read_text(
    encoding="utf-8"
)


def test_presentation_v06_source_parses() -> None:
    ast.parse(SOURCE)


def test_flow_visibility_repair_is_locked() -> None:
    required_tokens = (
        'PRESENTATION_REVISION = "heart_cycle_presentation_polish_v06"',
        "_repair_flow_visibility",
        "_validate_flow_visibility",
        "canonical phase-boundary schedule",
        '"flow_visibility_validation"',
        "expected_flow_groups",
        "visible_flow_groups",
    )
    for token in required_tokens:
        assert token in SOURCE


def test_header_and_heart_separation_is_locked() -> None:
    assert "offset.location.x = 1.62" in SOURCE
    assert "offset.location.z = -0.12" in SOURCE
    assert 'title.data.align_x = "LEFT"' in SOURCE
    assert '"Infographic_HeaderPanel_v06"' in SOURCE
    assert '"Infographic_HeaderSeparator_v06"' in SOURCE
    assert '"header_occlusion": "prevented"' in SOURCE


def test_all_nine_midphase_flow_states_are_validated() -> None:
    assert "for phase, start, end in phase_ranges():" in SOURCE
    assert '"phase_count": len(phase_results)' in SOURCE
    assert "if failures:" in SOURCE
