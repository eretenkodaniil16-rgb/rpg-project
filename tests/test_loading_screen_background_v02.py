from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets/branding/loading_screen/approved/loading_screen_visual_v02/background/loading_screen_tower_blue_v02.png"
MANIFEST = ROOT / "assets/branding/loading_screen/loading_screen_visual_v02.json"
BACKGROUND_SCRIPT = ROOT / "scripts/menus/loading_screen_background_v02.gd"
VISUAL_SCRIPT = ROOT / "scripts/menus/loading_screen_visual_v02.gd"
VISUAL_SCENE = ROOT / "scenes/menus/loading_screen_visual_v02.tscn"
EXPECTED_SHA256 = "271f14237067e093b783367fb9e7b2c6d5fa4249158aece8b21d963e639b65f0"
EXPECTED_SIZE = (1672, 941)


def png_header(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "background is not a PNG"
    assert data[12:16] == b"IHDR", "PNG does not start with IHDR"
    width, height, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", data[16:29])
    return width, height, bit_depth, color_type


def main() -> None:
    assert ASSET.is_file(), ASSET
    asset_bytes = ASSET.read_bytes()
    assert len(asset_bytes) == 2_674_332, "approved background bytes changed or were truncated"
    assert hashlib.sha256(asset_bytes).hexdigest() == EXPECTED_SHA256
    assert png_header(ASSET) == (*EXPECTED_SIZE, 8, 2), "expected 1672x941 RGB8 PNG"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = manifest["background_contract"]
    assert manifest["visual_id"] == "loading_screen_visual_v02"
    assert manifest["status"] == "runtime_candidate"
    assert tuple(contract["source_size"]) == EXPECTED_SIZE
    assert contract["sha256"] == EXPECTED_SHA256
    assert contract["contains_title"] is False
    assert contract["contains_subtitle"] is False
    assert contract["contains_loading_ui"] is False
    assert "bright_blue_tapestries" in contract["composition"]
    assert manifest["approval"]["background_reference_approved"] is True
    assert manifest["approval"]["android_physical_tested"] is False
    assert manifest["approval"]["final"] is False

    scene = VISUAL_SCENE.read_text(encoding="utf-8")
    background_script = BACKGROUND_SCRIPT.read_text(encoding="utf-8")
    visual_script = VISUAL_SCRIPT.read_text(encoding="utf-8")
    assert "loading_screen_background_v02.gd" in scene
    assert "main_menu_tiled_background.gd" not in scene
    assert "BACKGROUND_TEXTURE_PATH" in background_script
    assert "loading_screen_tower_blue_v02.png" in background_script
    assert "ResourceLoader.exists" in background_script
    assert "draw_texture_rect" in background_script
    assert "func has_background_texture() -> bool:" in background_script
    assert "func has_approved_background() -> bool:" in visual_script

    print("Loading screen approved background v02 contracts passed.")


if __name__ == "__main__":
    main()
