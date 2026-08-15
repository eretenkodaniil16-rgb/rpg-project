from __future__ import annotations

import bpy
from mathutils import Vector

import heart_cycle_model as model

REVISION = "heart_anatomy_v02_assembly_fix"


def _target_world(offset: bpy.types.Object | None, local_xyz: tuple[float, float, float]) -> Vector:
    point = Vector(local_xyz)
    if offset is None:
        return point
    return offset.matrix_world @ point


def _move_control_to_place_wall(
    control: bpy.types.Object | None,
    wall: bpy.types.Object | None,
    target_world: Vector,
) -> None:
    if control is None or wall is None:
        return
    bpy.context.view_layer.update()
    delta = target_world - wall.matrix_world.translation
    matrix = control.matrix_world.copy()
    matrix.translation += delta
    control.matrix_world = matrix
    bpy.context.view_layer.update()


def _move_object_center(obj: bpy.types.Object | None, target_world: Vector) -> None:
    if obj is None:
        return
    matrix = obj.matrix_world.copy()
    matrix.translation = target_world
    obj.matrix_world = matrix


def _reassemble_chambers(build: model.HeartBuild) -> None:
    """Collapse the old exploded/proxy layout into one coherent cardiac mass."""
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")

    _move_control_to_place_wall(
        build.controls.get("left_ventricle"),
        bpy.data.objects.get("LeftVentricle_Wall"),
        _target_world(offset, (0.42, 0.18, 2.55)),
    )
    _move_control_to_place_wall(
        build.controls.get("right_ventricle"),
        bpy.data.objects.get("RightVentricle_Wall"),
        _target_world(offset, (-0.42, 0.18, 2.76)),
    )
    _move_control_to_place_wall(
        build.controls.get("left_atrium"),
        bpy.data.objects.get("LeftAtrium_Wall"),
        _target_world(offset, (0.58, 0.20, 4.48)),
    )
    _move_control_to_place_wall(
        build.controls.get("right_atrium"),
        bpy.data.objects.get("RightAtrium_Wall"),
        _target_world(offset, (-0.62, 0.20, 4.48)),
    )

    # The septum is not chamber-controlled in the base scene.
    _move_object_center(
        bpy.data.objects.get("Interventricular_Septum"),
        _target_world(offset, (0.00, 0.28, 2.70)),
    )

    bpy.context.scene["assembly_layout"] = "single coherent heart; LV/RV and atria re-centered around common septum"


def _attach_post_infographic_vessels() -> None:
    """V02 vessels are authored after the infographic offset exists; attach them explicitly."""
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    if offset is None:
        return
    for obj in bpy.data.objects:
        if not obj.name.startswith("V02_"):
            continue
        if obj.name.startswith(("V02_LAD", "V02_Circumflex", "V02_RightCoronary", "V02_EpicardialFat")):
            # These were authored against pre-offset world coordinates in the first pass.
            # Hide them until they are rebuilt as proper surface-following curves.
            obj.hide_viewport = True
            obj.hide_render = True
            continue
        if obj.parent is not None:
            continue
        # The curve geometry uses heart-local coordinates, therefore do not preserve
        # its old world matrix when parenting: the offset must actually be applied.
        obj.parent = offset


def _trim_exploded_visuals() -> None:
    """Remove remaining decorative elements that read as detached anatomy."""
    for obj in bpy.data.objects:
        if obj.name.startswith(("LeftAuricle_Pectinate_", "RightAtrium_Pectinate_")):
            obj.hide_viewport = True
            obj.hide_render = True

    # Reduce visual dominance of papillary proxy cones; keep the landmark present.
    for obj in bpy.data.objects:
        if obj.name.startswith("Papillary_") and obj.type == "MESH":
            obj.scale *= 0.72
        if obj.name == "RightPapillary_Septal" and obj.type == "MESH":
            obj.scale *= 0.70


def apply(build: model.HeartBuild) -> model.HeartBuild:
    _reassemble_chambers(build)
    _attach_post_infographic_vessels()
    _trim_exploded_visuals()
    scene = bpy.context.scene
    scene["anatomy_assembly_revision"] = REVISION
    scene["anatomy_assembly_rule"] = "all chambers share one cardiac coordinate space; no exploded ventricular display"
    return build
