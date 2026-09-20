from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw, ImageFont

from environment_profile_v01 import AssetSpec, EnvironmentProfile, load_environment_profile


@dataclass(frozen=True)
class ExportArtifact:
    asset_id: str
    kind: str
    output_path: Path
    width: int
    height: int
    sha256: str
    anchor_x: int
    anchor_y: int


def process_run(
    repo_root: Path,
    config_path: Path,
    run_dir: Path,
) -> Path:
    root = repo_root.resolve()
    profile = load_environment_profile(config_path.resolve(), root)
    resolved_run = run_dir.resolve()
    _assert_within(profile.run_root, resolved_run, "run directory")
    raw_manifest_path = resolved_run / "raw_manifest.json"
    raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    raw_entries = _validate_raw_manifest(profile, resolved_run, raw_manifest)

    exports_root = resolved_run / "exports"
    if exports_root.exists() and any(exports_root.iterdir()):
        raise FileExistsError(
            f"Exports уже существуют; run-каталоги нельзя перезаписывать: {exports_root}"
        )
    exports_root.mkdir(exist_ok=True)

    palette = tuple(_hex_to_rgb(value) for value in profile.palette_hex)
    normalized: dict[str, Image.Image] = {}
    entry_by_id = {str(entry["asset_id"]): entry for entry in raw_entries}
    for asset in profile.assets:
        entry = entry_by_id[asset.asset_id]
        raw_path = (resolved_run / str(entry["raw_path"])).resolve()
        _assert_within(resolved_run / "raw", raw_path, "raw asset")
        with Image.open(raw_path) as source:
            normalized[asset.asset_id] = normalize_asset(source, asset, profile, palette)

    _harmonize_floor_opposite_edges(profile, normalized, palette)
    _validate_normalized_images(profile, normalized, palette)

    artifacts: list[ExportArtifact] = []
    for asset in profile.assets:
        output_dir = exports_root / _category_folder(asset)
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{asset.asset_id}.png"
        normalized[asset.asset_id].save(output_path, format="PNG", optimize=False)
        entry = entry_by_id[asset.asset_id]
        anchor = entry.get("anchor", [asset.canvas_width // 2, asset.canvas_height // 2])
        artifacts.append(
            ExportArtifact(
                asset_id=asset.asset_id,
                kind=asset.kind,
                output_path=output_path,
                width=asset.canvas_width,
                height=asset.canvas_height,
                sha256=_sha256_file(output_path),
                anchor_x=int(anchor[0]),
                anchor_y=int(anchor[1]),
            )
        )

    review_dir = resolved_run / "review"
    review_dir.mkdir()
    floors_atlas = _write_floor_atlas(profile, normalized, review_dir)
    module_sheet = _write_module_sheet(profile, normalized, review_dir)
    room_preview = _write_room_preview(profile, normalized, review_dir)
    room_preview_2x = _write_nearest_upscale(room_preview, 2)

    manifest_path = resolved_run / "run_manifest.json"
    payload = {
        "schema_version": 1,
        "factory_id": "blender_environment_factory_v01",
        "profile_id": profile.profile_id,
        "profile_sha256": profile.profile_sha256,
        "stage": profile.stage,
        "run_id": str(raw_manifest["run_id"]),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "blender_version": str(raw_manifest["blender_version"]),
        "source_blend": str(raw_manifest["source_blend"]),
        "game_contract": profile.payload["game_contract"],
        "camera": raw_manifest["camera"],
        "lighting_contract": raw_manifest["lighting_contract"],
        "palette": list(profile.palette_hex),
        "artifacts": [
            {
                "asset_id": artifact.asset_id,
                "kind": artifact.kind,
                "path": artifact.output_path.relative_to(resolved_run).as_posix(),
                "canvas": [artifact.width, artifact.height],
                "anchor": [artifact.anchor_x, artifact.anchor_y],
                "sha256": artifact.sha256,
            }
            for artifact in artifacts
        ],
        "review": {
            "floors_atlas": floors_atlas.relative_to(resolved_run).as_posix(),
            "module_sheet": module_sheet.relative_to(resolved_run).as_posix(),
            "room_preview": room_preview.relative_to(resolved_run).as_posix(),
            "room_preview_2x": room_preview_2x.relative_to(resolved_run).as_posix(),
        },
        "validation": {
            "asset_count": len(artifacts),
            "floor_variant_count": len(profile.assets_of_kind("floor")),
            "floor_variants_unique": _floor_hashes_unique(profile, artifacts),
            "floor_self_repeat_seam_safe": _floor_opposite_edges_match(
                profile, normalized
            ),
            "arbitrary_floor_adjacency_opaque": _floor_edges_are_opaque(
                profile, normalized
            ),
            "palette_only": True,
            "nearest_normalization": True,
            "transparent_object_borders": True,
        },
        "approval": {
            "manual_review_required": True,
            "approved": False,
            "runtime_integrated": False,
        },
    }
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def normalize_asset(
    source: Image.Image,
    asset: AssetSpec,
    profile: EnvironmentProfile,
    palette: tuple[tuple[int, int, int], ...],
) -> Image.Image:
    expected_raw = (
        asset.canvas_width * profile.raw_render_scale,
        asset.canvas_height * profile.raw_render_scale,
    )
    if source.size != expected_raw:
        raise ValueError(
            f"Raw canvas {asset.asset_id}: {source.size}, ожидается {expected_raw}"
        )
    reduced = source.convert("RGBA").resize(asset.canvas, Image.Resampling.NEAREST)
    output = Image.new("RGBA", asset.canvas, (0, 0, 0, 0))
    source_pixels = reduced.load()
    output_pixels = output.load()
    max_alpha = _maximum_alpha(asset)
    for y in range(asset.canvas_height):
        for x in range(asset.canvas_width):
            red, green, blue, alpha = source_pixels[x, y]
            if asset.is_floor:
                if alpha < 96:
                    raise ValueError(
                        f"Floor raw render не покрывает canvas: {asset.asset_id} ({x}, {y})"
                    )
                alpha = 255
            else:
                alpha = _pixel_alpha(alpha, max_alpha)
            if alpha <= 0:
                output_pixels[x, y] = (0, 0, 0, 0)
                continue
            nearest = min(
                palette,
                key=lambda color: (
                    (red - color[0]) ** 2
                    + (green - color[1]) ** 2
                    + (blue - color[2]) ** 2
                ),
            )
            output_pixels[x, y] = (*nearest, alpha)
    if not asset.is_floor:
        _clear_outer_border(output)
    return output


def _validate_raw_manifest(
    profile: EnvironmentProfile,
    run_dir: Path,
    manifest: object,
) -> list[dict[str, Any]]:
    if not isinstance(manifest, dict):
        raise ValueError("raw_manifest должен быть объектом")
    if manifest.get("factory_id") != "blender_environment_factory_v01":
        raise ValueError("Некорректный factory_id в raw_manifest")
    if manifest.get("profile_id") != profile.profile_id:
        raise ValueError("raw_manifest относится к другому profile_id")
    if manifest.get("profile_sha256") != profile.profile_sha256:
        raise ValueError("Profile изменился после Blender render")
    if manifest.get("stage") != "review_candidate":
        raise ValueError("Raw render не должен объявляться approved")
    if bool(manifest.get("game_contract", {}).get("local_light_baked_into_floor")):
        raise ValueError("Raw render нарушает контракт локального света")
    lighting = manifest.get("lighting_contract", {})
    if not bool(lighting.get("neutral_only")):
        raise ValueError("Raw render использовал ненейтральное освещение")
    entries = manifest.get("artifacts")
    if not isinstance(entries, list) or len(entries) != len(profile.assets):
        raise ValueError("raw_manifest должен содержать все 33 артефакта")
    expected_ids = {asset.asset_id for asset in profile.assets}
    actual_ids = {str(entry.get("asset_id", "")) for entry in entries if isinstance(entry, dict)}
    if actual_ids != expected_ids:
        raise ValueError("Набор raw artifact IDs не совпадает с profile")
    for raw_entry in entries:
        if not isinstance(raw_entry, dict):
            raise ValueError("Raw artifact entry должен быть объектом")
        asset = profile.asset(str(raw_entry["asset_id"]))
        if raw_entry.get("canvas") != [asset.canvas_width, asset.canvas_height]:
            raise ValueError(f"Canvas contract нарушен: {asset.asset_id}")
        expected_raw = [
            asset.canvas_width * profile.raw_render_scale,
            asset.canvas_height * profile.raw_render_scale,
        ]
        if raw_entry.get("raw_canvas") != expected_raw:
            raise ValueError(f"Raw canvas contract нарушен: {asset.asset_id}")
        raw_path = (run_dir / str(raw_entry["raw_path"])).resolve()
        _assert_within(run_dir / "raw", raw_path, "raw artifact")
        if not raw_path.is_file():
            raise FileNotFoundError(raw_path)
    return [entry for entry in entries if isinstance(entry, dict)]


def _harmonize_floor_opposite_edges(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
    palette: tuple[tuple[int, int, int], ...],
) -> None:
    seam = profile.payload["seam_contract"]
    if seam.get("mode") != "per_variant_opposite_edge_harmonization":
        raise ValueError("Неподдерживаемый floor seam mode")
    inset = int(seam["sample_inset_px"])
    if inset < 1:
        raise ValueError("Floor seam sample inset должен быть положительным")
    for asset in profile.assets_of_kind("floor"):
        image = images[asset.asset_id]
        source = image.copy()
        pixels = image.load()
        source_pixels = source.load()
        for y in range(image.height):
            color = _average_to_palette(
                source_pixels[inset, y],
                source_pixels[image.width - 1 - inset, y],
                palette,
            )
            pixels[0, y] = color
            pixels[image.width - 1, y] = color
        for x in range(image.width):
            color = _average_to_palette(
                source_pixels[x, inset],
                source_pixels[x, image.height - 1 - inset],
                palette,
            )
            pixels[x, 0] = color
            pixels[x, image.height - 1] = color
        corner = _average_many_to_palette(
            (
                source_pixels[inset, inset],
                source_pixels[image.width - 1 - inset, inset],
                source_pixels[inset, image.height - 1 - inset],
                source_pixels[
                    image.width - 1 - inset,
                    image.height - 1 - inset,
                ],
            ),
            palette,
        )
        pixels[0, 0] = corner
        pixels[image.width - 1, 0] = corner
        pixels[0, image.height - 1] = corner
        pixels[image.width - 1, image.height - 1] = corner


def _validate_normalized_images(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
    palette: tuple[tuple[int, int, int], ...],
) -> None:
    allowed = set(palette)
    for asset in profile.assets:
        image = images[asset.asset_id]
        if image.size != asset.canvas or image.mode != "RGBA":
            raise ValueError(f"Export contract нарушен: {asset.asset_id}")
        visible = 0
        for red, green, blue, alpha in _image_pixels(image):
            if alpha == 0:
                continue
            visible += 1
            if (red, green, blue) not in allowed:
                raise ValueError(f"Цвет вне палитры: {asset.asset_id}")
        if visible <= 0:
            raise ValueError(f"Пустой export: {asset.asset_id}")
        if asset.is_floor and any(
            alpha != 255 for *_, alpha in _image_pixels(image)
        ):
            raise ValueError(f"Floor должен быть полностью непрозрачным: {asset.asset_id}")
        if not asset.is_floor and not _border_is_transparent(image):
            raise ValueError(f"Object/decal касается края canvas: {asset.asset_id}")
    if not _floor_opposite_edges_match(profile, images):
        raise ValueError("Floor variants не совпадают по собственным противоположным краям")
    if not _floor_edges_are_opaque(profile, images):
        raise ValueError("Floor variants имеют прозрачные граничные пиксели")
    floor_hashes = {
        hashlib.sha256(images[asset.asset_id].tobytes()).hexdigest()
        for asset in profile.assets_of_kind("floor")
    }
    if len(floor_hashes) != 8:
        raise ValueError("Восемь floor variants должны быть визуально различны")


def _write_floor_atlas(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
    review_dir: Path,
) -> Path:
    floor_assets = profile.assets_of_kind("floor")
    atlas = Image.new("RGBA", (profile.tile_size * 4, profile.tile_size * 2))
    for index, asset in enumerate(floor_assets):
        atlas.alpha_composite(
            images[asset.asset_id],
            ((index % 4) * profile.tile_size, (index // 4) * profile.tile_size),
        )
    output = review_dir / "cold_stone_floor_variants_v01.png"
    atlas.save(output, format="PNG", optimize=False)
    return output


def _write_module_sheet(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
    review_dir: Path,
) -> Path:
    cell_width = 144
    cell_height = 132
    columns = 5
    rows = (len(profile.assets) + columns - 1) // columns
    sheet = Image.new("RGBA", (cell_width * columns, cell_height * rows), (18, 27, 38, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, asset in enumerate(profile.assets):
        column = index % columns
        row = index // columns
        origin_x = column * cell_width
        origin_y = row * cell_height
        draw.rectangle(
            (origin_x + 4, origin_y + 4, origin_x + cell_width - 5, origin_y + cell_height - 5),
            fill=(31, 45, 58, 255),
            outline=(92, 113, 128, 255),
            width=1,
        )
        image = images[asset.asset_id]
        position = (
            origin_x + (cell_width - image.width) // 2,
            origin_y + 8 + (96 - image.height) // 2,
        )
        sheet.alpha_composite(image, position)
        draw.text(
            (origin_x + 8, origin_y + 108),
            asset.asset_id,
            font=font,
            fill=(205, 218, 226, 255),
        )
    output = review_dir / "environment_modules_contact_sheet_v01.png"
    sheet.save(output, format="PNG", optimize=False)
    return output


def _write_room_preview(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
    review_dir: Path,
) -> Path:
    preview = profile.payload["preview"]
    tile = profile.tile_size
    room_width = int(preview["room_size_cells"][0]) * tile
    room_height = int(preview["room_size_cells"][1]) * tile
    room_x = 112
    room_y = 104
    canvas = Image.new("RGBA", (608, 608), (9, 14, 21, 255))

    for row, values in enumerate(preview["floor_rows"]):
        for column, value in enumerate(values):
            asset_id = f"cold_stone_floor_{int(value):02d}"
            canvas.alpha_composite(
                images[asset_id],
                (room_x + column * tile, room_y + row * tile),
            )
    for decal in preview["decals"]:
        cell_x, cell_y = (int(value) for value in decal["cell"])
        canvas.alpha_composite(
            images[str(decal["asset_id"])],
            (room_x + cell_x * tile, room_y + cell_y * tile),
        )

    stairs_x, stairs_y = (int(value) for value in preview["stairs_cell"])
    stairs = images["stone_stairs_down_01"]
    canvas.alpha_composite(
        stairs,
        (
            room_x + stairs_x * tile + (tile - stairs.width) // 2,
            room_y + stairs_y * tile - (stairs.height - tile),
        ),
    )

    north_wall = images["stone_wall_north"]
    south_wall = images["stone_wall_south"]
    west_wall = images["stone_wall_west"]
    east_wall = images["stone_wall_east"]
    door = images["stone_door_x_closed"]
    for column in range(6):
        top_asset = door if column == 2 else north_wall
        _composite_centered(
            canvas,
            top_asset,
            room_x + column * tile + tile // 2,
            room_y,
        )
    for row in range(6):
        _composite_centered(
            canvas,
            west_wall,
            room_x,
            room_y + row * tile + tile // 2,
        )
        _composite_centered(
            canvas,
            east_wall,
            room_x + room_width,
            room_y + row * tile + tile // 2,
        )

    rear_corner_positions = (
        ("stone_wall_corner_nw", room_x, room_y),
        ("stone_wall_corner_ne", room_x + room_width, room_y),
    )
    for asset_id, x, y in rear_corner_positions:
        _composite_centered(canvas, images[asset_id], x, y)

    character_x, character_y = (int(value) for value in preview["character_cell"])
    with Image.open(profile.character_idle_atlas) as atlas:
        character = atlas.convert("RGBA").crop(
            (0, 0, profile.character_sprite_canvas, profile.character_sprite_canvas)
        )
    character_baseline_x = room_x + character_x * tile + tile // 2
    character_baseline_y = room_y + character_y * tile + tile - 5
    canvas.alpha_composite(
        character,
        (
            character_baseline_x - profile.character_sprite_canvas // 2,
            character_baseline_y - profile.character_sprite_canvas + 5,
        ),
    )

    # The south wall is a foreground occluder in the approved top-down 3/4
    # convention, so it is composited after the character.
    for column in range(6):
        _composite_centered(
            canvas,
            south_wall,
            room_x + column * tile + tile // 2,
            room_y + room_height,
        )
    for asset_id, x, y in (
        ("stone_wall_corner_sw", room_x, room_y + room_height),
        ("stone_wall_corner_se", room_x + room_width, room_y + room_height),
    ):
        _composite_centered(canvas, images[asset_id], x, y)

    draw = ImageDraw.Draw(canvas)
    draw.rectangle((16, 16, 592, 76), fill=(14, 21, 30, 230), outline=(92, 113, 128, 255))
    draw.text((30, 30), "COLD ANCIENT STONE · BLENDER REVIEW V01", fill=(202, 220, 231, 255))
    draw.text((30, 49), "6×6 cells · native game cell 64 px · character canvas 96 px", fill=(126, 155, 174, 255))
    output = review_dir / "cold_ancient_stone_room_6x6_v01.png"
    canvas.save(output, format="PNG", optimize=False)
    return output


def _write_nearest_upscale(path: Path, factor: int) -> Path:
    with Image.open(path) as image:
        enlarged = image.resize(
            (image.width * factor, image.height * factor),
            Image.Resampling.NEAREST,
        )
    output = path.with_name(f"{path.stem}_{factor}x{path.suffix}")
    enlarged.save(output, format="PNG", optimize=False)
    return output


def _composite_centered(
    canvas: Image.Image,
    image: Image.Image,
    center_x: int,
    center_y: int,
) -> None:
    canvas.alpha_composite(
        image,
        (center_x - image.width // 2, center_y - image.height // 2),
    )


def _maximum_alpha(asset: AssetSpec) -> int:
    if asset.kind == "decal" and asset.shape == "dust":
        return 112
    if asset.kind == "decal" and asset.shape == "damp":
        return 144
    if asset.kind == "transition":
        return 160
    if asset.kind == "arcane":
        return 240
    return 255


def _pixel_alpha(source_alpha: int, maximum: int) -> int:
    if source_alpha < 96:
        return 0
    if source_alpha < 208:
        return max(1, maximum // 2)
    return maximum


def _clear_outer_border(image: Image.Image) -> None:
    pixels = image.load()
    for x in range(image.width):
        pixels[x, 0] = (0, 0, 0, 0)
        pixels[x, image.height - 1] = (0, 0, 0, 0)
    for y in range(image.height):
        pixels[0, y] = (0, 0, 0, 0)
        pixels[image.width - 1, y] = (0, 0, 0, 0)


def _border_is_transparent(image: Image.Image) -> bool:
    pixels = image.load()
    return all(pixels[x, 0][3] == 0 and pixels[x, image.height - 1][3] == 0 for x in range(image.width)) and all(
        pixels[0, y][3] == 0 and pixels[image.width - 1, y][3] == 0
        for y in range(image.height)
    )


def _floor_opposite_edges_match(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
) -> bool:
    floors = profile.assets_of_kind("floor")
    if not floors:
        return False
    for asset in floors:
        image = images[asset.asset_id]
        if _column(image, 0) != _column(image, image.width - 1):
            return False
        if _row(image, 0) != _row(image, image.height - 1):
            return False
    return True


def _floor_edges_are_opaque(
    profile: EnvironmentProfile,
    images: dict[str, Image.Image],
) -> bool:
    for asset in profile.assets_of_kind("floor"):
        image = images[asset.asset_id]
        edge_pixels = (
            *_column(image, 0),
            *_column(image, image.width - 1),
            *_row(image, 0),
            *_row(image, image.height - 1),
        )
        if any(pixel[3] != 255 for pixel in edge_pixels):
            return False
    return True


def _column(image: Image.Image, x: int) -> tuple[tuple[int, int, int, int], ...]:
    pixels = image.load()
    return tuple(pixels[x, y] for y in range(image.height))


def _row(image: Image.Image, y: int) -> tuple[tuple[int, int, int, int], ...]:
    pixels = image.load()
    return tuple(pixels[x, y] for x in range(image.width))


def _floor_hashes_unique(
    profile: EnvironmentProfile,
    artifacts: Iterable[ExportArtifact],
) -> bool:
    floor_ids = {asset.asset_id for asset in profile.assets_of_kind("floor")}
    hashes = {artifact.sha256 for artifact in artifacts if artifact.asset_id in floor_ids}
    return len(hashes) == len(floor_ids)


def _category_folder(asset: AssetSpec) -> str:
    if asset.kind == "floor":
        return "floors"
    if asset.kind in {"decal", "transition", "arcane"}:
        return "overlays"
    if asset.kind in {"wall_edge", "wall_corner"}:
        return "walls"
    if asset.kind == "door":
        return "doors"
    return "structures"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def _average_to_palette(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    palette: tuple[tuple[int, int, int], ...],
) -> tuple[int, int, int, int]:
    return _average_many_to_palette((first, second), palette)


def _average_many_to_palette(
    values: tuple[tuple[int, int, int, int], ...],
    palette: tuple[tuple[int, int, int], ...],
) -> tuple[int, int, int, int]:
    count = max(1, len(values))
    average = tuple(
        round(sum(value[channel] for value in values) / count)
        for channel in range(3)
    )
    nearest = min(
        palette,
        key=lambda color: sum(
            (average[channel] - color[channel]) ** 2 for channel in range(3)
        ),
    )
    return (*nearest, 255)


def _image_pixels(image: Image.Image):
    flattened = getattr(image, "get_flattened_data", None)
    return flattened() if callable(flattened) else image.getdata()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_within(parent: Path, child: Path, label: str) -> None:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} выходит за разрешённый root: {child}") from exc


def _parse_args(values: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize Blender environment run v01")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument(
        "--config",
        default="tools/blender_environment_factory/configs/cold_ancient_stone_v01.json",
    )
    parser.add_argument("--run-dir", required=True)
    return parser.parse_args(values)


def main() -> int:
    args = _parse_args(sys.argv[1:])
    repo_root = Path(args.repo_root).resolve()
    config = Path(args.config)
    config_path = config.resolve() if config.is_absolute() else (repo_root / config).resolve()
    run_dir = Path(args.run_dir)
    run_path = run_dir.resolve() if run_dir.is_absolute() else (repo_root / run_dir).resolve()
    result = process_run(repo_root, config_path, run_path)
    print(f"BLENDER_ENVIRONMENT_POSTPROCESS_RESULT={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
