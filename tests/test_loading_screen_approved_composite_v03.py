from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets/branding/loading_screen/approved/loading_screen_composite_v03/loading_screen_approved_composite_v03.json"
STRIPS = ROOT / "assets/branding/loading_screen/approved/loading_screen_composite_v03/strips"
SCENE = ROOT / "scenes/menus/loading_screen_visual_v02.tscn"
BACKGROUND_SCRIPT = ROOT / "scripts/menus/loading_screen_approved_composite_v03.gd"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_contract() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["visual_id"] == "loading_screen_approved_composite_v03"
    assert payload["source_size"] == [1672, 941]
    assert payload["encoding"] == "webp"
    assert payload["quality"] == 82
    assert payload["segment_count"] == 26

    segments = payload["segments"]
    assert len(segments) == 26
    assert sum(int(segment["width"]) for segment in segments) == 1672
    assert all(int(segment["height"]) == 941 for segment in segments)
    assert [int(segment["x"]) for segment in segments] == [index * 64 for index in range(26)]


def test_all_strips_match_manifest() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_names = []
    for segment in payload["segments"]:
        path = STRIPS / segment["name"]
        expected_names.append(segment["name"])
        assert path.is_file(), f"Missing approved loading strip: {path}"
        assert path.stat().st_size == int(segment["bytes"]), path
        assert sha256(path) == segment["sha256"], path

    actual_names = sorted(path.name for path in STRIPS.glob("*.webp"))
    assert actual_names == sorted(expected_names)


def test_scene_uses_approved_composite_without_duplicate_copy() -> None:
    text = SCENE.read_text(encoding="utf-8")
    assert "res://scripts/menus/loading_screen_approved_composite_v03.gd" in text
    assert 'show_decorative_frame = false' in text
    assert '[node name="TitlePanel"' in text and 'visible = false' in text
    assert '[node name="SubtitlePanel"' in text
    assert '[node name="LoadingLabel"' in text
    assert text.count('visible = false') >= 3
    assert 'text = "Башня, уходящая вниз"' in text


def test_background_renderer_contract() -> None:
    text = BACKGROUND_SCRIPT.read_text(encoding="utf-8")
    assert "Vector2(1672.0, 941.0)" in text
    assert 'SEGMENT_DIRECTORY: String = "res://assets/branding/loading_screen/approved/loading_screen_composite_v03/strips/"' in text
    assert text.count('"loading_screen_composite_c') == 26
    assert "CanvasItem.TEXTURE_FILTER_NEAREST" in text
    assert "SEAM_OVERLAP: float = 0.75" in text
    assert "func has_complete_tiles() -> bool:" in text
    assert "func expected_tile_count() -> int:" in text
