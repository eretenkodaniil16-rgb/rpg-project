from __future__ import annotations

from dataclasses import dataclass

from hair_crown_profile_v13 import HUMAN_WARRIOR_M01_HAIR_CROWN_V13


_COVERAGE_INDICES = (4, 6, 8)
_COVERAGE_FLOORS = (4.85, 4.84, 4.83, 4.77, 4.72)
_TAIL_INDICES = (15, 13, 11)
_SEPARATOR_INDICES = (14, 12)


@dataclass(frozen=True)
class HairIntegratedSliceV16:
    y: float
    points_xz: tuple[tuple[float, float], ...]

    def assert_valid(self, expected_points: int) -> None:
        if len(self.points_xz) != expected_points:
            raise ValueError("Every integrated crown/back slice must use the same point count")
        if len(set(self.points_xz)) != len(self.points_xz):
            raise ValueError("Integrated crown/back slice points must be unique")

        x_values = [point[0] for point in self.points_xz]
        z_values = [point[1] for point in self.points_xz]
        if min(x_values) >= -0.30 or max(x_values) <= 0.30:
            raise ValueError("Integrated crown/back slice must span both physical sides")
        if min(x_values) < -0.47 or max(x_values) > 0.47:
            raise ValueError("Integrated crown/back width exceeds the locked head budget")
        if min(z_values) < 4.00 or max(z_values) > 5.03:
            raise ValueError("Integrated crown/back height exceeds the medium-hair budget")
        if max(z_values) - min(z_values) < 0.48:
            raise ValueError("Integrated crown/back slice needs a readable vertical silhouette")


@dataclass(frozen=True)
class HairIntegratedCrownBackProfileV16:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairIntegratedSliceV16, ...]
    removed_overlay_names: tuple[str, ...]
    retained_profile_lock_names: tuple[str, ...]

    def assert_valid(self) -> None:
        if self.revision != "v16" or self.proxy_revision != "v19":
            raise ValueError("Integrated crown/back profile must match head v16 / proxy v19")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Integrated pass must preserve the established crown object identity")
        if len(self.slices) != 5:
            raise ValueError("Integrated crown/back mesh requires five depth slices")

        point_count = len(self.slices[0].points_xz)
        if point_count != 16:
            raise ValueError("Integrated crown/back contour must keep sixteen points per slice")
        for profile_slice in self.slices:
            profile_slice.assert_valid(point_count)

        y_values = [profile_slice.y for profile_slice in self.slices]
        if any(current <= previous for previous, current in zip(y_values, y_values[1:])):
            raise ValueError("Integrated crown/back slices must advance monotonically toward the rear")
        if y_values[-1] > 0.50:
            raise ValueError("Integrated rear depth exceeds the existing medium-hair envelope")

        previous_front = HUMAN_WARRIOR_M01_HAIR_CROWN_V13.slices[0]
        if self.slices[0].y != previous_front.y:
            raise ValueError("Front crown depth must remain locked to proxy v18")
        if self.slices[0].points_xz != previous_front.points_xz:
            raise ValueError("Front crown silhouette must remain locked to proxy v18")

        for slice_index, coverage_floor in enumerate(_COVERAGE_FLOORS):
            coverage_z = [
                self.slices[slice_index].points_xz[index][1]
                for index in _COVERAGE_INDICES
            ]
            if min(coverage_z) < coverage_floor:
                raise ValueError("Integrated crown/back mesh must keep closed scalp coverage")

        rear = self.slices[-1].points_xz
        tail_z = [rear[index][1] for index in _TAIL_INDICES]
        separator_z = [rear[index][1] for index in _SEPARATOR_INDICES]
        if max(tail_z) > 4.10:
            raise ValueError("Rear mesh needs three clearly descending broad lock tips")
        if min(separator_z) < 4.18:
            raise ValueError("Rear lock tips need raised separators between them")
        if min(separator_z) - max(tail_z) < 0.08:
            raise ValueError("Rear lock tips and separators need readable vertical separation")

        expected_removed = {
            "hair_back_shell",
            "hair_back_sweep_left",
            "hair_back_sweep_right",
        }
        if set(self.removed_overlay_names) != expected_removed:
            raise ValueError("Integrated mesh must remove exactly the three redundant back overlays")
        if len(self.removed_overlay_names) != len(expected_removed):
            raise ValueError("Integrated back overlay names must be unique")

        expected_retained = {
            "hair_side_mass_left",
            "hair_side_mass_right",
            "hair_nape_left",
            "hair_nape_center",
            "hair_nape_right",
        }
        if set(self.retained_profile_lock_names) != expected_retained:
            raise ValueError("Integrated mesh must retain exactly the side and nape profile locks")
        if len(self.retained_profile_lock_names) != len(expected_retained):
            raise ValueError("Retained profile lock names must be unique")


HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16 = HairIntegratedCrownBackProfileV16(
    revision="v16",
    proxy_revision="v19",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairIntegratedSliceV16(
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
        HairIntegratedSliceV16(
            y=-0.240,
            points_xz=(
                (-0.440, 4.360),
                (-0.450, 4.640),
                (-0.380, 4.810),
                (-0.310, 4.960),
                (-0.215, 4.870),
                (-0.105, 5.010),
                (0.005, 4.895),
                (0.130, 4.980),
                (0.250, 4.870),
                (0.355, 4.820),
                (0.445, 4.570),
                (0.415, 4.340),
                (0.235, 4.390),
                (0.060, 4.440),
                (-0.110, 4.320),
                (-0.300, 4.400),
            ),
        ),
        HairIntegratedSliceV16(
            y=0.030,
            points_xz=(
                (-0.455, 4.300),
                (-0.455, 4.620),
                (-0.385, 4.800),
                (-0.315, 4.940),
                (-0.220, 4.860),
                (-0.105, 4.990),
                (0.010, 4.885),
                (0.135, 4.955),
                (0.255, 4.855),
                (0.360, 4.800),
                (0.455, 4.540),
                (0.425, 4.290),
                (0.240, 4.350),
                (0.060, 4.400),
                (-0.115, 4.280),
                (-0.305, 4.370),
            ),
        ),
        HairIntegratedSliceV16(
            y=0.270,
            points_xz=(
                (-0.440, 4.220),
                (-0.445, 4.540),
                (-0.375, 4.720),
                (-0.305, 4.860),
                (-0.210, 4.790),
                (-0.095, 4.910),
                (0.020, 4.820),
                (0.145, 4.900),
                (0.260, 4.800),
                (0.350, 4.750),
                (0.435, 4.470),
                (0.405, 4.180),
                (0.230, 4.280),
                (0.055, 4.200),
                (-0.120, 4.300),
                (-0.295, 4.180),
            ),
        ),
        HairIntegratedSliceV16(
            y=0.460,
            points_xz=(
                (-0.410, 4.190),
                (-0.425, 4.460),
                (-0.360, 4.640),
                (-0.290, 4.790),
                (-0.200, 4.750),
                (-0.080, 4.860),
                (0.030, 4.770),
                (0.150, 4.840),
                (0.260, 4.740),
                (0.350, 4.680),
                (0.410, 4.380),
                (0.360, 4.070),
                (0.220, 4.220),
                (0.055, 4.020),
                (-0.120, 4.230),
                (-0.275, 4.060),
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


def load_hair_integrated_crown_back_profile_v16() -> HairIntegratedCrownBackProfileV16:
    HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_INTEGRATED_CROWN_BACK_V16
