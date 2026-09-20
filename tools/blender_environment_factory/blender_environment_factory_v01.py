from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    import bpy
    from mathutils import Vector
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "Этот entrypoint запускается только встроенным Python Blender. "
        "Используйте RUN_BLENDER_ENVIRONMENT_FACTORY_V01.cmd или Blender --background."
    ) from exc

from environment_profile_v01 import AssetSpec, EnvironmentProfile, load_environment_profile
from geometry_plan_v01 import crack_segments, damp_spots, dust_spots, floor_blocks


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
ASSET_PROPERTY = "environment_asset_id"
KIND_PROPERTY = "environment_asset_kind"


@dataclass(frozen=True)
class RawArtifact:
    asset_id: str
    kind: str
    canvas_width: int
    canvas_height: int
    raw_width: int
    raw_height: int
    raw_path: Path
    anchor_x: int
    anchor_y: int


@dataclass
class BuildContext:
    profile: EnvironmentProfile
    materials: dict[int, bpy.types.Material]
    metal_material: bpy.types.Material
    wood_materials: tuple[bpy.types.Material, ...]
    arcane_materials: tuple[bpy.types.Material, ...]
    asset_collections: dict[str, bpy.types.Collection]
    camera: bpy.types.Object


def main() -> int:
    args = _parse_args(_script_arguments())
    repo_root = Path(args.repo_root).resolve()
    config_path = _resolve_cli_path(repo_root, args.config)
    profile = load_environment_profile(config_path, repo_root)
    profile.assert_blender_version(tuple(int(value) for value in bpy.app.version))

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError("run_id должен содержать только буквы, цифры, '.', '_' и '-'")
    run_dir = (profile.run_root / run_id).resolve()
    _assert_within(profile.run_root, run_dir, "run directory")
    run_dir.mkdir(parents=True, exist_ok=False)

    context = build_scene(profile)
    source_dir = run_dir / "source"
    source_dir.mkdir()
    blend_path = source_dir / f"{profile.profile_id}_source_v01.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    artifacts: list[RawArtifact] = []
    if args.mode == "all":
        artifacts = render_assets(context, run_dir)
        _show_only(context, profile.assets[0].asset_id)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    manifest_path = _write_raw_manifest(
        context=context,
        run_dir=run_dir,
        run_id=run_id,
        blend_path=blend_path,
        artifacts=artifacts,
    )
    print(f"BLENDER_ENVIRONMENT_FACTORY_RESULT={manifest_path}")
    return 0


def build_scene(profile: EnvironmentProfile) -> BuildContext:
    _clear_scene()
    scene = bpy.context.scene
    scene.name = f"{profile.profile_id}_environment_factory"
    scene["factory_schema_version"] = profile.schema_version
    scene["environment_profile_id"] = profile.profile_id
    scene["environment_stage"] = profile.stage
    scene["camera_elevation_degrees"] = profile.elevation_degrees
    scene["combat_cell_size_px"] = profile.tile_size
    scene["character_sprite_canvas_px"] = profile.character_sprite_canvas
    scene["runtime_filter"] = "NEAREST"
    scene["walls_and_doors_placement"] = "cell_edges"
    scene["local_light_baked_into_floor"] = False

    factory_root = _new_collection("ENVIRONMENT_FACTORY")
    render_collection = _new_collection("RENDER", factory_root)
    asset_root = _new_collection("ASSETS", factory_root)
    materials = {
        index: _create_palette_material(index, value)
        for index, value in enumerate(profile.palette_hex)
    }
    metal_material = _create_principled_material(
        "MAT_environment_dark_metal",
        profile.palette_hex[19],
        roughness=0.46,
        metallic=0.72,
    )
    wood_materials = (
        _create_principled_material(
            "MAT_environment_wood_dark", profile.palette_hex[16], roughness=0.88
        ),
        _create_principled_material(
            "MAT_environment_wood_mid", profile.palette_hex[17], roughness=0.84
        ),
        _create_principled_material(
            "MAT_environment_wood_light", profile.palette_hex[18], roughness=0.80
        ),
    )
    arcane_materials = (
        _create_emission_material("MAT_arcane_low", profile.palette_hex[21], 0.75),
        _create_emission_material("MAT_arcane_mid", profile.palette_hex[22], 1.15),
        _create_emission_material("MAT_arcane_high", profile.palette_hex[23], 1.55),
    )
    camera = _create_camera(profile, render_collection)
    _create_neutral_lights(profile, render_collection)

    context = BuildContext(
        profile=profile,
        materials=materials,
        metal_material=metal_material,
        wood_materials=wood_materials,
        arcane_materials=arcane_materials,
        asset_collections={},
        camera=camera,
    )
    for asset in profile.assets:
        collection = _new_collection(f"ASSET_{asset.asset_id}", asset_root)
        collection[ASSET_PROPERTY] = asset.asset_id
        collection[KIND_PROPERTY] = asset.kind
        collection.hide_render = True
        context.asset_collections[asset.asset_id] = collection
        _build_asset(context, asset, collection)

    _configure_render(scene, profile)
    _validate_scene(context)
    _show_only(context, profile.assets[0].asset_id)
    return context


def render_assets(context: BuildContext, run_dir: Path) -> list[RawArtifact]:
    raw_dir = run_dir / "raw"
    raw_dir.mkdir()
    artifacts: list[RawArtifact] = []
    scene = bpy.context.scene
    for asset in context.profile.assets:
        _show_only(context, asset.asset_id)
        _frame_camera(context, asset)
        raw_path = raw_dir / f"{asset.asset_id}_raw.png"
        scene.render.filepath = str(raw_path)
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        if not raw_path.is_file():
            raise RuntimeError(f"Blender не создал raw render: {raw_path}")
        anchor_x, anchor_y = _asset_anchor(asset)
        artifacts.append(
            RawArtifact(
                asset_id=asset.asset_id,
                kind=asset.kind,
                canvas_width=asset.canvas_width,
                canvas_height=asset.canvas_height,
                raw_width=asset.canvas_width * context.profile.raw_render_scale,
                raw_height=asset.canvas_height * context.profile.raw_render_scale,
                raw_path=raw_path,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
            )
        )
    return artifacts


def _build_asset(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    if asset.kind == "floor":
        _build_floor(context, asset, collection)
    elif asset.kind == "decal":
        _build_decal(context, asset, collection)
    elif asset.kind == "transition":
        _build_damp_transition(context, asset, collection)
    elif asset.kind == "wall_edge":
        _build_wall_edge(context, asset, collection)
    elif asset.kind == "wall_corner":
        _build_wall_corner(context, asset, collection)
    elif asset.kind == "door":
        _build_door(context, asset, collection)
    elif asset.kind == "stairs":
        _build_stairs(context, asset, collection)
    elif asset.kind == "arcane":
        _build_arcane_inlay(context, asset, collection)
    else:
        raise ValueError(f"Неподдерживаемый asset kind: {asset.kind}")


def _build_floor(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    tile_width, tile_depth = _floor_world_size(context.profile)
    _box(
        collection,
        f"{asset.asset_id}_mortar",
        (0.0, 0.0, -0.055),
        (tile_width * 3.0, tile_depth * 3.0, 0.10),
        context.materials[1],
        bevel=0.0,
        asset=asset,
    )
    blocks = floor_blocks(asset)
    for repeat_y in (-1, 0, 1):
        for repeat_x in (-1, 0, 1):
            for index, block in enumerate(blocks):
                height = block.height * tile_width
                _box(
                    collection,
                    f"{asset.asset_id}_r{repeat_y + 1}{repeat_x + 1}_stone_{index:02d}",
                    (
                        (repeat_x + block.center_x) * tile_width,
                        (repeat_y + block.center_y) * tile_depth,
                        height * 0.5,
                    ),
                    (
                        block.width * tile_width,
                        block.depth * tile_depth,
                        height,
                    ),
                    context.materials[block.tone_index],
                    bevel=block.bevel * tile_width,
                    asset=asset,
                )
    _add_floor_wear(context, asset, collection, tile_width, tile_depth)


def _add_floor_wear(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
    tile_width: float,
    tile_depth: float,
) -> None:
    # Variation remains inside the tile core. Shared borders are finalized by the
    # postprocessor so all eight variants can be scattered in any order.
    wear_count = 2 + asset.seed % 3
    for index in range(wear_count):
        angle = _stable_unit(asset.seed, index * 3) * math.tau
        radius = 0.22 + _stable_unit(asset.seed, index * 3 + 1) * 0.72
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius * tile_depth / tile_width
        _flattened_sphere(
            collection,
            f"{asset.asset_id}_wear_{index:02d}",
            (x, y, 0.39),
            (0.055, 0.035, 0.012),
            context.materials[2 + index % 2],
            asset,
            segments=8,
        )


def _build_decal(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    tile_width, tile_depth = _floor_world_size(context.profile)
    if asset.shape == "crack":
        for index, segment in enumerate(crack_segments(asset)):
            _curve_segment(
                collection,
                f"{asset.asset_id}_segment_{index:02d}",
                (
                    segment.start_x * tile_width,
                    segment.start_y * tile_depth,
                    0.025,
                ),
                (
                    segment.end_x * tile_width,
                    segment.end_y * tile_depth,
                    0.025,
                ),
                max(0.012, segment.width * tile_width),
                context.materials[segment.tone_index],
                asset,
            )
    elif asset.shape == "dust":
        for index, spot in enumerate(dust_spots(asset)):
            _flattened_sphere(
                collection,
                f"{asset.asset_id}_spot_{index:02d}",
                (
                    spot.center_x * tile_width,
                    spot.center_y * tile_depth,
                    0.025,
                ),
                (
                    spot.radius_x * tile_width,
                    spot.radius_y * tile_depth,
                    0.012,
                ),
                context.materials[spot.tone_index],
                asset,
                segments=6,
            )
    elif asset.shape == "damp":
        _add_damp_spots(context, asset, collection, count=14)
    else:
        raise ValueError(f"Неизвестный decal shape: {asset.shape}")


def _build_damp_transition(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    _add_damp_spots(context, asset, collection, count=18)


def _add_damp_spots(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
    count: int,
) -> None:
    tile_width, tile_depth = _floor_world_size(context.profile)
    for index, spot in enumerate(damp_spots(asset, count=count)):
        _flattened_sphere(
            collection,
            f"{asset.asset_id}_damp_{index:02d}",
            (
                spot.center_x * tile_width,
                spot.center_y * tile_depth,
                0.022 + index * 0.0002,
            ),
            (
                spot.radius_x * tile_width,
                spot.radius_y * tile_depth,
                0.010,
            ),
            context.materials[spot.tone_index],
            asset,
            segments=10,
        )


def _build_wall_edge(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    angle = _edge_angle(asset.orientation)
    _wall_segment(context, asset, collection, angle=angle, center=(0.0, 0.0))


def _build_wall_corner(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    angle_pairs = {
        "north_east": (0.0, math.pi * 0.5),
        "south_east": (math.pi, math.pi * 0.5),
        "south_west": (math.pi, -math.pi * 0.5),
        "north_west": (0.0, -math.pi * 0.5),
    }
    if asset.orientation not in angle_pairs:
        raise ValueError(f"Некорректная ориентация угла: {asset.orientation}")
    for segment_index, angle in enumerate(angle_pairs[asset.orientation]):
        tangent = Vector((math.cos(angle), math.sin(angle)))
        center = tangent * 0.92
        _wall_segment(
            context,
            asset,
            collection,
            angle=angle,
            center=(float(center.x), float(center.y)),
            screen_length=2.3,
            name_suffix=f"corner_{segment_index}",
        )
    _cylinder(
        collection,
        f"{asset.asset_id}_corner_cap",
        (0.0, 0.0, 1.18),
        radius=0.44,
        depth=2.36,
        vertices=8,
        material=context.materials[7],
        asset=asset,
    )


def _wall_segment(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
    angle: float,
    center: tuple[float, float],
    screen_length: float = 4.0,
    name_suffix: str = "edge",
) -> None:
    elevation = math.radians(context.profile.elevation_degrees)
    projection_factor = math.sqrt(
        math.cos(angle) ** 2 + (math.sin(angle) * math.sin(elevation)) ** 2
    )
    world_length = screen_length / max(projection_factor, 0.01)
    tangent = Vector((math.cos(angle), math.sin(angle)))
    block_count = 4
    row_count = 3
    block_length = world_length / block_count
    wall_height = 2.30
    row_height = wall_height / row_count
    for row in range(row_count):
        row_shift = (block_length * 0.5) if row % 2 else 0.0
        for column in range(block_count):
            along = -world_length * 0.5 + block_length * (column + 0.5) + row_shift
            if along > world_length * 0.5:
                along -= world_length
            location_xy = Vector(center) + tangent * along
            tone = 4 + ((asset.seed + row * 3 + column) % 5)
            _box(
                collection,
                f"{asset.asset_id}_{name_suffix}_r{row}_c{column}",
                (float(location_xy.x), float(location_xy.y), row_height * (row + 0.5)),
                (block_length - 0.055, 0.44, row_height - 0.045),
                context.materials[tone],
                bevel=0.045,
                asset=asset,
                rotation_z=angle,
            )
    _box(
        collection,
        f"{asset.asset_id}_{name_suffix}_cap",
        (center[0], center[1], wall_height + 0.075),
        (world_length + 0.08, 0.52, 0.15),
        context.materials[8],
        bevel=0.035,
        asset=asset,
        rotation_z=angle,
    )


def _build_door(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    angle = 0.0 if asset.orientation == "x" else math.pi * 0.5
    tangent = Vector((math.cos(angle), math.sin(angle)))
    normal = Vector((-math.sin(angle), math.cos(angle)))
    opening_width = 2.65
    post_offset = tangent * (opening_width * 0.5 + 0.25)
    for index, sign in enumerate((-1.0, 1.0)):
        position = post_offset * sign
        _box(
            collection,
            f"{asset.asset_id}_frame_post_{index}",
            (float(position.x), float(position.y), 1.20),
            (0.46, 0.54, 2.40),
            context.materials[7],
            bevel=0.055,
            asset=asset,
            rotation_z=angle,
        )
    _box(
        collection,
        f"{asset.asset_id}_frame_lintel",
        (0.0, 0.0, 2.48),
        (opening_width + 0.95, 0.60, 0.42),
        context.materials[8],
        bevel=0.055,
        asset=asset,
        rotation_z=angle,
    )

    hinge = -post_offset + tangent * 0.24
    leaf_angle = angle
    leaf_tangent = tangent
    if asset.state == "open":
        leaf_angle += math.radians(72.0)
        leaf_tangent = Vector((math.cos(leaf_angle), math.sin(leaf_angle)))
    leaf_center = hinge + leaf_tangent * (opening_width * 0.48)
    _box(
        collection,
        f"{asset.asset_id}_leaf",
        (float(leaf_center.x), float(leaf_center.y), 1.22),
        (opening_width * 0.96, 0.18, 2.24),
        context.wood_materials[1],
        bevel=0.025,
        asset=asset,
        rotation_z=leaf_angle,
    )
    for band_index, band_height in enumerate((0.55, 1.18, 1.82)):
        band_center = hinge + leaf_tangent * (opening_width * 0.48) + normal * 0.01
        _box(
            collection,
            f"{asset.asset_id}_iron_band_{band_index}",
            (float(band_center.x), float(band_center.y), band_height),
            (opening_width * 0.92, 0.22, 0.10),
            context.metal_material,
            bevel=0.015,
            asset=asset,
            rotation_z=leaf_angle,
        )


def _build_stairs(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    tile_width, tile_depth = _floor_world_size(context.profile)
    step_count = 6
    step_depth = tile_depth / step_count
    for index in range(step_count):
        height = 0.18 + (step_count - index - 1) * 0.18
        y = -tile_depth * 0.5 + step_depth * (index + 0.5)
        _box(
            collection,
            f"{asset.asset_id}_step_{index:02d}",
            (0.0, y, height * 0.5),
            (tile_width * 0.88, step_depth - 0.04, height),
            context.materials[4 + index % 4],
            bevel=0.035,
            asset=asset,
        )
    for side in (-1.0, 1.0):
        _box(
            collection,
            f"{asset.asset_id}_side_{'l' if side < 0 else 'r'}",
            (side * tile_width * 0.47, 0.0, 0.58),
            (0.20, tile_depth, 1.16),
            context.materials[3],
            bevel=0.025,
            asset=asset,
        )


def _build_arcane_inlay(
    context: BuildContext,
    asset: AssetSpec,
    collection: bpy.types.Collection,
) -> None:
    tile_width, tile_depth = _floor_world_size(context.profile)
    variant = 0 if asset.asset_id.endswith("01") else 1
    radii = (0.28, 0.39) if variant == 0 else (0.22, 0.36)
    for ring_index, radius in enumerate(radii):
        points: list[tuple[float, float, float]] = []
        segments = 24
        for index in range(segments + 1):
            angle = math.tau * index / segments
            points.append(
                (
                    math.cos(angle) * radius * tile_width,
                    math.sin(angle) * radius * tile_depth,
                    0.028 + ring_index * 0.002,
                )
            )
        _poly_curve(
            collection,
            f"{asset.asset_id}_ring_{ring_index}",
            points,
            0.035,
            context.arcane_materials[ring_index + 1],
            asset,
        )
    spoke_count = 4 if variant == 0 else 6
    for index in range(spoke_count):
        angle = math.tau * index / spoke_count + variant * math.pi / 6.0
        start = (
            math.cos(angle) * tile_width * 0.08,
            math.sin(angle) * tile_depth * 0.08,
            0.032,
        )
        end = (
            math.cos(angle) * tile_width * 0.31,
            math.sin(angle) * tile_depth * 0.31,
            0.032,
        )
        _curve_segment(
            collection,
            f"{asset.asset_id}_spoke_{index}",
            start,
            end,
            0.038,
            context.arcane_materials[index % 2 + 1],
            asset,
        )


def _create_camera(
    profile: EnvironmentProfile,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new("CAM_environment_gameplay_ortho")
    camera = bpy.data.objects.new("CAM_environment_gameplay_ortho", camera_data)
    collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.lens = 50.0
    camera["projection_contract"] = "top_down_3_4"
    camera["elevation_degrees"] = profile.elevation_degrees
    bpy.context.scene.camera = camera
    return camera


def _frame_camera(context: BuildContext, asset: AssetSpec) -> None:
    scene = bpy.context.scene
    profile = context.profile
    scale = profile.raw_render_scale
    scene.render.resolution_x = asset.canvas_width * scale
    scene.render.resolution_y = asset.canvas_height * scale
    view_height = (
        profile.floor_view_height
        if asset.canvas_height == profile.tile_size
        else profile.object_view_height
    )
    context.camera.data.ortho_scale = view_height
    target_height = 0.02 if asset.kind in {"floor", "decal", "transition", "arcane"} else 1.02
    distance = float(profile.payload["camera"]["horizontal_distance_units"])
    elevation = math.radians(profile.elevation_degrees)
    context.camera.location = (
        0.0,
        -distance,
        target_height + math.tan(elevation) * distance,
    )
    target = Vector((0.0, 0.0, target_height))
    context.camera.rotation_euler = (
        target - context.camera.location
    ).to_track_quat("-Z", "Y").to_euler()


def _create_neutral_lights(
    profile: EnvironmentProfile,
    collection: bpy.types.Collection,
) -> None:
    lighting = profile.payload["lighting"]
    key = _new_light(
        "LGT_environment_key",
        "AREA",
        (-5.5, -7.0, 12.0),
        float(lighting["key_energy"]),
        7.0,
        collection,
    )
    key.data.color = (0.88, 0.94, 1.0)
    key.rotation_euler = _look_at_rotation(key.location, (0.0, 0.0, 0.5))
    fill = _new_light(
        "LGT_environment_fill",
        "AREA",
        (6.0, -2.5, 8.0),
        float(lighting["fill_energy"]),
        6.0,
        collection,
    )
    fill.data.color = (0.78, 0.86, 0.94)
    fill.rotation_euler = _look_at_rotation(fill.location, (0.0, 0.0, 0.7))
    rim = _new_light(
        "LGT_environment_rim",
        "AREA",
        (0.0, 6.0, 9.0),
        float(lighting["rim_energy"]),
        5.0,
        collection,
    )
    rim.data.color = (0.68, 0.78, 0.88)
    rim.rotation_euler = _look_at_rotation(rim.location, (0.0, 0.0, 0.9))


def _configure_render(scene: bpy.types.Scene, profile: EnvironmentProfile) -> None:
    engines = {
        item.identifier
        for item in scene.render.bl_rna.properties["engine"].enum_items
    }
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engines:
        scene.render.engine = "BLENDER_EEVEE"
    elif "BLENDER_WORKBENCH" in engines:
        scene.render.engine = "BLENDER_WORKBENCH"
    else:
        raise RuntimeError(f"Нет поддерживаемого realtime render engine: {sorted(engines)}")
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = bool(
        profile.payload["camera"]["transparent_background"]
    )
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.render.use_file_extension = True
    scene.render.fps = 1
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    world = bpy.data.worlds.new("WORLD_environment_factory")
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.025, 0.035, 0.048, 1.0)
        background.inputs["Strength"].default_value = float(
            profile.payload["lighting"]["world_strength"]
        )
    scene.world = world


def _validate_scene(context: BuildContext) -> None:
    profile = context.profile
    if set(context.asset_collections) != {asset.asset_id for asset in profile.assets}:
        raise RuntimeError("Blender scene asset collections не совпадают с profile")
    for asset in profile.assets:
        collection = context.asset_collections[asset.asset_id]
        if len(collection.all_objects) == 0:
            raise RuntimeError(f"Пустая asset collection: {asset.asset_id}")
        for obj in collection.all_objects:
            if obj.get(ASSET_PROPERTY) != asset.asset_id:
                raise RuntimeError(f"Object без стабильного asset_id: {obj.name}")
            if asset.is_edge_object and obj.get("placement_contract") != "cell_edge":
                raise RuntimeError(f"Edge object без cell_edge contract: {obj.name}")
    if context.camera.data.type != "ORTHO":
        raise RuntimeError("Environment camera должна быть ORTHO")
    if bool(bpy.context.scene["local_light_baked_into_floor"]):
        raise RuntimeError("Локальный свет ошибочно помечен как запечённый")


def _show_only(context: BuildContext, asset_id: str) -> None:
    if asset_id not in context.asset_collections:
        raise KeyError(asset_id)
    for current_id, collection in context.asset_collections.items():
        collection.hide_render = current_id != asset_id


def _asset_anchor(asset: AssetSpec) -> tuple[int, int]:
    if asset.kind == "stairs":
        return asset.canvas_width // 2, asset.canvas_height - 8
    return asset.canvas_width // 2, asset.canvas_height // 2


def _floor_world_size(profile: EnvironmentProfile) -> tuple[float, float]:
    width = profile.floor_view_height
    elevation = math.radians(profile.elevation_degrees)
    depth = width / math.sin(elevation)
    return width, depth


def _edge_angle(orientation: str) -> float:
    angles = {
        "north": 0.0,
        "east": math.pi * 0.5,
        "south": math.pi,
        "west": -math.pi * 0.5,
    }
    if orientation not in angles:
        raise ValueError(f"Некорректная edge orientation: {orientation}")
    return angles[orientation]


def _box(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    dimensions: tuple[float, float, float],
    material: bpy.types.Material,
    bevel: float,
    asset: AssetSpec,
    rotation_z: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_euler[2] = rotation_z
    _move_to_collection(obj, collection)
    obj.data.materials.append(material)
    if bevel > 0.0:
        modifier = obj.modifiers.new("pixel_bevel", "BEVEL")
        modifier.width = min(bevel, min(dimensions) * 0.35)
        modifier.segments = 1
    _tag_asset_object(obj, asset)
    return obj


def _flattened_sphere(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    asset: AssetSpec,
    segments: int,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=max(4, segments // 2),
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _move_to_collection(obj, collection)
    obj.data.materials.append(material)
    _tag_asset_object(obj, asset)
    return obj


def _cylinder(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    vertices: int,
    material: bpy.types.Material,
    asset: AssetSpec,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    _move_to_collection(obj, collection)
    obj.data.materials.append(material)
    _tag_asset_object(obj, asset)
    return obj


def _curve_segment(
    collection: bpy.types.Collection,
    name: str,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    width: float,
    material: bpy.types.Material,
    asset: AssetSpec,
) -> bpy.types.Object:
    return _poly_curve(collection, name, [start, end], width, material, asset)


def _poly_curve(
    collection: bpy.types.Collection,
    name: str,
    points: list[tuple[float, float, float]],
    width: float,
    material: bpy.types.Material,
    asset: AssetSpec,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = width
    curve.bevel_resolution = 0
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, value in zip(spline.points, points):
        point.co = (*value, 1.0)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    curve.materials.append(material)
    _tag_asset_object(obj, asset)
    return obj


def _tag_asset_object(obj: bpy.types.Object, asset: AssetSpec) -> None:
    obj[ASSET_PROPERTY] = asset.asset_id
    obj[KIND_PROPERTY] = asset.kind
    obj["source_seed"] = asset.seed
    if asset.is_edge_object:
        obj["placement_contract"] = "cell_edge"


def _move_to_collection(
    obj: bpy.types.Object,
    collection: bpy.types.Collection,
) -> None:
    for current in tuple(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def _create_palette_material(index: int, color_hex: str) -> bpy.types.Material:
    return _create_principled_material(
        f"MAT_environment_palette_{index:02d}",
        color_hex,
        roughness=0.76 + (index % 3) * 0.055,
        metallic=0.0,
    )


def _create_principled_material(
    name: str,
    color_hex: str,
    roughness: float,
    metallic: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*_hex_to_linear_rgb(color_hex), 1.0)
    node = material.node_tree.nodes.get("Principled BSDF")
    if node is not None:
        base = node.inputs.get("Base Color")
        if base is not None:
            base.default_value = (*_hex_to_linear_rgb(color_hex), 1.0)
        rough = node.inputs.get("Roughness")
        if rough is not None:
            rough.default_value = roughness
        metal = node.inputs.get("Metallic")
        if metal is not None:
            metal.default_value = metallic
    return material


def _create_emission_material(
    name: str,
    color_hex: str,
    strength: float,
) -> bpy.types.Material:
    material = _create_principled_material(name, color_hex, roughness=0.35)
    node = material.node_tree.nodes.get("Principled BSDF")
    if node is not None:
        emission = node.inputs.get("Emission Color")
        if emission is None:
            emission = node.inputs.get("Emission")
        if emission is not None:
            emission.default_value = (*_hex_to_linear_rgb(color_hex), 1.0)
        emission_strength = node.inputs.get("Emission Strength")
        if emission_strength is not None:
            emission_strength.default_value = strength
    material["no_light_spill"] = True
    return material


def _new_light(
    name: str,
    light_type: str,
    location: tuple[float, float, float],
    energy: float,
    size: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    data = bpy.data.lights.new(name, type=light_type)
    data.energy = energy
    if hasattr(data, "shape"):
        data.shape = "DISK"
    if hasattr(data, "size"):
        data.size = size
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    obj["lighting_contract"] = "neutral_studio_no_local_bake"
    collection.objects.link(obj)
    return obj


def _look_at_rotation(
    location: Vector | tuple[float, float, float],
    target: tuple[float, float, float],
) -> Any:
    return (Vector(target) - Vector(location)).to_track_quat("-Z", "Y").to_euler()


def _new_collection(
    name: str,
    parent: bpy.types.Collection | None = None,
) -> bpy.types.Collection:
    collection = bpy.data.collections.new(name)
    if parent is None:
        bpy.context.scene.collection.children.link(collection)
    else:
        parent.children.link(collection)
    return collection


def _clear_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in tuple(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def _write_raw_manifest(
    context: BuildContext,
    run_dir: Path,
    run_id: str,
    blend_path: Path,
    artifacts: list[RawArtifact],
) -> Path:
    profile = context.profile
    payload = {
        "schema_version": 1,
        "factory_id": "blender_environment_factory_v01",
        "profile_id": profile.profile_id,
        "profile_sha256": profile.profile_sha256,
        "stage": profile.stage,
        "run_id": run_id,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "blender_version": bpy.app.version_string,
        "source_blend": blend_path.relative_to(run_dir).as_posix(),
        "camera": {
            "projection": "ORTHOGRAPHIC",
            "elevation_degrees": profile.elevation_degrees,
            "raw_render_scale": profile.raw_render_scale,
        },
        "game_contract": profile.payload["game_contract"],
        "lighting_contract": {
            "neutral_only": True,
            "local_light_baked_into_floor": False,
            "arcane_emission_has_light_spill": False,
        },
        "artifacts": [
            {
                "asset_id": artifact.asset_id,
                "kind": artifact.kind,
                "canvas": [artifact.canvas_width, artifact.canvas_height],
                "raw_canvas": [artifact.raw_width, artifact.raw_height],
                "raw_path": artifact.raw_path.relative_to(run_dir).as_posix(),
                "anchor": [artifact.anchor_x, artifact.anchor_y],
            }
            for artifact in artifacts
        ],
    }
    manifest_path = run_dir / "raw_manifest.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _hex_to_linear_rgb(value: str) -> tuple[float, float, float]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValueError(value)
    srgb = tuple(int(value[index : index + 2], 16) / 255.0 for index in (1, 3, 5))
    return tuple(
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in srgb
    )


def _stable_unit(seed: int, channel: int) -> float:
    value = math.sin(seed * 12.9898 + channel * 78.233) * 43758.5453
    return value - math.floor(value)


def _resolve_cli_path(repo_root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()


def _assert_within(parent: Path, child: Path, label: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} выходит за разрешённый root: {child}") from exc


def _script_arguments() -> list[str]:
    return sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []


def _parse_args(values: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Blender Environment Factory v01")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument(
        "--config",
        default="tools/blender_environment_factory/configs/cold_ancient_stone_v01.json",
    )
    parser.add_argument("--run-id")
    parser.add_argument("--mode", choices=("build", "all"), default="all")
    return parser.parse_args(values)


if __name__ == "__main__":
    raise SystemExit(main())
