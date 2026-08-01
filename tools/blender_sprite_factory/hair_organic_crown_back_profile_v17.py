from __future__ import annotations

from dataclasses import dataclass

from hair_integrated_crown_back_profile_v16 import (
    HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16,
)


_CONTROL_POINT_COUNT = 16
_SAMPLED_POINT_COUNT = 32
_TOP_CONTROL_INDICES = (3, 4, 5, 6, 7, 8)
_REAR_TIP_CONTROL_INDICES = (11, 13, 15)
_REAR_SEPARATOR_CONTROL_INDICES = (12, 14)
_COVERAGE_FLOORS = (4.88, 4.87, 4.84, 4.81, 4.76, 4.71, 4.67)


def _chaikin_closed(
    control_points: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    sampled: list[tuple[float, float]] = []
    for index, current in enumerate(control_points):
        following = control_points[(index + 1) % len(control_points)]
        sampled.append(
            (
                current[0] * 0.75 + following[0] * 0.25,
                current[1] * 0.75 + following[1] * 0.25,
            )
        )
        sampled.append(
            (
                current[0] * 0.25 + following[0] * 0.75,
                current[1] * 0.25 + following[1] * 0.75,
            )
        )
    return tuple(sampled)


@dataclass(frozen=True)
class HairOrganicSliceV17:
    y: float
    control_points_xz: tuple[tuple[float, float], ...]

    @property
    def points_xz(self) -> tuple[tuple[float, float], ...]:
        return _chaikin_closed(self.control_points_xz)

    def assert_valid(self) -> None:
        if len(self.control_points_xz) != _CONTROL_POINT_COUNT:
            raise ValueError("Organic crown/back slice needs sixteen broad control points")
        if len(set(self.control_points_xz)) != len(self.control_points_xz):
            raise ValueError("Organic crown/back control points must be unique")

        sampled = self.points_xz
        if len(sampled) != _SAMPLED_POINT_COUNT:
            raise ValueError("Organic crown/back smoothing must produce thirty-two points")
        if len(set(sampled)) != len(sampled):
            raise ValueError("Organic crown/back sampled points must be unique")

        x_values = [point[0] for point in sampled]
        z_values = [point[1] for point in sampled]
        if min(x_values) >= -0.30 or max(x_values) <= 0.30:
            raise ValueError("Organic crown/back slice must span both physical sides")
        if min(x_values) < -0.47 or max(x_values) > 0.47:
            raise ValueError("Organic crown/back width exceeds the locked head budget")
        if min(z_values) < 4.00 or max(z_values) > 5.00:
            raise ValueError("Organic crown/back height exceeds the medium-hair budget")
        if max(z_values) - min(z_values) < 0.48:
            raise ValueError("Organic crown/back slice needs a readable vertical silhouette")

        top_z = [self.control_points_xz[index][1] for index in _TOP_CONTROL_INDICES]
        if max(top_z) - min(top_z) > 0.14:
            raise ValueError("Top crown waves must stay broad and natural, not deliberately jagged")


@dataclass(frozen=True)
class HairOrganicCrownBackProfileV17:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairOrganicSliceV17, ...]
    removed_overlay_names: tuple[str, ...]
    retained_profile_lock_names: tuple[str, ...]

    def assert_valid(self) -> None:
        if self.revision != "v17" or self.proxy_revision != "v20":
            raise ValueError("Organic crown/back profile must match head v17 / proxy v20")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Organic pass must preserve the established crown object identity")
        if len(self.slices) != 7:
            raise ValueError("Organic crown/back mesh requires seven gradual depth slices")

        for profile_slice in self.slices:
            profile_slice.assert_valid()

        y_values = [profile_slice.y for profile_slice in self.slices]
        if any(current <= previous for previous, current in zip(y_values, y_values[1:])):
            raise ValueError("Organic crown/back slices must advance monotonically toward the rear")
        if y_values[0] != -0.492 or y_values[-1] > 0.50:
            raise ValueError("Organic crown/back depth must stay inside the established envelope")

        previous = HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16
        previous_front_top = max(point[1] for point in previous.slices[0].points_xz)
        current_front_top = max(point[1] for point in self.slices[0].points_xz)
        if current_front_top >= previous_front_top:
            raise ValueError("Organic pass must reduce the overly tall front crown profile")

        previous_rear_top = max(point[1] for point in previous.slices[-1].points_xz)
        current_rear_top = max(point[1] for point in self.slices[-1].points_xz)
        if current_rear_top >= previous_rear_top:
            raise ValueError("Organic pass must lower the rear crown profile")

        for slice_index, coverage_floor in enumerate(_COVERAGE_FLOORS):
            coverage_z = [
                self.slices[slice_index].control_points_xz[index][1]
                for index in (4, 5, 6, 7, 8)
            ]
            if min(coverage_z) < coverage_floor:
                raise ValueError("Organic crown/back mesh must keep closed scalp coverage")

        rear_controls = self.slices[-1].control_points_xz
        tip_z = [rear_controls[index][1] for index in _REAR_TIP_CONTROL_INDICES]
        separator_z = [
            rear_controls[index][1] for index in _REAR_SEPARATOR_CONTROL_INDICES
        ]
        if max(tip_z) > 4.10:
            raise ValueError("Rear silhouette needs three descending broad lock tips")
        if min(separator_z) < 4.22:
            raise ValueError("Rear lock tips need two raised organic separators")
        if min(separator_z) - max(tip_z) < 0.10:
            raise ValueError("Rear tips and separators need readable vertical separation")

        if self.removed_overlay_names != previous.removed_overlay_names:
            raise ValueError("Organic pass must not change the removed back overlay contract")
        if self.retained_profile_lock_names != previous.retained_profile_lock_names:
            raise ValueError("Organic pass must preserve side and nape profile locks")


HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17 = HairOrganicCrownBackProfileV17(
    revision="v17",
    proxy_revision="v20",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairOrganicSliceV17(
            y=-0.492,
            control_points_xz=(
                (-0.415, 4.420),
                (-0.430, 4.640),
                (-0.365, 4.800),
                (-0.285, 4.930),
                (-0.195, 4.900),
                (-0.090, 4.980),
                (0.020, 4.940),
                (0.140, 4.970),
                (0.250, 4.910),
                (0.350, 4.820),
                (0.420, 4.600),
                (0.390, 4.430),
                (0.240, 4.450),
                (0.060, 4.480),
                (-0.110, 4.420),
                (-0.280, 4.450),
            ),
        ),
        HairOrganicSliceV17(
            y=-0.340,
            control_points_xz=(
                (-0.425, 4.390),
                (-0.440, 4.620),
                (-0.370, 4.790),
                (-0.290, 4.920),
                (-0.195, 4.890),
                (-0.085, 4.970),
                (0.025, 4.930),
                (0.145, 4.960),
                (0.255, 4.900),
                (0.355, 4.800),
                (0.430, 4.560),
                (0.395, 4.380),
                (0.235, 4.430),
                (0.055, 4.460),
                (-0.115, 4.390),
                (-0.290, 4.430),
            ),
        ),
        HairOrganicSliceV17(
            y=-0.170,
            control_points_xz=(
                (-0.435, 4.340),
                (-0.445, 4.590),
                (-0.375, 4.760),
                (-0.295, 4.890),
                (-0.200, 4.870),
                (-0.085, 4.940),
                (0.030, 4.910),
                (0.150, 4.940),
                (0.260, 4.880),
                (0.360, 4.770),
                (0.435, 4.510),
                (0.400, 4.330),
                (0.230, 4.400),
                (0.050, 4.430),
                (-0.120, 4.340),
                (-0.300, 4.390),
            ),
        ),
        HairOrganicSliceV17(
            y=0.020,
            control_points_xz=(
                (-0.445, 4.290),
                (-0.450, 4.550),
                (-0.380, 4.720),
                (-0.300, 4.860),
                (-0.205, 4.840),
                (-0.080, 4.910),
                (0.035, 4.880),
                (0.155, 4.910),
                (0.265, 4.850),
                (0.360, 4.730),
                (0.440, 4.460),
                (0.400, 4.270),
                (0.225, 4.370),
                (0.045, 4.390),
                (-0.125, 4.300),
                (-0.305, 4.350),
            ),
        ),
        HairOrganicSliceV17(
            y=0.200,
            control_points_xz=(
                (-0.440, 4.240),
                (-0.445, 4.500),
                (-0.375, 4.670),
                (-0.295, 4.810),
                (-0.200, 4.790),
                (-0.075, 4.860),
                (0.040, 4.830),
                (0.160, 4.860),
                (0.270, 4.800),
                (0.355, 4.680),
                (0.435, 4.400),
                (0.390, 4.210),
                (0.220, 4.330),
                (0.040, 4.340),
                (-0.130, 4.250),
                (-0.300, 4.300),
            ),
        ),
        HairOrganicSliceV17(
            y=0.360,
            control_points_xz=(
                (-0.425, 4.210),
                (-0.430, 4.450),
                (-0.360, 4.620),
                (-0.285, 4.760),
                (-0.190, 4.740),
                (-0.070, 4.810),
                (0.045, 4.780),
                (0.165, 4.810),
                (0.270, 4.750),
                (0.350, 4.630),
                (0.420, 4.340),
                (0.370, 4.140),
                (0.215, 4.280),
                (0.035, 4.120),
                (-0.130, 4.300),
                (-0.290, 4.160),
            ),
        ),
        HairOrganicSliceV17(
            y=0.480,
            control_points_xz=(
                (-0.400, 4.180),
                (-0.415, 4.410),
                (-0.350, 4.580),
                (-0.275, 4.720),
                (-0.180, 4.700),
                (-0.060, 4.770),
                (0.050, 4.740),
                (0.170, 4.770),
                (0.275, 4.700),
                (0.345, 4.580),
                (0.405, 4.290),
                (0.350, 4.080),
                (0.205, 4.240),
                (0.030, 4.010),
                (-0.135, 4.260),
                (-0.285, 4.060),
            ),
        ),
    ),
    removed_overlay_names=(
        "hair_back_shell",
        "hair_back_sweep_left",
        "hair_back_sweep_right",
    ),
    retained_profile_lock_names=(
        "hair_side_mass_left",
        "hair_side_mass_right",
        "hair_nape_left",
        "hair_nape_center",
        "hair_nape_right",
    ),
)


def load_hair_organic_crown_back_profile_v17() -> HairOrganicCrownBackProfileV17:
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17
