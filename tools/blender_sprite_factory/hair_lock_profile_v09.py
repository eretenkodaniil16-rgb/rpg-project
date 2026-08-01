from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


GroovePlane = Literal["XZ", "YZ"]


@dataclass(frozen=True)
class HairLockGroove:
    name: str
    zone: str
    plane: GroovePlane
    fixed_coordinate: float
    points_uv: tuple[tuple[float, float], ...]
    half_width: float

    def assert_valid(self) -> None:
        if len(self.points_uv) != 3:
            raise ValueError(f"Large lock groove must use exactly three control points: {self.name}")
        if len(set(self.points_uv)) != len(self.points_uv):
            raise ValueError(f"Lock groove points must be unique: {self.name}")
        if not 0.022 <= self.half_width <= 0.034:
            raise ValueError(f"Lock groove width is outside the 96x96 readability budget: {self.name}")
        z_values = [point[1] for point in self.points_uv]
        if max(z_values) - min(z_values) < 0.22:
            raise ValueError(f"Lock groove is too short to survive normalization: {self.name}")
        if self.plane == "XZ" and self.zone not in {"front", "back"}:
            raise ValueError(f"XZ grooves are reserved for front/back crown surfaces: {self.name}")
        if self.plane == "YZ" and self.zone not in {"left", "right"}:
            raise ValueError(f"YZ grooves are reserved for physical side surfaces: {self.name}")


@dataclass(frozen=True)
class HairLockProfileV09:
    revision: str
    proxy_revision: str
    mesh_name: str
    material_role: str
    grooves: tuple[HairLockGroove, ...]

    def assert_valid(self) -> None:
        if self.revision != "v09" or self.proxy_revision != "v12":
            raise ValueError("Lock profile must match head v09 / proxy v12")
        if self.mesh_name != "hair_reference_lock_separators_mesh":
            raise ValueError("Unexpected lock separator mesh identity")
        if self.material_role != "shadow":
            raise ValueError("Lock separators must use the darkest approved hair role")
        if len(self.grooves) != 8:
            raise ValueError("Proxy v12 must use three front, three back and two side grooves")
        names = [item.name for item in self.grooves]
        if len(names) != len(set(names)):
            raise ValueError("Lock groove names must be unique")
        for item in self.grooves:
            item.assert_valid()
        zones = [item.zone for item in self.grooves]
        if zones.count("front") != 3 or zones.count("back") != 3:
            raise ValueError("Crown needs exactly three large front and back separations")
        if zones.count("left") != 1 or zones.count("right") != 1:
            raise ValueError("Each physical side needs exactly one large separation")
        left = next(item for item in self.grooves if item.zone == "left")
        right = next(item for item in self.grooves if item.zone == "right")
        if left.fixed_coordinate <= 0.0 or right.fixed_coordinate >= 0.0:
            raise ValueError("Side grooves must remain on their physical character sides")


HUMAN_WARRIOR_M01_HAIR_LOCKS_V09 = HairLockProfileV09(
    revision="v09",
    proxy_revision="v12",
    mesh_name="hair_reference_lock_separators_mesh",
    material_role="shadow",
    grooves=(
        HairLockGroove(
            name="hair_lock_groove_front_left",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.502,
            points_uv=((-0.180, 4.840), (-0.210, 4.670), (-0.250, 4.480)),
            half_width=0.028,
        ),
        HairLockGroove(
            name="hair_lock_groove_front_center",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.504,
            points_uv=((0.020, 4.900), (-0.020, 4.700), (-0.080, 4.460)),
            half_width=0.027,
        ),
        HairLockGroove(
            name="hair_lock_groove_front_right",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.502,
            points_uv=((0.225, 4.870), (0.210, 4.680), (0.180, 4.480)),
            half_width=0.026,
        ),
        HairLockGroove(
            name="hair_lock_groove_back_left",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.296,
            points_uv=((-0.180, 4.780), (-0.200, 4.550), (-0.200, 4.280)),
            half_width=0.027,
        ),
        HairLockGroove(
            name="hair_lock_groove_back_center",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.298,
            points_uv=((0.000, 4.850), (0.000, 4.570), (0.000, 4.240)),
            half_width=0.028,
        ),
        HairLockGroove(
            name="hair_lock_groove_back_right",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.296,
            points_uv=((0.180, 4.760), (0.200, 4.540), (0.180, 4.290)),
            half_width=0.027,
        ),
        HairLockGroove(
            name="hair_lock_groove_side_left",
            zone="left",
            plane="YZ",
            fixed_coordinate=0.448,
            points_uv=((-0.170, 4.770), (0.020, 4.600), (0.170, 4.330)),
            half_width=0.025,
        ),
        HairLockGroove(
            name="hair_lock_groove_side_right",
            zone="right",
            plane="YZ",
            fixed_coordinate=-0.448,
            points_uv=((-0.150, 4.750), (0.030, 4.580), (0.180, 4.340)),
            half_width=0.025,
        ),
    ),
)


def load_hair_lock_profile_v09() -> HairLockProfileV09:
    HUMAN_WARRIOR_M01_HAIR_LOCKS_V09.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_LOCKS_V09
