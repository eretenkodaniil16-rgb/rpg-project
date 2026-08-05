#!/usr/bin/env python3
"""Static validation for modular loading bar texture pack v03."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets/branding/loading_screen/approved/loading_bar_v03"
MANIFEST = ROOT / "assets/branding/loading_screen/loading_screen_v01.json"
BAR_SCENE = ROOT / "scenes/ui/loading_progress_bar_v03.tscn"
PREVIEW_SCENE = ROOT / "scenes/menus/loading_screen_texture_preview.tscn"
BAR_SCRIPT = ROOT / "scripts/ui/loading_progress_bar_v03.gd"

EXPECTED = {
    "loading_bar_left_cap_v03.png": (176, 128),
    "loading_bar_track_v03.png": (128, 128),
    "loading_bar_fill_v03.png": (128, 44),
    "loading_bar_glint_v03.png": (64, 44),
    "loading_bar_right_cap_v03.png": (176, 128),
    "loading_bar_center_rune_v03.png": (144, 144),
}


def require(path: Path, fragment: str) -> None:
    content = path.read_text(encoding="utf-8")
    if fragment not in content:
        raise AssertionError(f"Missing fragment in {path}: {fragment}")


def validate_png(path: Path, expected_size: tuple[int, int]) -> None:
    with Image.open(path) as image:
        if image.size != expected_size:
            raise AssertionError(f"Unexpected size for {path.name}: {image.size}")
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        extrema = alpha.getextrema()
        if extrema[0] == 255 or extrema[1] == 0:
            raise AssertionError(f"Expected useful alpha channel in {path.name}")


def main() -> None:
    actual = sorted(path.name for path in ASSET_DIR.glob("*.png"))
    if actual != sorted(EXPECTED):
        raise AssertionError(f"Unexpected loading bar asset set: {actual}")

    for name, size in EXPECTED.items():
        validate_png(ASSET_DIR / name, size)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("visual_id") != "loading_bar_v03":
        raise AssertionError("Unexpected loading bar visual_id")
    if manifest.get("status") != "runtime_candidate":
        raise AssertionError("Loading bar must remain runtime_candidate")
    if manifest.get("approved_variant") != 3:
        raise AssertionError("Loading bar variant 3 must be fixed in the manifest")
    if manifest.get("integration", {}).get("connected_to_game_transitions"):
        raise AssertionError("Texture-only stage must not connect game transitions")
    if manifest.get("approval", {}).get("final"):
        raise AssertionError("Texture pack must not be marked final before physical checks")
    if manifest.get("background_reference", {}).get("included_in_this_stage"):
        raise AssertionError("HQ background must remain outside this isolated bar stage")

    for fragment in (
        'script = ExtResource("1_script")',
        'node name="Track" type="TextureRect"',
        'node name="FillClip" type="Control"',
        'clip_contents = true',
        'node name="CenterRune" type="TextureRect"',
    ):
        require(BAR_SCENE, fragment)

    for fragment in (
        'class_name LoadingProgressBarV03',
        '@export_range(0.0, 100.0, 0.1) var value: float',
        'func set_progress(next_value: float)',
        'func has_complete_textures() -> bool',
        'accessibility/reduced_motion',
        'TEXTURE_FILTER_LINEAR',
    ):
        require(BAR_SCRIPT, fragment)

    require(PREVIEW_SCENE, 'instance=ExtResource("2_bar")')
    require(PREVIEW_SCENE, 'node name="PreviewBackground" type="ColorRect"')
    require(PREVIEW_SCENE, 'text = "Загрузка..."')
    print("Loading screen texture validation passed")


if __name__ == "__main__":
    main()
