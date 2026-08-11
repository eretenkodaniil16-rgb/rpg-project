from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets/branding/loading_screen/approved/loading_screen_composite_v03"
MANIFEST = ASSET_DIR / "loading_screen_approved_composite_v03.json"
ASSET = ASSET_DIR / "loading_screen_approved_composite_v03.webp"
SCENE = ROOT / "scenes/menus/loading_screen_visual_v02.tscn"
BACKGROUND_SCRIPT = ROOT / "scripts/menus/loading_screen_approved_composite_v03.gd"
TRANSPORT = ROOT / "tools/loading_screen_approved_composite_v03_transport"
MATERIALIZER = ROOT / ".github/workflows/materialize-loading-screen-approved-composite-v03.yml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_contract() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert payload["visual_id"] == "loading_screen_approved_composite_v03"
    assert payload["source_size"] == [768, 432]
    assert payload["source_reference_size"] == [1672, 941]
    assert payload["encoding"] == "webp"
    assert payload["quality"] == 75
    assert payload["pixelation_mode"] == "nearest_neighbor_downscale"
    assert payload["file"] == ASSET.name
    assert payload["bytes"] == 47864
    assert payload["sha256"] == "09484720511999dcff2b7be5311a74dad646d469af0c40b21856092770e38005"


def test_pixel_master_matches_manifest() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert ASSET.is_file(), f"Missing approved loading master: {ASSET}"
    assert ASSET.stat().st_size == int(payload["bytes"])
    assert sha256(ASSET) == payload["sha256"]
    header = ASSET.read_bytes()[:12]
    assert header[:4] == b"RIFF"
    assert header[8:12] == b"WEBP"


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
    assert "Vector2(768.0, 432.0)" in text
    assert 'ASSET_PATH: String = "res://assets/branding/loading_screen/approved/loading_screen_composite_v03/loading_screen_approved_composite_v03.webp"' in text
    assert "CanvasItem.TEXTURE_FILTER_NEAREST" in text
    assert "TEXTURE_REPEAT_DISABLED" in text
    assert "draw_texture_rect" in text
    assert "func has_complete_tiles() -> bool:" in text
    assert "func expected_tile_count() -> int:" in text
    assert "return 1" in text
    assert "SEGMENT_NAMES" not in text
    assert "SEAM_OVERLAP" not in text


def test_materialization_transport_is_not_committed_in_final_package() -> None:
    assert not TRANSPORT.exists(), "Temporary loading transport must be removed after materialization"
    assert not MATERIALIZER.exists(), "One-shot loading materializer must remove itself"


def main() -> None:
    test_manifest_contract()
    test_pixel_master_matches_manifest()
    test_scene_uses_approved_composite_without_duplicate_copy()
    test_background_renderer_contract()
    test_materialization_transport_is_not_committed_in_final_package()
    print("Loading screen approved composite v03 static contracts passed.")


if __name__ == "__main__":
    main()
