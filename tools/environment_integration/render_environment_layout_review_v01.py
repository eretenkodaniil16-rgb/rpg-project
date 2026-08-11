#!/usr/bin/env python3
"""Render the data-driven guard-post layout for pixel-placement review.

This is not a replacement for the Godot runtime smoke test. It composites the
same approved modules at the exact runtime coordinates so wall anchors, partial
edges, deterministic floor variants, doors, and character scale can be reviewed
in environments where Godot is running with its dummy headless renderer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


TILE_SIZE = 64
ROOM_PARENT_GLOBAL = (245, 360)
VIEWPORT_SIZE = (1280, 720)


def floor_variant(x: int, y: int, seed: int) -> int:
    mixed = seed
    mixed = (mixed ^ (x * 73856093)) & 0x7FFFFFFF
    mixed = (mixed ^ (y * 19349663)) & 0x7FFFFFFF
    mixed = (mixed ^ (x * y * 83492791)) & 0x7FFFFFFF
    return mixed % 8


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def paste_centered(canvas: Image.Image, image: Image.Image, center: tuple[float, float]) -> None:
    x = round(center[0] - image.width * 0.5)
    y = round(center[1] - image.height * 0.5)
    canvas.alpha_composite(image, (x, y))


def global_point(local_x: float, local_y: float) -> tuple[float, float]:
    return ROOM_PARENT_GLOBAL[0] + local_x, ROOM_PARENT_GLOBAL[1] + local_y


def render(repo_root: Path, output_path: Path) -> None:
    config_path = repo_root / "data/environment/guard_post_environment_v01.json"
    config: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    module_root = repo_root / "assets/environment/approved/cold_ancient_stone_v01/modules"
    bounds = config["local_bounds"]
    left, top = (int(value) for value in bounds["position"])
    width, height = (int(value) for value in bounds["size"])
    seed = int(config["floor_seed"])
    columns = (width + TILE_SIZE - 1) // TILE_SIZE
    rows = (height + TILE_SIZE - 1) // TILE_SIZE

    canvas = Image.new("RGBA", VIEWPORT_SIZE, (9, 16, 25, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((45, 45, 1234, 674), fill=(19, 28, 39, 255))

    # Exact floor bounds, including the final 38×54 partial region.
    for y in range(rows):
        for x in range(columns):
            variant = floor_variant(x, y, seed) + 1
            tile = load_rgba(module_root / f"floors/cold_stone_floor_{variant:02d}.png")
            tile_width = min(TILE_SIZE, width - x * TILE_SIZE)
            tile_height = min(TILE_SIZE, height - y * TILE_SIZE)
            tile = tile.crop((0, 0, tile_width, tile_height))
            destination = global_point(left + x * TILE_SIZE, top + y * TILE_SIZE)
            canvas.alpha_composite(tile, (round(destination[0]), round(destination[1])))

    overlay_by_id = {
        path.stem: load_rgba(path) for path in (module_root / "overlays").glob("*.png")
    }
    for group in ("transitions", "decals"):
        for entry in config[group]:
            cell_x, cell_y = (int(value) for value in entry["cell"])
            destination = global_point(left + cell_x * TILE_SIZE, top + cell_y * TILE_SIZE)
            canvas.alpha_composite(
                overlay_by_id[entry["asset_id"]],
                (round(destination[0]), round(destination[1])),
            )

    wall_by_id = {
        path.stem: load_rgba(path) for path in (module_root / "walls").glob("*.png")
    }
    walls = config["walls"]
    room_left = float(walls["room_left"])
    room_right = float(walls["room_right"])
    room_top = float(walls["room_top"])
    room_bottom = float(walls["room_bottom"])
    full_columns = int((room_right - room_left) // TILE_SIZE)
    full_rows = int((room_bottom - room_top) // TILE_SIZE)

    for x in range(full_columns):
        center_x = room_left + x * TILE_SIZE + TILE_SIZE * 0.5
        paste_centered(canvas, wall_by_id["stone_wall_north"], global_point(center_x, room_top))
        paste_centered(canvas, wall_by_id["stone_wall_south"], global_point(center_x, room_bottom))
    horizontal_remainder = round(room_right - room_left) - full_columns * TILE_SIZE
    for asset_id, wall_y in (("stone_wall_north", room_top), ("stone_wall_south", room_bottom)):
        remainder = wall_by_id[asset_id].crop((0, 0, horizontal_remainder, 96))
        destination = global_point(room_left + full_columns * TILE_SIZE, wall_y - 48)
        canvas.alpha_composite(remainder, (round(destination[0]), round(destination[1])))

    for asset_id, wall_x in (("stone_wall_west", room_left), ("stone_wall_east", room_right)):
        for y in range(full_rows):
            paste_centered(
                canvas,
                wall_by_id[asset_id],
                global_point(wall_x, room_top + y * TILE_SIZE + TILE_SIZE * 0.5),
            )
        remainder_height = round(room_bottom - room_top) - full_rows * TILE_SIZE
        remainder = wall_by_id[asset_id].crop((0, 16, 64, 16 + remainder_height))
        destination = global_point(wall_x - 32, room_top + full_rows * TILE_SIZE)
        canvas.alpha_composite(remainder, (round(destination[0]), round(destination[1])))

    gap_top = float(walls["door_gap_top"])
    gap_bottom = float(walls["door_gap_bottom"])
    for index, partition_x_value in enumerate(walls["partition_x"]):
        partition_x = float(partition_x_value)
        asset_id = "stone_wall_east" if index == 0 else "stone_wall_west"
        center_y = room_top + TILE_SIZE * 0.5
        while center_y < gap_top:
            paste_centered(canvas, wall_by_id[asset_id], global_point(partition_x, center_y))
            center_y += TILE_SIZE
        center_y = gap_bottom + TILE_SIZE * 0.5
        while center_y + TILE_SIZE * 0.5 <= room_top + full_rows * TILE_SIZE:
            paste_centered(canvas, wall_by_id[asset_id], global_point(partition_x, center_y))
            center_y += TILE_SIZE
        remainder_height = round(room_bottom - room_top) - full_rows * TILE_SIZE
        remainder = wall_by_id["stone_wall_east"].crop((0, 16, 64, 16 + remainder_height))
        destination = global_point(partition_x - 32, room_top + full_rows * TILE_SIZE)
        canvas.alpha_composite(remainder, (round(destination[0]), round(destination[1])))

    corner_specs = [
        ("stone_wall_corner_nw", room_left, room_top),
        ("stone_wall_corner_ne", room_right, room_top),
        ("stone_wall_corner_sw", room_left, room_bottom),
        ("stone_wall_corner_se", room_right, room_bottom),
    ]
    for index, partition_x_value in enumerate(walls["partition_x"]):
        partition_x = float(partition_x_value)
        corner_specs.extend(
            [
                ("stone_wall_corner_ne" if index == 0 else "stone_wall_corner_nw", partition_x, room_top),
                ("stone_wall_corner_se" if index == 0 else "stone_wall_corner_sw", partition_x, room_bottom),
            ]
        )
    for asset_id, corner_x, corner_y in corner_specs:
        paste_centered(canvas, wall_by_id[asset_id], global_point(corner_x, corner_y))

    closed_door = load_rgba(module_root / "doors/stone_door_y_closed.png")
    for door_x in (-8.0, 632.0):
        for module_offset in (-32.0, 32.0):
            paste_centered(canvas, closed_door, global_point(door_x, 5.0 + module_offset))

    character_atlas = load_rgba(
        repo_root
        / "assets/characters/human/warrior_m01/gameplay/approved/atlases/human_warrior_m01_idle_v01.png"
    )
    character = character_atlas.crop((0, 0, 96, 96))
    paste_centered(canvas, character, (650.0, 360.0))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=False, compress_level=9)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/environment-integration-v01/guard_post_layout_review_v01.png"),
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    output_path = args.output if args.output.is_absolute() else repo_root / args.output
    render(repo_root, output_path)
    print(f"Environment layout review written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
