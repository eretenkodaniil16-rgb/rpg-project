from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

BACKGROUND = Path("assets/branding/loading_screen/approved/loading_screen_composite_v01/loading_screen_composite_v01.webp")
MANIFEST = Path("assets/branding/loading_screen/loading_screen_composite_v01.json")
SCENE = Path("scenes/menus/loading_screen_composite_preview_v01.tscn")
SCRIPT = Path("scripts/menus/loading_screen_composite_preview_v01.gd")
EXPECTED_SIZE = (1672, 941)


def test_files_exist() -> None:
    for path in (BACKGROUND, MANIFEST, SCENE, SCRIPT):
        assert path.exists(), f"Missing required file: {path}"


def test_background_contract() -> None:
    assert BACKGROUND.stat().st_size > 300_000, "Composite background is unexpectedly compressed or truncated"
    with Image.open(BACKGROUND) as image:
        assert image.size == EXPECTED_SIZE, image.size
        assert image.format == "WEBP", image.format
        assert image.mode == "RGB", image.mode


def test_manifest_contract() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["visual_id"] == "loading_screen_composite_v01"
    assert manifest["status"] == "runtime_candidate"
    assert manifest["connected_to_game_transitions"] is False
    assert manifest["loading_bar_visual_id"] == "loading_bar_v03"
    assert (manifest["size"]["width"], manifest["size"]["height"]) == EXPECTED_SIZE


def test_scene_uses_modular_bar_and_adaptive_anchors() -> None:
    scene = SCENE.read_text(encoding="utf-8")
    assert "res://scenes/ui/loading_progress_bar_v03.tscn" in scene
    assert 'text = "Загрузка..."' in scene
    assert "anchor_left = 0.18" in scene
    assert "anchor_right = 0.82" in scene
    assert "stretch_mode = 6" in scene
