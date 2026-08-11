"""Screen-space-like teaching layout adjustments for the synapse scene.

The procedural geometry lives in world space. This pass moves the explanatory
text toward the teaching camera and keeps it inside the 16:9 safe area without
changing the underlying physiology animation.
"""

from __future__ import annotations

import bpy

from blender_helpers import cube


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


def apply_teaching_layout() -> None:
    # Anatomical labels: keep them inside the left/right safe margins.
    _move("Label pre", (-6.15, -5.35, 3.25), 0.25)
    _move("Label cleft", (-6.15, -5.35, 0.05), 0.24)
    _move("Label post", (-6.15, -5.35, -2.65), 0.25)
    _move("Ionotropic label", (-2.00, -5.35, -2.35), 0.22)
    _move("Metabotropic label", (3.25, -5.35, -2.35), 0.22)
    _move("Reuptake label", (5.15, -5.35, 1.70), 0.20)

    # Phase title/caption overlays. Objects retain their visibility keyframes.
    for index in range(1, 10):
        title = bpy.data.objects.get(f"Phase title {index}")
        if title is not None:
            title.location = (-5.95, -6.00, 5.35)
            title.data.align_x = "LEFT"
            title.data.size = 0.34
        caption = bpy.data.objects.get(f"Phase caption {index}")
        if caption is not None:
            caption.location = (0.0, -6.00, -3.65)
            caption.data.align_x = "CENTER"
            caption.data.size = 0.20
            caption.data.space_line = 1.15

    # Opaque dark plates deliberately sit between text and anatomy. This is more
    # legible in compressed 1080p video than relying on outline/shadow alone.
    dark = bpy.data.materials.get("Dark panel")
    if dark is not None:
        cube("Phase title plate", (-2.75, -5.72, 5.35), (3.55, 0.035, 0.43), dark, bevel=0.09)
        cube("Phase caption plate", (0.0, -5.72, -3.65), (6.20, 0.035, 0.62), dark, bevel=0.09)

    # The compact phase cards replace the old always-on source note/timeline.
    # Source attribution remains in the manifest and will be placed on a final
    # end card once the exact Pokrovsky/Guyton pages are supplied.
    _hide("Source note")
    _hide("Timeline")
    _hide("Timeline playhead")

    # Bring the potential-action inset into frame and keep it away from the
    # phase title. The graph curve stores absolute point coordinates, so its
    # object transform carries the whole inset as one unit.
    panel = bpy.data.objects.get("AP graph panel")
    if panel is not None:
        panel.location.x += 8.65
        panel.location.z -= 4.60
    graph = bpy.data.objects.get("Action potential graph")
    if graph is not None:
        graph.location.x += 8.65
        graph.location.z -= 4.60
    label = bpy.data.objects.get("AP label")
    if label is not None:
        label.location.x += 8.65
        label.location.z -= 4.60
        label.data.size = 0.20
    marker = bpy.data.objects.get("AP graph marker")
    if marker is not None:
        # Marker location is keyframed; parent it to an empty to apply a stable
        # offset without rewriting Blender 5.x layered action data.
        empty = bpy.data.objects.new("AP inset offset", None)
        bpy.context.collection.objects.link(empty)
        empty.location = (8.65, 0.0, -4.60)
        marker.parent = empty
