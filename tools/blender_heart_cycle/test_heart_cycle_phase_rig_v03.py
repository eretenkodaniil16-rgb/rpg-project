from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RIG_SOURCE = (ROOT / "heart_cycle_phase_rig_v03.py").read_text(encoding="utf-8")
ENTRY_SOURCE = (ROOT / "heart_cycle_phase_rig_render_v03.py").read_text(encoding="utf-8")


def test_phase_rig_sources_parse() -> None:
    ast.parse(RIG_SOURCE)
    ast.parse(ENTRY_SOURCE)


def test_phase_rig_revision_and_loop_contract_are_locked() -> None:
    assert 'PHASE_RIG_REVISION = "heart_cycle_phase_rig_v03"' in RIG_SOURCE
    assert 'MODEL_REVISION = "heart_cutaway_v02_phase_rig_v03"' in RIG_SOURCE
    assert "State 0 is also state 9" in RIG_SOURCE
    assert "frame 1 and frame 450 share the same boundary state" in RIG_SOURCE


def test_all_nine_phases_have_flow_profiles() -> None:
    for slug in (
        "atrial_systole",
        "asynchronous_contraction",
        "isometric_contraction",
        "rapid_ejection",
        "slow_ejection",
        "protodiastolic_period",
        "isometric_relaxation",
        "rapid_filling",
        "slow_filling",
    ):
        assert f'"{slug}":' in RIG_SOURCE


def test_pressure_and_valve_channels_are_exported() -> None:
    for channel in (
        "left_ventricular_pressure_mmHg",
        "right_ventricular_pressure_mmHg",
        "aortic_pressure_mmHg",
        "pulmonary_artery_pressure_mmHg",
        "ventricular_volume_fraction",
        "av_valve_open_fraction",
        "semilunar_valve_open_fraction",
    ):
        assert f'"{channel}"' in RIG_SOURCE


def test_render_entry_applies_phase_rig_once() -> None:
    assert "model._animate = _no_base_animation" in ENTRY_SOURCE
    assert "rig._PREVIOUS_BUILD_MODEL(resolution)" in ENTRY_SOURCE
    assert "rig._animate_phase_rig(build)" in ENTRY_SOURCE
    assert "scene.timeline_markers.remove(marker)" in ENTRY_SOURCE
    assert "model.build_model = build_model_once" in ENTRY_SOURCE


def test_nine_midphase_previews_are_rendered() -> None:
    assert "for phase, start, end in phase_ranges():" in RIG_SOURCE
    assert 'preview_root = output_root / "phase_previews"' in RIG_SOURCE
    assert 'f"phase_{phase.index:02d}_{phase.slug}_f{frame:03d}.png"' in RIG_SOURCE
