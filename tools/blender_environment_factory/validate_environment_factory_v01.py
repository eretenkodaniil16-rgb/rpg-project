from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from environment_profile_v01 import load_environment_profile
from geometry_plan_v01 import floor_blocks


REPO_ROOT = SCRIPT_DIR.parents[1]
CONFIG_PATH = SCRIPT_DIR / "configs/cold_ancient_stone_v01.json"


def main() -> int:
    profile = load_environment_profile(CONFIG_PATH, REPO_ROOT)
    _validate_required_files()
    _validate_python_sources()
    _validate_live_project_dimensions(profile.tile_size, profile.character_sprite_canvas)
    _validate_factory_boundary()
    _validate_deterministic_geometry(profile)
    _validate_workflow_contract()
    _validate_no_unapproved_runtime_assets()
    report = {
        "profile_id": profile.profile_id,
        "profile_sha256": profile.profile_sha256,
        "asset_count": len(profile.assets),
        "floor_variants": len(profile.assets_of_kind("floor")),
        "combat_cell_size": profile.tile_size,
        "character_sprite_canvas": profile.character_sprite_canvas,
        "camera_elevation_degrees": profile.elevation_degrees,
        "stage": profile.stage,
        "status": "static_contract_valid_real_blender_render_required",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _validate_required_files() -> None:
    required = (
        REPO_ROOT / "RUN_BLENDER_ENVIRONMENT_FACTORY_V01.cmd",
        REPO_ROOT / "docs/BLENDER_ENVIRONMENT_FACTORY_V01.md",
        REPO_ROOT / ".github/workflows/validate-blender-environment-v01.yml",
        SCRIPT_DIR / "README.md",
        SCRIPT_DIR / "environment_profile_v01.py",
        SCRIPT_DIR / "geometry_plan_v01.py",
        SCRIPT_DIR / "blender_environment_factory_v01.py",
        SCRIPT_DIR / "postprocess_environment_run_v01.py",
        SCRIPT_DIR / "run_blender_environment_factory_v01.ps1",
        SCRIPT_DIR / "tests/test_environment_profile_v01.py",
        SCRIPT_DIR / "tests/test_geometry_plan_v01.py",
        SCRIPT_DIR / "tests/test_postprocess_environment_run_v01.py",
    )
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Environment Factory неполна: {missing}")


def _validate_python_sources() -> None:
    for path in sorted(SCRIPT_DIR.rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _validate_live_project_dimensions(tile_size: int, sprite_canvas: int) -> None:
    distance_source = (
        REPO_ROOT / "scripts/systems/distance_system.gd"
    ).read_text(encoding="utf-8")
    distance_match = re.search(
        r"PIXELS_PER_5_FEET:\s*float\s*=\s*([0-9.]+)", distance_source
    )
    if distance_match is None:
        raise ValueError("Не найден live PIXELS_PER_5_FEET")
    live_tile_size = int(float(distance_match.group(1)))
    if live_tile_size != tile_size:
        raise ValueError(
            f"Profile tile_size={tile_size}, live grid={live_tile_size}; "
            "арт не должен молча менять механику"
        )

    animation_source = (
        REPO_ROOT / "scripts/game/human_warrior_animation_library.gd"
    ).read_text(encoding="utf-8")
    canvas_match = re.search(
        r"EXPECTED_CELL_SIZE:\s*int\s*=\s*([0-9]+)", animation_source
    )
    if canvas_match is None:
        raise ValueError("Не найден live EXPECTED_CELL_SIZE")
    live_sprite_canvas = int(canvas_match.group(1))
    if live_sprite_canvas != sprite_canvas:
        raise ValueError(
            f"Profile sprite_canvas={sprite_canvas}, live canvas={live_sprite_canvas}"
        )


def _validate_factory_boundary() -> None:
    blender_source = (SCRIPT_DIR / "blender_environment_factory_v01.py").read_text(
        encoding="utf-8"
    )
    postprocess_source = (
        SCRIPT_DIR / "postprocess_environment_run_v01.py"
    ).read_text(encoding="utf-8")
    profile_source = (SCRIPT_DIR / "environment_profile_v01.py").read_text(
        encoding="utf-8"
    )
    geometry_source = (SCRIPT_DIR / "geometry_plan_v01.py").read_text(
        encoding="utf-8"
    )
    if "import bpy" not in blender_source:
        raise ValueError("Blender entrypoint не использует bpy")
    if "from PIL" in blender_source:
        raise ValueError("Blender entrypoint не должен зависеть от внешнего Pillow")
    if "from PIL" not in postprocess_source:
        raise ValueError("Postprocessor должен явно использовать Pillow")
    if "import bpy" in profile_source or "import bpy" in geometry_source:
        raise ValueError("Чистые profile/geometry модули не должны импортировать Blender")
    required_tokens = (
        'scene["combat_cell_size_px"] = profile.tile_size',
        'scene["character_sprite_canvas_px"] = profile.character_sprite_canvas',
        'scene["runtime_filter"] = "NEAREST"',
        'scene["walls_and_doors_placement"] = "cell_edges"',
        'scene["local_light_baked_into_floor"] = False',
        'camera_data.type = "ORTHO"',
    )
    for token in required_tokens:
        if token not in blender_source:
            raise ValueError(f"Blender contract marker отсутствует: {token}")


def _validate_deterministic_geometry(profile) -> None:
    signatures = []
    for asset in profile.assets_of_kind("floor"):
        first = floor_blocks(asset)
        second = floor_blocks(asset)
        if first != second:
            raise ValueError(f"Недетерминированная floor geometry: {asset.asset_id}")
        signatures.append(first)
    if len(set(signatures)) != 8:
        raise ValueError("Восемь floor variants должны иметь разные geometry signatures")


def _validate_workflow_contract() -> None:
    workflow = (
        REPO_ROOT / ".github/workflows/validate-blender-environment-v01.yml"
    ).read_text(encoding="utf-8")
    required_tokens = (
        "workflow_dispatch:",
        "tools/blender-environment-tiles-v01",
        "blender-5.2.0-linux-x64.tar.xz",
        "96f6c181a30f4950607839dc84d42a354b250d8a0231b098b59b7bc69c351c48",
        "postprocess_environment_run_v01.py",
        "art/blender_environment_runs/cold_ancient_stone_v01/**",
    )
    for token in required_tokens:
        if token not in workflow:
            raise ValueError(f"CI render contract отсутствует: {token}")


def _validate_no_unapproved_runtime_assets() -> None:
    approved_root = REPO_ROOT / "assets/environment"
    if not approved_root.exists():
        return
    forbidden = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in approved_root.rglob("*")
        if path.is_file() and "cold_ancient_stone_v01" in path.as_posix()
    ]
    if forbidden:
        raise ValueError(
            f"Review assets преждевременно попали в runtime: {forbidden}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
