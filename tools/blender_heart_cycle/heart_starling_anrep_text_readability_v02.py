from __future__ import annotations

"""Readability pass for the Frank-Starling / Anrep teaching layout.

The first HRA review proved that the anatomy reads well at 720p, but the text
cards were undersized on phone screens. This pass enlarges the existing camera-
space typography without changing physiology, timing, or the HRA heart rig.
"""

import bpy

REVISION = "heart_starling_anrep_text_readability_v02"


def _scale_text(name: str, factor: float, *, dy: float = 0.0) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "FONT":
        return
    obj.data.size *= factor
    if dy:
        obj.location.y += dy


def _scale_panel(name: str, sx: float, sy: float) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.scale.x *= sx
    obj.scale.y *= sy


def apply() -> None:
    # Main teaching cards: titles +32%, body copy +45%.
    for prefix in (
        "Law_Intro_v01",
        "Law_Baseline_v01",
        "Law_FS1_v01",
        "Law_FS2_v01",
        "Law_Transition_v01",
        "Law_Anrep1_v01",
        "Law_Anrep2_v01",
    ):
        _scale_text(prefix + "_Title", 1.32)
        _scale_text(prefix + "_Body", 1.45, dy=-0.006)
        _scale_panel(prefix + "_Panel", 1.035, 1.14)

    # Comparison panel is denser, so use a slightly more conservative increase.
    _scale_text("Law_CompareTitle_v01", 1.28)
    _scale_text("Law_CompareLeft_v01", 1.27, dy=-0.004)
    _scale_text("Law_CompareRight_v01", 1.27, dy=-0.004)
    _scale_panel("Law_ComparePanel_v01", 1.04, 1.10)

    # Outro remains large and concise.
    _scale_text("Law_OutroTitle_v01", 1.28)
    _scale_text("Law_OutroBody_v01", 1.30, dy=-0.004)
    _scale_panel("Law_OutroPanel_v01", 1.04, 1.08)

    # Frank-Starling graph labels were the smallest elements in the first review.
    _scale_text("FS_XLabel_v01", 1.48)
    _scale_text("FS_YLabel_v01", 1.48)
    _scale_panel("FS_GraphPanel_v01", 1.035, 1.06)

    scene = bpy.context.scene
    scene["text_readability_revision"] = REVISION
    scene["text_readability_note"] = (
        "main card titles +32%; body copy +45%; comparison +27%; "
        "graph labels +48%; panels expanded to preserve spacing"
    )
