#!/usr/bin/env python3
"""Promote an approved Blender environment run into Godot-ready atlases.

The review run itself stays ignored. This tool validates the immutable profile
and artifact hashes, copies only approved normalized PNGs, builds deterministic
atlases, and writes a provenance manifest beside the runtime assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image


EXPECTED_PROFILE_ID = "cold_ancient_stone_v01"
EXPECTED_PROFILE_SHA256 = "a589602410f3cdaac775ee3e690d701c24926e1754b847aec3161af0e4edffb9"
EXPECTED_ASSET_COUNT = 33

ATLAS_GROUPS: dict[str, tuple[tuple[int, int], list[str]]] = {
    "cold_stone_floor_atlas_v01.png": (
        (64, 64),
        [f"cold_stone_floor_{index:02d}" for index in range(1, 9)],
    ),
    "cold_stone_overlay_atlas_v01.png": (
        (64, 64),
        [
            "stone_crack_01",
            "stone_crack_02",
            "stone_dust_01",
            "stone_dust_02",
            "stone_damp_01",
            "stone_damp_02",
            "dry_to_damp_north",
            "dry_to_damp_east",
            "dry_to_damp_south",
            "dry_to_damp_west",
            "arcane_inlay_01",
            "arcane_inlay_02",
        ],
    ),
    "cold_stone_wall_edge_atlas_v01.png": (
        (64, 96),
        [
            "stone_wall_north",
            "stone_wall_east",
            "stone_wall_south",
            "stone_wall_west",
        ],
    ),
    "cold_stone_wall_corner_atlas_v01.png": (
        (96, 96),
        [
            "stone_wall_corner_ne",
            "stone_wall_corner_se",
            "stone_wall_corner_sw",
            "stone_wall_corner_nw",
        ],
    ),
    "cold_stone_door_atlas_v01.png": (
        (64, 96),
        [
            "stone_door_x_closed",
            "stone_door_x_open",
            "stone_door_y_closed",
            "stone_door_y_open",
        ],
    ),
    "cold_stone_structure_atlas_v01.png": (
        (64, 96),
        ["stone_stairs_down_01"],
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_run(run_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest_path = run_root / "run_manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"Run manifest not found: {manifest_path}")
    manifest = read_json(manifest_path)
    if manifest.get("profile_id") != EXPECTED_PROFILE_ID:
        raise ValueError(f"Unexpected profile_id: {manifest.get('profile_id')!r}")
    if manifest.get("profile_sha256") != EXPECTED_PROFILE_SHA256:
        raise ValueError("The review run does not match the approved profile SHA-256")
    artifacts = manifest.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) != EXPECTED_ASSET_COUNT:
        raise ValueError(f"Expected {EXPECTED_ASSET_COUNT} artifacts, got {len(artifacts)}")

    by_id: dict[str, dict[str, Any]] = {}
    for artifact in artifacts:
        asset_id = str(artifact.get("asset_id", ""))
        relative_path = Path(str(artifact.get("path", "")))
        source = run_root / relative_path
        if not asset_id or asset_id in by_id:
            raise ValueError(f"Invalid or duplicate asset_id: {asset_id!r}")
        if not source.is_file():
            raise ValueError(f"Missing normalized artifact: {source}")
        if sha256(source) != artifact.get("sha256"):
            raise ValueError(f"Artifact hash mismatch: {asset_id}")
        with Image.open(source) as image:
            expected_size = tuple(int(value) for value in artifact.get("canvas", []))
            if image.mode != "RGBA" or image.size != expected_size:
                raise ValueError(
                    f"Invalid image contract for {asset_id}: {image.mode} {image.size}, "
                    f"expected RGBA {expected_size}"
                )
        by_id[asset_id] = artifact
    return manifest, by_id


def copy_modules(
    run_root: Path,
    output_root: Path,
    artifacts_by_id: dict[str, dict[str, Any]],
) -> dict[str, Path]:
    modules_root = output_root / "modules"
    result: dict[str, Path] = {}
    for asset_id in sorted(artifacts_by_id):
        artifact = artifacts_by_id[asset_id]
        source_relative = Path(str(artifact["path"]))
        category = source_relative.parent.name
        destination = modules_root / category / source_relative.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_root / source_relative, destination)
        result[asset_id] = destination
    return result


def build_atlases(output_root: Path, module_paths: dict[str, Path]) -> dict[str, dict[str, Any]]:
    atlas_root = output_root / "atlases"
    atlas_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict[str, Any]] = {}
    for atlas_name, (region_size, asset_ids) in ATLAS_GROUPS.items():
        atlas = Image.new("RGBA", (region_size[0] * len(asset_ids), region_size[1]), (0, 0, 0, 0))
        coordinates: dict[str, list[int]] = {}
        for index, asset_id in enumerate(asset_ids):
            source_path = module_paths.get(asset_id)
            if source_path is None:
                raise ValueError(f"Atlas {atlas_name} references missing module {asset_id}")
            with Image.open(source_path) as source:
                rgba = source.convert("RGBA")
                if rgba.size != region_size:
                    raise ValueError(
                        f"Atlas region mismatch for {asset_id}: {rgba.size}, expected {region_size}"
                    )
                atlas.alpha_composite(rgba, (index * region_size[0], 0))
            coordinates[asset_id] = [index, 0]
        atlas_path = atlas_root / atlas_name
        atlas.save(atlas_path, format="PNG", optimize=False, compress_level=9)
        result[atlas_name] = {
            "path": atlas_path.relative_to(output_root).as_posix(),
            "sha256": sha256(atlas_path),
            "region_size": list(region_size),
            "atlas_size": list(atlas.size),
            "coordinates": coordinates,
        }
    return result


def write_manifest(
    output_root: Path,
    source_manifest: dict[str, Any],
    module_paths: dict[str, Path],
    artifacts_by_id: dict[str, dict[str, Any]],
    atlases: dict[str, dict[str, Any]],
    approved_on: str,
) -> None:
    modules: list[dict[str, Any]] = []
    for asset_id in sorted(module_paths):
        source_artifact = artifacts_by_id[asset_id]
        path = module_paths[asset_id]
        modules.append(
            {
                "asset_id": asset_id,
                "kind": source_artifact["kind"],
                "path": path.relative_to(output_root).as_posix(),
                "canvas": source_artifact["canvas"],
                "anchor": source_artifact["anchor"],
                "sha256": sha256(path),
            }
        )
    manifest = {
        "schema_version": 1,
        "visual_id": "cold_ancient_stone_v01",
        "stage": "approved_runtime_asset",
        "approved_on": approved_on,
        "source": {
            "factory_id": source_manifest["factory_id"],
            "profile_id": source_manifest["profile_id"],
            "profile_sha256": source_manifest["profile_sha256"],
            "run_id": source_manifest["run_id"],
            "blender_version": source_manifest["blender_version"],
        },
        "game_contract": source_manifest["game_contract"],
        "tile_set_contract": {
            "path": "tilesets/cold_ancient_stone_v01.tres",
            "tile_size": [64, 64],
            "source_ids": [0, 1, 2, 3, 4, 5],
            "custom_data_layer": "visual_id",
            "texture_filter": "nearest",
            "collision_enabled": False,
            "navigation_enabled": False,
        },
        "palette": source_manifest["palette"],
        "modules": modules,
        "atlases": atlases,
        "approval": {
            "manual_review_required": True,
            "approved": True,
            "runtime_integrated": True,
        },
    }
    (output_root / "cold_ancient_stone_v01.approved.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--approved-on", default="2026-08-11")
    args = parser.parse_args()

    source_run = args.source_run.resolve()
    output_root = args.output_root.resolve()
    source_manifest, artifacts_by_id = validate_run(source_run)
    output_root.mkdir(parents=True, exist_ok=True)
    module_paths = copy_modules(source_run, output_root, artifacts_by_id)
    atlases = build_atlases(output_root, module_paths)
    write_manifest(
        output_root,
        source_manifest,
        module_paths,
        artifacts_by_id,
        atlases,
        args.approved_on,
    )
    print(f"Promoted {len(module_paths)} modules and built {len(atlases)} atlases in {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
