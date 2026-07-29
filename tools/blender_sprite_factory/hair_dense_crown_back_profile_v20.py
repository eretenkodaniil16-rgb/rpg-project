from __future__ import annotations

from dataclasses import dataclass

from hair_organic_crown_back_profile_v17 import (
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17,
    HairOrganicSliceV17,
)


_TOP_LIFT_INDICES = (5, 6, 7)
_TOP_LIFTS = (
    (0.020, 0.040, 0.020),
    (0.020, 0.035, 0.020),
    (0.020, 0.035, 0.020),
    (0.015, 0.030, 0.015),
    (0.015, 0.030, 0.015),
    (0.010, 0.025, 0.010),
    (0.010, 0.020, 0.010),
)


def _lift_dense_slice(
    source: HairOrganicSliceV17,
    lifts: tuple[float, float, float],
) -> HairOrganicSliceV17:
    controls = list(source.control_points_xz)
    for control_index, lift in zip(_TOP_LIFT_INDICES, lifts):
        x, z = controls[control_index]
        controls[control_index] = (x, z + lift)
    return HairOrganicSliceV17(
        y=source.y,
        control_points_xz=tuple(controls),
    )


@dataclass(frozen=True)
class HairDenseCrownBackProfileV20:
    revision: str
    proxy_revision: str
    mesh_name: str
    slices: tuple[HairOrganicSliceV17, ...]
    removed_overlay_names: tuple[str, ...]
    retained_profile_lock_names: tuple[str, ...]

    def assert_valid(self) -> None:
        if self.revision != "v20" or self.proxy_revision != "v23":
            raise ValueError("Dense profile must match head v20 / proxy v23")
        if self.mesh_name != "hair_reference_crown_mesh":
            raise ValueError("Dense pass must preserve the established crown object identity")

        previous = HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17
        if len(self.slices) != len(previous.slices):
            raise ValueError("Dense pass must preserve all seven depth slices")

        for slice_index, (current, source) in enumerate(zip(self.slices, previous.slices)):
            current.assert_valid()
            if current.y != source.y:
                raise ValueError("Dense pass must preserve depth slice positions")

            current_x = tuple(point[0] for point in current.control_points_xz)
            source_x = tuple(point[0] for point in source.control_points_xz)
            if current_x != source_x:
                raise ValueError(
                    "Dense correction must not narrow the crown/back silhouette"
                )

            expected_lifts = dict(zip(_TOP_LIFT_INDICES, _TOP_LIFTS[slice_index]))
            for control_index, (current_point, source_point) in enumerate(
                zip(current.control_points_xz, source.control_points_xz)
            ):
                expected_z = source_point[1] + expected_lifts.get(control_index, 0.0)
                if abs(current_point[1] - expected_z) > 1e-9:
                    raise ValueError(
                        "Dense correction may only lift the three broad crown controls"
                    )

            current_width = max(point[0] for point in current.points_xz) - min(
                point[0] for point in current.points_xz
            )
            source_width = max(point[0] for point in source.points_xz) - min(
                point[0] for point in source.points_xz
            )
            if abs(current_width - source_width) > 1e-9:
                raise ValueError("Dense correction must preserve sampled silhouette width")

            current_top = max(point[1] for point in current.points_xz)
            source_top = max(point[1] for point in source.points_xz)
            if current_top <= source_top:
                raise ValueError("Dense correction must restore, not reduce, crown volume")
            if current_top - source_top > 0.04:
                raise ValueError("Dense correction must remain a restrained broad lift")

        if self.removed_overlay_names != previous.removed_overlay_names:
            raise ValueError("Dense pass must not restore redundant back overlays")
        if self.retained_profile_lock_names != previous.retained_profile_lock_names:
            raise ValueError("Dense pass must preserve side and nape profile locks")


HUMAN_WARRIOR_M01_HAIR_DENSE_CROWN_BACK_V20 = HairDenseCrownBackProfileV20(
    revision="v20",
    proxy_revision="v23",
    mesh_name="hair_reference_crown_mesh",
    slices=tuple(
        _lift_dense_slice(source, lifts)
        for source, lifts in zip(
            HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17.slices,
            _TOP_LIFTS,
        )
    ),
    removed_overlay_names=(
        HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17.removed_overlay_names
    ),
    retained_profile_lock_names=(
        HUMAN_WARRIOR_M01_HAIR_ORGANIC_CROWN_BACK_V17.retained_profile_lock_names
    ),
)


def load_hair_dense_crown_back_profile_v20() -> HairDenseCrownBackProfileV20:
    HUMAN_WARRIOR_M01_HAIR_DENSE_CROWN_BACK_V20.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_DENSE_CROWN_BACK_V20
