#!/usr/bin/env python3
"""Static contract checks for animated main menu branding v01."""

from __future__ import annotations

import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = ROOT / "assets/branding/main_menu/approved/main_menu_tower_down_title_v01.webp"
MANIFEST = ROOT / "assets/branding/main_menu/main_menu_tower_down_v01.json"
SCENE = ROOT / "scenes/menus/main_menu.tscn"
MENU_SCRIPT = ROOT / "scripts/menus/main_menu.gd"
ATMOSPHERE_SCRIPT = ROOT / "scripts/menus/main_menu_atmosphere.gd"
WEBP_RIFF = b"RIFF"
WEBP_FORMAT = b"WEBP"


def read_webp_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != WEBP_RIFF or data[8:12] != WEBP_FORMAT:
        raise AssertionError(f"Not a WebP file: {path}")
    declared_size = struct.unpack("<I", data[4:8])[0] + 8
    if declared_size != len(data):
        raise AssertionError(f"WebP RIFF size mismatch: {declared_size} != {len(data)}")
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 ":
        marker = data.find(b"\x9d\x01\x2a", 20)
        if marker < 0:
            raise AssertionError("VP8 frame marker not found")
        width = struct.unpack("<H", data[marker + 3 : marker + 5])[0] & 0x3FFF
        height = struct.unpack("<H", data[marker + 5 : marker + 7])[0] & 0x3FFF
        return width, height
    if chunk == b"VP8L":
        if data[20] != 0x2F:
            raise AssertionError("VP8L signature not found")
        bits = int.from_bytes(data[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    raise AssertionError(f"Unsupported WebP chunk: {chunk!r}")


def require(path: Path, fragment: str) -> None:
    text = path.read_text(encoding="utf-8")
    if fragment not in text:
        raise AssertionError(f"Missing contract fragment in {path}: {fragment}")


def main() -> None:
    width, height = read_webp_size(BACKGROUND)
    if (width, height) != (1280, 720):
        raise AssertionError(f"Unexpected background size: {(width, height)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_id") != "main_menu_tower_down_v01":
        raise AssertionError("Unexpected main-menu visual_id")
    if manifest.get("status") != "runtime_candidate":
        raise AssertionError("Main menu must remain a runtime candidate before physical testing")
    if manifest.get("approval", {}).get("logo_variant_approved") != 2:
        raise AssertionError("Approved logo variant must remain 2")
    if manifest.get("render_contract", {}).get("heavy_video_background") is not False:
        raise AssertionError("The Android menu must not use a video background")

    require(SCENE, 'node name="FallbackBackground"')
    require(SCENE, 'node name="ApprovedBackground"')
    require(SCENE, 'node name="Atmosphere"')
    require(SCENE, 'script = ExtResource("2_atmosphere")')
    require(SCENE, 'stretch_mode = 6')
    for button_name in ("ContinueButton", "NewGameButton", "QuitButton"):
        require(SCENE, f'node name="{button_name}"')

    background_path = "res://assets/branding/main_menu/approved/main_menu_tower_down_title_v01.webp"
    require(MENU_SCRIPT, f'const MAIN_MENU_BACKGROUND_PATH: String = "{background_path}"')
    require(MENU_SCRIPT, "ResourceLoader.exists(MAIN_MENU_BACKGROUND_PATH")
    require(MENU_SCRIPT, "_install_save_slots_panel()")
    require(MENU_SCRIPT, "_on_new_game_pressed")
    require(MENU_SCRIPT, "_on_continue_pressed")

    require(ATMOSPHERE_SCRIPT, "const PARTICLE_COUNT: int = 28")
    require(ATMOSPHERE_SCRIPT, "_draw_torch_glow")
    require(ATMOSPHERE_SCRIPT, "ProjectSettings.get_setting(\"accessibility/reduced_motion\"")
    print("Main menu branding validation passed")


if __name__ == "__main__":
    main()
