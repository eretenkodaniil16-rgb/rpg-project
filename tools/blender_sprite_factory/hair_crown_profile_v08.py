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
        hairline = front[12:16]
        if min(point[1] for point in hairline) >= 4.42:
            raise ValueError("Hairline needs a separate asymmetric forelock root")
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
                (-0.430, 4.430),
                (-0.440, 4.680),
                (-0.355, 4.825),
                (-0.285, 4.965),
                (-0.190, 4.885),
                (-0.080, 5.045),
                (0.015, 4.945),
                (0.140, 5.015),
                (0.245, 4.905),
                (0.350, 4.870),
                (0.435, 4.650),
                (0.400, 4.430),
                (0.220, 4.455),
                (0.040, 4.510),
                (-0.100, 4.395),
                (-0.285, 4.460),
            ),
        ),
        HairCrownSlice(
            y=-0.050,
            points_xz=(
                (-0.475, 4.380),
                (-0.465, 4.675),
                (-0.370, 4.830),
                (-0.300, 4.950),
                (-0.205, 4.900),
                (-0.100, 5.020),
                (0.000, 4.960),
                (0.130, 5.000),
                (0.245, 4.910),
                (0.350, 4.850),
                (0.470, 4.600),
                (0.430, 4.380),
                (0.230, 4.400),
                (0.050, 4.440),
                (-0.110, 4.370),
                (-0.300, 4.410),
            ),
        ),
        HairCrownSlice(
            y=0.285,
            points_xz=(
                (-0.410, 4.205),
                (-0.440, 4.540),
                (-0.360, 4.680),
                (-0.290, 4.820),
                (-0.200, 4.770),
                (-0.080, 4.930),
                (0.020, 4.850),
                (0.150, 4.900),
                (0.250, 4.820),
                (0.335, 4.720),
                (0.420, 4.435),
                (0.380, 4.205),
                (0.220, 4.220),
                (0.050, 4.260),
                (-0.100, 4.200),
                (-0.280, 4.230),
            ),
        ),
    ),
)


def load_hair_crown_profile_v08() -> HairCrownProfileV08:
    HUMAN_WARRIOR_M01_HAIR_CROWN_V08.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_CROWN_V08
