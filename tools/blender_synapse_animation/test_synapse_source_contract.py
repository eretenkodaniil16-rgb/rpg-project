from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def test_blender_sources_parse():
    for name in (
        "blender_helpers.py",
        "synapse_scene_v01.py",
        "synapse_layout_v01.py",
        "render_synapse_v01.py",
    ):
        ast.parse((ROOT / name).read_text(encoding="utf-8"))


def test_render_contract_is_png_sequence_and_blend_source():
    source = (ROOT / "render_synapse_v01.py").read_text(encoding="utf-8")
    assert 'f"synapse_{frame:04d}.png"' in source
    assert "chemical_synapse_neurotransmitter_v01.blend" in source
    assert '"BLENDER_EEVEE_NEXT"' in source
    assert "apply_teaching_layout()" in source


def test_scene_contains_core_chemical_synapse_steps():
    source = (ROOT / "synapse_scene_v01.py").read_text(encoding="utf-8")
    for token in (
        "Action potential pulse",
        "Ca2+",
        "Active synaptic vesicle",
        "Released NT",
        "Ionotropic",
        "Metabotropic",
        "Second messenger",
        "Reuptake transporter",
    ):
        assert token in source


def test_teaching_layout_keeps_phase_cards_in_render_safe_area():
    source = (ROOT / "synapse_layout_v01.py").read_text(encoding="utf-8")
    assert "Phase title plate" in source
    assert "Phase caption plate" in source
    assert "Source note" in source
