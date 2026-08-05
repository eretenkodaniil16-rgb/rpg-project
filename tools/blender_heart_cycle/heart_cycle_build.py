from __future__ import annotations

import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy
from mathutils import Vector

import heart_cycle_model as model

ANATOMY_REVISION = "heart_cutaway_v02"
model.MODEL_REVISION = ANATOMY_REVISION

_BASE_BUILD_MODEL = model.build_model


def _setup_render_compatible(build: model.HeartBuild, resolution: int) -> None:
    scene = bpy.context.scene
    supported_engines = {
        item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items
    }
    for candidate in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        if candidate in supported_engines:
            scene.render.engine = candidate
            break
    else:
        raise RuntimeError(f"No supported render engine found: {sorted(supported_engines)}")

    scene.render.resolution_x = int(resolution * 16 / 9)
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.world.color = (0.035, 0.035, 0.045)

    camera_data = bpy.data.cameras.new("HeartCamera")
    camera = bpy.data.objects.new("HeartCamera", camera_data)
    build.collections["render"].objects.link(camera)
    camera.location = (0.0, -20.5, 4.2)
    camera.data.lens = 58
    model._look_at(camera, (0.0, 0.0, 3.85))
    scene.camera = camera

    key_data = bpy.data.lights.new("Key", type="AREA")
    key_data.energy = 1250
    key_data.shape = "DISK"
    key_data.size = 5.0
    key = bpy.data.objects.new("Key", key_data)
    key.location = (-4.5, -6.0, 9.0)
    model._look_at(key, (0.0, 0.0, 3.8))
    build.collections["render"].objects.link(key)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 650
    fill_data.size = 4.0
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (5.0, -4.0, 6.0)
    model._look_at(fill, (0.0, 0.0, 3.8))
    build.collections["render"].objects.link(fill)

    rim_data = bpy.data.lights.new("Rim", type="AREA")
    rim_data.energy = 950
    rim_data.size = 3.0
    rim = bpy.data.objects.new("Rim", rim_data)
    rim.location = (0.0, 3.5, 8.0)
    model._look_at(rim, (0.0, 0.0, 4.2))
    build.collections["render"].objects.link(rim)

    bpy.ops.mesh.primitive_plane_add(
        size=30,
        location=(0.0, 2.6, 4.0),
        rotation=(math.pi / 2.0, 0.0, 0.0),
    )
    backdrop = bpy.context.object
    backdrop.name = "Backdrop"
    backdrop.data.materials.append(
        model._material("M_Backdrop", (0.025, 0.028, 0.04, 1.0), roughness=0.9)
    )
    model._move_to_collection(backdrop, build.collections["render"])


def _require_object(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required heart object is missing: {name}")
    return obj


def _multiply_object_scale(name: str, factors: tuple[float, float, float]) -> None:
    obj = _require_object(name)
    obj.scale = tuple(obj.scale[index] * factors[index] for index in range(3))


def _translate_world(name: str, delta: tuple[float, float, float]) -> None:
    obj = _require_object(name)
    matrix = obj.matrix_world.copy()
    matrix.translation += Vector(delta)
    obj.matrix_world = matrix


def _parent_preserve_world(
    obj: bpy.types.Object,
    parent: bpy.types.Object,
) -> bpy.types.Object:
    matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = matrix
    return obj


def _set_material_appearance(
    material: bpy.types.Material,
    color: tuple[float, float, float, float],
    *,
    roughness: float,
    subsurface: float | None = None,
) -> None:
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError(f"Material has no Principled BSDF: {material.name}")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    if subsurface is not None and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface


def _refine_materials(build: model.HeartBuild) -> None:
    _set_material_appearance(
        build.materials["myocardium"],
        (0.34, 0.035, 0.028, 1.0),
        roughness=0.56,
        subsurface=0.10,
    )
    _set_material_appearance(
        build.materials["myocardium_cut"],
        (0.70, 0.14, 0.105, 1.0),
        roughness=0.66,
        subsurface=0.14,
    )
    _set_material_appearance(
        build.materials["right_chamber"],
        (0.115, 0.145, 0.285, 1.0),
        roughness=0.70,
    )
    _set_material_appearance(
        build.materials["left_chamber"],
        (0.31, 0.045, 0.055, 1.0),
        roughness=0.70,
    )
    _set_material_appearance(
        build.materials["valve"],
        (0.82, 0.67, 0.52, 1.0),
        roughness=0.50,
        subsurface=0.08,
    )


def _refine_chamber_silhouette(build: model.HeartBuild) -> None:
    # Left ventricle: thicker, narrower and responsible for the apex.
    _multiply_object_scale("LeftVentricle_Wall", (0.94, 1.00, 1.12))
    _multiply_object_scale("LeftVentricle_Cavity", (0.89, 0.96, 1.10))
    _translate_world("LeftVentricle_Wall", (0.10, 0.00, -0.10))
    _translate_world("LeftVentricle_Cavity", (0.10, -0.01, -0.08))

    # Right ventricle: broader, shorter and more crescent-like around the septum.
    _multiply_object_scale("RightVentricle_Wall", (1.15, 0.90, 0.88))
    _multiply_object_scale("RightVentricle_Cavity", (1.18, 0.78, 0.84))
    _translate_world("RightVentricle_Wall", (-0.10, -0.03, 0.10))
    _translate_world("RightVentricle_Cavity", (-0.08, -0.06, 0.12))

    _multiply_object_scale("Interventricular_Septum", (0.82, 0.74, 1.03))
    _translate_world("Interventricular_Septum", (-0.04, -0.03, -0.02))

    _multiply_object_scale("LeftAtrium_Wall", (0.90, 0.94, 0.88))
    _multiply_object_scale("LeftAtrium_Cavity", (0.87, 0.90, 0.86))
    _multiply_object_scale("RightAtrium_Wall", (1.06, 0.96, 0.98))
    _multiply_object_scale("RightAtrium_Cavity", (1.04, 0.92, 0.96))


def _refine_valves() -> None:
    # Annuli are elliptical rather than four identical circular rings.
    for name, factors in {
        "Mitral_Annulus": (0.78, 0.58, 0.70),
        "Tricuspid_Annulus": (0.86, 0.62, 0.76),
        "Aortic_Annulus": (0.70, 0.64, 0.70),
        "Pulmonary_Annulus": (0.74, 0.66, 0.74),
    }.items():
        _multiply_object_scale(name, factors)

    for prefix, count, factors in (
        ("Mitral", 2, (0.82, 0.52, 1.02)),
        ("Tricuspid", 3, (0.78, 0.50, 0.94)),
        ("Aortic", 3, (0.68, 0.46, 0.80)),
        ("Pulmonary", 3, (0.70, 0.46, 0.82)),
    ):
        for index in range(1, count + 1):
            _multiply_object_scale(f"{prefix}_Leaflet_{index}", factors)


def _refine_papillary_muscles() -> None:
    for name in ("Papillary_+0.48_2.20", "Papillary_+0.98_2.00"):
        _multiply_object_scale(name, (0.72, 0.72, 1.16))
    for name in ("Papillary_-0.48_2.15", "Papillary_-0.98_2.05"):
        _multiply_object_scale(name, (0.82, 0.82, 1.04))


def _add_atrial_appendages(build: model.HeartBuild) -> None:
    chambers = build.collections["chambers"]
    myocardium = build.materials["myocardium"]

    appendage_specs = (
        (
            "LeftAuricle",
            build.controls["left_atrium"],
            (
                ((1.66, 0.18, 4.95), (0.48, 0.38, 0.36), (0.0, math.radians(-18.0), math.radians(12.0))),
                ((1.93, 0.16, 4.86), (0.33, 0.30, 0.25), (0.0, math.radians(-24.0), math.radians(22.0))),
            ),
        ),
        (
            "RightAuricle",
            build.controls["right_atrium"],
            (
                ((-1.70, 0.16, 4.92), (0.53, 0.40, 0.38), (0.0, math.radians(16.0), math.radians(-14.0))),
                ((-2.00, 0.14, 4.80), (0.35, 0.31, 0.27), (0.0, math.radians(25.0), math.radians(-24.0))),
            ),
        ),
    )

    for prefix, parent, lobes in appendage_specs:
        for index, (location, scale, rotation) in enumerate(lobes, start=1):
            lobe = model._uv_sphere(
                f"{prefix}_Lobe_{index}",
                location,
                scale,
                myocardium,
                chambers,
                segments=40,
                rings=20,
            )
            lobe.rotation_euler = rotation
            _parent_preserve_world(lobe, parent)


def _add_trabeculae(build: model.HeartBuild) -> None:
    anatomy = build.collections["anatomy"]
    ridge_material = build.materials["myocardium_cut"]

    left_paths = (
        ((0.35, -0.07, 3.45), (0.43, -0.10, 2.82), (0.55, -0.07, 1.55)),
        ((0.60, -0.08, 3.42), (0.68, -0.11, 2.68), (0.78, -0.08, 1.35)),
        ((0.88, -0.08, 3.40), (0.94, -0.11, 2.62), (0.98, -0.08, 1.48)),
        ((1.15, -0.07, 3.35), (1.20, -0.10, 2.72), (1.18, -0.07, 1.72)),
        ((0.42, -0.06, 2.65), (0.72, -0.11, 2.48), (1.14, -0.06, 2.42)),
        ((0.48, -0.06, 2.05), (0.74, -0.11, 1.90), (1.05, -0.06, 1.84)),
    )
    right_paths = (
        ((-0.32, -0.08, 3.35), (-0.48, -0.12, 2.75), (-0.58, -0.08, 1.75)),
        ((-0.63, -0.08, 3.38), (-0.78, -0.12, 2.72), (-0.85, -0.08, 1.66)),
        ((-0.96, -0.08, 3.32), (-1.10, -0.12, 2.72), (-1.18, -0.08, 1.92)),
        ((-1.28, -0.07, 3.18), (-1.37, -0.11, 2.70), (-1.38, -0.07, 2.15)),
        ((-0.34, -0.06, 2.74), (-0.82, -0.13, 2.55), (-1.36, -0.06, 2.50)),
    )

    for side, paths, radius, parent in (
        ("LV", left_paths, 0.030, build.controls["left_ventricle"]),
        ("RV", right_paths, 0.042, build.controls["right_ventricle"]),
    ):
        for index, points in enumerate(paths, start=1):
            ridge = model._curve_tube(
                f"{side}_Trabecula_{index:02d}",
                points,
                radius,
                ridge_material,
                anatomy,
            )
            _parent_preserve_world(ridge, parent)

    moderator = model._curve_tube(
        "RV_ModeratorBand",
        ((-0.18, -0.16, 2.62), (-0.70, -0.18, 2.48), (-1.25, -0.14, 2.42)),
        0.075,
        ridge_material,
        anatomy,
    )
    _parent_preserve_world(moderator, build.controls["right_ventricle"])


def _add_pectinate_muscles(build: model.HeartBuild) -> None:
    anatomy = build.collections["anatomy"]
    ridge_material = build.materials["myocardium_cut"]
    right_parent = build.controls["right_atrium"]
    left_parent = build.controls["left_atrium"]

    for index, z in enumerate((4.28, 4.45, 4.62, 4.79, 4.96), start=1):
        ridge = model._curve_tube(
            f"RightAtrium_Pectinate_{index:02d}",
            ((-1.58, -0.05, z), (-1.28, -0.11, z + 0.04), (-0.96, -0.06, 4.60)),
            0.025,
            ridge_material,
            anatomy,
        )
        _parent_preserve_world(ridge, right_parent)

    for index, z in enumerate((4.70, 4.84, 4.98), start=1):
        ridge = model._curve_tube(
            f"LeftAuricle_Pectinate_{index:02d}",
            ((1.96, -0.03, z - 0.10), (1.72, -0.09, z), (1.45, -0.05, 4.78)),
            0.020,
            ridge_material,
            anatomy,
        )
        _parent_preserve_world(ridge, left_parent)


def _add_outflow_tracts(build: model.HeartBuild) -> None:
    anatomy = build.collections["anatomy"]
    vessels = build.collections["vessels"]
    cut = build.materials["myocardium_cut"]

    lvot = model._curve_tube(
        "LVOT_SeptalRidge",
        ((0.18, -0.04, 3.55), (0.27, -0.08, 4.20), (0.42, -0.04, 4.88)),
        0.105,
        cut,
        anatomy,
    )
    _parent_preserve_world(lvot, build.controls["left_ventricle"])

    rvot = model._curve_tube(
        "RVOT_InfundibularRidge",
        ((-0.22, -0.05, 3.48), (-0.32, -0.09, 4.16), (-0.42, -0.05, 4.88)),
        0.095,
        cut,
        anatomy,
    )
    _parent_preserve_world(rvot, build.controls["right_ventricle"])

    septal_papillary = model._cone(
        "RightPapillary_Septal",
        (-0.24, -0.04, 2.44),
        0.14,
        0.07,
        0.58,
        cut,
        anatomy,
        rotation=(math.radians(8.0), 0.0, math.radians(-6.0)),
    )
    _parent_preserve_world(septal_papillary, build.controls["right_ventricle"])

    for index, leaflet in enumerate(build.valve_leaflets["Tricuspid"], start=1):
        start = tuple(leaflet.matrix_world.translation + Vector((0.0, -0.08, -0.18)))
        chord = model._curve_tube(
            f"Tricuspid_SeptalChord_{index}",
            (start, (-0.24, -0.05, 2.66)),
            0.014,
            build.materials["chordae"],
            anatomy,
        )
        _parent_preserve_world(chord, build.controls["right_ventricle"])

    # Pulmonary bifurcation is added explicitly so the outflow does not end as
    # a single decorative tube.
    model._curve_tube(
        "PulmonaryArtery_LeftBranch",
        ((-1.50, 0.30, 6.10), (-2.05, 0.38, 6.12), (-2.62, 0.42, 6.00)),
        0.235,
        build.materials["vein"],
        vessels,
    )
    model._curve_tube(
        "PulmonaryArtery_RightBranch",
        ((-0.72, 0.42, 6.10), (-0.10, 0.66, 6.14), (0.72, 0.78, 6.02)),
        0.215,
        build.materials["vein"],
        vessels,
    )


def _subordinate_flow_guides(build: model.HeartBuild) -> None:
    for obj in build.collections["flow"].objects:
        if obj.type == "CURVE":
            obj.data.bevel_depth *= 0.68
        elif obj.type == "MESH" and obj.name.endswith("_Head"):
            obj.scale = tuple(value * 0.74 for value in obj.scale)


def _add_anatomy_v02(build: model.HeartBuild) -> None:
    _refine_materials(build)
    _refine_chamber_silhouette(build)
    _refine_valves()
    _refine_papillary_muscles()
    _add_atrial_appendages(build)
    _add_trabeculae(build)
    _add_pectinate_muscles(build)
    _add_outflow_tracts(build)
    _subordinate_flow_guides(build)

    scene = bpy.context.scene
    scene["model_revision"] = ANATOMY_REVISION
    scene["anatomy_revision"] = "anatomy_pass_v02"
    scene["anatomy_features"] = (
        "ventricular asymmetry; atrial appendages; trabeculae; pectinate muscles; "
        "RV moderator band; LV/RV outflow ridges; septal papillary muscle; "
        "pulmonary artery bifurcation"
    )


def _build_model_with_stable_parenting(resolution: int) -> model.HeartBuild:
    build = _BASE_BUILD_MODEL(resolution)

    # Objects are authored in world coordinates and parented later to chamber
    # controls. Parent inverses preserve the authored pose while retaining
    # contraction around the chamber-specific control origins.
    for obj in bpy.data.objects:
        if obj.parent is not None:
            obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()

    _add_anatomy_v02(build)

    cutters = build.collections.get("cutters")
    if cutters is not None:
        cutters.hide_viewport = True
        cutters.hide_render = True
    return build


model._setup_render = _setup_render_compatible
model.build_model = _build_model_with_stable_parenting


if __name__ == "__main__":
    raise SystemExit(model.main())
