from __future__ import annotations

"""Blender 5.2 compatibility runner for heart_starling_anrep_v01.

Blender 5.x can store animation curves in layered Actions.  The v01 teaching
scene intentionally reuses a few helpers written against legacy Action.fcurves.
This runner patches only those traversal points so the authored physiology and
scene code remain unchanged.
"""

import bpy

import heart_starling_anrep_v01 as app


def iter_action_fcurves(action):
    """Yield FCurves from both legacy and layered Blender Actions."""
    seen: set[int] = set()

    legacy = getattr(action, "fcurves", None)
    if legacy is not None:
        for fcurve in legacy:
            pointer = int(fcurve.as_pointer())
            if pointer not in seen:
                seen.add(pointer)
                yield fcurve

    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for channelbag in getattr(strip, "channelbags", ()):
                for fcurve in getattr(channelbag, "fcurves", ()):
                    pointer = int(fcurve.as_pointer())
                    if pointer not in seen:
                        seen.add(pointer)
                        yield fcurve


def repeat_base_cycle_52() -> None:
    """Repeat the approved 15 s mechanics across the 105 s teaching timeline."""
    for action in bpy.data.actions:
        for fcurve in iter_action_fcurves(action):
            if not fcurve.keyframe_points:
                continue
            xs = [float(point.co.x) for point in fcurve.keyframe_points]
            if min(xs) >= 1.0 and max(xs) <= app.SOURCE_FRAMES + 0.5:
                if not any(mod.type == "CYCLES" for mod in fcurve.modifiers):
                    modifier = fcurve.modifiers.new(type="CYCLES")
                    modifier.mode_before = "REPEAT"
                    modifier.mode_after = "REPEAT"

    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = app.TOTAL_FRAMES
    scene.render.fps = app.FPS


def smooth_scale_52(obj: bpy.types.Object) -> None:
    animation = obj.animation_data
    if animation is None or animation.action is None:
        return
    for curve in iter_action_fcurves(animation.action):
        if curve.data_path != "scale":
            continue
        for point in curve.keyframe_points:
            point.interpolation = "BEZIER"
            point.easing = "AUTO"


def set_constant_visibility_52(objects) -> None:
    for obj in objects:
        animation = obj.animation_data
        if animation is None or animation.action is None:
            continue
        for curve in iter_action_fcurves(animation.action):
            if "hide_" not in curve.data_path:
                continue
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"


# Patch the three legacy traversal points before the scene is built.
app.repeat_base_cycle = repeat_base_cycle_52
app.smooth_scale = smooth_scale_52
app.minute._set_constant_visibility = set_constant_visibility_52


if __name__ == "__main__":
    raise SystemExit(app.main())
