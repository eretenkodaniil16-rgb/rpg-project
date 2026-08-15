from __future__ import annotations

"""Human Reference Atlas heart integration for Blender teaching scenes.

Source model:
  HuBMAP Human Reference Atlas, Heart Male reference organ
  https://ccf-ontology.hubmapconsortium.org/objects/v1.2/VH_M_Heart.glb
License:
  CC BY 4.0 — https://humanatlas.io/3d-reference-library
Provenance:
  Visible Human Male, U.S. National Library of Medicine.

The mesh is downloaded by CI, imported into Blender, normalized to the teaching
scene, and attached to the proven cardiac control rig.  The source binary is
not vendored into this repository.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector

SOURCE_URL = "https://ccf-ontology.hubmapconsortium.org/objects/v1.2/VH_M_Heart.glb"
SOURCE_LICENSE = "CC BY 4.0"
REVISION = "hra_heart_male_v1_2_integration_v01"


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
    # Keep render/UI objects, camera, lights, afterload indicator and intro torso.
    for key in ("chambers", "valves", "vessels", "flow"):
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
    # glTF importer resolves coordinate-system conversion; yaw selects the best
    # anatomical view relative to the teaching camera.
    root.rotation_euler[2] = math.radians(yaw_degrees)
    bpy.context.view_layer.update()

    minimum, maximum = _bbox(imported)
    size = maximum - minimum
    largest = max(size.x, size.y, size.z)
    if largest <= 1e-6:
        raise RuntimeError("HRA heart has degenerate bounds")

    # Fit the whole heart/great vessels into the right-side teaching viewport.
    scale = 5.35 / largest
    root.scale = (scale, scale, scale)
    bpy.context.view_layer.update()

    minimum, maximum = _bbox(imported)
    center = (minimum + maximum) * 0.5
    target = Vector((1.95, 0.20, 3.75))
    root.location += target - center
    bpy.context.view_layer.update()


def _refine_imported_materials(imported: list[bpy.types.Object]) -> None:
    """Retain HRA anatomical colors but remove flat/plastic appearance."""
    for obj in imported:
        if obj.type != "MESH":
            continue
        for material in obj.data.materials:
            if material is None:
                continue
            material.use_nodes = True
            bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
            if bsdf is None:
                continue
            bsdf.inputs["Roughness"].default_value = 0.38
            if "Coat Weight" in bsdf.inputs:
                bsdf.inputs["Coat Weight"].default_value = 0.08
            if "Coat Roughness" in bsdf.inputs:
                bsdf.inputs["Coat Roughness"].default_value = 0.30


def _attach_to_rig(root: bpy.types.Object, build) -> None:
    # The original LV control is already a child of the law-specific wrapper by
    # the time this integration runs, so the HRA heart inherits both base pulse
    # and Frank-Starling/Anrep scale response.
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
    _refine_imported_materials(imported)
    _attach_to_rig(root, build)

    scene = bpy.context.scene
    scene["anatomical_source"] = "Human Reference Atlas Heart Male v1.2"
    scene["anatomical_source_url"] = SOURCE_URL
    scene["anatomical_source_license"] = SOURCE_LICENSE
    scene["anatomical_source_revision"] = REVISION
    scene["hra_yaw_degrees"] = float(yaw_degrees)
    return root, imported
