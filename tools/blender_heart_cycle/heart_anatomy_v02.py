from __future__ import annotations

"""Anatomical v02 geometry upgrade for the cardiac teaching scenes.

The module deliberately reuses the proven v01 controls/animation rig while
replacing the weak visible proxy anatomy.  It is therefore safe to use with
Frank-Starling/Anrep timing without re-authoring the physiology.
"""

import math
import bpy

import heart_cycle_model as model

REVISION = "heart_anatomy_v02"


def _hide(name: str) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.hide_viewport = True
    obj.hide_render = True


def _parent_keep_world(obj: bpy.types.Object, parent: bpy.types.Object | None) -> None:
    if parent is None:
        return
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def _organic_surface(obj: bpy.types.Object, name: str, strength: float = 0.035, scale: float = 0.55) -> None:
    """Subtle non-plastic myocardial surface; small enough to preserve anatomy."""
    tex = bpy.data.textures.new(name=f"{name}_Noise", type="CLOUDS")
    tex.noise_scale = scale
    tex.noise_depth = 1
    displace = obj.modifiers.new(name=f"{name}_Microrelief", type="DISPLACE")
    displace.texture = tex
    displace.strength = strength
    displace.mid_level = 0.52
    displace.texture_coords = "GLOBAL"


def _material_v02(name: str, color, roughness: float, subsurface: float = 0.0, emission=None):
    mat = model._material(name, color, roughness=roughness, subsurface=subsurface, emission=emission)
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
    if bsdf is not None:
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.10
        if "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.28
    return mat


def _replace_materials(build: model.HeartBuild) -> None:
    build.materials["myocardium_v02"] = _material_v02(
        "M_Myocardium_v02", (0.31, 0.028, 0.024, 1.0), roughness=0.39, subsurface=0.10
    )
    build.materials["myocardium_cut_v02"] = _material_v02(
        "M_MyocardiumCut_v02", (0.62, 0.13, 0.105, 1.0), roughness=0.56, subsurface=0.13
    )
    build.materials["endocardium_v02"] = _material_v02(
        "M_Endocardium_v02", (0.48, 0.11, 0.105, 1.0), roughness=0.23, subsurface=0.05
    )
    build.materials["artery_v02"] = _material_v02(
        "M_Artery_v02", (0.47, 0.035, 0.028, 1.0), roughness=0.34, subsurface=0.07
    )
    build.materials["vein_v02"] = _material_v02(
        "M_Vein_v02", (0.075, 0.105, 0.28, 1.0), roughness=0.37, subsurface=0.05
    )
    build.materials["valve_v02"] = _material_v02(
        "M_Valve_v02", (0.78, 0.68, 0.56, 1.0), roughness=0.31, subsurface=0.08
    )
    build.materials["fat_v02"] = _material_v02(
        "M_EpicardialFat_v02", (0.63, 0.42, 0.14, 1.0), roughness=0.55, subsurface=0.04
    )
    build.materials["coronary_v02"] = _material_v02(
        "M_Coronary_v02", (0.72, 0.035, 0.025, 1.0), roughness=0.28, subsurface=0.03
    )


def _hide_proxy_anatomy() -> None:
    for name in (
        "LeftVentricle_Wall", "RightVentricle_Wall",
        "LeftVentricle_Cavity", "RightVentricle_Cavity",
        "Interventricular_Septum",
        "LeftAtrium_Wall", "RightAtrium_Wall",
        "LeftAtrium_Cavity", "RightAtrium_Cavity",
        "Aorta", "PulmonaryTrunk", "SuperiorVenaCava", "InferiorVenaCava",
    ):
        _hide(name)


def _build_ventricles(build: model.HeartBuild) -> dict[str, bpy.types.Object]:
    chambers = build.collections["chambers"]
    cutters = build.collections["cutters"]
    myocardium = build.materials["myocardium_v02"]
    cut = build.materials["myocardium_cut_v02"]
    endo = build.materials["endocardium_v02"]

    lv_ctrl = build.controls.get("left_ventricle")
    rv_ctrl = build.controls.get("right_ventricle")

    # LV is dominant and forms the anatomical apex.  Its wall/cavity ratio is
    # intentionally much larger than RV to read correctly in a cutaway.
    lv = model._make_cutaway_shell(
        "V02_LeftVentricle",
        (0.43, 0.15, 2.62),
        (1.42, 0.98, 2.32),
        (0.73, 0.58, 1.67),
        myocardium, cut, chambers, cutters,
    )
    lv.rotation_euler[1] = math.radians(-8.0)
    _organic_surface(lv, "LV", 0.040, 0.62)
    _parent_keep_world(lv, lv_ctrl)

    # RV is thinner, broader and shifted anterior/left, wrapping the LV.
    rv = model._make_cutaway_shell(
        "V02_RightVentricle",
        (-0.70, 0.03, 2.92),
        (1.24, 0.79, 1.92),
        (0.90, 0.57, 1.56),
        myocardium, cut, chambers, cutters,
    )
    rv.rotation_euler[1] = math.radians(13.0)
    rv.rotation_euler[2] = math.radians(-6.0)
    _organic_surface(rv, "RV", 0.032, 0.60)
    _parent_keep_world(rv, rv_ctrl)

    lv_cavity = model._uv_sphere(
        "V02_LV_EndocardialCavity", (0.47, 0.39, 2.72), (0.70, 0.105, 1.62), endo, chambers,
        segments=64, rings=32,
    )
    lv_cavity.rotation_euler[1] = math.radians(-8.0)
    _parent_keep_world(lv_cavity, lv_ctrl)

    rv_cavity = model._uv_sphere(
        "V02_RV_EndocardialCavity", (-0.71, 0.38, 2.97), (0.85, 0.095, 1.43), endo, chambers,
        segments=64, rings=32,
    )
    rv_cavity.rotation_euler[1] = math.radians(13.0)
    _parent_keep_world(rv_cavity, rv_ctrl)

    septum = model._uv_sphere(
        "V02_InterventricularSeptum", (-0.03, 0.25, 2.78), (0.30, 0.30, 1.93), cut, chambers,
        segments=56, rings=28,
    )
    septum.rotation_euler[1] = math.radians(-9.0)
    _organic_surface(septum, "Septum", 0.025, 0.40)

    # Muscular apex overlay visually unifies the two ventricular shells.
    apex = model._uv_sphere(
        "V02_ApexCap", (0.22, 0.13, 0.72), (0.68, 0.58, 0.72), myocardium, chambers,
        segments=56, rings=28,
    )
    apex.rotation_euler[1] = math.radians(-10.0)
    _organic_surface(apex, "Apex", 0.025, 0.45)
    _parent_keep_world(apex, lv_ctrl)

    return {"lv": lv, "rv": rv, "lv_cavity": lv_cavity, "rv_cavity": rv_cavity, "septum": septum}


def _build_atria(build: model.HeartBuild) -> dict[str, bpy.types.Object]:
    chambers = build.collections["chambers"]
    cutters = build.collections["cutters"]
    myocardium = build.materials["myocardium_v02"]
    cut = build.materials["myocardium_cut_v02"]
    endo = build.materials["endocardium_v02"]

    la_ctrl = build.controls.get("left_atrium")
    ra_ctrl = build.controls.get("right_atrium")

    la = model._make_cutaway_shell(
        "V02_LeftAtrium", (0.76, 0.25, 4.58), (0.88, 0.70, 0.80), (0.66, 0.48, 0.58),
        myocardium, cut, chambers, cutters,
    )
    la.rotation_euler[2] = math.radians(10.0)
    _parent_keep_world(la, la_ctrl)

    ra = model._make_cutaway_shell(
        "V02_RightAtrium", (-0.94, 0.25, 4.52), (1.05, 0.76, 0.96), (0.80, 0.54, 0.72),
        myocardium, cut, chambers, cutters,
    )
    ra.rotation_euler[2] = math.radians(-7.0)
    _parent_keep_world(ra, ra_ctrl)

    la_cavity = model._uv_sphere("V02_LA_Cavity", (0.78, 0.43, 4.59), (0.61, 0.095, 0.54), endo, chambers)
    ra_cavity = model._uv_sphere("V02_RA_Cavity", (-0.94, 0.43, 4.52), (0.73, 0.095, 0.65), endo, chambers)
    _parent_keep_world(la_cavity, la_ctrl); _parent_keep_world(ra_cavity, ra_ctrl)

    # Atrial appendages remove the spherical 'two balls on top' silhouette.
    laa = model._uv_sphere("V02_LeftAtrialAppendage", (1.48, 0.18, 4.74), (0.47, 0.38, 0.36), myocardium, chambers, segments=40, rings=20)
    laa.rotation_euler = (math.radians(8), math.radians(-18), math.radians(30))
    raa = model._uv_sphere("V02_RightAtrialAppendage", (-1.63, 0.15, 4.70), (0.52, 0.40, 0.42), myocardium, chambers, segments=40, rings=20)
    raa.rotation_euler = (math.radians(-5), math.radians(18), math.radians(-25))
    _organic_surface(laa, "LAA", 0.025, 0.35); _organic_surface(raa, "RAA", 0.025, 0.35)
    _parent_keep_world(laa, la_ctrl); _parent_keep_world(raa, ra_ctrl)

    return {"la": la, "ra": ra, "laa": laa, "raa": raa}


def _build_great_vessels(build: model.HeartBuild) -> list[bpy.types.Object]:
    vessels = build.collections["vessels"]
    artery = build.materials["artery_v02"]
    vein = build.materials["vein_v02"]
    made: list[bpy.types.Object] = []

    # Ascending aorta + arch are one continuous organic curve, not cylinders.
    made.append(model._curve_tube(
        "V02_Aorta",
        ((0.38, 0.16, 5.02), (0.52, 0.22, 5.66), (0.52, 0.30, 6.34), (0.18, 0.46, 6.78), (-0.46, 0.56, 6.72), (-0.86, 0.56, 6.32)),
        0.31, artery, vessels,
    ))
    made.append(model._curve_tube(
        "V02_PulmonaryTrunk",
        ((-0.37, 0.10, 5.02), (-0.28, 0.15, 5.58), (-0.52, 0.24, 5.98), (-0.90, 0.31, 6.14)),
        0.29, vein, vessels,
    ))
    made.append(model._curve_tube("V02_LeftPulmonaryArtery", ((-0.88, 0.31, 6.14), (-1.45, 0.34, 6.16), (-1.92, 0.28, 6.05)), 0.22, vein, vessels))
    made.append(model._curve_tube("V02_RightPulmonaryArtery", ((-0.75, 0.42, 6.12), (-0.15, 0.70, 6.15), (0.72, 0.76, 6.03)), 0.20, vein, vessels))

    made.append(model._curve_tube("V02_SVC", ((-1.18, 0.40, 6.20), (-1.12, 0.38, 5.65), (-1.04, 0.30, 5.05)), 0.28, vein, vessels))
    made.append(model._curve_tube("V02_IVC", ((-1.02, 0.30, 4.12), (-1.05, 0.34, 3.62), (-0.98, 0.35, 3.20)), 0.29, vein, vessels))

    # Pulmonary veins: four short, paired inflows to LA.
    for i, (x, z) in enumerate(((0.68, 4.86), (1.05, 4.83), (0.69, 4.42), (1.04, 4.39)), start=1):
        made.append(model._curve_tube(
            f"V02_PulmonaryVein_{i}", ((x, 0.36, z), (x + 0.42, 0.58, z + (0.05 if i < 3 else -0.05)), (x + 0.78, 0.66, z)),
            0.16, artery, vessels,
        ))

    # Three aortic arch branches.
    for name, pts in (
        ("V02_Brachiocephalic", ((-0.10, 0.48, 6.76), (-0.02, 0.55, 7.18), (0.06, 0.55, 7.55))),
        ("V02_LeftCommonCarotid", ((-0.38, 0.54, 6.77), (-0.42, 0.60, 7.18), (-0.43, 0.61, 7.52))),
        ("V02_LeftSubclavian", ((-0.62, 0.55, 6.66), (-0.78, 0.60, 6.98), (-1.05, 0.63, 7.12))),
    ):
        made.append(model._curve_tube(name, pts, 0.115, artery, vessels))

    return made


def _build_coronary_surface_detail(build: model.HeartBuild) -> list[bpy.types.Object]:
    anatomy = build.collections["anatomy"]
    coronary = build.materials["coronary_v02"]
    fat = build.materials["fat_v02"]
    made: list[bpy.types.Object] = []

    # Anterior interventricular groove and LAD make the exterior recognisably cardiac.
    made.append(model._curve_tube(
        "V02_LAD", ((0.05, -0.62, 4.20), (0.10, -0.73, 3.55), (0.13, -0.73, 2.75), (0.14, -0.65, 1.82), (0.18, -0.50, 1.05)),
        0.055, coronary, anatomy,
    ))
    made.append(model._curve_tube(
        "V02_RightCoronary", ((-0.20, -0.56, 4.65), (-0.78, -0.62, 4.45), (-1.15, -0.58, 4.05), (-1.30, -0.45, 3.55)),
        0.050, coronary, anatomy,
    ))
    made.append(model._curve_tube(
        "V02_Circumflex", ((0.25, -0.55, 4.70), (0.72, -0.58, 4.58), (1.18, -0.46, 4.32)),
        0.047, coronary, anatomy,
    ))

    # Thin epicardial fat pads accentuate AV/interventricular grooves without clutter.
    for idx, (loc, scale) in enumerate((
        ((0.02, -0.43, 4.18), (0.34, 0.09, 0.16)),
        ((-0.72, -0.40, 4.34), (0.38, 0.08, 0.14)),
        ((0.76, -0.39, 4.39), (0.34, 0.08, 0.13)),
    ), start=1):
        pad = model._uv_sphere(f"V02_EpicardialFat_{idx}", loc, scale, fat, anatomy, segments=32, rings=16)
        made.append(pad)
    return made


def _build_internal_detail(build: model.HeartBuild) -> list[bpy.types.Object]:
    anatomy = build.collections["anatomy"]
    cut = build.materials["myocardium_cut_v02"]
    valve = build.materials["valve_v02"]
    chord = build.materials.get("chordae", valve)
    made: list[bpy.types.Object] = []

    # Papillary muscles are intentionally asymmetric and chamber-specific.
    for idx, (loc, r1, r2, depth, parent_key) in enumerate((
        ((0.32, -0.02, 2.18), 0.18, 0.085, 0.74, "left_ventricle"),
        ((0.82, -0.01, 2.00), 0.20, 0.09, 0.80, "left_ventricle"),
        ((-0.54, -0.02, 2.32), 0.15, 0.07, 0.62, "right_ventricle"),
        ((-0.98, -0.01, 2.50), 0.14, 0.065, 0.56, "right_ventricle"),
    ), start=1):
        pap = model._cone(f"V02_Papillary_{idx}", loc, r1, r2, depth, cut, anatomy, rotation=(math.radians(-7 if loc[0] > 0 else 7), 0, 0))
        _parent_keep_world(pap, build.controls.get(parent_key)); made.append(pap)

    # A few trabeculae add depth to the opened ventricles but remain readable.
    trabeculae = (
        ((0.16, -0.055, 1.62), (0.55, -0.050, 2.05)),
        ((0.30, -0.055, 1.38), (0.76, -0.050, 1.82)),
        ((-0.32, -0.055, 1.75), (-0.78, -0.050, 2.12)),
        ((-0.50, -0.055, 2.16), (-1.02, -0.050, 2.52)),
    )
    for idx, pts in enumerate(trabeculae, start=1):
        made.append(model._curve_tube(f"V02_Trabecula_{idx}", pts, 0.045, cut, anatomy))

    # Upgrade visible valve materials from the old rig; geometry/animation stays proven.
    for obj in bpy.data.objects:
        if obj.name.startswith(("Mitral_", "Tricuspid_", "Aortic_", "Pulmonary_")) and obj.type == "MESH":
            if len(obj.data.materials): obj.data.materials[0] = valve
        if "Chord" in obj.name and hasattr(obj.data, "materials") and len(obj.data.materials):
            obj.data.materials[0] = chord
    return made


def upgrade(build: model.HeartBuild) -> model.HeartBuild:
    """Replace the visible v01 proxy with anatomy v02, preserving all controls."""
    _replace_materials(build)
    _hide_proxy_anatomy()
    ventricles = _build_ventricles(build)
    atria = _build_atria(build)
    vessels = _build_great_vessels(build)
    coronary = _build_coronary_surface_detail(build)
    internal = _build_internal_detail(build)

    scene = bpy.context.scene
    scene["anatomy_revision"] = REVISION
    scene["anatomy_notes"] = "asymmetric LV/RV, true apex, atrial appendages, great-vessel branching, coronary surface detail, refined cutaway"
    scene["lv_wall_design"] = "thick dominant wall"
    scene["rv_wall_design"] = "thin anterior wrapping wall"

    # Store references for downstream QA/debugging.
    build.controls["anatomy_v02_lv_visible"] = ventricles["lv"]
    build.controls["anatomy_v02_rv_visible"] = ventricles["rv"]
    build.controls["anatomy_v02_la_visible"] = atria["la"]
    build.controls["anatomy_v02_ra_visible"] = atria["ra"]
    return build
