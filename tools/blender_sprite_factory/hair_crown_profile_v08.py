from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HairCrownSlice:
    y: float
    points_xz: tuple[tuple[float, float], ...]

    def assert_valid(self, expected_points: int) -> None:
        if len(self.points_xz) != expected_points:
            raise ValueError("Every crown slice must use the same point count")
        if len(set(self.points_xz)) != len(self.points_xz):
            raise ValueError("Crown slice points must be unique")
        x_values = [point[0] for point in self.points_xz]
        z_values = [point[1] for point in self.points_xz]
        if min(x_values) >= -0.30 or max(x_values) <= 0.30:
            raise ValueError("Crown slice must span both physical sides of the head")
        if max(z_values) - min(z_values) < 0.35:
            raise ValueError("Crown slice needs a readable vertical silhouette")


@dataclass(frozen=True)
class HairCrownProfileV08:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairCrownSlice, ...]

    def assert_valid(self) -> None:
        if self.revision != "v08" or self.proxy_revision != "v11":
            raise ValueError("Crown profile must match head v08 / proxy v11")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Unexpected crown mesh identity")
        if len(self.slices) != 3:
            raise ValueError("Reference crown must use front, middle and back slices")
        point_count = len(self.slices[0].points_xz)
        if point_count != 16:
            raise ValueError("Reference crown needs sixteen coarse contour points")
        for item in self.slices:
            item.assert_valid(point_count)
        y_values = [item.y for item in self.slices]
        if y_values != sorted(y_values):
            raise ValueError("Crown slices must run from face side to back side")
        if self.slices[0].y > -0.40:
            raise ValueError("Front crown slice must remain ahead of the cranium")
        if self.slices[-1].y < 0.20:
            raise ValueError("Back crown slice must cover the rear silhouette")

        front = self.slices[0].points_xz
        top_wave = front[3:9]
        if max(point[1] for point in top_wave) - min(point[1] for point in top_wave) < 0.13:
            raise ValueError("Front crown needs several readable large waves")
        highest = max(top_wave, key=lambda point: point[1])
        if highest[0] >= 0.0:
            raise ValueError("Canonical highest wave must remain on the character-left side")
        if highest[1] > 5.00:
            raise ValueError("Crown must stay compact instead of becoming a tall helmet")
        hairline = front[12:16]
        if not 4.40 <= min(point[1] for point in hairline) <= 4.44:
            raise ValueError("Crown hairline must leave room for the separate forelock mesh")
        if min(point[1] for point in front) <= 4.20:
            raise ValueError("Front crown must not cover the readable eye line")
        if min(point[1] for point in self.slices[-1].points_xz) > 4.21:
            raise ValueError("Back crown needs sufficient medium-length drop")


HUMAN_WARRIOR_M01_HAIR_CROWN_V08 = HairCrownProfileV08(
    revision="v08",
    proxy_revision="v11",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairCrownSlice(
            y=-0.485,
            points_xz=(
                (-0.405, 4.430),
                (-0.415, 4.650),
                (-0.340, 4.790),
                (-0.270, 4.920),
                (-0.180, 4.840),
                (-0.075, 4.990),
                (0.020, 4.900),
                (0.130, 4.960),
                (0.225, 4.870),
                (0.330, 4.820),
                (0.405, 4.620),
                (0.380, 4.430),
                (0.210, 4.450),
                (0.040, 4.500),
                (-0.100, 4.420),
                (-0.270, 4.450),
            ),
        ),
        HairCrownSlice(
            y=-0.050,
            points_xz=(
                (-0.445, 4.380),
                (-0.440, 4.650),
                (-0.350, 4.790),
                (-0.285, 4.910),
                (-0.195, 4.850),
                (-0.095, 4.970),
                (0.000, 4.900),
                (0.120, 4.945),
                (0.225, 4.860),
                (0.325, 4.810),
                (0.440, 4.590),
                (0.405, 4.380),
                (0.220, 4.400),
                (0.050, 4.440),
                (-0.105, 4.380),
                (-0.285, 4.410),
            ),
        ),
        HairCrownSlice(
            y=0.285,
            points_xz=(
                (-0.400, 4.205),
                (-0.420, 4.530),
                (-0.340, 4.665),
                (-0.275, 4.795),
                (-0.190, 4.745),
                (-0.075, 4.895),
                (0.020, 4.820),
                (0.140, 4.870),
                (0.235, 4.790),
                (0.320, 4.700),
                (0.400, 4.425),
                (0.365, 4.205),
                (0.210, 4.220),
                (0.050, 4.260),
                (-0.095, 4.200),
                (-0.270, 4.230),
            ),
        ),
    ),
)


def load_hair_crown_profile_v08() -> HairCrownProfileV08:
    HUMAN_WARRIOR_M01_HAIR_CROWN_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_CROWN_V08
