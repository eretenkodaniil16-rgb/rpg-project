from __future__ import annotations

from dataclasses import dataclass

from hair_crown_profile_v12 import HUMAN_WARRIOR_M01_HAIR_CROWN_V12


_COVERAGE_INDICES = (4, 6, 8)
_COVERAGE_FLOORS = (4.85, 4.86, 4.76)


@dataclass(frozen=True)
class HairCrownSliceV13:
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
class HairCrownProfileV13:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairCrownSliceV13, ...]

    def assert_valid(self) -> None:
        if self.revision != "v13" or self.proxy_revision != "v16":
            raise ValueError("Crown profile must match head v13 / proxy v16")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Unexpected crown mesh identity")
        if len(self.slices) != 3:
            raise ValueError("Side/back silhouette crown must keep three slices")

        point_count = len(self.slices[0].points_xz)
        if point_count != 16:
            raise ValueError("Side/back silhouette crown needs sixteen contour points")
        for item in self.slices:
            item.assert_valid(point_count)

        previous = HUMAN_WARRIOR_M01_HAIR_CROWN_V12
        if self.slices[0].y != previous.slices[0].y:
            raise ValueError("Front crown depth must remain locked to proxy v15")
        if self.slices[0].points_xz != previous.slices[0].points_xz:
            raise ValueError("Front crown silhouette must remain locked to proxy v15")
        if self.slices[1].y != previous.slices[1].y:
            raise ValueError("Middle crown depth must remain locked")
        if self.slices[-1].y <= previous.slices[-1].y:
            raise ValueError("Rear crown needs a small physical depth increase")
        if self.slices[-1].y > 0.33:
            raise ValueError("Rear crown depth exceeds the medium-hair budget")

        for slice_index, coverage_floor in enumerate(_COVERAGE_FLOORS):
            coverage_z = [
                self.slices[slice_index].points_xz[index][1]
                for index in _COVERAGE_INDICES
            ]
            if min(coverage_z) < coverage_floor:
                raise ValueError("Side/back pass must preserve closed scalp coverage")

        back = self.slices[-1].points_xz
        rear_indices = (11, 12, 13, 14, 15, 0)
        rear_z = [back[index][1] for index in rear_indices]
        if max(rear_z) - min(rear_z) < 0.18:
            raise ValueError("Rear lower edge needs two or three broad hanging masses")
        if min(rear_z) < 4.12:
            raise ValueError("Rear hair drops below the medium-length silhouette budget")

        previous_back = previous.slices[-1].points_xz
        changed_rear = sum(
            back[index] != previous_back[index]
            for index in rear_indices
        )
        if changed_rear < 5:
            raise ValueError("Rear silhouette pass must reshape most lower-edge anchors")


HUMAN_WARRIOR_M01_HAIR_CROWN_V13 = HairCrownProfileV13(
    revision="v13",
    proxy_revision="v16",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairCrownSliceV13(
            y=-0.492,
            points_xz=(
                (-0.420, 4.420),
                (-0.430, 4.650),
                (-0.365, 4.805),
                (-0.300, 4.965),
                (-0.205, 4.860),
                (-0.105, 5.015),
                (0.005, 4.900),
                (0.125, 4.985),
                (0.245, 4.875),
                (0.345, 4.840),
                (0.420, 4.615),
                (0.395, 4.425),
                (0.225, 4.445),
                (0.055, 4.505),
                (-0.105, 4.405),
                (-0.285, 4.455),
            ),
        ),
        HairCrownSliceV13(
            y=-0.050,
            points_xz=(
                (-0.455, 4.345),
                (-0.450, 4.655),
                (-0.375, 4.805),
                (-0.305, 4.940),
                (-0.215, 4.870),
                (-0.110, 4.995),
                (0.005, 4.890),
                (0.130, 4.965),
                (0.250, 4.870),
                (0.350, 4.825),
                (0.455, 4.590),
                (0.420, 4.345),
                (0.235, 4.405),
                (0.060, 4.465),
                (-0.110, 4.335),
                (-0.300, 4.420),
            ),
        ),
        HairCrownSliceV13(
            y=0.315,
            points_xz=(
                (-0.410, 4.140),
                (-0.430, 4.520),
                (-0.365, 4.680),
                (-0.295, 4.825),
                (-0.205, 4.770),
                (-0.090, 4.925),
                (0.020, 4.815),
                (0.145, 4.890),
                (0.255, 4.785),
                (0.345, 4.735),
                (0.415, 4.420),
                (0.385, 4.150),
                (0.225, 4.235),
                (0.065, 4.335),
                (-0.110, 4.125),
                (-0.285, 4.305),
            ),
        ),
    ),
)


def load_hair_crown_profile_v13() -> HairCrownProfileV13:
    HUMAN_WARRIOR_M01_HAIR_CROWN_V13.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_CROWN_V13
