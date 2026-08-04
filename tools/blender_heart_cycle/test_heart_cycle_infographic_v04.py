from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("heart_cycle_infographic_v04.py").read_text(
    encoding="utf-8"
)


def test_infographic_source_parses() -> None:
    ast.parse(SOURCE)


def test_infographic_revision_and_layout_are_locked() -> None:
    required = (
        'INFOGRAPHIC_REVISION = "heart_cycle_infographic_v04"',
        '"СЕРДЕЧНЫЙ ЦИКЛ"',
        '"ФАЗА {phase.index} ИЗ 9"',
        '"АВ-клапаны: {av_state}',
        '"Полулунные: {semilunar_state}',
        '"title_top; phase_panel_left; cutaway_heart_right"',
        'offset.location.x = 1.35',
    )
    for token in required:
        assert token in SOURCE


def test_all_nine_phase_cards_are_generated_from_shared_timeline() -> None:
    assert "for phase, start, end in phase_ranges():" in SOURCE
    assert "_set_phase_visibility(group, start, end)" in SOURCE
    assert "_render_infographic_phase_previews" in SOURCE
    assert 'print(f"HEART_CYCLE_INFOGRAPHIC_PREVIEWS={len(preview_paths)}")' in SOURCE


def test_russian_font_has_cross_platform_fallbacks() -> None:
    assert "C:/Windows/Fonts/segoeui.ttf" in SOURCE
    assert "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" in SOURCE
    assert "/System/Library/Fonts/Supplemental/Arial.ttf" in SOURCE


def test_compositor_reuses_phase_rig_without_rebuilding_anatomy() -> None:
    assert "phase_render.build_model_once(resolution)" in SOURCE
    assert 'scene["phase_rig_revision"] = rig.PHASE_RIG_REVISION' in SOURCE
    assert 'scene["infographic_revision"] = INFOGRAPHIC_REVISION' in SOURCE
