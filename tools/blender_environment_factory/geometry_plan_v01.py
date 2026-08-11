from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from environment_profile_v01 import AssetSpec


@dataclass(frozen=True)
class StoneBlock:
    center_x: float
    center_y: float
    width: float
    depth: float
    height: float
    tone_index: int
    bevel: float


@dataclass(frozen=True)
class LineSegment:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    width: float
    tone_index: int


@dataclass(frozen=True)
class Spot:
    center_x: float
    center_y: float
    radius_x: float
    radius_y: float
    tone_index: int


def floor_blocks(asset: AssetSpec) -> tuple[StoneBlock, ...]:
    if asset.kind != "floor":
        raise ValueError(f"floor_blocks ожидает floor, получено {asset.kind}")
    blocks: list[StoneBlock] = []
    groove = 0.024
    row_edges = (-0.5, -0.18, 0.15, 0.5)
    column_edges = (
        (-0.5, -0.18, 0.19, 0.5),
        (-0.5, -0.29, 0.08, 0.5),
        (-0.5, -0.07, 0.26, 0.5),
    )
    for row in range(3):
        for column in range(3):
            index = row * 3 + column
            common_seed = 9000 + index
            variable_seed = asset.seed if index in {1, 3, 4, 5, 7} else common_seed
            start_x = column_edges[row][column]
            end_x = column_edges[row][column + 1]
            start_y = row_edges[row]
            end_y = row_edges[row + 1]
            width = end_x - start_x - groove
            depth = end_y - start_y - groove
            height = 0.055 + _unit(variable_seed, 5) * 0.035
            tone_index = 5 + int(_unit(variable_seed, 6) * 5.0)
            blocks.append(
                StoneBlock(
                    center_x=(start_x + end_x) * 0.5,
                    center_y=(start_y + end_y) * 0.5,
                    width=width,
                    depth=depth,
                    height=height,
                    tone_index=min(tone_index, 9),
                    bevel=0.012 + _unit(common_seed, 7) * 0.009,
                )
            )
    return tuple(blocks)


def crack_segments(asset: AssetSpec) -> tuple[LineSegment, ...]:
    if asset.shape != "crack":
        raise ValueError("crack_segments требует decal shape=crack")
    points: list[tuple[float, float]] = [(-0.31, -0.20)]
    for index in range(1, 6):
        ratio = index / 5.0
        points.append(
            (
                -0.31 + ratio * 0.64 + _signed(asset.seed, index * 2) * 0.055,
                -0.20 + ratio * 0.43 + _signed(asset.seed, index * 2 + 1) * 0.075,
            )
        )
    segments = [
        LineSegment(
            start_x=points[index][0],
            start_y=points[index][1],
            end_x=points[index + 1][0],
            end_y=points[index + 1][1],
            width=0.010 + _unit(asset.seed, 40 + index) * 0.009,
            tone_index=1 if index % 2 == 0 else 2,
        )
        for index in range(len(points) - 1)
    ]
    branch_origin = points[2]
    segments.append(
        LineSegment(
            start_x=branch_origin[0],
            start_y=branch_origin[1],
            end_x=branch_origin[0] - 0.13,
            end_y=branch_origin[1] + 0.16,
            width=0.009,
            tone_index=1,
        )
    )
    return tuple(segments)


def dust_spots(asset: AssetSpec) -> tuple[Spot, ...]:
    if asset.shape != "dust":
        raise ValueError("dust_spots требует decal shape=dust")
    spots: list[Spot] = []
    for index in range(18):
        angle = _unit(asset.seed, index * 5) * math.tau
        radius = 0.08 + _unit(asset.seed, index * 5 + 1) * 0.30
        spots.append(
            Spot(
                center_x=math.cos(angle) * radius,
                center_y=math.sin(angle) * radius * 0.72,
                radius_x=0.010 + _unit(asset.seed, index * 5 + 2) * 0.025,
                radius_y=0.008 + _unit(asset.seed, index * 5 + 3) * 0.018,
                tone_index=8 + int(_unit(asset.seed, index * 5 + 4) * 3.0),
            )
        )
    return tuple(spots)


def damp_spots(asset: AssetSpec, count: int = 12) -> tuple[Spot, ...]:
    if asset.kind not in {"decal", "transition"}:
        raise ValueError("damp_spots поддерживает decal/transition")
    spots: list[Spot] = []
    orientation_bias = {
        "north": (0.0, -0.24),
        "east": (0.24, 0.0),
        "south": (0.0, 0.24),
        "west": (-0.24, 0.0),
    }.get(asset.orientation, (0.0, 0.0))
    for index in range(count):
        center_x = _signed(asset.seed, index * 6) * 0.34 + orientation_bias[0]
        center_y = _signed(asset.seed, index * 6 + 1) * 0.31 + orientation_bias[1]
        if asset.kind == "transition":
            if asset.orientation == "north":
                center_y = -0.28 + _unit(asset.seed, index * 6 + 1) * 0.30
            elif asset.orientation == "south":
                center_y = 0.28 - _unit(asset.seed, index * 6 + 1) * 0.30
            elif asset.orientation == "east":
                center_x = 0.28 - _unit(asset.seed, index * 6) * 0.30
            elif asset.orientation == "west":
                center_x = -0.28 + _unit(asset.seed, index * 6) * 0.30
        spots.append(
            Spot(
                center_x=max(-0.48, min(0.48, center_x)),
                center_y=max(-0.48, min(0.48, center_y)),
                radius_x=0.08 + _unit(asset.seed, index * 6 + 2) * 0.12,
                radius_y=0.06 + _unit(asset.seed, index * 6 + 3) * 0.10,
                tone_index=13 + int(_unit(asset.seed, index * 6 + 4) * 3.0),
            )
        )
    return tuple(spots)


def _unit(seed: int, channel: int) -> float:
    payload = f"{seed}:{channel}:cold_ancient_stone_v01".encode("ascii")
    digest = hashlib.sha256(payload).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float((1 << 64) - 1)


def _signed(seed: int, channel: int) -> float:
    return _unit(seed, channel) * 2.0 - 1.0
