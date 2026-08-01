from __future__ import annotations

import math

import blender_sprite_factory as factory
from head_profile_v04 import DetailedEllipsoidPart
from hair_sweep_profile_v08 import (
    HairSweepMeshPart,
    HairSweepRing,
    load_hair_sweep_profile_v08,
)
from head_profile_v08 import load_head_detail_profile_v08


def _apply_reference_palette(context: factory.BuildContext) -> None:
    material = context.materials["hair"]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    texture = next(node for node in nodes if node.type == "TEX_IMAGE")
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    for link in tuple(output.inputs["Surface"].links):
        links.remove(link)
    rgb_to_bw = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "hair_reference_palette"
    ramp.color_ramp.interpolation = "CONSTANT"
    elements = ramp.color_ramp.elements
    elements[0].position = 0.005
    elements[0].color = (0x0B / 255.0, 0x06 / 255.0, 0x02 / 255.0, 1.0)
    elements[1].position = 0.10
    elements[1].color = (0x7C / 255.0, 0x49 / 255.0, 0x24 / 255.0, 1.0)
    for position, color in (
        (0.010, (0x1A, 0x12, 0x0A)),
        (0.020, (0x26, 0x18, 0x0B)),
        (0.045, (0x58, 0x2A, 0x15)),
    ):
        element = elements.new(position)
        element.color = tuple(value / 255.0 for value in color) + (1.0,)
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 0.82
    links.new(texture.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(rgb_to_bw.outputs["Val"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])


def _clear_old_hair() -> None:
    for obj in tuple(factory.bpy.data.objects):
        if obj.get(factory.MODULE_PROPERTY) == "hair":
            factory.bpy.data.objects.remove(obj, do_unlink=True)


def _ring_arc(part: HairSweepMeshPart, ring: HairSweepRing) -> tuple[float, float]:
    arc_start_degrees, arc_end_degrees = part.ring_arc(ring)
    return math.radians(arc_start_degrees), math.radians(
        arc_end_degrees - arc_start_degrees
    )


def _sweep_mesh(part: HairSweepMeshPart, material: object) -> object:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    point_count = part.segments if part.closed_around else part.segments + 1

    for ring in part.rings:
        phase = math.radians(ring.phase_degrees)
        arc_start, arc_span = _ring_arc(part, ring)
        for point_index in range(point_count):
            angle = arc_start + arc_span * point_index / part.segments
            wave = 1.0 + part.wave_amplitude * math.cos(
                part.wave_frequency * angle + phase
            )
            vertices.append(
                (
                    ring.center_x + ring.radius_x * math.cos(angle) * wave,
                    ring.center_y + ring.radius_y * math.sin(angle) * wave,
                    ring.z,
                )
            )

    for ring_index in range(1, len(part.rings)):
        previous = (ring_index - 1) * point_count
        current = ring_index * point_count
        for index in range(part.segments):
            next_index = (index + 1) % point_count
            faces.append(
                (
                    previous + index,
                    previous + next_index,
                    current + next_index,
                    current + index,
                )
            )

    if part.closed_around:
        faces.append(tuple(reversed(range(point_count))))
        top = (len(part.rings) - 1) * point_count
        faces.append(tuple(top + index for index in range(point_count)))
    else:
        for index in range(len(part.rings) - 1):
            current = index * point_count
            following = (index + 1) * point_count
            faces.append(
                (
                    current,
                    following,
                    following + point_count - 1,
                    current + point_count - 1,
                )
            )

    mesh = factory.bpy.data.meshes.new(f"{part.name}_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update(calc_edges=True)
    mesh.validate(verbose=False, clean_customdata=False)
    obj = factory.bpy.data.objects.new(part.name, mesh)
    obj.location = part.location
    factory._flat_shade(obj)
    factory._assign_material(obj, material)
    return obj


def _register_ellipsoid(
    context: factory.BuildContext,
    item: DetailedEllipsoidPart,
) -> None:
    factory._register(
        context,
        factory._ellipsoid(
            item.part.name,
            item.part.location,
            item.part.scale,
            context.materials[item.material_slot],
            segments=item.density.segments,
            rings=item.density.rings,
        ),
        "hair",
        "head",
    )


def replace_hair_with_reference_sweeps(context: factory.BuildContext) -> None:
    sweep = load_hair_sweep_profile_v08()
    detail = load_head_detail_profile_v08(context.config.character_id)
    _clear_old_hair()
    _apply_reference_palette(context)
    for part in sweep.meshes:
        factory._register(
            context,
            _sweep_mesh(part, context.materials["hair"]),
            "hair",
            "head",
        )
    for part in context.head.hair_front_locks + context.head.hair_side_locks:
        if part.name not in sweep.profile_accent_names:
            continue
        density = (
            detail.hair_secondary_density
            if max(part.scale) >= 0.16
            else detail.hair_tertiary_density
        )
        _register_ellipsoid(context, DetailedEllipsoidPart(part, "hair", density))
    for item in detail.hair_detail_masses:
        if item.part.name in sweep.detail_accent_names:
            _register_ellipsoid(context, item)
    for name, degrees in sweep.accent_rotations_degrees:
        obj = factory.bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Reference hair accent was not built: {name}")
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = tuple(math.radians(value) for value in degrees)
    factory.bpy.context.view_layer.update()
