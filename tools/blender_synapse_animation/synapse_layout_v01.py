"""Camera-safe teaching layout adjustments for the synapse scene."""

from __future__ import annotations

import bpy

from blender_helpers import cube, visibility_window
from synapse_data import TOTAL_FRAMES, sec_to_frame


def _move(name: str, location, size: float | None = None) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.location = location
    if size is not None and getattr(obj, "data", None) is not None and hasattr(obj.data, "size"):
        obj.data.size = size


def _hide(name: str) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.hide_render = True
    obj.hide_viewport = True


def _ap_visibility(obj) -> None:
    if obj is not None:
        visibility_window(obj, sec_to_frame(3.7), sec_to_frame(8.5), TOTAL_FRAMES)


def apply_teaching_layout() -> None:
    # Anatomy labels live within the empirically verified 16:9 safe area of the
    # animated teaching camera. Keep them secondary to the phase narration.
    _move("Label pre", (-6.15, -5.35, 2.35), 0.22)
    _move("Label cleft", (-6.15, -5.35, 0.05), 0.22)
    _move("Label post", (-6.15, -5.35, -1.85), 0.22)
    _move("Ionotropic label", (-2.05, -5.35, -1.78), 0.19)
    _move("Metabotropic label", (3.25, -5.35, -1.78), 0.19)
    _move("Reuptake label", (5.15, -5.35, 1.55), 0.18)

    # Phase narration. Title uses the upper-left safe area; the two-line caption
    # occupies a lower strip while remaining visible during camera push-ins.
    for index in range(1, 10):
        title = bpy.data.objects.get(f"Phase title {index}")
        if title is not None:
            title.location = (-6.00, -6.05, 3.45)
            title.data.align_x = "LEFT"
            title.data.size = 0.30
        caption = bpy.data.objects.get(f"Phase caption {index}")
        if caption is not None:
            caption.location = (0.0, -6.05, -2.52)
            caption.data.align_x = "CENTER"
            caption.data.size = 0.175
            caption.data.space_line = 1.10

    dark = bpy.data.materials.get("Dark panel")
    if dark is not None:
        cube("Phase title plate", (-2.70, -5.75, 3.45), (3.65, 0.035, 0.36), dark, bevel=0.08)
        cube("Phase caption plate", (0.0, -5.75, -2.52), (6.15, 0.035, 0.46), dark, bevel=0.08)

    # The permanent source/timeline strip was outside the camera-safe area and
    # also competed with phase captions. Source attribution remains in manifest
    # until exact Pokrovsky/Guyton pages are supplied for the final end card.
    _hide("Source note")
    _hide("Timeline")
    _hide("Timeline playhead")

    # Potential-action inset: visible only during the AP phase, rather than
    # obscuring later exocytosis/receptor phases.
    panel = bpy.data.objects.get("AP graph panel")
    if panel is not None:
        panel.location.x += 8.65
        panel.location.z -= 6.15
        panel.scale.x *= 0.86
        panel.scale.z *= 0.78
        _ap_visibility(panel)

    graph = bpy.data.objects.get("Action potential graph")
    if graph is not None:
        graph.location.x += 8.65
        graph.location.z -= 6.15
        _ap_visibility(graph)

    label = bpy.data.objects.get("AP label")
    if label is not None:
        label.location.x += 8.65
        label.location.z -= 6.15
        label.data.size = 0.18
        _ap_visibility(label)

    marker = bpy.data.objects.get("AP graph marker")
    if marker is not None:
        # Marker location is keyframed; parent it to an empty to apply a stable
        # offset without rewriting Blender 5.x layered action data.
        empty = bpy.data.objects.new("AP inset offset", None)
        bpy.context.collection.objects.link(empty)
        empty.location = (8.65, 0.0, -6.15)
        marker.parent = empty
