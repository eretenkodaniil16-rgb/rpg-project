from __future__ import annotations

from dataclasses import dataclass

from hair_organic_crown_back_profile_v17 import (
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17,
    HairOrganicSliceV17,
)


_COVERAGE_FLOORS = (4.88, 4.87, 4.84, 4.81, 4.76, 4.71, 4.67)
_TOP_CONTROL_INDICES = (3, 4, 5, 6, 7, 8)
_CENTRAL_RISE_INDICES = (5, 6, 7)
_SHOULDER_INDICES = (3, 4, 8)
_REAR_TIP_CONTROL_INDICES = (11, 13, 15)
_REAR_SEPARATOR_CONTROL_INDICES = (12, 14)


@dataclass(frozen=True)
class HairVolumeCrownBackProfileV19:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairOrganicSliceV17, ...]
    removed_overlay_names: tuple[str, ...]
    retained_profile_lock_names: tuple[str, ...]

    def assert_valid(self) -> None:
        if self.revision != "v19" or self.proxy_revision != "v22":
            raise ValueError("Volume profile must match head v19 / proxy v22")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Volume pass must preserve the established crown object identity")
        if len(self.slices) != 7:
            raise ValueError("Volume crown/back mesh requires seven gradual depth slices")

        previous = HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17
        if tuple(item.y for item in self.slices) != tuple(item.y for item in previous.slices):
            raise ValueError("Volume pass must preserve the established depth slice positions")

        for profile_slice in self.slices:
            profile_slice.assert_valid()
            top_values = [
                profile_slice.control_points_xz[index][1]
                for index in _TOP_CONTROL_INDICES
            ]
            central_values = [
                profile_slice.control_points_xz[index][1]
                for index in _CENTRAL_RISE_INDICES
            ]
            shoulder_values = [
                profile_slice.control_points_xz[index][1]
                for index in _SHOULDER_INDICES
            ]
            central_average = sum(central_values) / len(central_values)
            shoulder_average = sum(shoulder_values) / len(shoulder_values)
            if central_average - shoulder_average < 0.04:
                raise ValueError(
                    "Volume pass needs one broad central rise above the crown shoulders"
                )
            if max(top_values) - min(top_values) > 0.10:
                raise ValueError(
                    "Central rise must remain broad and organic, not deliberately jagged"
                )

        for slice_index, coverage_floor in enumerate(_COVERAGE_FLOORS):
            coverage_z = [
                self.slices[slice_index].control_points_xz[index][1]
                for index in (4, 5, 6, 7, 8)
            ]
            if min(coverage_z) < coverage_floor:
                raise ValueError("Volume crown/back mesh must keep closed scalp coverage")

        widths = [
            max(point[0] for point in profile_slice.points_xz)
            - min(point[0] for point in profile_slice.points_xz)
            for profile_slice in self.slices
        ]
        previous_front_width = (
            max(point[0] for point in previous.slices[0].points_xz)
            - min(point[0] for point in previous.slices[0].points_xz)
        )
        if abs(widths[0] - previous_front_width) > 0.03:
            raise ValueError("Volume pass must preserve the established front silhouette width")

        previous_rear_width = (
            max(point[0] for point in previous.slices[-1].points_xz)
            - min(point[0] for point in previous.slices[-1].points_xz)
        )
        if previous_rear_width - widths[-1] < 0.07:
            raise ValueError("Volume pass must visibly taper the integrated mass at the rear")

        taper_widths = widths[2:]
        if any(
            next_width >= current_width
            for current_width, next_width in zip(taper_widths, taper_widths[1:])
        ):
            raise ValueError("Volume pass must narrow monotonically from crown center to nape")
        if any(
            current_width - next_width > 0.07
            for current_width, next_width in zip(taper_widths, taper_widths[1:])
        ):
            raise ValueError("Volume taper must stay gradual without abrupt angular steps")

        previous_front_top = max(point[1] for point in previous.slices[0].points_xz)
        current_front_top = max(point[1] for point in self.slices[0].points_xz)
        if not 0.01 <= current_front_top - previous_front_top <= 0.04:
            raise ValueError("Volume pass needs a restrained central lift at the front crown")

        previous_rear_top = max(point[1] for point in previous.slices[-1].points_xz)
        current_rear_top = max(point[1] for point in self.slices[-1].points_xz)
        if abs(current_rear_top - previous_rear_top) > 0.01:
            raise ValueError("Volume pass must taper width without raising the rear crown")

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
            raise ValueError("Volume pass must not change the removed back overlay contract")
        if self.retained_profile_lock_names != previous.retained_profile_lock_names:
            raise ValueError("Volume pass must preserve side and nape profile locks")


HUMAN_WARRIOR_M01_HAIR_VOLUME_CROWN_BACK_V19 = HairVolumeCrownBackProfileV19(
    revision="v19",
    proxy_revision="v22",
    mesh_name="hair_reference_crown_mesh",
    slices=(
        HairOrganicSliceV17(
            y=-0.492,
            control_points_xz=(
                (-0.405, 4.420),
                (-0.425, 4.625),
                (-0.360, 4.800),
                (-0.275, 4.915),
                (-0.175, 4.920),
                (-0.065, 4.985),
                (0.045, 4.995),
                (0.155, 4.975),
                (0.250, 4.915),
                (0.345, 4.815),
                (0.410, 4.600),
                (0.385, 4.430),
                (0.235, 4.450),
                (0.055, 4.480),
                (-0.115, 4.420),
                (-0.280, 4.450),
            ),
        ),
        HairOrganicSliceV17(
            y=-0.340,
            control_points_xz=(
                (-0.410, 4.390),
                (-0.430, 4.610),
                (-0.365, 4.785),
                (-0.280, 4.905),
                (-0.175, 4.915),
                (-0.060, 4.975),
                (0.050, 4.985),
                (0.160, 4.965),
                (0.255, 4.905),
                (0.345, 4.795),
                (0.415, 4.565),
                (0.390, 4.380),
                (0.230, 4.430),
                (0.050, 4.460),
                (-0.120, 4.390),
                (-0.285, 4.430),
            ),
        ),
        HairOrganicSliceV17(
            y=-0.170,
            control_points_xz=(
                (-0.415, 4.340),
                (-0.435, 4.580),
                (-0.365, 4.750),
                (-0.280, 4.880),
                (-0.175, 4.890),
                (-0.055, 4.950),
                (0.055, 4.960),
                (0.165, 4.940),
                (0.260, 4.880),
                (0.350, 4.765),
                (0.420, 4.510),
                (0.395, 4.330),
                (0.225, 4.400),
                (0.045, 4.430),
                (-0.125, 4.340),
                (-0.295, 4.390),
            ),
        ),
        HairOrganicSliceV17(
            y=0.020,
            control_points_xz=(
                (-0.410, 4.290),
                (-0.430, 4.545),
                (-0.360, 4.710),
                (-0.275, 4.845),
                (-0.170, 4.855),
                (-0.050, 4.915),
                (0.060, 4.925),
                (0.170, 4.905),
                (0.265, 4.845),
                (0.350, 4.725),
                (0.415, 4.460),
                (0.390, 4.270),
                (0.220, 4.370),
                (0.040, 4.390),
                (-0.130, 4.300),
                (-0.300, 4.350),
            ),
        ),
        HairOrganicSliceV17(
            y=0.200,
            control_points_xz=(
                (-0.395, 4.240),
                (-0.415, 4.490),
                (-0.350, 4.660),
                (-0.265, 4.790),
                (-0.160, 4.800),
                (-0.045, 4.860),
                (0.065, 4.870),
                (0.175, 4.850),
                (0.270, 4.790),
                (0.345, 4.675),
                (0.400, 4.400),
                (0.380, 4.210),
                (0.215, 4.330),
                (0.035, 4.340),
                (-0.135, 4.250),
                (-0.295, 4.300),
            ),
        ),
        HairOrganicSliceV17(
            y=0.360,
            control_points_xz=(
                (-0.375, 4.210),
                (-0.395, 4.445),
                (-0.330, 4.610),
                (-0.250, 4.735),
                (-0.150, 4.745),
                (-0.035, 4.805),
                (0.070, 4.815),
                (0.175, 4.795),
                (0.265, 4.735),
                (0.330, 4.625),
                (0.380, 4.340),
                (0.360, 4.140),
                (0.210, 4.280),
                (0.030, 4.120),
                (-0.130, 4.300),
                (-0.280, 4.160),
            ),
        ),
        HairOrganicSliceV17(
            y=0.480,
            control_points_xz=(
                (-0.345, 4.180),
                (-0.365, 4.405),
                (-0.305, 4.570),
                (-0.230, 4.690),
                (-0.135, 4.700),
                (-0.025, 4.755),
                (0.075, 4.765),
                (0.175, 4.745),
                (0.260, 4.690),
                (0.315, 4.580),
                (0.350, 4.290),
                (0.335, 4.080),
                (0.200, 4.240),
                (0.025, 4.010),
                (-0.130, 4.260),
                (-0.270, 4.060),
            ),
        ),
    ),
    removed_overlay_names=HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17.removed_overlay_names,
    retained_profile_lock_names=HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17.retained_profile_lock_names,
)


def load_hair_volume_crown_back_profile_v19() -> HairVolumeCrownBackProfileV19:
    HUMAN_WARRIOR_M01_HAIR_VOLUME_CROWN_BACK_V19.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_VOLUME_CROWN_BACK_V19
