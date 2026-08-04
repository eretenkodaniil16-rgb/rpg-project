#!/usr/bin/env python3
"""Static contract checks for animated main menu branding v01."""

from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRIPS = ROOT / "assets/branding/main_menu/approved/strips"
MANIFEST = ROOT / "assets/branding/main_menu/main_menu_tower_down_v01.json"
SCENE = ROOT / "scenes/menus/main_menu.tscn"
MENU_SCRIPT = ROOT / "scripts/menus/main_menu.gd"
TILED_SCRIPT = ROOT / "scripts/menus/main_menu_tiled_background.gd"
ATMOSPHERE_SCRIPT = ROOT / "scripts/menus/main_menu_atmosphere.gd"
WEBP_RIFF = b"RIFF"
WEBP_FORMAT = b"WEBP"
COLUMNS = 8
STRIP_SIZE = (160, 720)


def read_webp_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != WEBP_RIFF or data[8:12] != WEBP_FORMAT:
        raise AssertionError(f"Not a WebP file: {path}")
    declared_size = struct.unpack("<I", data[4:8])[0] + 8
    if declared_size != len(data):
        raise AssertionError(f"WebP RIFF size mismatch for {path}: {declared_size} != {len(data)}")
    chunk = data[12:16]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if chunk == b"VP8 ":
        marker = data.find(b"\x9d\x01\x2a", 20)
        if marker < 0:
            raise AssertionError(f"VP8 frame marker not found: {path}")
        width = struct.unpack("<H", data[marker + 3 : marker + 5])[0] & 0x3FFF
        height = struct.unpack("<H", data[marker + 5 : marker + 7])[0] & 0x3FFF
        return width, height
    if chunk == b"VP8L":
        if data[20] != 0x2F:
            raise AssertionError(f"VP8L signature not found: {path}")
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    raise AssertionError(f"Unsupported WebP chunk in {path}: {chunk!r}")


def require(path: Path, fragment: str) -> None:
    text = path.read_text(encoding="utf-8")
    if fragment not in text:
        raise AssertionError(f"Missing contract fragment in {path}: {fragment}")


def main() -> None:
    expected_names = [f"main_menu_strip_c{column:02d}.webp" for column in range(COLUMNS)]
    actual_names = sorted(path.name for path in STRIPS.glob("*.webp"))
    if actual_names != expected_names:
        missing = sorted(set(expected_names) - set(actual_names))
        extra = sorted(set(actual_names) - set(expected_names))
        raise AssertionError(f"Strip set mismatch; missing={missing}, extra={extra}")
    for name in expected_names:
        size = read_webp_size(STRIPS / name)
        if size != STRIP_SIZE:
            raise AssertionError(f"Unexpected strip size for {name}: {size}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_id") != "main_menu_tower_down_v01":
        raise AssertionError("Unexpected main-menu visual_id")
    if manifest.get("status") != "runtime_candidate":
        raise AssertionError("Main menu must remain a runtime candidate before physical testing")
    if manifest.get("approval", {}).get("logo_variant_approved") != 2:
        raise AssertionError("Approved logo variant must remain 2")
    contract = manifest.get("render_contract", {})
    if contract.get("strip_count") != 8 or contract.get("strip_size") != [160, 720]:
        raise AssertionError("Unexpected strip contract")
    if contract.get("heavy_video_background") is not False:
        raise AssertionError("The Android menu must not use a video background")

    require(SCENE, 'node name="FallbackBackground"')
    require(SCENE, 'node name="ApprovedBackground" type="Control"')
    require(SCENE, 'script = ExtResource("3_tiled_background")')
    require(SCENE, 'node name="Atmosphere"')
    require(SCENE, 'script = ExtResource("2_atmosphere")')
    require(SCENE, 'node name="Title" type="Label"')
    require(SCENE, 'text = "ХРОНИКИ СТРАННИКА"')
    require(SCENE, 'node name="Subtitle" type="Label"')
    require(SCENE, 'text = "Башня, уходящая вниз"')
    for button_name in ("ContinueButton", "NewGameButton", "QuitButton"):
        require(SCENE, f'node name="{button_name}"')

    require(MENU_SCRIPT, "MainMenuTiledBackground")
    require(MENU_SCRIPT, "has_complete_tiles()")
    require(MENU_SCRIPT, "_install_save_slots_panel()")
    require(MENU_SCRIPT, "_on_new_game_pressed")
    require(MENU_SCRIPT, "_on_continue_pressed")

    require(TILED_SCRIPT, "const COLUMNS: int = 8")
    require(TILED_SCRIPT, "const STRIP_SIZE: Vector2 = Vector2(160.0, 720.0)")
    require(TILED_SCRIPT, "scale_factor: float = maxf")
    require(TILED_SCRIPT, "has_complete_tiles")
    require(ATMOSPHERE_SCRIPT, "const PARTICLE_COUNT: int = 28")
    require(ATMOSPHERE_SCRIPT, "_draw_torch_glow")
    require(ATMOSPHERE_SCRIPT, "ProjectSettings.get_setting(\"accessibility/reduced_motion\"")
    print("Main menu branding validation passed")


if __name__ == "__main__":
    main()
