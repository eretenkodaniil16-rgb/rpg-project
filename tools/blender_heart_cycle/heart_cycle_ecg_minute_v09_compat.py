from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_ecg_minute_v09 as v09
import heart_cycle_layout_fix_v05 as layout_v05


_BASE_BUILD_ECG_OVERLAY = v09._build_ecg_overlay


def _iter_action_fcurves(action: bpy.types.Action):
    yield from layout_v05._iter_action_fcurves(action)


def _retime_existing_animation_compat() -> None:
    for action in bpy.data.actions:
        for fcurve in _iter_action_fcurves(action):
            for point in fcurve.keyframe_points:
                original_x = float(point.co.x)
                if 1.0 <= original_x <= float(v09.SOURCE_TOTAL_FRAMES):
                    new_x = v09._map_source_frame(original_x)
                    delta = new_x - original_x
                    point.co.x = new_x
                    point.handle_left.x += delta
                    point.handle_right.x += delta
            fcurve.update()

    scene = bpy.context.scene
    for marker in scene.timeline_markers:
        if 1 <= marker.frame <= v09.SOURCE_TOTAL_FRAMES:
            marker.frame = int(round(v09._map_source_frame(marker.frame)))

    scene.frame_start = 1
    scene.frame_end = v09.TOTAL_FRAMES
    scene.render.fps = v09.FPS
    scene.render.fps_base = 1.0


def _set_constant_visibility_compat(objects: Iterable[bpy.types.Object]) -> None:
    for obj in objects:
        animation = obj.animation_data
        if animation is None or animation.action is None:
            continue
        for fcurve in _iter_action_fcurves(animation.action):
            if "hide_" not in fcurve.data_path:
                continue
            for key in fcurve.keyframe_points:
                key.interpolation = "CONSTANT"


def _finish_ecg_overlay_after_blender52_action_error(build) -> tuple[bpy.types.Object, ...]:
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None:
        raise RuntimeError("Heart scene has no active camera")
    collection = build.collections["render"]
    font = v09.infographic._load_cyrillic_font()
    text_mat = bpy.data.materials.get("M_ECGText_v09")
    if text_mat is None:
        text_mat = v09._make_material(
            "M_ECGText_v09", (0.94, 0.97, 1.00, 1.0), 1.30
        )

    cursor = bpy.data.objects.get("ECG_Cursor_v09")
    if cursor is None:
        raise RuntimeError("ECG cursor was not created before the Blender 5.2 Action compatibility error")
    if cursor.animation_data is not None and cursor.animation_data.action is not None:
        for fcurve in _iter_action_fcurves(cursor.animation_data.action):
            for key in fcurve.keyframe_points:
                key.interpolation = "CONSTANT" if "hide_" in fcurve.data_path else "LINEAR"

    phase_labels: list[bpy.types.Object] = []
    for phase, start, end in v09._mapped_phase_ranges():
        existing = bpy.data.objects.get(f"ECG_PhaseElectrical_{phase.index:02d}_v09")
        if existing is not None:
            label = existing
        else:
            label = v09.infographic._camera_text(
                f"ECG_PhaseElectrical_{phase.index:02d}_v09",
                v09.PHASE_ELECTRICAL_LABELS[phase.index],
                camera,
                collection,
                (-0.705, 0.120, -2.49),
                0.0165,
                text_mat,
                font,
            )
            v09._set_visibility_interval((label,), start, end)
        phase_labels.append(label)

    _set_constant_visibility_compat(phase_labels)
    return tuple(
        obj
        for obj in bpy.data.objects
        if obj.name.startswith("ECG_")
    )


def _build_ecg_overlay_compat(build) -> tuple[bpy.types.Object, ...]:
    try:
        return _BASE_BUILD_ECG_OVERLAY(build)
    except AttributeError as exc:
        if "Action" not in str(exc) or "fcurves" not in str(exc):
            raise
        return _finish_ecg_overlay_after_blender52_action_error(build)


v09._retime_existing_animation = _retime_existing_animation_compat
v09._set_constant_visibility = _set_constant_visibility_compat
v09._build_ecg_overlay = _build_ecg_overlay_compat


if __name__ == "__main__":
    raise SystemExit(v09.main())
