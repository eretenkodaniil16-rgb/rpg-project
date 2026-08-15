from __future__ import annotations

"""Unified anatomical v02 upgrade for the cardiac teaching scenes.

This pass reshapes the existing cutaway heart in-place. It does NOT create a
second ventricular/atrial shell, so valves, chordae and trabeculae remain
spatially coherent with the chamber walls and with the proven animation rig.
"""

import math
import bpy

import heart_cycle_model as model

REVISION = "heart_anatomy_v02_unified"


def _hide(name: str) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.animation_data_clear()
    obj.hide_viewport = True
    obj.hide_render = True


def _parent_keep_world(obj: bpy.types.Object, parent: bpy.types.Object | None) -> None:
    if parent is None:
        return
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def _set_material(material: bpy.types.Material, color, roughness: float, subsurface: float = 0.0) -> None:
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.08
    if "Coat Roughness" in bsdf.inputs:
        bsdf.inputs["Coat Roughness"].default_value = 0.30


def _new_material(name: str, color, roughness: float, subsurface: float = 0.0):
    return model._material(name, color, roughness=roughness, subsurface=subsurface)


def _refine_materials(build: model.HeartBuild) -> None:
    _set_material(build.materials["myocardium"], (0.285, 0.022, 0.020, 1.0), 0.38, 0.11)
    _set_material(build.materials["myocardium_cut"], (0.57, 0.105, 0.085, 1.0), 0.53, 0.14)
    _set_material(build.materials["left_chamber"], (0.39, 0.070, 0.073, 1.0), 0.25, 0.05)
    _set_material(build.materials["right_chamber"], (0.105, 0.130, 0.285, 1.0), 0.29, 0.04)
    _set_material(build.materials["valve"], (0.80, 0.71, 0.60, 1.0), 0.30, 0.08)
    _set_material(build.materials["chordae"], (0.89, 0.82, 0.70, 1.0), 0.38, 0.02)
    _set_material(build.materials["artery"], (0.49, 0.030, 0.025, 1.0), 0.32, 0.07)
    _set_material(build.materials["vein"], (0.060, 0.095, 0.255, 1.0), 0.36, 0.05)

    build.materials["coronary_v02"] = _new_material("M_Coronary_v02", (0.73, 0.026, 0.020, 1.0), 0.26, 0.03)
    build.materials["fat_v02"] = _new_material("M_EpicardialFat_v02", (0.58, 0.37, 0.11, 1.0), 0.52, 0.04)


def _organic_surface(obj: bpy.types.Object, key: str, strength: float, noise_scale: float) -> None:
    if obj.type != "MESH":
        return
    tex = bpy.data.textures.new(name=f"{key}_Noise", type="CLOUDS")
    tex.noise_scale = noise_scale
    tex.noise_depth = 1
    mod = obj.modifiers.new(name=f"{key}_Microrelief", type="DISPLACE")
    mod.texture = tex
    mod.strength = strength
    mod.mid_level = 0.51
    mod.texture_coords = "GLOBAL"


def _taper_mesh(obj: bpy.types.Object, *, bottom_scale: float, mid_bulge: float, x_shift_bottom: float = 0.0, flatten_y: float = 1.0) -> None:
    """Convert an ellipsoidal chamber into a more cardiac, tapered form."""
    if obj.type != "MESH" or not obj.data.vertices:
        return
    zs = [v.co.z for v in obj.data.vertices]
    zmin, zmax = min(zs), max(zs)
    span = max(zmax - zmin, 1e-6)
    for vert in obj.data.vertices:
        t = (vert.co.z - zmin) / span
        # Narrow inferior apex, restore full width basally, slight mid-ventricular bulge.
        taper = bottom_scale + (1.0 - bottom_scale) * min(1.0, t / 0.62)
        bulge = 1.0 + mid_bulge * math.sin(math.pi * t)
        factor = taper * bulge
        vert.co.x *= factor
        vert.co.y *= factor * flatten_y
        vert.co.x += x_shift_bottom * (1.0 - t) ** 2
    obj.data.update()


def _reshape_existing_chambers(build: model.HeartBuild) -> None:
    lv_wall = bpy.data.objects.get("LeftVentricle_Wall")
    rv_wall = bpy.data.objects.get("RightVentricle_Wall")
    lv_cavity = bpy.data.objects.get("LeftVentricle_Cavity")
    rv_cavity = bpy.data.objects.get("RightVentricle_Cavity")
    la_wall = bpy.data.objects.get("LeftAtrium_Wall")
    ra_wall = bpy.data.objects.get("RightAtrium_Wall")

    if lv_wall:
        _taper_mesh(lv_wall, bottom_scale=0.50, mid_bulge=0.10, x_shift_bottom=-0.10, flatten_y=0.94)
        lv_wall.rotation_euler[1] += math.radians(-5.0)
        _organic_surface(lv_wall, "LV", 0.028, 0.52)
    if lv_cavity:
        _taper_mesh(lv_cavity, bottom_scale=0.44, mid_bulge=0.06, x_shift_bottom=-0.07, flatten_y=0.96)
        lv_cavity.rotation_euler[1] += math.radians(-5.0)

    if rv_wall:
        _taper_mesh(rv_wall, bottom_scale=0.68, mid_bulge=0.08, x_shift_bottom=0.12, flatten_y=0.72)
        rv_wall.scale.x *= 1.08
        rv_wall.scale.z *= 0.94
        rv_wall.rotation_euler[1] += math.radians(10.0)
        _organic_surface(rv_wall, "RV", 0.022, 0.50)
    if rv_cavity:
        _taper_mesh(rv_cavity, bottom_scale=0.64, mid_bulge=0.05, x_shift_bottom=0.10, flatten_y=0.68)
        rv_cavity.scale.x *= 1.06
        rv_cavity.scale.z *= 0.93
        rv_cavity.rotation_euler[1] += math.radians(10.0)

    if la_wall:
        la_wall.scale *= 0.93
        la_wall.rotation_euler[2] += math.radians(7.0)
        _organic_surface(la_wall, "LA", 0.014, 0.36)
    if ra_wall:
        ra_wall.scale.x *= 1.02
        ra_wall.scale.z *= 0.96
        ra_wall.rotation_euler[2] += math.radians(-6.0)
        _organic_surface(ra_wall, "RA", 0.014, 0.36)


def _simplify_internal_clutter() -> None:
    """Keep anatomical landmarks but remove duplicate v02 ridges that read as floating sticks."""
    hide_prefixes = (
        "LV_Trabecula_", "RV_Trabecula_", "RightAtrium_Pectinate_", "LeftAuricle_Pectinate_",
        "LVOT_SeptalRidge", "RVOT_InfundibularRidge", "RV_ModeratorBand",
    )
    for obj in bpy.data.objects:
        if obj.name.startswith(hide_prefixes):
            obj.hide_viewport = True
            obj.hide_render = True

    # Thin the old chordae rather than removing them.
    for obj in bpy.data.objects:
        if "Chord" in obj.name and obj.type == "CURVE":
            obj.data.bevel_depth = min(obj.data.bevel_depth, 0.010)


def _hide_legacy_vessels() -> None:
    for name in (
        "Aorta", "PulmonaryTrunk", "SuperiorVenaCava", "InferiorVenaCava",
        "RightPulmonaryVein_1", "RightPulmonaryVein_2", "LeftPulmonaryVein_1", "LeftPulmonaryVein_2",
        "AorticBranch_1", "AorticBranch_2", "AorticBranch_3",
        "PulmonaryArtery_LeftBranch", "PulmonaryArtery_RightBranch",
    ):
        _hide(name)


def _build_great_vessels(build: model.HeartBuild) -> list[bpy.types.Object]:
    vessels = build.collections["vessels"]
    artery, vein = build.materials["artery"], build.materials["vein"]
    made = []
    made.append(model._curve_tube("V02_Aorta", ((0.40, 0.16, 5.02), (0.52, 0.22, 5.62), (0.52, 0.30, 6.28), (0.18, 0.48, 6.72), (-0.40, 0.57, 6.68), (-0.82, 0.56, 6.30)), 0.30, artery, vessels))
    made.append(model._curve_tube("V02_PulmonaryTrunk", ((-0.39, 0.11, 5.02), (-0.30, 0.17, 5.55), (-0.48, 0.26, 5.96), (-0.83, 0.31, 6.12)), 0.27, vein, vessels))
    made.append(model._curve_tube("V02_LeftPulmonaryArtery", ((-0.83, 0.31, 6.12), (-1.42, 0.35, 6.14), (-1.88, 0.29, 6.04)), 0.20, vein, vessels))
    made.append(model._curve_tube("V02_RightPulmonaryArtery", ((-0.70, 0.43, 6.10), (-0.12, 0.67, 6.14), (0.66, 0.76, 6.03)), 0.19, vein, vessels))
    made.append(model._curve_tube("V02_SVC", ((-1.20, 0.42, 6.18), (-1.13, 0.39, 5.60), (-1.04, 0.31, 5.05)), 0.27, vein, vessels))
    made.append(model._curve_tube("V02_IVC", ((-1.02, 0.31, 4.13), (-1.04, 0.35, 3.67), (-0.98, 0.36, 3.22)), 0.28, vein, vessels))

    for i, (x, z) in enumerate(((0.68, 4.83), (1.00, 4.80), (0.69, 4.45), (1.01, 4.42)), 1):
        made.append(model._curve_tube(f"V02_PulmonaryVein_{i}", ((x, 0.38, z), (x + 0.40, 0.57, z), (x + 0.76, 0.65, z)), 0.14, artery, vessels))

    for name, pts in (
        ("V02_Brachiocephalic", ((-0.08, 0.49, 6.73), (-0.01, 0.55, 7.13), (0.05, 0.55, 7.46))),
        ("V02_LeftCommonCarotid", ((-0.34, 0.54, 6.73), (-0.38, 0.60, 7.12), (-0.39, 0.61, 7.44))),
        ("V02_LeftSubclavian", ((-0.58, 0.56, 6.64), (-0.75, 0.61, 6.94), (-1.02, 0.64, 7.08))),
    ):
        made.append(model._curve_tube(name, pts, 0.105, artery, vessels))
    return made


def _build_coronary_detail(build: model.HeartBuild) -> list[bpy.types.Object]:
    anatomy = build.collections["anatomy"]
    coronary = build.materials["coronary_v02"]
    fat = build.materials["fat_v02"]
    made = []

    # Parent to the proven chamber walls so the vessels follow both base-cycle and law-specific deformation.
    lv_parent = bpy.data.objects.get("LeftVentricle_Wall")
    rv_parent = bpy.data.objects.get("RightVentricle_Wall")

    specs = (
        ("V02_LAD", ((0.02, -0.63, 4.05), (0.06, -0.72, 3.35), (0.10, -0.70, 2.55), (0.13, -0.60, 1.55), (0.16, -0.45, 0.95)), 0.045, lv_parent),
        ("V02_Circumflex", ((0.22, -0.56, 4.55), (0.72, -0.57, 4.45), (1.14, -0.45, 4.20)), 0.040, lv_parent),
        ("V02_RightCoronary", ((-0.24, -0.55, 4.52), (-0.76, -0.60, 4.34), (-1.16, -0.54, 3.98), (-1.30, -0.42, 3.55)), 0.042, rv_parent),
    )
    for name, pts, radius, parent in specs:
        obj = model._curve_tube(name, pts, radius, coronary, anatomy)
        _parent_keep_world(obj, parent)
        made.append(obj)

    for idx, (loc, scale, parent) in enumerate((
        ((0.05, -0.44, 4.05), (0.28, 0.07, 0.12), lv_parent),
        ((0.75, -0.41, 4.30), (0.26, 0.07, 0.11), lv_parent),
        ((-0.72, -0.41, 4.22), (0.30, 0.07, 0.11), rv_parent),
    ), 1):
        pad = model._uv_sphere(f"V02_EpicardialFat_{idx}", loc, scale, fat, anatomy, segments=28, rings=14)
        _parent_keep_world(pad, parent)
        made.append(pad)
    return made


def _refine_valves(build: model.HeartBuild) -> None:
    for name, scale in {
        "Mitral_Annulus": (0.92, 0.78, 0.92),
        "Tricuspid_Annulus": (0.95, 0.82, 0.94),
        "Aortic_Annulus": (0.90, 0.84, 0.90),
        "Pulmonary_Annulus": (0.90, 0.84, 0.90),
    }.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.scale = tuple(obj.scale[i] * scale[i] for i in range(3))

    for prefix, count, factors in (
        ("Mitral", 2, (0.88, 0.70, 0.90)),
        ("Tricuspid", 3, (0.86, 0.70, 0.88)),
        ("Aortic", 3, (0.82, 0.68, 0.82)),
        ("Pulmonary", 3, (0.82, 0.68, 0.82)),
    ):
        for idx in range(1, count + 1):
            obj = bpy.data.objects.get(f"{prefix}_Leaflet_{idx}")
            if obj:
                obj.scale = tuple(obj.scale[i] * factors[i] for i in range(3))


def upgrade(build: model.HeartBuild) -> model.HeartBuild:
    _refine_materials(build)
    _reshape_existing_chambers(build)
    _simplify_internal_clutter()
    _refine_valves(build)
    _hide_legacy_vessels()
    _build_great_vessels(build)
    _build_coronary_detail(build)

    scene = bpy.context.scene
    scene["anatomy_revision"] = REVISION
    scene["anatomy_notes"] = "single unified cutaway mesh; tapered LV apex; flattened wrapping RV; refined valve scale; rebuilt great vessels; coronary surface detail"
    scene["lv_wall_design"] = "dominant tapered thick-walled chamber forming apex"
    scene["rv_wall_design"] = "broader flatter chamber wrapping LV anteriorly"
    return build
