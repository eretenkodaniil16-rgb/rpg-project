from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


CELL_SIZE = 96
BASELINE_Y = 91
DIRECTIONS = ("down", "left", "right", "up")
FRAMES = tuple(range(1, 9))
ONEHAND_ARTIFACT_ID = 8932504901
TWOHAND_ARTIFACT_ID = 8913799114
ONEHAND_ARTIFACT_SHA256 = (
    "da09d827e77a61e554b257f42fd4d78ea1c590ca20ae81018d567f578595007b"
)
TWOHAND_ARTIFACT_SHA256 = (
    "5c3f5ede5f50c72952b7f52d67b1e7d2e51d52aba83d6cd074a55c07e5262f38"
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--onehand-root", type=Path, required=True)
    parser.add_argument("--twohand-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--lock-path", type=Path, required=True)
    return parser.parse_args()


def _find_onehand_frame(root: Path, direction: str, frame: int) -> Path:
    revision = "v20" if direction == "down" else "v21"
    name = (
        "human_warrior_m01_attack_sword_01_onehand_"
        f"{direction}_{revision}_f{frame:02d}_proxy_v25.png"
    )
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one frame {name}, found {len(matches)}")
    return matches[0]


def _find_twohand_frame(root: Path, direction: str, frame: int) -> Path:
    name = (
        "human_warrior_m01_attack_sword_01_twohand_"
        f"{direction}_overhead_v21_f{frame:02d}_proxy_v25.png"
    )
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one frame {name}, found {len(matches)}")
    return matches[0]


def _validate_frame(path: Path, *, require_edge_alpha_zero: bool) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    if image.size != (CELL_SIZE, CELL_SIZE):
        raise RuntimeError(f"invalid frame size: {path}={image.size}")

    alpha = image.getchannel("A")
    values = set(alpha.getdata())
    if not values or not values.issubset({0, 255}):
        raise RuntimeError(f"non-binary alpha: {path}={sorted(values)[:8]}")

    bbox = alpha.getbbox()
    if bbox is None:
        raise RuntimeError(f"empty frame: {path}")
    if bbox[3] - 1 != BASELINE_Y:
        raise RuntimeError(
            f"baseline drift: {path}={bbox[3] - 1}, expected={BASELINE_Y}"
        )

    if require_edge_alpha_zero:
        pixels = alpha.load()
        edge_values = []
        for x in range(CELL_SIZE):
            edge_values.extend((pixels[x, 0], pixels[x, CELL_SIZE - 1]))
        for y in range(CELL_SIZE):
            edge_values.extend((pixels[0, y], pixels[CELL_SIZE - 1, y]))
        if max(edge_values) != 0:
            raise RuntimeError(f"frame touches canvas edge: {path}")
    return image


def _assemble_atlas(frame_resolver: object, root: Path, output_path: Path) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    atlas = Image.new(
        "RGBA",
        (CELL_SIZE * len(FRAMES), CELL_SIZE * len(DIRECTIONS)),
        (0, 0, 0, 0),
    )
    frame_hashes: dict[str, str] = {}
    first_last_identical: dict[str, bool] = {}

    for row, direction in enumerate(DIRECTIONS):
        direction_images: list[Image.Image] = []
        for column, frame_number in enumerate(FRAMES):
            path = frame_resolver(root, direction, frame_number)
            image = _validate_frame(path, require_edge_alpha_zero=True)
            direction_images.append(image)
            atlas.paste(image, (column * CELL_SIZE, row * CELL_SIZE))
            frame_hashes[f"{direction}/f{frame_number:02d}"] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        first_last_identical[direction] = (
            direction_images[0].tobytes() == direction_images[-1].tobytes()
        )
        if not first_last_identical[direction]:
            raise RuntimeError(f"f01/f08 mismatch for {direction}: {output_path.name}")

    atlas.save(output_path, format="PNG", optimize=False, compress_level=9)
    return {
        "path": output_path.as_posix(),
        "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "size": list(atlas.size),
        "frame_hashes": frame_hashes,
        "first_last_identical": first_last_identical,
    }


def _hash_existing_atlases(output_dir: Path) -> dict[str, str]:
    expected = (
        "human_warrior_m01_idle_v01.png",
        "human_warrior_m01_walk_v01.png",
        "human_warrior_m01_combat_idle_onehand_v01.png",
        "human_warrior_m01_combat_idle_twohand_v01.png",
        "human_warrior_m01_walk_onehand_v01.png",
        "human_warrior_m01_walk_twohand_v01.png",
    )
    hashes: dict[str, str] = {}
    for name in expected:
        path = output_dir / name
        if not path.is_file():
            raise RuntimeError(f"approved atlas is missing: {path}")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def main() -> int:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    onehand_path = args.output_dir / "human_warrior_m01_attack_sword_01_onehand_v01.png"
    twohand_path = args.output_dir / "human_warrior_m01_attack_sword_01_twohand_v01.png"
    onehand = _assemble_atlas(_find_onehand_frame, args.onehand_root, onehand_path)
    twohand = _assemble_atlas(_find_twohand_frame, args.twohand_root, twohand_path)

    payload = {
        "revision": "animation_assets_v01",
        "cell_size": CELL_SIZE,
        "baseline_y": BASELINE_Y,
        "direction_order": list(DIRECTIONS),
        "existing_atlas_sha256": _hash_existing_atlases(args.output_dir),
        "attack_atlases": {"onehand": onehand, "twohand": twohand},
        "source_artifacts": {
            "onehand": {
                "artifact_id": ONEHAND_ARTIFACT_ID,
                "artifact_sha256": ONEHAND_ARTIFACT_SHA256,
            },
            "twohand": {
                "artifact_id": TWOHAND_ARTIFACT_ID,
                "artifact_sha256": TWOHAND_ARTIFACT_SHA256,
            },
        },
    }
    args.lock_path.parent.mkdir(parents=True, exist_ok=True)
    args.lock_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
