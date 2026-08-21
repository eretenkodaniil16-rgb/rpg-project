from __future__ import annotations

"""Large-type readability pass for the Frank-Starling / Anrep layout.

The video is frequently reviewed on a phone, so this pass deliberately uses
larger-than-desktop teaching typography. Panels expand with the text to avoid
collisions. Mechanism inset typography is authored separately at comparable
visual sizes.
"""

import bpy

REVISION = "heart_starling_anrep_text_readability_v03"


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
    # Main teaching cards: noticeably larger than the already-enlarged v02 pass.
    for prefix in (
        "Law_Intro_v01",
        "Law_Baseline_v01",
        "Law_FS1_v01",
        "Law_FS2_v01",
        "Law_Transition_v01",
        "Law_Anrep1_v01",
        "Law_Anrep2_v01",
    ):
        _scale_text(prefix + "_Title", 1.45)
        _scale_text(prefix + "_Body", 1.60, dy=-0.008)
        _scale_panel(prefix + "_Panel", 1.075, 1.19)

    # Comparison is text-dense, but still enlarged substantially for a phone.
    _scale_text("Law_CompareTitle_v01", 1.40)
    _scale_text("Law_CompareLeft_v01", 1.39, dy=-0.006)
    _scale_text("Law_CompareRight_v01", 1.39, dy=-0.006)
    _scale_panel("Law_ComparePanel_v01", 1.075, 1.15)

    _scale_text("Law_OutroTitle_v01", 1.40)
    _scale_text("Law_OutroBody_v01", 1.43, dy=-0.006)
    _scale_panel("Law_OutroPanel_v01", 1.07, 1.12)

    # Frank-Starling graph labels remain readable next to the larger cards.
    _scale_text("FS_XLabel_v01", 1.65)
    _scale_text("FS_YLabel_v01", 1.65)
    _scale_panel("FS_GraphPanel_v01", 1.06, 1.09)

    scene = bpy.context.scene
    scene["text_readability_revision"] = REVISION
    scene["text_readability_note"] = (
        "main card titles +45%; body copy +60%; comparison +39%; "
        "graph labels +65%; panels expanded for phone-first readability"
    )
