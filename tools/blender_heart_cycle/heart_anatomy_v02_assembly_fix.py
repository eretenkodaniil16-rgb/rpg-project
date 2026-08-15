from __future__ import annotations

import bpy
from mathutils import Vector

import heart_cycle_model as model

REVISION = "heart_anatomy_v02_assembly_fix_v02"


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


def _scale_object(name: str, factors: tuple[float, float, float]) -> None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return
    obj.scale = tuple(obj.scale[i] * factors[i] for i in range(3))


def _reassemble_chambers(build: model.HeartBuild) -> None:
    """Collapse the old exploded/proxy layout into one compact cardiac mass."""
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")

    # The ventricle shells intentionally overlap in frontal projection.  LV
    # supplies the inferior apex; RV is slightly left/anterior and flatter.
    _move_control_to_place_wall(
        build.controls.get("left_ventricle"),
        bpy.data.objects.get("LeftVentricle_Wall"),
        _target_world(offset, (0.10, 0.18, 2.55)),
    )
    _move_control_to_place_wall(
        build.controls.get("right_ventricle"),
        bpy.data.objects.get("RightVentricle_Wall"),
        _target_world(offset, (-0.16, -0.04, 2.77)),
    )
    _move_control_to_place_wall(
        build.controls.get("left_atrium"),
        bpy.data.objects.get("LeftAtrium_Wall"),
        _target_world(offset, (0.34, 0.24, 4.43)),
    )
    _move_control_to_place_wall(
        build.controls.get("right_atrium"),
        bpy.data.objects.get("RightAtrium_Wall"),
        _target_world(offset, (-0.38, 0.18, 4.43)),
    )

    _move_object_center(
        bpy.data.objects.get("Interventricular_Septum"),
        _target_world(offset, (-0.01, 0.16, 2.72)),
    )

    # The old proxy was dimensioned for side-by-side display; after overlap its
    # absolute size is too large. Reduce chamber widths while preserving LV wall dominance.
    for name, factors in {
        "LeftVentricle_Wall": (0.84, 0.92, 0.94),
        "LeftVentricle_Cavity": (0.82, 0.90, 0.93),
        "RightVentricle_Wall": (0.83, 0.72, 0.90),
        "RightVentricle_Cavity": (0.80, 0.70, 0.88),
        "LeftAtrium_Wall": (0.82, 0.86, 0.86),
        "LeftAtrium_Cavity": (0.80, 0.84, 0.84),
        "RightAtrium_Wall": (0.84, 0.86, 0.88),
        "RightAtrium_Cavity": (0.82, 0.84, 0.86),
        "Interventricular_Septum": (0.80, 0.78, 0.94),
    }.items():
        _scale_object(name, factors)

    bpy.context.scene["assembly_layout"] = (
        "compact single heart; ventricular projected centers separated by 0.26 local units; "
        "LV forms apex; RV overlaps anterior-left"
    )


def _attach_post_infographic_vessels() -> None:
    """V02 vessels use heart-local points; make the infographic heart offset their parent."""
    offset = bpy.data.objects.get("CTRL_InfographicHeartOffset")
    if offset is None:
        return
    for obj in bpy.data.objects:
        if not obj.name.startswith("V02_"):
            continue
        if obj.name.startswith(("V02_LAD", "V02_Circumflex", "V02_RightCoronary", "V02_EpicardialFat")):
            obj.hide_viewport = True
            obj.hide_render = True
            continue
        if obj.parent is None:
            # Curves were created in heart-local coordinates after the offset;
            # parenting without preserving world applies exactly one offset.
            obj.parent = offset


def _compact_valve_apparatus() -> None:
    """Keep valve identity but remove the oversized white-ring/proxy appearance."""
    for name, factors in {
        "Mitral_Annulus": (0.62, 0.56, 0.62),
        "Tricuspid_Annulus": (0.64, 0.56, 0.64),
        "Aortic_Annulus": (0.60, 0.56, 0.60),
        "Pulmonary_Annulus": (0.60, 0.56, 0.60),
    }.items():
        _scale_object(name, factors)

    for prefix, count in (("Mitral", 2), ("Tricuspid", 3), ("Aortic", 3), ("Pulmonary", 3)):
        for index in range(1, count + 1):
            _scale_object(f"{prefix}_Leaflet_{index}", (0.72, 0.60, 0.72))

    for obj in bpy.data.objects:
        if "Chord" in obj.name and obj.type == "CURVE":
            obj.data.bevel_depth = min(obj.data.bevel_depth, 0.007)


def _trim_exploded_visuals() -> None:
    for obj in bpy.data.objects:
        if obj.name.startswith((
            "LeftAuricle_Pectinate_", "RightAtrium_Pectinate_",
            "LV_Trabecula_", "RV_Trabecula_",
            "LVOT_SeptalRidge", "RVOT_InfundibularRidge",
        )):
            obj.hide_viewport = True
            obj.hide_render = True

    for obj in bpy.data.objects:
        if obj.name.startswith("Papillary_") and obj.type == "MESH":
            obj.scale *= 0.55
        if obj.name == "RightPapillary_Septal" and obj.type == "MESH":
            obj.scale *= 0.52
        if obj.name == "RV_ModeratorBand":
            obj.hide_viewport = True
            obj.hide_render = True


def apply(build: model.HeartBuild) -> model.HeartBuild:
    _reassemble_chambers(build)
    _attach_post_infographic_vessels()
    _compact_valve_apparatus()
    _trim_exploded_visuals()
    scene = bpy.context.scene
    scene["anatomy_assembly_revision"] = REVISION
    scene["anatomy_assembly_rule"] = (
        "LV/RV physically overlap as one organ; compact valve apparatus; "
        "new great vessels inherit heart offset"
    )
    return build
