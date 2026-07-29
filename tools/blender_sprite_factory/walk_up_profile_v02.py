from __future__ import annotations

from dataclasses import dataclass, replace

from walk_up_profile_v01 import (
    WalkUpFramePoseV01,
    load_walk_up_profile_v01,
)


@dataclass(frozen=True)
class WalkUpProfileV02:
    revision: str
    animation_revision: str
    animation_id: str
    direction: str
    fps: int
    loop: bool
    poses: tuple[WalkUpFramePoseV01, ...]

    def assert_valid(self) -> None:
        if self.revision != "v02" or self.animation_revision != "v02":
            raise ValueError("Walk up correction must remain data v02 / animation v02")
        if self.animation_id != "walk_up" or self.direction != "up":
            raise ValueError("Walk up v02 must retain the real rear direction")
        if self.fps != 8 or not self.loop or len(self.poses) != 6:
            raise ValueError("Walk up v02 must remain a six-frame 8 FPS loop")

        base = load_walk_up_profile_v01("human_warrior_m01")
        if self.poses[:5] != base.poses[:5]:
            raise ValueError("Walk up v02 may only correct physical_right_passing")
        corrected = self.poses[5]
        if corrected.phase != "physical_right_passing" or corrected.frame != 6:
            raise ValueError("Walk up v02 corrected an incorrect phase")
        if (
            corrected.thigh_left_x_degrees,
            corrected.thigh_right_x_degrees,
            corrected.shin_left_x_degrees,
            corrected.shin_right_x_degrees,
            corrected.foot_left_x_degrees,
            corrected.foot_right_x_degrees,
        ) != (10.0, -4.0, 6.0, -4.0, 0.0, 5.0):
            raise ValueError("Walk up v02 rear passing leg correction drifted")

        first = self.poses[0].numeric_channels()
        last = corrected.numeric_channels()
        if max(abs(end - start) for start, end in zip(first, last)) > 10.0:
            raise ValueError("Walk up v02 loop wrap exceeds ten degrees")
        if max(
            abs(corrected.thigh_left_x_degrees),
            abs(corrected.thigh_right_x_degrees),
        ) > 16.0:
            raise ValueError("Walk up v02 thigh correction exceeds the budget")
        if max(
            abs(corrected.shin_left_x_degrees),
            abs(corrected.shin_right_x_degrees),
        ) > 12.0:
            raise ValueError("Walk up v02 shin correction exceeds the budget")
        if max(
            abs(corrected.foot_left_x_degrees),
            abs(corrected.foot_right_x_degrees),
        ) > 7.0:
            raise ValueError("Walk up v02 foot correction exceeds the budget")


_BASE = load_walk_up_profile_v01("human_warrior_m01")
_CORRECTED_F06 = replace(
    _BASE.poses[5],
    thigh_left_x_degrees=10.0,
    thigh_right_x_degrees=-4.0,
    shin_left_x_degrees=6.0,
    shin_right_x_degrees=-4.0,
    foot_left_x_degrees=0.0,
    foot_right_x_degrees=5.0,
)

HUMAN_WARRIOR_M01_WALK_UP_V02 = WalkUpProfileV02(
    revision="v02",
    animation_revision="v02",
    animation_id="walk_up",
    direction="up",
    fps=8,
    loop=True,
    poses=(*_BASE.poses[:5], _CORRECTED_F06),
)


def load_walk_up_profile_v02(character_id: str) -> WalkUpProfileV02:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No walk_up v02 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_WALK_UP_V02.assert_valid()
    return HUMAN_WARRIOR_M01_WALK_UP_V02
