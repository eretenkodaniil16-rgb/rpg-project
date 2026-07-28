from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


GroovePlane = Literal["XZ", "YZ"]


@dataclass(frozen=True)
class HairLockGrooveV11:
    name: str
    zone: str
    plane: GroovePlane
    fixed_coordinate: float
    points_uv: tuple[tuple[float, float], ...]
    half_width: float

    def assert_valid(self) -> None:
        if len(self.points_uv) != 4:
            raise ValueError(f"Localized lock groove must use four control points: {self.name}")
        if len(set(self.points_uv)) != len(self.points_uv):
            raise ValueError(f"Lock groove points must be unique: {self.name}")
        if not 0.020 <= self.half_width <= 0.028:
            raise ValueError(f"Lock groove width is outside the 96x96 readability budget: {self.name}")

        z_values = [point[1] for point in self.points_uv]
        z_span = max(z_values) - min(z_values)
        if not 0.16 <= z_span <= 0.30:
            raise ValueError(f"Lock groove must remain a short local depression: {self.name}")
        u_values = [point[0] for point in self.points_uv]
        if max(u_values) - min(u_values) < 0.07:
            raise ValueError(f"Lock groove must bend diagonally instead of reading as a stripe: {self.name}")

        if self.plane == "XZ" and self.zone not in {"front", "back"}:
            raise ValueError(f"XZ grooves are reserved for front/back crown surfaces: {self.name}")
        if self.plane == "YZ" and self.zone not in {"left", "right"}:
            raise ValueError(f"YZ grooves are reserved for physical side surfaces: {self.name}")


@dataclass(frozen=True)
class HairLockProfileV11:
    revision: str
    proxy_revision: str
    mesh_name: str
    material_role: str
    grooves: tuple[HairLockGrooveV11, ...]

    def assert_valid(self) -> None:
        if self.revision != "v11" or self.proxy_revision != "v14":
            raise ValueError("Lock profile must match head v11 / proxy v14")
        if self.mesh_name != "hair_reference_lock_separators_mesh":
            raise ValueError("Unexpected lock separator mesh identity")
        if self.material_role != "separator":
            raise ValueError("Localized lock grooves must retain the darkest palette role")
        if len(self.grooves) != 6:
            raise ValueError("Proxy v14 must use two front, two back and two side grooves")

        names = [item.name for item in self.grooves]
        if len(names) != len(set(names)):
            raise ValueError("Lock groove names must be unique")
        for item in self.grooves:
            item.assert_valid()

        zones = [item.zone for item in self.grooves]
        if zones.count("front") != 2 or zones.count("back") != 2:
            raise ValueError("Crown needs exactly two localized front and back depressions")
        if zones.count("left") != 1 or zones.count("right") != 1:
            raise ValueError("Each physical side needs exactly one localized depression")
        left = next(item for item in self.grooves if item.zone == "left")
        right = next(item for item in self.grooves if item.zone == "right")
        if left.fixed_coordinate <= 0.0 or right.fixed_coordinate >= 0.0:
            raise ValueError("Side grooves must remain on their physical character sides")


HUMAN_WARRIOR_M01_HAIR_LOCKS_V11 = HairLockProfileV11(
    revision="v11",
    proxy_revision="v14",
    mesh_name="hair_reference_lock_separators_mesh",
    material_role="separator",
    grooves=(
        HairLockGrooveV11(
            name="hair_lock_groove_front_left_local",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.512,
            points_uv=((-0.235, 4.900), (-0.180, 4.850), (-0.210, 4.765), (-0.145, 4.690)),
            half_width=0.024,
        ),
        HairLockGrooveV11(
            name="hair_lock_groove_front_right_local",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.512,
            points_uv=((0.050, 4.930), (0.120, 4.875), (0.095, 4.790), (0.175, 4.710)),
            half_width=0.023,
        ),
        HairLockGrooveV11(
            name="hair_lock_groove_back_left_local",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.307,
            points_uv=((-0.220, 4.810), (-0.160, 4.740), (-0.205, 4.630), (-0.135, 4.535)),
            half_width=0.024,
        ),
        HairLockGrooveV11(
            name="hair_lock_groove_back_right_local",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.307,
            points_uv=((0.050, 4.825), (0.120, 4.755), (0.085, 4.645), (0.165, 4.555)),
            half_width=0.024,
        ),
        HairLockGrooveV11(
            name="hair_lock_groove_side_left_local",
            zone="left",
            plane="YZ",
            fixed_coordinate=0.456,
            points_uv=((-0.080, 4.720), (-0.010, 4.660), (0.070, 4.570), (0.150, 4.470)),
            half_width=0.022,
        ),
        HairLockGrooveV11(
            name="hair_lock_groove_side_right_local",
            zone="right",
            plane="YZ",
            fixed_coordinate=-0.456,
            points_uv=((-0.100, 4.700), (-0.020, 4.640), (0.080, 4.550), (0.160, 4.460)),
            half_width=0.022,
        ),
    ),
)


def load_hair_lock_profile_v11() -> HairLockProfileV11:
    HUMAN_WARRIOR_M01_HAIR_LOCKS_V11.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_LOCKS_V11
