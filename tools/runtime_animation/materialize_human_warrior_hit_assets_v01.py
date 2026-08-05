from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image


CELL_SIZE = 96
FRAME_COUNT = 6
DIRECTIONS = ("down", "left", "right", "up")
GRIPS = ("onehand", "twohand")
EXPECTED_ATLAS_SHA256 = {
    "onehand": "77ebc7a5148891f5e9feff6a293eab681eb12744254a7d3e65f6bb1e1fced5ea",
    "twohand": "f863064b643e396779a1a99f181e0b83285b0a858f75123b3eeb1a8cf03d5238",
}


def frame_path(frames_dir: Path, grip: str, direction: str, frame_number: int) -> Path:
    prefix = f"human_warrior_m01_hit_01_{grip}_down_v01"
    if direction == "down":
        filename = f"{prefix}_f{frame_number:02d}_proxy_v25.png"
    else:
        filename = f"{prefix}_{direction}_f{frame_number:02d}_proxy_v25.png"
    return frames_dir / filename


def validate_frame(path: Path) -> Image.Image:
    if not path.is_file():
        raise FileNotFoundError(path)
    image = Image.open(path).convert("RGBA")
    if image.size != (CELL_SIZE, CELL_SIZE):
        raise ValueError(f"unexpected frame size for {path}: {image.size}")
    alpha_values = set(image.getchannel("A").getdata())
    if not alpha_values.issubset({0, 255}):
        raise ValueError(f"non-binary alpha in {path}")
    bbox = image.getchannel("A").getbbox()
    if bbox is None or bbox[3] - 1 != 91:
        raise ValueError(f"baseline mismatch in {path}: {bbox}")
    return image


def build_atlas(frames_dir: Path, output_dir: Path, grip: str) -> Path:
    atlas = Image.new(
        "RGBA",
        (CELL_SIZE * FRAME_COUNT, CELL_SIZE * len(DIRECTIONS)),
        (0, 0, 0, 0),
    )
    for row, direction in enumerate(DIRECTIONS):
        for column in range(FRAME_COUNT):
            source = frame_path(frames_dir, grip, direction, column + 1)
            frame = validate_frame(source)
            atlas.alpha_composite(frame, (column * CELL_SIZE, row * CELL_SIZE))
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"human_warrior_m01_hit_01_{grip}_v01.png"
    atlas.save(output, optimize=False)
    actual_sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    expected_sha256 = EXPECTED_ATLAS_SHA256[grip]
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"atlas hash mismatch for {grip}: {actual_sha256} != {expected_sha256}"
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    frames_dirs = list(args.artifact_root.glob("**/31044413873_1/frames"))
    if len(frames_dirs) != 1:
        raise RuntimeError(f"expected one source frames directory, found {frames_dirs}")
    for grip in GRIPS:
        output = build_atlas(frames_dirs[0], args.output_dir, grip)
        print(f"materialized {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
