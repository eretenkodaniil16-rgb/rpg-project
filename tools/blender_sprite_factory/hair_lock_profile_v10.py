from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


GroovePlane = Literal["XZ", "YZ"]


@dataclass(frozen=True)
class HairLockGrooveV10:
    name: str
    zone: str
    plane: GroovePlane
    fixed_coordinate: float
    points_uv: tuple[tuple[float, float], ...]
    half_width: float

    def assert_valid(self) -> None:
        if len(self.points_uv) != 4:
            raise ValueError(f"Curved lock groove must use four control points: {self.name}")
        if len(set(self.points_uv)) != len(self.points_uv):
            raise ValueError(f"Lock groove points must be unique: {self.name}")
        if not 0.022 <= self.half_width <= 0.032:
            raise ValueError(f"Lock groove width is outside the 96x96 readability budget: {self.name}")
        z_values = [point[1] for point in self.points_uv]
        if max(z_values) - min(z_values) < 0.24:
            raise ValueError(f"Lock groove is too short to survive normalization: {self.name}")
        horizontal_steps = [
            self.points_uv[index + 1][0] - self.points_uv[index][0]
            for index in range(len(self.points_uv) - 1)
        ]
        if max(horizontal_steps) - min(horizontal_steps) < 0.035:
            raise ValueError(f"Lock groove must bend instead of reading as a straight stripe: {self.name}")
        if self.plane == "XZ" and self.zone not in {"front", "back"}:
            raise ValueError(f"XZ grooves are reserved for front/back crown surfaces: {self.name}")
        if self.plane == "YZ" and self.zone not in {"left", "right"}:
            raise ValueError(f"YZ grooves are reserved for physical side surfaces: {self.name}")


@dataclass(frozen=True)
class HairLockProfileV10:
    revision: str
    proxy_revision: str
    mesh_name: str
    material_role: str
    grooves: tuple[HairLockGrooveV10, ...]

    def assert_valid(self) -> None:
        if self.revision != "v10" or self.proxy_revision != "v13":
            raise ValueError("Lock profile must match head v10 / proxy v13")
        if self.mesh_name != "hair_reference_lock_separators_mesh":
            raise ValueError("Unexpected lock separator mesh identity")
        if self.material_role != "separator":
            raise ValueError("Lock separators must use the dedicated darkest palette role")
        if len(self.grooves) != 8:
            raise ValueError("Proxy v13 must keep three front, three back and two side grooves")
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


HUMAN_WARRIOR_M01_HAIR_LOCKS_V10 = HairLockProfileV10(
    revision="v10",
    proxy_revision="v13",
    mesh_name="hair_reference_lock_separators_mesh",
    material_role="separator",
    grooves=(
        HairLockGrooveV10(
            name="hair_lock_groove_front_left",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.505,
            points_uv=((-0.225, 4.855), (-0.155, 4.755), (-0.235, 4.615), (-0.175, 4.475)),
            half_width=0.027,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_front_center",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.507,
            points_uv=((0.020, 4.915), (-0.045, 4.795), (0.020, 4.645), (-0.075, 4.465)),
            half_width=0.027,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_front_right",
            zone="front",
            plane="XZ",
            fixed_coordinate=-0.505,
            points_uv=((0.230, 4.875), (0.175, 4.765), (0.245, 4.620), (0.160, 4.485)),
            half_width=0.025,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_back_left",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.299,
            points_uv=((-0.195, 4.805), (-0.145, 4.665), (-0.230, 4.485), (-0.175, 4.285)),
            half_width=0.026,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_back_center",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.301,
            points_uv=((0.000, 4.865), (0.045, 4.705), (-0.030, 4.500), (0.020, 4.245)),
            half_width=0.027,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_back_right",
            zone="back",
            plane="XZ",
            fixed_coordinate=0.299,
            points_uv=((0.185, 4.785), (0.230, 4.645), (0.145, 4.470), (0.205, 4.295)),
            half_width=0.026,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_side_left",
            zone="left",
            plane="YZ",
            fixed_coordinate=0.451,
            points_uv=((-0.175, 4.775), (-0.035, 4.670), (0.065, 4.515), (0.165, 4.335)),
            half_width=0.024,
        ),
        HairLockGrooveV10(
            name="hair_lock_groove_side_right",
            zone="right",
            plane="YZ",
            fixed_coordinate=-0.451,
            points_uv=((-0.150, 4.755), (0.000, 4.650), (0.105, 4.495), (0.185, 4.345)),
            half_width=0.024,
        ),
    ),
)


def load_hair_lock_profile_v10() -> HairLockProfileV10:
    HUMAN_WARRIOR_M01_HAIR_LOCKS_V10.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_LOCKS_V10
