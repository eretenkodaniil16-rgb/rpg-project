from __future__ import annotations

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
    supported_engines = {item.identifier for item in scene.bl_rna.properties["render"].fixed_type.properties["engine"].enum_items}
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
    camera.location = (0.0, -17.5, 4.3)
    camera.data.lens = 58
    model._look_at(camera, (0.0, 0.0, 3.8))
    scene.camera = camera

    key_data = bpy.data.lights.new("Key", type="AREA")
    key_data.energy = 1100
    key_data.shape = "DISK"
    key_data.size = 5.0
    key = bpy.data.objects.new("Key", key_data)
    key.location = (-4.5, -6.0, 9.0)
    model._look_at(key, (0.0, 0.0, 3.8))
    build.collections["render"].objects.link(key)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 700
    fill_data.size = 4.0
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (5.0, -4.0, 6.0)
    model._look_at(fill, (0.0, 0.0, 3.8))
    build.collections["render"].objects.link(fill)

    rim_data = bpy.data.lights.new("Rim", type="AREA")
    rim_data.energy = 900
    rim_data.size = 3.0
    rim = bpy.data.objects.new("Rim", rim_data)
    rim.location = (0.0, 3.5, 8.0)
    model._look_at(rim, (0.0, 0.0, 4.2))
    build.collections["render"].objects.link(rim)

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0.0, 2.2, 0.20))
    backdrop = bpy.context.object
    backdrop.name = "Backdrop"
    backdrop.data.materials.append(
        model._material("M_Backdrop", (0.025, 0.028, 0.04, 1.0), roughness=0.9)
    )
    model._move_to_collection(backdrop, build.collections["render"])


def _build_model_with_stable_parenting(resolution: int) -> model.HeartBuild:
    build = _BASE_BUILD_MODEL(resolution)

    # Objects are authored in world coordinates and parented later to chamber
    # controls. Parent inverses preserve the authored pose while retaining
    # contraction around the chamber-specific control origins.
    for obj in bpy.data.objects:
        if obj.parent is not None:
            obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()

    cutters = build.collections.get("cutters")
    if cutters is not None:
        cutters.hide_viewport = True
        cutters.hide_render = True
    return build


model._setup_render = _setup_render_compatible
model.build_model = _build_model_with_stable_parenting


if __name__ == "__main__":
    raise SystemExit(model.main())
