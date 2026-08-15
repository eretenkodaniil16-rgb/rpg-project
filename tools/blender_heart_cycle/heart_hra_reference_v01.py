from __future__ import annotations

"""Human Reference Atlas heart integration for Blender teaching scenes.

Source model:
  HuBMAP Human Reference Atlas, Heart Male reference organ
  https://ccf-ontology.hubmapconsortium.org/objects/v1.2/VH_M_Heart.glb
License:
  CC BY 4.0 — https://humanatlas.io/3d-reference-library
Provenance:
  Visible Human Male, U.S. National Library of Medicine.

The binary is downloaded by CI, never vendored. HRA supplies the anatomical
meshes; the project supplies the great vessels, animation controls and the
Frank-Starling/Anrep teaching timeline.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE_URL = "https://ccf-ontology.hubmapconsortium.org/objects/v1.2/VH_M_Heart.glb"
SOURCE_LICENSE = "CC BY 4.0"
REVISION = "hra_heart_male_v1_2_integration_v04"


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
            minimum.x = min(minimum.x, world.x)
            minimum.y = min(minimum.y, world.y)
            minimum.z = min(minimum.z, world.z)
            maximum.x = max(maximum.x, world.x)
            maximum.y = max(maximum.y, world.y)
            maximum.z = max(maximum.z, world.z)
    if not found:
        raise RuntimeError("HRA model contains no renderable mesh bounds")
    return minimum, maximum


def _hide_procedural_anatomy(build) -> None:
    # Preserve the rebuilt great-vessel tree. HRA replaces only chamber,
    # valve, flow and old anatomy meshes.
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
    target = Vector((1.90, 0.18, 3.48))
    root.location += target - center
    bpy.context.view_layer.update()


def _add_myocardial_microtexture(material: bpy.types.Material) -> None:
    tree = material.node_tree
    if tree is None:
        return
    bsdf = tree.nodes.get("Principled BSDF")
    if bsdf is None or "Normal" not in bsdf.inputs:
        return
    if tree.nodes.get("HRA_Myocardium_Bump") is not None:
        return

    texcoord = tree.nodes.new("ShaderNodeTexCoord")
    texcoord.name = "HRA_Myocardium_TexCoord"
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.name = "HRA_Myocardium_Noise"
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 3.4
    noise.inputs["Roughness"].default_value = 0.60
    bump = tree.nodes.new("ShaderNodeBump")
    bump.name = "HRA_Myocardium_Bump"
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.032

    tree.links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _material(
    name: str,
    color,
    roughness: float,
    *,
    myocardium: bool = False,
) -> bpy.types.Material:
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = 0.12 if myocardium else 0.035
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.02 if myocardium else 0.045
        if "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.42 if myocardium else 0.34
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 1.0
    if myocardium:
        _add_myocardial_microtexture(mat)
    return mat


def _category_material(obj_name: str) -> bpy.types.Material:
    low = obj_name.lower()
    if "valve" in low:
        return _material("M_HRA_Valve_v04", (0.60, 0.34, 0.27, 1.0), 0.43)
    if "papillary" in low:
        return _material("M_HRA_Papillary_v04", (0.30, 0.020, 0.019, 1.0), 0.54, myocardium=True)
    if "interventricular_septum" in low:
        return _material("M_HRA_Septum_v04", (0.27, 0.016, 0.015, 1.0), 0.53, myocardium=True)
    if "left_ventricle" in low:
        return _material("M_HRA_LV_Myocardium_v04", (0.255, 0.014, 0.013, 1.0), 0.54, myocardium=True)
    if "right_ventricle" in low:
        return _material("M_HRA_RV_Myocardium_v04", (0.34, 0.024, 0.022, 1.0), 0.53, myocardium=True)
    if "left_cardiac_atrium" in low:
        return _material("M_HRA_LA_Myocardium_v04", (0.31, 0.020, 0.018, 1.0), 0.54, myocardium=True)
    if "right_cardiac_atrium" in low:
        return _material("M_HRA_RA_Myocardium_v04", (0.36, 0.027, 0.024, 1.0), 0.54, myocardium=True)
    return _material("M_HRA_Myocardium_v04", (0.29, 0.018, 0.016, 1.0), 0.54, myocardium=True)


def _style_imported_structures(imported: list[bpy.types.Object]) -> None:
    for obj in imported:
        if obj.type != "MESH":
            continue
        material = _category_material(obj.name)
        obj.data.materials.clear()
        obj.data.materials.append(material)


def _seat_great_vessels(build) -> None:
    collection = build.collections.get("vessels")
    if collection is None:
        return
    for obj in collection.objects:
        if not obj.name.startswith("V02_"):
            continue
        obj.location.z -= 0.43
        obj.location.x += 0.03

    # Match the HRA myocardium's more matte medical-CGI finish.
    for key, roughness in (("artery", 0.44), ("vein", 0.47)):
        material = build.materials.get(key)
        if material is None or not material.use_nodes:
            continue
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        bsdf.inputs["Roughness"].default_value = roughness
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.025


def _reparent_keep_world(obj: bpy.types.Object, parent: bpy.types.Object | None) -> None:
    if parent is None:
        return
    matrix = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = matrix


def _control_for_structure(name: str, build) -> bpy.types.Object | None:
    low = name.lower()
    if "left_cardiac_atrium" in low:
        return build.controls.get("left_atrium")
    if "right_cardiac_atrium" in low:
        return build.controls.get("right_atrium")
    if "heart_left_ventricle" in low:
        return build.controls.get("left_ventricle")
    if "heart_right_ventricle" in low:
        return build.controls.get("right_ventricle")

    # Structures mechanically coupled to LV.
    if any(token in low for token in (
        "mitral_valve",
        "aortic_valve",
        "interventricular_septum",
        "papillary_muscle_of_heart_anterolateral",
        "papillary_muscle_of_heart_posteromedial",
    )):
        return build.controls.get("left_ventricle")

    # Structures mechanically coupled to RV.
    if any(token in low for token in (
        "tricuspid_valve",
        "pulmonary_valve",
        "papillary_muscle_of_heart_anterior",
        "papillary_muscle_of_heart_posterior",
        "papillary_muscle_of_heart_medial",
    )):
        return build.controls.get("right_ventricle")

    return build.controls.get("left_ventricle")


def _attach_structures_to_rig(
    root: bpy.types.Object,
    imported: list[bpy.types.Object],
    build,
) -> None:
    # Default non-mesh/import helper nodes follow LV; individual anatomical
    # meshes are detached from the GLB root and attached to chamber-specific
    # controls while preserving their normalized world transforms.
    _reparent_keep_world(root, build.controls.get("left_ventricle"))
    bpy.context.view_layer.update()

    for obj in imported:
        if obj.type != "MESH":
            continue
        control = _control_for_structure(obj.name, build)
        _reparent_keep_world(obj, control)
    bpy.context.view_layer.update()


def integrate(build, glb_path: str, yaw_degrees: float = 0.0):
    path = Path(glb_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    _hide_procedural_anatomy(build)
    imported = _import_glb(path)
    root = _make_root(imported)
    _normalize(root, imported, yaw_degrees)
    _style_imported_structures(imported)
    _seat_great_vessels(build)
    _attach_structures_to_rig(root, imported, build)

    scene = bpy.context.scene
    scene["anatomical_source"] = "Human Reference Atlas Heart Male v1.2"
    scene["anatomical_source_url"] = SOURCE_URL
    scene["anatomical_source_license"] = SOURCE_LICENSE
    scene["anatomical_source_revision"] = REVISION
    scene["hra_yaw_degrees"] = float(yaw_degrees)
    scene["hra_presentation"] = (
        "opaque HRA anatomy; chamber-specific rigging; myocardial micro-bump; "
        "seated procedural great vessels"
    )
    scene["hra_rigging"] = (
        "LV, RV, LA and RA HRA meshes follow their corresponding proven controls; "
        "mitral/aortic structures follow LV; tricuspid/pulmonary structures follow RV"
    )
    return root, imported
