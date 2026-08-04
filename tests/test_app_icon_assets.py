#!/usr/bin/env python3
"""Validate the pixel app icon and Godot/Android references without third-party packages."""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets/branding/source/app_icon_pixel_master_64_v01.png"
EXPORT = ROOT / "assets/branding/exports/app_icon_192_v01.png"
MANIFEST = ROOT / "assets/branding/app_icon_dungeon_spiral_v01.json"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_indexed_png(path: Path) -> tuple[int, int, bytes, list[bytes]]:
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise AssertionError(f"Not a PNG: {path}")

    offset = 8
    width = height = bit_depth = color_type = interlace = -1
    palette = b""
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
        elif chunk_type == b"PLTE":
            palette = bytes(chunk_data)
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    if (bit_depth, color_type, interlace) != (8, 3, 0):
        raise AssertionError(
            f"Expected non-interlaced 8-bit indexed PNG for {path}, got "
            f"bit_depth={bit_depth}, color_type={color_type}, interlace={interlace}"
        )
    if not palette or len(palette) > 64 * 3:
        raise AssertionError(f"Palette contract failed for {path}: {len(palette) // 3} colors")

    raw = zlib.decompress(bytes(compressed))
    stride = width
    expected_length = height * (stride + 1)
    if len(raw) != expected_length:
        raise AssertionError(f"Unexpected decompressed length for {path}: {len(raw)} != {expected_length}")

    rows: list[bytes] = []
    cursor = 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = raw[cursor]
        cursor += 1
        source = raw[cursor : cursor + stride]
        cursor += stride
        row = bytearray(stride)
        for x, value in enumerate(source):
            left = row[x - 1] if x > 0 else 0
            up = previous[x]
            up_left = previous[x - 1] if x > 0 else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = (value + left) & 0xFF
            elif filter_type == 2:
                decoded = (value + up) & 0xFF
            elif filter_type == 3:
                decoded = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                decoded = (value + paeth(left, up, up_left)) & 0xFF
            else:
                raise AssertionError(f"Unsupported PNG filter {filter_type} in {path}")
            row[x] = decoded
        rows.append(bytes(row))
        previous = row
    return width, height, palette, rows


def require_fragment(path: Path, fragment: str) -> None:
    text = path.read_text(encoding="utf-8")
    if fragment not in text:
        raise AssertionError(f"Missing reference in {path}: {fragment}")


def main() -> None:
    master_width, master_height, master_palette, master_rows = read_indexed_png(MASTER)
    export_width, export_height, export_palette, export_rows = read_indexed_png(EXPORT)
    if (master_width, master_height) != (64, 64):
        raise AssertionError(f"Unexpected pixel master size: {(master_width, master_height)}")
    if (export_width, export_height) != (192, 192):
        raise AssertionError(f"Unexpected Android icon size: {(export_width, export_height)}")
    if master_palette != export_palette:
        raise AssertionError("Master and export palettes differ")

    for y in range(export_height):
        source_row = master_rows[y // 3]
        expected_row = bytes(source_row[x // 3] for x in range(export_width))
        if export_rows[y] != expected_row:
            raise AssertionError(f"Export is not an exact 3x nearest-neighbor scale at row {y}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_id") != "app_icon_dungeon_spiral_v01":
        raise AssertionError("Unexpected visual_id")
    if manifest.get("status") != "runtime_candidate":
        raise AssertionError("Icon must remain a runtime candidate before Android testing")
    if manifest.get("render_contract", {}).get("scale_factor") != 3:
        raise AssertionError("Manifest scale factor must be 3")

    icon_path = "res://assets/branding/exports/app_icon_192_v01.png"
    require_fragment(ROOT / "project.godot", f'config/icon="{icon_path}"')
    require_fragment(ROOT / "export_presets.cfg", f'launcher_icons/main_192x192="{icon_path}"')
    print("App icon validation passed")


if __name__ == "__main__":
    main()
