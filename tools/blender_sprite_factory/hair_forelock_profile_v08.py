from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HairForelockSlice:
    y: float
    points_xz: tuple[tuple[float, float], ...]

    def assert_valid(self, expected_points: int) -> None:
        if len(self.points_xz) != expected_points:
            raise ValueError("Every forelock slice must use the same point count")
        if len(set(self.points_xz)) != len(self.points_xz):
            raise ValueError("Forelock slice points must be unique")
        x_values = [point[0] for point in self.points_xz]
        z_values = [point[1] for point in self.points_xz]
        if max(x_values) >= 0.08 or min(x_values) > -0.18:
            raise ValueError("Canonical forelock must stay on the character-left forehead")
        if max(z_values) - min(z_values) < 0.34:
            raise ValueError("Forelock must remain long enough to read at 96x96")


@dataclass(frozen=True)
class HairForelockProfileV08:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairForelockSlice, ...]

    def assert_valid(self) -> None:
        if self.revision != "v08" or self.proxy_revision != "v11":
            raise ValueError("Forelock profile must match head v08 / proxy v11")
        if self.mesh_name != "hair_reference_forelock_mesh":
            raise ValueError("Unexpected forelock mesh identity")
        if len(self.slices) != 3:
            raise ValueError("Forelock must use front, middle and root slices")
        point_count = len(self.slices[0].points_xz)
        if point_count != 7:
            raise ValueError("Forelock needs seven coarse contour points")
        for item in self.slices:
            item.assert_valid(point_count)
        y_values = [item.y for item in self.slices]
        if y_values != sorted(y_values):
            raise ValueError("Forelock slices must run from camera-facing tip to embedded root")
        if self.slices[0].y > -0.54:
            raise ValueError("Forelock front must project ahead of the face")
        if self.slices[-1].y < -0.42:
            raise ValueError("Forelock root must embed into the crown")

        front = self.slices[0].points_xz
        lowest = min(front, key=lambda point: point[1])
        if not (-0.16 <= lowest[0] <= -0.06):
            raise ValueError("Forelock tip must descend near the canonical left forehead")
        if not 4.27 <= lowest[1] <= 4.34:
            raise ValueError("Forelock tip must stop above the eye line")
        if max(point[1] for point in front) < 4.68:
            raise ValueError("Forelock root needs enough overlap with the crown")


HUMAN_WARRIOR_M01_HAIR_FORELOCK_V08 = HairForelockProfileV08(
    revision="v08",
    proxy_revision="v11",
    mesh_name="hair_reference_forelock_mesh",
    slices=(
        HairForelockSlice(
            y=-0.575,
            points_xz=(
                (-0.235, 4.520),
                (-0.185, 4.665),
                (-0.075, 4.720),
                (0.015, 4.625),
                (-0.035, 4.455),
                (-0.105, 4.300),
                (-0.185, 4.385),
            ),
        ),
        HairForelockSlice(
            y=-0.500,
            points_xz=(
                (-0.215, 4.535),
                (-0.170, 4.670),
                (-0.075, 4.710),
                (0.005, 4.620),
                (-0.035, 4.475),
                (-0.105, 4.325),
                (-0.175, 4.405),
            ),
        ),
        HairForelockSlice(
            y=-0.405,
            points_xz=(
                (-0.190, 4.550),
                (-0.150, 4.670),
                (-0.070, 4.695),
                (-0.005, 4.615),
                (-0.040, 4.495),
                (-0.105, 4.350),
                (-0.165, 4.425),
            ),
        ),
    ),
)


def load_hair_forelock_profile_v08() -> HairForelockProfileV08:
    HUMAN_WARRIOR_M01_HAIR_FORELOCK_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_FORELOCK_V08
