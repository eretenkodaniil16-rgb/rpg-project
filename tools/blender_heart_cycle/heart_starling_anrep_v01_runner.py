from __future__ import annotations

"""Blender 5.2 compatibility + review-quality runner for heart_starling_anrep_v01."""

import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

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
        if curve.data_path == "scale":
            for point in curve.keyframe_points:
                point.interpolation = "BEZIER"
                point.easing = "AUTO"


def set_constant_visibility_52(objects) -> None:
    for obj in objects:
        animation = obj.animation_data
        if animation is None or animation.action is None:
            continue
        for curve in iter_action_fcurves(animation.action):
            if "hide_" in curve.data_path:
                for key in curve.keyframe_points:
                    key.interpolation = "CONSTANT"


def hide_legacy_ui_52() -> None:
    """Remove all UI inherited from the earlier cardiac-cycle/ECG teaching scene."""
    legacy_prefixes = (
        "Info_",
        "ECG_",
        "Minute_",
        "Infographic_",
        "Presentation_",
    )
    for obj in bpy.data.objects:
        if not obj.name.startswith(legacy_prefixes):
            continue
        obj.animation_data_clear()
        obj.hide_viewport = True
        obj.hide_render = True


def wireframe_user_reference(build: app.model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    """Clean medical wireframe proxy based on the user's turntable proportions."""
    material = app.model._material(
        "M_UserReferenceWire_v02",
        (0.12, 0.30, 0.48, 1.0),
        roughness=0.42,
        emission=(0.08, 0.28, 0.50, 1.0),
    )
    parts: list[bpy.types.Object] = []

    for name, location, scale, segments, rings, thickness in (
        ("UserReference_TorsoWire_v02", (0.0, 0.78, 4.10), (3.0, 1.18, 3.55), 24, 12, 0.018),
        ("UserReference_HeadWire_v02", (0.0, 0.72, 8.05), (1.05, 0.84, 1.22), 24, 12, 0.014),
    ):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments,
            ring_count=rings,
            location=location,
        )
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        obj.data.materials.append(material)
        modifier = obj.modifiers.new(name="MedicalWireframe", type="WIREFRAME")
        modifier.thickness = thickness
        modifier.use_replace = True
        app.model._move_to_collection(obj, build.collections["anatomy"])
        parts.append(obj)

    bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=0.72, depth=1.0, location=(0.0, 0.74, 6.95))
    neck = bpy.context.object
    neck.name = "UserReference_NeckWire_v02"
    neck.data.materials.append(material)
    modifier = neck.modifiers.new(name="MedicalWireframe", type="WIREFRAME")
    modifier.thickness = 0.014
    modifier.use_replace = True
    app.model._move_to_collection(neck, build.collections["anatomy"])
    parts.append(neck)

    app.set_visibility(parts, *app.span(0, 8))
    set_constant_visibility_52(parts)
    return tuple(parts)


# Patch the compatibility and visual-cleanup points before the scene is built.
app.repeat_base_cycle = repeat_base_cycle_52
app.smooth_scale = smooth_scale_52
app.minute._set_constant_visibility = set_constant_visibility_52
app.hide_legacy_ui = hide_legacy_ui_52
app.reference_torso = wireframe_user_reference


if __name__ == "__main__":
    raise SystemExit(app.main())
