from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HairForelockSliceV11:
    y: float
    points_xz: tuple[tuple[float, float], ...]

    def assert_valid(self, expected_points: int) -> None:
        if len(self.points_xz) != expected_points:
            raise ValueError("Every forelock slice must use the same point count")
        if len(set(self.points_xz)) != len(self.points_xz):
            raise ValueError("Forelock slice points must be unique")
        x_values = [point[0] for point in self.points_xz]
        z_values = [point[1] for point in self.points_xz]
        if max(x_values) > 0.04 or min(x_values) > -0.22:
            raise ValueError("Canonical forelock must stay on the character-left forehead")
        if max(z_values) - min(z_values) < 0.45:
            raise ValueError("Forelock must be large enough to survive 96x96 normalization")


@dataclass(frozen=True)
class HairForelockProfileV11:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairForelockSliceV11, ...]

    def assert_valid(self) -> None:
        if self.revision != "v11" or self.proxy_revision != "v14":
            raise ValueError("Forelock profile must match head v11 / proxy v14")
        if self.mesh_name != "hair_reference_forelock_mesh":
            raise ValueError("Unexpected forelock mesh identity")
        if len(self.slices) != 3:
            raise ValueError("Forelock must keep front, middle and embedded root slices")

        point_count = len(self.slices[0].points_xz)
        if point_count != 7:
            raise ValueError("Forelock needs seven coarse contour points")
        for item in self.slices:
            item.assert_valid(point_count)

        y_values = [item.y for item in self.slices]
        if y_values != sorted(y_values):
            raise ValueError("Forelock slices must run from camera-facing tip to embedded root")
        if self.slices[0].y > -0.60:
            raise ValueError("Forelock front must project farther ahead of the face")
        if self.slices[-1].y < -0.42:
            raise ValueError("Forelock root must remain embedded in the crown")

        front = self.slices[0].points_xz
        lowest = min(front, key=lambda point: point[1])
        if not (-0.17 <= lowest[0] <= -0.10):
            raise ValueError("Forelock tip must descend on the physical character-left forehead")
        if not 4.18 <= lowest[1] <= 4.24:
            raise ValueError("Forelock tip must break the hairline without covering the eye")
        if max(point[1] for point in front) < 4.77:
            raise ValueError("Forelock root needs enough overlap with the physical crown")
        if min(point[0] for point in front) > -0.29:
            raise ValueError("Forelock root must visibly break the left front silhouette")


HUMAN_WARRIOR_M01_HAIR_FORELOCK_V11 = HairForelockProfileV11(
    revision="v11",
    proxy_revision="v14",
    mesh_name="hair_reference_forelock_mesh",
    slices=(
        HairForelockSliceV11(
            y=-0.625,
            points_xz=(
                (-0.300, 4.555),
                (-0.235, 4.735),
                (-0.105, 4.790),
                (0.020, 4.680),
                (-0.030, 4.455),
                (-0.135, 4.215),
                (-0.245, 4.360),
            ),
        ),
        HairForelockSliceV11(
            y=-0.525,
            points_xz=(
                (-0.275, 4.565),
                (-0.215, 4.725),
                (-0.100, 4.770),
                (0.010, 4.670),
                (-0.035, 4.465),
                (-0.130, 4.240),
                (-0.225, 4.375),
            ),
        ),
        HairForelockSliceV11(
            y=-0.395,
            points_xz=(
                (-0.235, 4.580),
                (-0.190, 4.715),
                (-0.090, 4.750),
                (0.000, 4.655),
                (-0.040, 4.480),
                (-0.125, 4.280),
                (-0.200, 4.400),
            ),
        ),
    ),
)


def load_hair_forelock_profile_v11() -> HairForelockProfileV11:
    HUMAN_WARRIOR_M01_HAIR_FORELOCK_V11.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_FORELOCK_V11
