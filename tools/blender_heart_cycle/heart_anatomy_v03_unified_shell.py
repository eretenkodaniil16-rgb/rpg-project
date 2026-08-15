from __future__ import annotations

"""Unified visible heart shell for the Starling/Anrep teaching film.

The old procedural heart was architected as independently displayed chamber
shells.  This pass keeps those objects only as hidden animation/control donors
and builds one visible myocardial cutaway around compact LV/RV cavities.
"""

import math
import bpy
from mathutils import Vector

import heart_cycle_model as model
import heart_anatomy_v02 as anatomy_v02

REVISION = "heart_anatomy_v03_unified_shell"


def _world(offset: bpy.types.Object | None, local_xyz: tuple[float, float, float]) -> tuple[float, float, float]:
    p = Vector(local_xyz)
    if offset is not None:
        p = offset.matrix_world @ p
    return tuple(p)


def _parent_keep_world(obj: bpy.types.Object, parent: bpy.types.Object | None) -> None:
    if parent is None:
        return
    matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = matrix


def _hide_split_display() -> None:
    exact = {
        "LeftVentricle_Wall", "RightVentricle_Wall",
        "LeftVentricle_Cavity", "RightVentricle_Cavity",
        "Interventricular_Septum",
        "LeftAtrium_Wall", "RightAtrium_Wall",
        "LeftAtrium_Cavity", "RightAtrium_Cavity",
    }
    prefixes = (
        "Mitral_", "Tricuspid_", "Aortic_", "Pulmonary_",
        "Papillary_", "RightPapillary_", "LeftAuricle_", "RightAuricle_",
    )
    for obj in bpy.data.objects:
        if obj.name in exact or obj.name.startswith(prefixes) or "Chord" in obj.name:
            obj.hide_viewport = True
            obj.hide_render = True


def _endocardium_material(build: model.HeartBuild, key: str, color) -> bpy.types.Material:
    material = model._material(key, color, roughness=0.27, subsurface=0.055)
    bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
    if bsdf is not None:
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.12
        if "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.24
    return material


def _make_unified_ventricular_shell(build: model.HeartBuild) -> bpy.types.Object:
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    chambers = build.collections["chambers"]
    cutters = build.collections["cutters"]
    myocardium = build.materials["myocardium"]
    cut = build.materials["myocardium_cut"]

    shell = model._make_cutaway_shell(
        "V03_UnifiedVentricularMyocardium",
        _world(offset, (-0.02, 0.18, 2.93)),
        (1.55, 0.96, 2.35),
        (1.10, 0.66, 1.82),
        myocardium,
        cut,
        chambers,
        cutters,
    )
    anatomy_v02._taper_mesh(shell, bottom_scale=0.33, mid_bulge=0.11, x_shift_bottom=0.08, flatten_y=0.92)
    shell.rotation_euler[1] = math.radians(-7.0)

    tex = bpy.data.textures.new("V03_MyocardiumNoise", type="CLOUDS")
    tex.noise_scale = 0.48
    tex.noise_depth = 1
    disp = shell.modifiers.new("V03_MyocardialMicrorelief", "DISPLACE")
    disp.texture = tex
    disp.strength = 0.024
    disp.mid_level = 0.51

    # LV control is the dominant contractile driver in this film.  The internal
    # RV cavity still follows the independent RV control below.
    _parent_keep_world(shell, build.controls.get("left_ventricle"))
    return shell


def _make_cavities(build: model.HeartBuild) -> list[bpy.types.Object]:
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    chambers = build.collections["chambers"]
    left_mat = _endocardium_material(build, "M_V03_LV_Endocardium", (0.46, 0.075, 0.078, 1.0))
    right_mat = _endocardium_material(build, "M_V03_RV_Endocardium", (0.095, 0.135, 0.31, 1.0))
    cut = build.materials["myocardium_cut"]

    lv = model._uv_sphere(
        "V03_LV_Cavity",
        _world(offset, (0.34, 0.31, 3.02)),
        (0.57, 0.105, 1.46),
        left_mat,
        chambers,
        segments=56,
        rings=28,
    )
    anatomy_v02._taper_mesh(lv, bottom_scale=0.38, mid_bulge=0.05, x_shift_bottom=0.02, flatten_y=0.95)
    lv.rotation_euler[1] = math.radians(-7.0)
    _parent_keep_world(lv, build.controls.get("left_ventricle"))

    rv = model._uv_sphere(
        "V03_RV_Cavity",
        _world(offset, (-0.47, 0.24, 3.22)),
        (0.50, 0.085, 1.18),
        right_mat,
        chambers,
        segments=52,
        rings=26,
    )
    anatomy_v02._taper_mesh(rv, bottom_scale=0.58, mid_bulge=0.04, x_shift_bottom=0.05, flatten_y=0.66)
    rv.rotation_euler[1] = math.radians(12.0)
    _parent_keep_world(rv, build.controls.get("right_ventricle"))

    septum = model._uv_sphere(
        "V03_InterventricularSeptum",
        _world(offset, (-0.05, 0.18, 3.08)),
        (0.20, 0.15, 1.53),
        cut,
        chambers,
        segments=48,
        rings=24,
    )
    septum.rotation_euler[1] = math.radians(-7.0)
    _parent_keep_world(septum, build.controls.get("left_ventricle"))
    return [lv, rv, septum]


def _make_atria(build: model.HeartBuild) -> list[bpy.types.Object]:
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    chambers = build.collections["chambers"]
    cutters = build.collections["cutters"]
    myocardium = build.materials["myocardium"]
    cut = build.materials["myocardium_cut"]
    left_endo = bpy.data.materials.get("M_V03_LV_Endocardium") or build.materials["left_chamber"]
    right_endo = bpy.data.materials.get("M_V03_RV_Endocardium") or build.materials["right_chamber"]

    made = []
    for side, center, outer, inner, material, control_key, rot in (
        ("LA", (0.47, 0.22, 4.65), (0.69, 0.59, 0.66), (0.51, 0.40, 0.47), left_endo, "left_atrium", 8.0),
        ("RA", (-0.50, 0.21, 4.62), (0.76, 0.61, 0.72), (0.57, 0.42, 0.53), right_endo, "right_atrium", -8.0),
    ):
        wall = model._make_cutaway_shell(
            f"V03_{side}_Wall", _world(offset, center), outer, inner,
            myocardium, cut, chambers, cutters,
        )
        wall.rotation_euler[2] = math.radians(rot)
        _parent_keep_world(wall, build.controls.get(control_key))
        made.append(wall)

        cavity = model._uv_sphere(
            f"V03_{side}_Cavity", _world(offset, (center[0], 0.34, center[2])),
            (inner[0] * 0.93, 0.080, inner[2] * 0.93), material, chambers,
            segments=40, rings=20,
        )
        _parent_keep_world(cavity, build.controls.get(control_key))
        made.append(cavity)

    # Small muscular auricles integrated into the atrial silhouette.
    for name, loc, scale, control in (
        ("V03_LeftAuricle", (0.94, 0.14, 4.76), (0.34, 0.28, 0.28), build.controls.get("left_atrium")),
        ("V03_RightAuricle", (-1.02, 0.13, 4.73), (0.39, 0.30, 0.31), build.controls.get("right_atrium")),
    ):
        aur = model._uv_sphere(name, _world(offset, loc), scale, myocardium, chambers, segments=36, rings=18)
        _parent_keep_world(aur, control)
        made.append(aur)
    return made


def _make_valve_landmarks(build: model.HeartBuild) -> list[bpy.types.Object]:
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    valves = build.collections["valves"]
    valve_mat = build.materials["valve"]
    made = []

    # Compact leaflet landmarks: enough to locate AV valves without white ring clutter.
    specs = (
        ("V03_Mitral_A", (0.30, -0.03, 4.00), (0.22, 0.035, 0.27), math.radians(16), build.controls.get("left_ventricle")),
        ("V03_Mitral_P", (0.58, -0.03, 3.94), (0.20, 0.035, 0.24), math.radians(-14), build.controls.get("left_ventricle")),
        ("V03_Tricuspid_A", (-0.31, -0.03, 3.98), (0.19, 0.032, 0.23), math.radians(14), build.controls.get("right_ventricle")),
        ("V03_Tricuspid_P", (-0.52, -0.03, 3.92), (0.18, 0.032, 0.21), math.radians(-10), build.controls.get("right_ventricle")),
        ("V03_Tricuspid_S", (-0.13, -0.03, 3.90), (0.16, 0.030, 0.20), math.radians(4), build.controls.get("right_ventricle")),
    )
    for name, loc, scale, rot, parent in specs:
        leaflet = model._uv_sphere(name, _world(offset, loc), scale, valve_mat, valves, segments=28, rings=14)
        leaflet.rotation_euler[0] = rot
        _parent_keep_world(leaflet, parent)
        made.append(leaflet)
    return made


def apply(build: model.HeartBuild) -> model.HeartBuild:
    _hide_split_display()
    _make_unified_ventricular_shell(build)
    _make_cavities(build)
    _make_atria(build)
    _make_valve_landmarks(build)

    scene = bpy.context.scene
    scene["visible_anatomy_revision"] = REVISION
    scene["visible_anatomy_architecture"] = (
        "one tapered ventricular myocardial cutaway with embedded LV/RV cavities and septum; "
        "compact atria; split-shell proxy hidden"
    )
    return build
