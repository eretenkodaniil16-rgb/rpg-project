from __future__ import annotations

import argparse
from pathlib import Path

from factory_config import load_factory_config, validate_required_files
from head_profile import load_head_profile
from silhouette_profile import load_silhouette_profile


def main() -> int:
    args = _parse_args()
    repo_root = Path(args.repo_root).resolve()
    manifest = (repo_root / args.config).resolve()
    config = load_factory_config(manifest, repo_root)
    silhouette = load_silhouette_profile(config.character_id)
    head = load_head_profile(config.character_id)
    missing = validate_required_files(config)
    if missing:
        formatted = "\n".join(f"- {config.relative_to_repo(path)}" for path in missing)
        raise FileNotFoundError(f"Reference pack или texture slots неполны:\n{formatted}")

    print(
        "Blender sprite factory contract valid: "
        f"{config.character_id}, "
        f"{config.technical.canvas_width}x{config.technical.canvas_height}, "
        f"height={config.technical.pilot_sprite_height}px, "
        f"baseline={config.technical.baseline_y}, "
        f"camera={config.camera['elevation_degrees']}deg, "
        f"silhouette={silhouette.revision}, "
        f"head={head.revision}, "
        f"proxy={head.proxy_revision}, "
        f"modules={len(config.required_modules)}, "
        f"bones={len(config.required_bones)}."
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the Blender sprite factory contract without Blender."
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[2]),
    )
    parser.add_argument(
        "--config",
        default="tools/blender_sprite_factory/configs/human_warrior_m01.json",
    )
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
