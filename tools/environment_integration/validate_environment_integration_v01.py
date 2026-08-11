#!/usr/bin/env python3
"""Static contract validation for Godot Environment Integration v01."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = REPO_ROOT / "assets/environment/approved/cold_ancient_stone_v01"
MANIFEST_PATH = ASSET_ROOT / "cold_ancient_stone_v01.approved.json"
LAYOUT_PATH = REPO_ROOT / "data/environment/guard_post_environment_v01.json"
TILE_SET_PATH = ASSET_ROOT / "tilesets/cold_ancient_stone_v01.tres"
GAME_SCENE_PATH = REPO_ROOT / "scenes/game/game.tscn"
EXPECTED_PROFILE_SHA256 = "a589602410f3cdaac775ee3e690d701c24926e1754b847aec3161af0e4edffb9"
MAX_RUNTIME_ASSET_BYTES = 2 * 1024 * 1024


def fail(message: str) -> None:
    raise ValueError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Cannot read JSON {path.relative_to(REPO_ROOT)}: {error}")
    if not isinstance(value, dict):
        fail(f"JSON root must be an object: {path.relative_to(REPO_ROOT)}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        fail(f"Invalid PNG header: {path.relative_to(REPO_ROOT)}")
    return struct.unpack(">II", header[16:24])


def validate_manifest() -> tuple[dict[str, Any], int]:
    manifest = read_json(MANIFEST_PATH)
    if manifest.get("schema_version") != 1:
        fail("Approved manifest schema_version must be 1")
    if manifest.get("visual_id") != "cold_ancient_stone_v01":
        fail("Approved manifest visual_id is invalid")
    if manifest.get("stage") != "approved_runtime_asset":
        fail("Approved manifest stage is invalid")
    source = manifest.get("source", {})
    if not isinstance(source, dict) or source.get("profile_sha256") != EXPECTED_PROFILE_SHA256:
        fail("Approved manifest does not reference the accepted Blender profile")
    approval = manifest.get("approval", {})
    if not isinstance(approval, dict) or not approval.get("approved") or not approval.get("runtime_integrated"):
        fail("Approved manifest does not declare manual approval and runtime integration")

    modules = manifest.get("modules", [])
    atlases = manifest.get("atlases", {})
    if not isinstance(modules, list) or len(modules) != 33:
        fail(f"Expected 33 approved modules, got {len(modules) if isinstance(modules, list) else 'invalid'}")
    if not isinstance(atlases, dict) or len(atlases) != 6:
        fail(f"Expected six atlases, got {len(atlases) if isinstance(atlases, dict) else 'invalid'}")

    seen_asset_ids: set[str] = set()
    total_bytes = 0
    for item in modules:
        if not isinstance(item, dict):
            fail("Manifest module entry must be an object")
        asset_id = str(item.get("asset_id", ""))
        if not asset_id or asset_id in seen_asset_ids:
            fail(f"Invalid or duplicate module asset_id: {asset_id!r}")
        seen_asset_ids.add(asset_id)
        path = ASSET_ROOT / str(item.get("path", ""))
        if not path.is_file():
            fail(f"Approved module is missing: {path.relative_to(REPO_ROOT)}")
        if sha256(path) != item.get("sha256"):
            fail(f"Approved module hash mismatch: {asset_id}")
        expected_canvas = tuple(int(value) for value in item.get("canvas", []))
        if png_dimensions(path) != expected_canvas:
            fail(f"Approved module size mismatch: {asset_id}")
        total_bytes += path.stat().st_size

    for atlas_name, item in atlases.items():
        if not isinstance(item, dict):
            fail(f"Atlas entry must be an object: {atlas_name}")
        path = ASSET_ROOT / str(item.get("path", ""))
        if not path.is_file():
            fail(f"Atlas is missing: {path.relative_to(REPO_ROOT)}")
        if sha256(path) != item.get("sha256"):
            fail(f"Atlas hash mismatch: {atlas_name}")
        expected_size = tuple(int(value) for value in item.get("atlas_size", []))
        if png_dimensions(path) != expected_size:
            fail(f"Atlas size mismatch: {atlas_name}")
        coordinates = item.get("coordinates", {})
        if not isinstance(coordinates, dict) or not coordinates:
            fail(f"Atlas has no stable coordinate map: {atlas_name}")
        if any(asset_id not in seen_asset_ids for asset_id in coordinates):
            fail(f"Atlas references an unknown asset_id: {atlas_name}")
        total_bytes += path.stat().st_size

    if total_bytes > MAX_RUNTIME_ASSET_BYTES:
        fail(f"Runtime environment PNG budget exceeded: {total_bytes} bytes")
    return manifest, total_bytes


def validate_layout() -> None:
    layout = read_json(LAYOUT_PATH)
    if layout.get("schema_version") != 1 or layout.get("visual_id") != "guard_post_cold_ancient_stone_v01":
        fail("Guard-post environment layout identity is invalid")
    if layout.get("tile_size") != 64 or layout.get("floor_seed") != 1729:
        fail("Guard-post tile size or deterministic seed changed")
    bounds = layout.get("local_bounds", {})
    if not isinstance(bounds, dict) or bounds.get("position") != [-200, -315] or bounds.get("size") != [1190, 630]:
        fail("Guard-post visual bounds no longer match mechanical room bounds")
    columns = 19
    rows = 10
    for group in ("transitions", "decals"):
        entries = layout.get(group, [])
        if not isinstance(entries, list):
            fail(f"Layout {group} must be an array")
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("cell"), list):
                fail(f"Invalid {group} entry")
            cell = entry["cell"]
            if len(cell) != 2 or not (0 <= int(cell[0]) < columns and 0 <= int(cell[1]) < rows):
                fail(f"Out-of-bounds {group} cell: {cell}")
    walls = layout.get("walls", {})
    if not isinstance(walls, dict):
        fail("Layout walls must be an object")
    if walls.get("partition_x") != [-8, 632] or walls.get("door_gap_top") != -59 or walls.get("door_gap_bottom") != 69:
        fail("Visual walls or doors no longer match cell-edge mechanics")
    doors = layout.get("doors", {})
    if doors != {"west_service_door": "y", "inner_watch_gate": "y"}:
        fail("Door orientation mapping is invalid")


def validate_tileset_and_scene() -> None:
    manifest = read_json(MANIFEST_PATH)
    tile_set_contract = manifest.get("tile_set_contract", {})
    expected_contract = {
        "path": "tilesets/cold_ancient_stone_v01.tres",
        "tile_size": [64, 64],
        "source_ids": [0, 1, 2, 3, 4, 5],
        "custom_data_layer": "visual_id",
        "texture_filter": "nearest",
        "collision_enabled": False,
        "navigation_enabled": False,
    }
    if tile_set_contract != expected_contract:
        fail("Approved manifest TileSet contract is invalid")
    if not TILE_SET_PATH.is_file():
        fail("Godot TileSet resource is missing")
    text = TILE_SET_PATH.read_text(encoding="utf-8")
    for source_id in range(6):
        if f"sources/{source_id} =" not in text:
            fail(f"TileSet source {source_id} is missing")
    if "tile_size = Vector2i(64, 64)" not in text:
        fail("TileSet tile_size must remain 64×64")
    required_visual_ids = [
        "cold_stone_floor_01",
        "stone_crack_01",
        "stone_wall_north",
        "stone_wall_corner_ne",
        "stone_door_x_closed",
        "stone_stairs_down_01",
    ]
    for visual_id in required_visual_ids:
        if f'custom_data_0 = "{visual_id}"' not in text:
            fail(f"TileSet visual_id metadata is missing: {visual_id}")
    scene_text = GAME_SCENE_PATH.read_text(encoding="utf-8")
    if "res://scripts/game/guard_post_environment_integration.gd" not in scene_text:
        fail("Production game scene does not use the environment integration subclass")


def main() -> int:
    _, total_bytes = validate_manifest()
    validate_layout()
    validate_tileset_and_scene()
    print(
        "Godot Environment Integration v01 static validation passed: "
        f"33 modules, 6 atlases, 6 TileSet sources, {total_bytes} PNG bytes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
