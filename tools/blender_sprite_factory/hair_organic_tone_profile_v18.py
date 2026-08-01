from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToneEllipsoidV18:
    role: str
    center_xyz: tuple[float, float, float]
    radius_xyz: tuple[float, float, float]

    def assert_valid(self) -> None:
        if self.role not in {"mid", "highlight"}:
            raise ValueError(f"Unsupported organic tone role: {self.role}")
        if any(value <= 0.0 for value in self.radius_xyz):
            raise ValueError(f"Organic tone radii must stay positive: {self.role}")
        if any(value > 0.80 for value in self.radius_xyz):
            raise ValueError(f"Organic tone region is too broad: {self.role}")

    def contains(self, x: float, y: float, z: float) -> bool:
        return sum(
            ((value - center) / radius) ** 2
            for value, center, radius in zip(
                (x, y, z),
                self.center_xyz,
                self.radius_xyz,
            )
        ) < 1.0


@dataclass(frozen=True)
class HairOrganicToneProfileV18:
    revision: str
    proxy_revision: str
    lower_shadow_base_z: float
    lower_shadow_x_slope: float
    lower_shadow_y_slope: float
    rear_shadow_min_y: float
    rear_shadow_base_z: float
    rear_shadow_x_slope: float
    highlight_region: ToneEllipsoidV18
    main_mid_region: ToneEllipsoidV18
    rear_mid_region: ToneEllipsoidV18

    def assert_valid(self) -> None:
        if self.revision != "v18" or self.proxy_revision != "v21":
            raise ValueError("Organic tone profile must match head v18 / proxy v21")
        if not 4.15 <= self.lower_shadow_base_z <= 4.35:
            raise ValueError("Lower shadow boundary is outside the hair envelope")
        if not 0.20 <= self.rear_shadow_min_y <= 0.40:
            raise ValueError("Rear shadow must begin only in the back portion of the crown")
        if not 4.30 <= self.rear_shadow_base_z <= 4.55:
            raise ValueError("Rear shadow boundary is outside the hair envelope")
        for region in (
            self.highlight_region,
            self.main_mid_region,
            self.rear_mid_region,
        ):
            region.assert_valid()
        if self.highlight_region.role != "highlight":
            raise ValueError("Highlight region must use the highlight role")
        if self.main_mid_region.role != "mid" or self.rear_mid_region.role != "mid":
            raise ValueError("Both broad support regions must use the mid role")
        if any(
            highlight >= mid
            for highlight, mid in zip(
                self.highlight_region.radius_xyz,
                self.main_mid_region.radius_xyz,
            )
        ):
            raise ValueError("Highlight must stay smaller than the main mid-tone region")


HUMAN_WARRIOR_M01_HAIR_ORGANIC_TONE_V18 = HairOrganicToneProfileV18(
    revision="v18",
    proxy_revision="v21",
    lower_shadow_base_z=4.26,
    lower_shadow_x_slope=0.08,
    lower_shadow_y_slope=-0.04,
    rear_shadow_min_y=0.30,
    rear_shadow_base_z=4.44,
    rear_shadow_x_slope=-0.05,
    highlight_region=ToneEllipsoidV18(
        role="highlight",
        center_xyz=(-0.08, -0.16, 4.88),
        radius_xyz=(0.18, 0.28, 0.11),
    ),
    main_mid_region=ToneEllipsoidV18(
        role="mid",
        center_xyz=(0.00, -0.02, 4.78),
        radius_xyz=(0.34, 0.58, 0.22),
    ),
    rear_mid_region=ToneEllipsoidV18(
        role="mid",
        center_xyz=(0.14, 0.30, 4.66),
        radius_xyz=(0.30, 0.32, 0.18),
    ),
)


def load_hair_organic_tone_profile_v18() -> HairOrganicToneProfileV18:
    HUMAN_WARRIOR_M01_HAIR_ORGANIC_TONE_V18.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_ORGANIC_TONE_V18
