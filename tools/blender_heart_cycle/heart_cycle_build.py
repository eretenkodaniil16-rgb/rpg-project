from __future__ import annotations

import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bpy

import heart_cycle_model as model

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


def _multiply_object_scale(name: str, factors: tuple[float, float, float]) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required heart object is missing: {name}")
    obj.scale = tuple(obj.scale[index] * factors[index] for index in range(3))


def _refine_visual_proxy(build: model.HeartBuild) -> None:
    # Give the left ventricle a longer, narrower pressure-pump silhouette and
    # make the right ventricle shorter and wider instead of mirroring it.
    _multiply_object_scale("LeftVentricle_Wall", (0.97, 1.00, 1.08))
    _multiply_object_scale("LeftVentricle_Cavity", (0.94, 1.00, 1.08))
    _multiply_object_scale("RightVentricle_Wall", (1.08, 0.98, 0.92))
    _multiply_object_scale("RightVentricle_Cavity", (1.10, 0.98, 0.90))

    _multiply_object_scale("LeftAtrium_Wall", (0.92, 1.00, 0.90))
    _multiply_object_scale("LeftAtrium_Cavity", (0.90, 1.00, 0.90))
    _multiply_object_scale("RightAtrium_Wall", (1.03, 1.00, 0.96))
    _multiply_object_scale("RightAtrium_Cavity", (1.02, 1.00, 0.95))

    # The v01 anatomical rings were intentionally oversized for debugging.
    # Reduce them for the first presentable proxy while keeping each leaflet
    # separately selectable and animated.
    for name in ("Mitral_Annulus", "Tricuspid_Annulus"):
        _multiply_object_scale(name, (0.76, 0.76, 0.76))
    for name in ("Aortic_Annulus", "Pulmonary_Annulus"):
        _multiply_object_scale(name, (0.72, 0.72, 0.72))

    for prefix, count, factor in (
        ("Mitral", 2, 0.82),
        ("Tricuspid", 3, 0.82),
        ("Aortic", 3, 0.72),
        ("Pulmonary", 3, 0.72),
    ):
        for index in range(1, count + 1):
            _multiply_object_scale(
                f"{prefix}_Leaflet_{index}",
                (factor, factor, factor),
            )

    # Preserve visible flow direction while making the arrows subordinate to
    # the anatomy rather than the dominant foreground objects.
    for obj in build.collections["flow"].objects:
        if obj.type == "CURVE":
            obj.data.bevel_depth *= 0.72
        elif obj.type == "MESH" and obj.name.endswith("_Head"):
            obj.scale = tuple(value * 0.78 for value in obj.scale)


def _build_model_with_stable_parenting(resolution: int) -> model.HeartBuild:
    build = _BASE_BUILD_MODEL(resolution)

    # Objects are authored in world coordinates and parented later to chamber
    # controls. Parent inverses preserve the authored pose while retaining
    # contraction around the chamber-specific control origins.
    for obj in bpy.data.objects:
        if obj.parent is not None:
            obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()

    _refine_visual_proxy(build)

    cutters = build.collections.get("cutters")
    if cutters is not None:
        cutters.hide_viewport = True
        cutters.hide_render = True
    return build


model._setup_render = _setup_render_compatible
model.build_model = _build_model_with_stable_parenting


if __name__ == "__main__":
    raise SystemExit(model.main())
