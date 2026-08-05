from __future__ import annotations

import json
from pathlib import Path

CORRUPT_BACKGROUND = Path("assets/branding/loading_screen/approved/loading_screen_composite_v01/loading_screen_composite_v01.webp")
MANIFEST = Path("assets/branding/loading_screen/loading_screen_composite_v01.json")
LOGO_MANIFEST = Path("assets/branding/loading_screen/loading_screen_logo_blue_v01.json")
SCENE = Path("scenes/menus/loading_screen_composite_preview_v01.tscn")
SCRIPT = Path("scripts/menus/loading_screen_composite_preview_v01.gd")
EXPECTED_SIZE = (1672, 941)
CORRECT_TITLE = "Хроники странника"
CORRECT_SUBTITLE = "Башня, уходящая вниз"
INVALID_SUBTITLE_FRAGMENTS = ("вннз", "вннс", "уходяшая", "уходящяя", "Башня уходящая")


def test_required_text_resources_exist() -> None:
    for path in (MANIFEST, LOGO_MANIFEST, SCENE, SCRIPT):
        assert path.exists(), f"Missing required file: {path}"


def test_corrupt_background_is_not_in_runtime_tree() -> None:
    assert not CORRUPT_BACKGROUND.exists(), "Truncated background must not remain in the runtime tree"


def test_manifest_contract() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["visual_id"] == "loading_screen_composite_v01"
    assert manifest["status"] == "runtime_candidate"
    assert manifest["connected_to_game_transitions"] is False
    assert manifest["background_mode"] == "procedural_fallback"
    assert manifest["background_path"] == ""
    assert manifest["loading_bar_visual_id"] == "loading_bar_v03"
    assert (manifest["size"]["width"], manifest["size"]["height"]) == EXPECTED_SIZE

    logo_manifest = json.loads(LOGO_MANIFEST.read_text(encoding="utf-8"))
    assert logo_manifest["status"] == "reference_approved"
    assert logo_manifest["standalone_graphic_layer_available"] is False
    assert logo_manifest["title"] == CORRECT_TITLE
    assert logo_manifest["subtitle"] == CORRECT_SUBTITLE
    assert logo_manifest["subtitle_render_mode"] == "live_text"
    assert logo_manifest["baked_subtitle_authoritative"] is False


def test_scene_uses_safe_fallback_and_modular_bar() -> None:
    scene = SCENE.read_text(encoding="utf-8")
    assert "res://scenes/ui/loading_progress_bar_v03.tscn" in scene
    assert "loading_screen_composite_v01.webp" not in scene
    assert '[node name="Background" type="ColorRect"' in scene
    assert f'text = "{CORRECT_TITLE}"' in scene
    assert 'text = "Загрузка..."' in scene
    assert "anchor_left = 0.18" in scene
    assert "anchor_right = 0.82" in scene


def test_subtitle_is_exact_live_text() -> None:
    scene = SCENE.read_text(encoding="utf-8")
    assert 'name="SubtitleCorrection"' in scene
    assert f'text = "{CORRECT_SUBTITLE}"' in scene
    for invalid_fragment in INVALID_SUBTITLE_FRAGMENTS:
        assert invalid_fragment not in scene
