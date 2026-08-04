from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Iterator

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy
from mathutils import Vector

import heart_cycle_build as anatomy_v02
import heart_cycle_model as model
import heart_cycle_phase_rig_v03 as rig


LAYOUT_REVISION = "heart_cycle_layout_fix_v05"
MODEL_REVISION = "heart_cutaway_reference_layout_v05_phase_rig_v03_infographic_v04"
DEFAULT_BLEND_NAME = f"{MODEL_REVISION}.blend"


REFERENCE_WORLD_LOCATIONS: dict[str, tuple[float, float, float]] = {
    "LeftVentricle_Wall": (0.78, 0.18, 2.55),
    "LeftVentricle_Cavity": (0.78, 0.40, 2.64),
    "RightVentricle_Wall": (-0.78, 0.23, 2.65),
    "RightVentricle_Cavity": (-0.78, 0.40, 2.72),
    "Interventricular_Septum": (0.00, 0.28, 2.62),
    "LeftAtrium_Wall": (0.97, 0.20, 4.58),
    "LeftAtrium_Cavity": (0.97, 0.40, 4.58),
    "RightAtrium_Wall": (-0.97, 0.20, 4.58),
    "RightAtrium_Cavity": (-0.97, 0.40, 4.58),
}

REFERENCE_SCALE_FACTORS: dict[str, tuple[float, float, float]] = {
    "LeftVentricle_Wall": (0.97, 1.00, 1.08),
    "LeftVentricle_Cavity": (0.94, 1.00, 1.08),
    "RightVentricle_Wall": (1.08, 0.98, 0.92),
    "RightVentricle_Cavity": (1.10, 0.98, 0.90),
    "LeftAtrium_Wall": (0.92, 1.00, 0.90),
    "LeftAtrium_Cavity": (0.90, 1.00, 0.90),
    "RightAtrium_Wall": (1.03, 1.00, 0.96),
    "RightAtrium_Cavity": (1.02, 1.00, 0.95),
}

_LAST_LAYOUT_METRICS: dict[str, float | str] = {}


def _require_object(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required heart object is missing: {name}")
    return obj


def _set_world_location(name: str, location: tuple[float, float, float]) -> None:
    obj = _require_object(name)
    matrix = obj.matrix_world.copy()
    matrix.translation = Vector(location)
    obj.matrix_world = matrix


def _restore_reference_chamber_layout(_build: model.HeartBuild) -> None:
    """Restore the gross chamber layout from the approved first preview.

    The previous v02 pass read matrix_world before Blender had evaluated newly
    assigned parent inverses. Writing that stale matrix back moved both
    ventricular shells to the atrial level. This pass updates the dependency
    graph first, assigns the known-good world locations explicitly, and applies
    only the moderate scale factors used by the approved v01 preview.
    """

    bpy.context.view_layer.update()
    for name, location in REFERENCE_WORLD_LOCATIONS.items():
        _set_world_location(name, location)
    bpy.context.view_layer.update()

    for name, factors in REFERENCE_SCALE_FACTORS.items():
        obj = _require_object(name)
        obj.scale = factors

    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene["layout_revision"] = LAYOUT_REVISION
    scene["layout_reference"] = "approved heart_cutaway_v01 preview"
    scene["layout_rule"] = "ventricular centers below atrial centers; LV forms apex"


def _iter_action_fcurves(action: bpy.types.Action) -> Iterator[bpy.types.FCurve]:
    """Yield F-curves from legacy and Blender 5.2 layered Actions."""

    legacy_fcurves = getattr(action, "fcurves", None)
    if legacy_fcurves is not None:
        yield from legacy_fcurves
        return

    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for channelbag in getattr(strip, "channelbags", ()):
                yield from channelbag.fcurves


def _set_interpolation_blender_52() -> None:
    for action in bpy.data.actions:
        for fcurve in _iter_action_fcurves(action):
            for keyframe in fcurve.keyframe_points:
                if "hide_" in fcurve.data_path or "phase_index" in fcurve.data_path:
                    keyframe.interpolation = "CONSTANT"
                else:
                    keyframe.interpolation = "BEZIER"
                    keyframe.easing = "AUTO"


def _set_constant_visibility_interpolation_blender_52(
    objects: Iterable[bpy.types.Object],
) -> None:
    for obj in objects:
        animation = obj.animation_data
        if animation is None or animation.action is None:
            continue
        for fcurve in _iter_action_fcurves(animation.action):
            if "hide_" not in fcurve.data_path:
                continue
            for point in fcurve.keyframe_points:
                point.interpolation = "CONSTANT"


def _world_bounds_z(name: str) -> tuple[float, float, float]:
    obj = _require_object(name)
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = min(point.z for point in points)
    maximum = max(point.z for point in points)
    return minimum, maximum, (minimum + maximum) * 0.5


def _validate_layout() -> dict[str, float | str]:
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

    lv_min, lv_max, lv_center = _world_bounds_z("LeftVentricle_Wall")
    rv_min, rv_max, rv_center = _world_bounds_z("RightVentricle_Wall")
    _la_min, _la_max, la_center = _world_bounds_z("LeftAtrium_Wall")
    _ra_min, _ra_max, ra_center = _world_bounds_z("RightAtrium_Wall")

    if not lv_center < la_center - 0.80:
        raise RuntimeError(
            "Invalid heart layout: left ventricular center is not sufficiently below left atrium"
        )
    if not rv_center < ra_center - 0.75:
        raise RuntimeError(
            "Invalid heart layout: right ventricular center is not sufficiently below right atrium"
        )
    if not lv_min < rv_min - 0.12:
        raise RuntimeError(
            "Invalid heart layout: left ventricle does not form the inferior apex"
        )
    if lv_max <= lv_center or rv_max <= rv_center:
        raise RuntimeError("Invalid ventricular bounds")

    return {
        "status": "passed",
        "left_ventricle_center_z": round(lv_center, 4),
        "right_ventricle_center_z": round(rv_center, 4),
        "left_atrium_center_z": round(la_center, 4),
        "right_atrium_center_z": round(ra_center, 4),
        "left_ventricle_apex_z": round(lv_min, 4),
        "right_ventricle_apex_z": round(rv_min, 4),
    }


# Patch the two problematic layers before importing the final compositor.
anatomy_v02._refine_chamber_silhouette = _restore_reference_chamber_layout
rig._set_interpolation = _set_interpolation_blender_52

import heart_cycle_infographic_v04 as infographic  # noqa: E402

infographic._set_constant_visibility_interpolation = (
    _set_constant_visibility_interpolation_blender_52
)
infographic.MODEL_REVISION = MODEL_REVISION
infographic.DEFAULT_BLEND_NAME = DEFAULT_BLEND_NAME
model.MODEL_REVISION = MODEL_REVISION

_BASE_BUILD_MODEL = infographic.build_model
_BASE_AUGMENT_MANIFEST = infographic._augment_manifest


def build_model(resolution: int) -> model.HeartBuild:
    global _LAST_LAYOUT_METRICS

    build = _BASE_BUILD_MODEL(resolution)
    _LAST_LAYOUT_METRICS = _validate_layout()
    scene = bpy.context.scene
    scene["model_revision"] = MODEL_REVISION
    scene["layout_revision"] = LAYOUT_REVISION
    scene["layout_validation"] = "passed"
    for key, value in _LAST_LAYOUT_METRICS.items():
        scene[f"layout_{key}"] = value
    return build


def _augment_manifest(path: Path) -> Path:
    path = _BASE_AUGMENT_MANIFEST(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["model_revision"] = MODEL_REVISION
    payload["layout_revision"] = LAYOUT_REVISION
    payload["layout_reference"] = "approved heart_cutaway_v01 preview"
    payload["layout_validation"] = dict(_LAST_LAYOUT_METRICS)
    payload["layout_correction"] = {
        "ventricular_world_positions": "restored from v01",
        "unsafe_stale_matrix_world_translation": "removed",
        "left_ventricle_forms_apex": True,
        "ventricular_centers_below_atria": True,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


infographic.build_model = build_model
infographic._augment_manifest = _augment_manifest
model.build_model = build_model


if __name__ == "__main__":
    raise SystemExit(infographic.main())
