from __future__ import annotations

"""Human Reference Atlas heart integration for Blender teaching scenes.

Source model:
  HuBMAP Human Reference Atlas, Heart Male reference organ
  https://ccf-ontology.hubmapconsortium.org/objects/v1.2/VH_M_Heart.glb
License:
  CC BY 4.0 — https://humanatlas.io/3d-reference-library
Provenance:
  Visible Human Male, U.S. National Library of Medicine.

The binary is downloaded by CI, never vendored.  We keep the HRA geometry and
replace only presentation materials/rig attachment for the physiology film.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE_URL = "https://ccf-ontology.hubmapconsortium.org/objects/v1.2/VH_M_Heart.glb"
SOURCE_LICENSE = "CC BY 4.0"
REVISION = "hra_heart_male_v1_2_integration_v02"


def _collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def _move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _import_glb(path: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = [obj for obj in bpy.data.objects if obj not in before]
    if not imported:
        raise RuntimeError(f"HRA GLB imported no objects: {path}")
    return imported


def _bbox(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    bpy.context.view_layer.update()
    minimum = Vector((float("inf"), float("inf"), float("inf")))
    maximum = Vector((float("-inf"), float("-inf"), float("-inf")))
    found = False
    for obj in objects:
        if obj.type != "MESH" or not obj.data.vertices:
            continue
        found = True
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            minimum.x = min(minimum.x, world.x); minimum.y = min(minimum.y, world.y); minimum.z = min(minimum.z, world.z)
            maximum.x = max(maximum.x, world.x); maximum.y = max(maximum.y, world.y); maximum.z = max(maximum.z, world.z)
    if not found:
        raise RuntimeError("HRA model contains no renderable mesh bounds")
    return minimum, maximum


def _hide_procedural_anatomy(build) -> None:
    # Keep the procedural great-vessel tree because the HRA reference organ
    # intentionally contains the cardiac structures/valves but terminates at
    # vessel ostia.  Hide all old procedural chamber/valve geometry instead.
    for key in ("chambers", "valves", "flow"):
        collection = build.collections.get(key)
        if collection is None:
            continue
        for obj in collection.objects:
            obj.hide_viewport = True
            obj.hide_render = True

    anatomy = build.collections.get("anatomy")
    if anatomy is not None:
        for obj in anatomy.objects:
            if obj.name.startswith(("UserTorso_", "UserReference_")):
                continue
            obj.hide_viewport = True
            obj.hide_render = True


def _make_root(imported: list[bpy.types.Object]) -> bpy.types.Object:
    collection = _collection("HRA_Heart_Reference_v01")
    root = bpy.data.objects.new("CTRL_HRA_HeartRoot_v01", None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.45
    collection.objects.link(root)

    imported_set = set(imported)
    for obj in imported:
        _move_to_collection(obj, collection)
    for obj in imported:
        if obj.parent not in imported_set:
            matrix = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_world = matrix
    return root


def _normalize(root: bpy.types.Object, imported: list[bpy.types.Object], yaw_degrees: float) -> None:
    root.rotation_euler[2] = math.radians(yaw_degrees)
    bpy.context.view_layer.update()

    minimum, maximum = _bbox(imported)
    size = maximum - minimum
    largest = max(size.x, size.y, size.z)
    if largest <= 1e-6:
        raise RuntimeError("HRA heart has degenerate bounds")

    scale = 5.05 / largest
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()

    minimum, maximum = _bbox(imported)
    center = (minimum + maximum) * 0.5
    # Slightly lower than v01 so aortic/pulmonary procedural roots sit naturally
    # above the HRA vessel ostia instead of intersecting the ventricular body.
    target = Vector((1.90, 0.18, 3.48))
    root.location += target - center
    bpy.context.view_layer.update()


def _material(name: str, color, roughness: float, alpha: float = 1.0) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.08 if "Myocardium" in name else 0.03
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.08
        if "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.28
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    return mat


def _category_material(obj_name: str) -> tuple[bpy.types.Material, bool]:
    low = obj_name.lower()
    if "valve" in low:
        return _material("M_HRA_Valve_v02", (0.82, 0.72, 0.57, 1.0), 0.31), False
    if "papillary" in low:
        return _material("M_HRA_Papillary_v02", (0.42, 0.036, 0.031, 1.0), 0.46), False
    if "interventricular_septum" in low:
        return _material("M_HRA_Septum_v02", (0.36, 0.027, 0.024, 1.0), 0.44), False
    if "left_ventricle" in low:
        return _material("M_HRA_LV_Myocardium_v02", (0.31, 0.020, 0.018, 1.0), 0.40), True
    if "right_ventricle" in low:
        return _material("M_HRA_RV_Myocardium_v02", (0.43, 0.035, 0.031, 1.0), 0.42), True
    if "left_cardiac_atrium" in low:
        return _material("M_HRA_LA_Myocardium_v02", (0.38, 0.028, 0.026, 1.0), 0.42), False
    if "right_cardiac_atrium" in low:
        return _material("M_HRA_RA_Myocardium_v02", (0.46, 0.042, 0.038, 1.0), 0.43), False
    return _material("M_HRA_Myocardium_v02", (0.36, 0.027, 0.024, 1.0), 0.42), False


def _animate_wall_alpha(material: bpy.types.Material) -> None:
    bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
    if bsdf is None or "Alpha" not in bsdf.inputs:
        return
    socket = bsdf.inputs["Alpha"]
    for frame, value in ((1, 1.0), (330, 1.0), (420, 0.46), (2700, 0.46), (2940, 0.92), (3150, 1.0)):
        socket.default_value = value
        socket.keyframe_insert(data_path="default_value", frame=frame)


def _style_imported_structures(imported: list[bpy.types.Object]) -> None:
    transparent_materials: set[bpy.types.Material] = set()
    for obj in imported:
        if obj.type != "MESH":
            continue
        material, wall = _category_material(obj.name)
        obj.data.materials.clear()
        obj.data.materials.append(material)
        if wall:
            transparent_materials.add(material)
    for material in transparent_materials:
        _animate_wall_alpha(material)


def _attach_to_rig(root: bpy.types.Object, build) -> None:
    control = build.controls.get("left_ventricle")
    if control is None:
        return
    matrix = root.matrix_world.copy()
    root.parent = control
    root.matrix_world = matrix


def integrate(build, glb_path: str, yaw_degrees: float = 0.0):
    path = Path(glb_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    _hide_procedural_anatomy(build)
    imported = _import_glb(path)
    root = _make_root(imported)
    _normalize(root, imported, yaw_degrees)
    _style_imported_structures(imported)
    _attach_to_rig(root, build)

    scene = bpy.context.scene
    scene["anatomical_source"] = "Human Reference Atlas Heart Male v1.2"
    scene["anatomical_source_url"] = SOURCE_URL
    scene["anatomical_source_license"] = SOURCE_LICENSE
    scene["anatomical_source_revision"] = REVISION
    scene["hra_yaw_degrees"] = float(yaw_degrees)
    scene["hra_presentation"] = "anatomical materials + ventricular transparency during teaching interval + procedural great vessels"
    return root, imported
