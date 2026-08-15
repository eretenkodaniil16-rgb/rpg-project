from __future__ import annotations

"""Blender 5.2 runner for the anatomical v02 Frank-Starling/Anrep scene."""

import sys
from pathlib import Path

import bpy

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import heart_starling_anrep_v01 as app
import heart_anatomy_v02 as anatomy_v02

# Delivery identity is v02 even though the stable teaching/timeline authoring is
# inherited from v01.
app.REVISION = "heart_starling_anrep_v02"
app.MODEL_REVISION = "heart_cutaway_v02_starling_anrep"
app.BLEND_NAME = "heart_cutaway_v02_starling_anrep.blend"
app.VIDEO_NAME = "heart_starling_anrep_v02_720p15_review.mp4"
app.FRAME_DIR = "starling_anrep_v02_frames"
app.FRAME_PREFIX = "starling_anrep_v02_"


def iter_action_fcurves(action):
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
    for obj in bpy.data.objects:
        if obj.name.startswith(("Info_", "ECG_", "Minute_", "Infographic_", "Presentation_")):
            obj.animation_data_clear()
            obj.hide_viewport = True
            obj.hide_render = True


def intro_torso_v02(build: app.model.HeartBuild) -> tuple[bpy.types.Object, ...]:
    """A cleaner medical torso shell; the heart remains the focal object."""
    shell = app.model._material(
        "M_UserTorsoShell_v02", (0.055, 0.12, 0.18, 1.0), roughness=0.46,
        emission=(0.018, 0.075, 0.12, 1.0),
    )
    rib = app.model._material(
        "M_RibHint_v02", (0.33, 0.48, 0.56, 1.0), roughness=0.48,
        emission=(0.06, 0.13, 0.17, 1.0),
    )
    parts: list[bpy.types.Object] = []

    # Shoulder/upper-torso mass is deliberately asymmetric and tapered rather
    # than a single sphere. It is only used for the opening 8 seconds.
    for name, loc, scale, rot in (
        ("UserTorso_Thorax_v02", (0.0, 0.93, 4.20), (2.55, 0.94, 2.95), (0.0, 0.0, 0.0)),
        ("UserTorso_Abdomen_v02", (0.0, 0.98, 1.95), (1.82, 0.78, 1.90), (0.0, 0.0, 0.0)),
        ("UserTorso_LeftShoulder_v02", (2.25, 0.91, 5.48), (1.15, 0.76, 0.72), (0.0, 0.0, 0.12)),
        ("UserTorso_RightShoulder_v02", (-2.25, 0.91, 5.48), (1.15, 0.76, 0.72), (0.0, 0.0, -0.12)),
        ("UserTorso_Head_v02", (0.0, 0.78, 8.02), (0.92, 0.78, 1.12), (0.0, 0.0, 0.0)),
    ):
        obj = app.model._uv_sphere(name, loc, scale, shell, build.collections["anatomy"], segments=40, rings=20)
        obj.rotation_euler = rot
        wire = obj.modifiers.new(name="MedicalShellWire", type="WIREFRAME")
        wire.thickness = 0.012
        wire.use_replace = True
        parts.append(obj)

    # Rib-cage hints establish heart position without trying to be a full body model.
    for i, z in enumerate((5.55, 5.15, 4.75, 4.35, 3.95), start=1):
        for side in (-1.0, 1.0):
            x = 0.06 * side
            points = (
                (x, 0.42, z),
                (1.05 * side, 0.18, z - 0.05),
                (1.82 * side, 0.40, z - 0.18),
            )
            curve = app.model._curve_tube(f"UserTorso_Rib_{i}_{'L' if side > 0 else 'R'}", points, 0.022, rib, build.collections["anatomy"])
            parts.append(curve)

    app.set_visibility(parts, *app.span(0, 8))
    set_constant_visibility_52(parts)
    return tuple(parts)


# Anatomy patch must happen inside the stable base builder, before app.build_model
# wraps the ventricular controls for the two autoregulation mechanisms.
_original_base_builder = app.export_v07.build_model


def upgraded_base_builder(resolution: int):
    build = _original_base_builder(resolution)
    anatomy_v02.upgrade(build)
    return build


app.export_v07.build_model = upgraded_base_builder
app.repeat_base_cycle = repeat_base_cycle_52
app.smooth_scale = smooth_scale_52
app.minute._set_constant_visibility = set_constant_visibility_52
app.hide_legacy_ui = hide_legacy_ui_52
app.reference_torso = intro_torso_v02


if __name__ == "__main__":
    raise SystemExit(app.main())
