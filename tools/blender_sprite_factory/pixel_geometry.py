from __future__ import annotations

from collections.abc import Sequence


BoundingBox = tuple[int, int, int, int]


def alpha_bbox(
    pixels: Sequence[float],
    width: int,
    height: int,
    threshold: float,
) -> BoundingBox | None:
    _validate_canvas(pixels, width, height)
    min_x = width
    min_y = height
    max_x = -1
    max_y = -1
    for y in range(height):
        for x in range(width):
            alpha = pixels[(y * width + x) * 4 + 3]
            if alpha <= threshold:
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if max_x < 0:
        return None
    return min_x, min_y, max_x, max_y


def anchor_rgba_to_baseline(
    pixels: Sequence[float],
    width: int,
    height: int,
    baseline_y: int,
    threshold: float,
) -> tuple[list[float], BoundingBox]:
    """Move the visible silhouette vertically onto a top-down baseline."""
    if not 0 <= baseline_y < height:
        raise ValueError("baseline_y must be inside the canvas")

    bbox = alpha_bbox(pixels, width, height, threshold)
    if bbox is None:
        raise ValueError("cannot anchor a canvas without a visible silhouette")

    min_x, min_y, max_x, max_y = bbox
    target_min_y = height - 1 - baseline_y
    delta_y = target_min_y - min_y
    shifted_max_y = max_y + delta_y
    if target_min_y < 0 or shifted_max_y >= height:
        raise ValueError(
            "anchoring the silhouette would crop visible pixels: "
            f"source_y={min_y}..{max_y}, target_y={target_min_y}..{shifted_max_y}"
        )

    if delta_y == 0:
        return list(pixels), bbox

    anchored = [0.0] * len(pixels)
    row_stride = width * 4
    for source_y in range(min_y, max_y + 1):
        target_y = source_y + delta_y
        source_start = source_y * row_stride
        target_start = target_y * row_stride
        anchored[target_start : target_start + row_stride] = pixels[
            source_start : source_start + row_stride
        ]

    anchored_bbox = alpha_bbox(anchored, width, height, threshold)
    if anchored_bbox is None:
        raise RuntimeError("baseline anchoring removed the visible silhouette")
    if anchored_bbox[1] != target_min_y:
        raise RuntimeError(
            f"baseline anchoring failed: {anchored_bbox[1]} instead of {target_min_y}"
        )
    return anchored, anchored_bbox


def _validate_canvas(
    pixels: Sequence[float],
    width: int,
    height: int,
) -> None:
    if width <= 0 or height <= 0:
        raise ValueError("canvas dimensions must be positive")
    expected_length = width * height * 4
    if len(pixels) != expected_length:
        raise ValueError(
            f"RGBA buffer has {len(pixels)} values instead of {expected_length}"
        )
