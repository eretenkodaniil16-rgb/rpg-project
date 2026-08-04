from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Callable

from PIL import Image


CELL_SIZE = 96
DIRECTIONS = ("down", "left", "right", "up")
EXPECTED_PIXEL_HASHES = {
    "human_warrior_m01_idle_v01.png": "2e5baccebe9e5967d790f82dc01d561204f08b5cef109fc864b2d6b31e968acf",
    "human_warrior_m01_walk_v01.png": "d0b6db19fe90f4556a6f161207c6fb7ed9a0c610ab4b227c02bdb261c5eeb5c1",
    "human_warrior_m01_combat_idle_onehand_v01.png": "3cb88d97055aee7395ad37457eda672a7bdfc0c402a20e2432876f68c746d422",
    "human_warrior_m01_combat_idle_twohand_v01.png": "1353cda714d154a4ea5dbcca541f6cc4b03669e474aee5ce3b3aa7e1f9c4870c",
    "human_warrior_m01_walk_onehand_v01.png": "802f43d11655e5841e718b27d4d93e37dd732a5364797f831524b3b077c61a63",
    "human_warrior_m01_walk_twohand_v01.png": "79fbc8648f0cba0df1b9cb9cb0b92ec2508bd246fcf11ce961dfc75e7cc039ee",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v14-root", required=True, type=Path)
    parser.add_argument("--v16-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def find_frame(root: Path, filename: str) -> Path:
    matches = [path for path in root.rglob(filename) if path.is_file()]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one {filename} under {root}, found {len(matches)}"
        )
    return matches[0]


def load_frame(root: Path, filename: str) -> Image.Image:
    path = find_frame(root, filename)
    image = Image.open(path).convert("RGBA")
    if image.size != (CELL_SIZE, CELL_SIZE):
        raise RuntimeError(f"{filename} must remain 96x96, got {image.size}")
    if not set(image.getchannel("A").getdata()).issubset({0, 255}):
        raise RuntimeError(f"{filename} lost binary alpha")
    return image


def build_atlas(
    root: Path,
    output: Path,
    frame_count: int,
    filename_for: Callable[[str, int], str],
) -> None:
    atlas = Image.new(
        "RGBA",
        (frame_count * CELL_SIZE, len(DIRECTIONS) * CELL_SIZE),
        (0, 0, 0, 0),
    )
    for row, direction in enumerate(DIRECTIONS):
        for column in range(frame_count):
            filename = filename_for(direction, column + 1)
            frame = load_frame(root, filename)
            atlas.alpha_composite(frame, (column * CELL_SIZE, row * CELL_SIZE))
    output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(output, format="PNG", optimize=False)


def verify_pixels(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    actual = hashlib.sha256(image.tobytes()).hexdigest()
    expected = EXPECTED_PIXEL_HASHES[path.name]
    if actual != expected:
        raise RuntimeError(
            f"Deterministic atlas pixels drifted for {path.name}: {actual} != {expected}"
        )


def main() -> int:
    args = parse_args()
    output = args.output
    jobs = (
        (
            args.v14_root,
            output / "human_warrior_m01_idle_v01.png",
            1,
            lambda direction, _frame: (
                f"human_warrior_m01_idle_{direction}_proxy_v25.png"
            ),
        ),
        (
            args.v14_root,
            output / "human_warrior_m01_walk_v01.png",
            6,
            lambda direction, frame: (
                f"human_warrior_m01_walk_{direction}_f{frame:02d}_proxy_v25.png"
            ),
        ),
        (
            args.v14_root,
            output / "human_warrior_m01_combat_idle_onehand_v01.png",
            4,
            lambda direction, frame: (
                "human_warrior_m01_combat_idle_onehand_ready_directional_"
                f"cycle_v14_{direction}_f{frame:02d}_proxy_v25.png"
            ),
        ),
        (
            args.v14_root,
            output / "human_warrior_m01_combat_idle_twohand_v01.png",
            4,
            lambda direction, frame: (
                "human_warrior_m01_combat_idle_twohand_center_high_directional_"
                f"cycle_v14_{direction}_f{frame:02d}_proxy_v25.png"
            ),
        ),
        (
            args.v16_root,
            output / "human_warrior_m01_walk_onehand_v01.png",
            6,
            lambda direction, frame: (
                f"human_warrior_m01_walk_onehand_{direction}_v15_"
                f"f{frame:02d}_proxy_v25.png"
            ),
        ),
        (
            args.v16_root,
            output / "human_warrior_m01_walk_twohand_v01.png",
            6,
            lambda direction, frame: (
                f"human_warrior_m01_walk_twohand_{direction}_v15_"
                f"f{frame:02d}_proxy_v25.png"
            ),
        ),
    )
    for source_root, destination, frame_count, filename_for in jobs:
        build_atlas(source_root, destination, frame_count, filename_for)
        verify_pixels(destination)
        print(f"materialized {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
