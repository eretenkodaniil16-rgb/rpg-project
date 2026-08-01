from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HairCrownSliceV11:
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
        if max(z_values) - min(z_values) < 0.45:
            raise ValueError("Crown slice needs a readable vertical silhouette")
        if min(x_values) < -0.47 or max(x_values) > 0.47:
            raise ValueError("Crown width exceeds the locked head budget")


@dataclass(frozen=True)
class HairCrownProfileV11:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairCrownSliceV11, ...]

    def assert_valid(self) -> None:
        if self.revision != "v11" or self.proxy_revision != "v14":
            raise ValueError("Crown profile must match head v11 / proxy v14")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Unexpected crown mesh identity")
        if len(self.slices) != 3:
            raise ValueError("Physical crown must keep front, middle and back slices")

        point_count = len(self.slices[0].points_xz)
        if point_count != 16:
            raise ValueError("Physical crown needs sixteen coarse contour points")
        for item in self.slices:
            item.assert_valid(point_count)

        y_values = [item.y for item in self.slices]
        if y_values != sorted(y_values):
            raise ValueError("Crown slices must run from face side to back side")
        if self.slices[0].y > -0.48 or self.slices[-1].y < 0.28:
            raise ValueError("Crown depth must continue covering front and rear silhouettes")

        front = self.slices[0].points_xz
        for peak_index, left_valley, right_valley in ((3, 2, 4), (5, 4, 6), (7, 6, 8)):
            peak = front[peak_index][1]
            if peak - front[left_valley][1] < 0.12 or peak - front[right_valley][1] < 0.12:
                raise ValueError("Front crown peaks must create physical large-wave silhouette breaks")
        highest = max(front[3:9], key=lambda point: point[1])
        if highest[0] >= 0.0:
            raise ValueError("Canonical highest wave must remain on the character-left side")
        if highest[1] > 5.03:
            raise ValueError("Crown must stay compact instead of becoming taller")

        back = self.slices[-1].points_xz
        rear_lower_edge = (back[11], back[12], back[13], back[14], back[15], back[0])
        rear_z = [point[1] for point in rear_lower_edge]
        if max(rear_z) - min(rear_z) < 0.14:
            raise ValueError("Rear lower edge must form two or three broad hanging masses")
        if min(rear_z) < 4.12:
            raise ValueError("Rear hair drops below the medium-length silhouette budget")


HUMAN_WARRIOR_M01_HAIR_CROWN_V11 = HairCrownProfileV11(
    revision="v11",
    proxy_revision="v14",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairCrownSliceV11(
            y=-0.492,
            points_xz=(
                (-0.420, 4.420),
                (-0.430, 4.650),
                (-0.365, 4.805),
                (-0.300, 4.965),
                (-0.205, 4.790),
                (-0.105, 5.015),
                (0.005, 4.830),
                (0.125, 4.985),
                (0.245, 4.815),
                (0.345, 4.840),
                (0.420, 4.615),
                (0.395, 4.425),
                (0.225, 4.445),
                (0.055, 4.505),
                (-0.105, 4.405),
                (-0.285, 4.455),
            ),
        ),
        HairCrownSliceV11(
            y=-0.050,
            points_xz=(
                (-0.455, 4.365),
                (-0.450, 4.655),
                (-0.375, 4.805),
                (-0.305, 4.940),
                (-0.215, 4.805),
                (-0.110, 4.995),
                (0.005, 4.825),
                (0.130, 4.965),
                (0.250, 4.805),
                (0.350, 4.825),
                (0.455, 4.590),
                (0.420, 4.365),
                (0.235, 4.390),
                (0.060, 4.455),
                (-0.110, 4.350),
                (-0.300, 4.405),
            ),
        ),
        HairCrownSliceV11(
            y=0.295,
            points_xz=(
                (-0.410, 4.165),
                (-0.430, 4.520),
                (-0.365, 4.680),
                (-0.295, 4.825),
                (-0.205, 4.705),
                (-0.090, 4.925),
                (0.020, 4.745),
                (0.145, 4.890),
                (0.255, 4.720),
                (0.345, 4.735),
                (0.415, 4.420),
                (0.385, 4.175),
                (0.225, 4.205),
                (0.065, 4.315),
                (-0.110, 4.150),
                (-0.285, 4.280),
            ),
        ),
    ),
)


def load_hair_crown_profile_v11() -> HairCrownProfileV11:
    HUMAN_WARRIOR_M01_HAIR_CROWN_V11.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_CROWN_V11
