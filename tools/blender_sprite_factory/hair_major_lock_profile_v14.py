from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HairZone = Literal["side", "back", "nape"]
HairMaterialRole = Literal["shadow", "base", "mid"]


@dataclass(frozen=True)
class HairLockRingV14:
    z_ratio: float
    center_x_ratio: float
    center_y_ratio: float
    radius_x_ratio: float
    radius_y_ratio: float

    def assert_valid(self) -> None:
        if not -1.0 <= self.z_ratio <= 1.0:
            raise ValueError("Hair lock ring z ratio is outside the local extent")
        if abs(self.center_x_ratio) > 0.35 or abs(self.center_y_ratio) > 0.35:
            raise ValueError("Hair lock ring center offset exceeds the profile budget")
        if not 0.10 <= self.radius_x_ratio <= 1.05:
            raise ValueError("Hair lock ring x radius is invalid")
        if not 0.10 <= self.radius_y_ratio <= 1.05:
            raise ValueError("Hair lock ring y radius is invalid")


@dataclass(frozen=True)
class HairMajorLockV14:
    name: str
    zone: HairZone
    physical_side: str
    material_role: HairMaterialRole
    half_extent: tuple[float, float, float]
    ring_sides: int
    rings: tuple[HairLockRingV14, ...]

    def assert_valid(self) -> None:
        if self.physical_side not in {"left", "right", "center"}:
            raise ValueError(f"Invalid physical side for {self.name}")
        if any(value <= 0.0 for value in self.half_extent):
            raise ValueError(f"Hair lock extent must stay positive: {self.name}")
        if self.half_extent[0] > 0.41 or self.half_extent[1] > 0.32:
            raise ValueError(f"Hair lock exceeds the locked head width/depth: {self.name}")
        if self.half_extent[2] > 0.31:
            raise ValueError(f"Hair lock exceeds the medium-length budget: {self.name}")
        if self.ring_sides != 6:
            raise ValueError("Major locks must use a coarse six-sided cross-section")
        if len(self.rings) != 6:
            raise ValueError("Major locks must use six vertical profile rings")
        for ring in self.rings:
            ring.assert_valid()
        z_values = [ring.z_ratio for ring in self.rings]
        if z_values != sorted(z_values, reverse=True):
            raise ValueError("Hair lock rings must run from root to hanging tip")
        if self.rings[0].z_ratio != 1.0 or self.rings[-1].z_ratio != -1.0:
            raise ValueError("Hair lock profile must span its full vertical extent")
        if self.rings[0].radius_x_ratio >= 0.45 or self.rings[-1].radius_x_ratio >= 0.35:
            raise ValueError("Hair lock root and tip must stay narrower than the body")
        if max(ring.radius_x_ratio for ring in self.rings[1:-1]) < 0.85:
            raise ValueError("Hair lock needs a broad readable middle mass")


@dataclass(frozen=True)
class HairMajorLockProfileV14:
    revision: str
    proxy_revision: str
    locks: tuple[HairMajorLockV14, ...]

    def assert_valid(self) -> None:
        if self.revision != "v14" or self.proxy_revision != "v17":
            raise ValueError("Major lock profile must match head v14 / proxy v17")
        expected_names = {
            "hair_back_shell",
            "hair_back_sweep_left",
            "hair_back_sweep_right",
            "hair_side_mass_left",
            "hair_side_mass_right",
            "hair_nape_left",
            "hair_nape_center",
            "hair_nape_right",
        }
        names = [lock.name for lock in self.locks]
        if set(names) != expected_names or len(names) != len(expected_names):
            raise ValueError("Major lock pass must replace exactly eight existing masses")
        if len(names) != len(set(names)):
            raise ValueError("Major lock names must be unique")
        for lock in self.locks:
            lock.assert_valid()

        left_side = next(lock for lock in self.locks if lock.name == "hair_side_mass_left")
        right_side = next(lock for lock in self.locks if lock.name == "hair_side_mass_right")
        left_path = tuple((ring.center_x_ratio, ring.center_y_ratio) for ring in left_side.rings)
        right_path = tuple((ring.center_x_ratio, ring.center_y_ratio) for ring in right_side.rings)
        if left_path == tuple((-x, y) for x, y in right_path):
            raise ValueError("Physical side locks must not be mirrored copies")

        nape_locks = [lock for lock in self.locks if lock.zone == "nape"]
        if len(nape_locks) != 3:
            raise ValueError("Rear lower edge requires three major nape locks")
        tip_paths = {
            (lock.rings[-1].center_x_ratio, lock.rings[-1].center_y_ratio)
            for lock in nape_locks
        }
        if len(tip_paths) != 3:
            raise ValueError("Nape tips must form three distinct hanging endpoints")


R = HairLockRingV14

HUMAN_WARRIOR_M01_HAIR_MAJOR_LOCKS_V14 = HairMajorLockProfileV14(
    revision="v14",
    proxy_revision="v17",
    locks=(
        HairMajorLockV14(
            name="hair_back_shell",
            zone="back",
            physical_side="center",
            material_role="base",
            half_extent=(0.400, 0.310, 0.300),
            ring_sides=6,
            rings=(
                R(1.00, 0.00, -0.10, 0.34, 0.42),
                R(0.58, -0.03, -0.04, 0.82, 0.80),
                R(0.14, 0.04, 0.03, 1.00, 0.96),
                R(-0.30, -0.02, 0.10, 0.92, 0.86),
                R(-0.68, 0.06, 0.16, 0.66, 0.62),
                R(-1.00, -0.03, 0.22, 0.22, 0.28),
            ),
        ),
        HairMajorLockV14(
            name="hair_back_sweep_left",
            zone="back",
            physical_side="left",
            material_role="mid",
            half_extent=(0.205, 0.220, 0.260),
            ring_sides=6,
            rings=(
                R(1.00, -0.08, -0.08, 0.32, 0.38),
                R(0.58, -0.02, -0.02, 0.78, 0.84),
                R(0.14, 0.05, 0.04, 1.00, 0.95),
                R(-0.30, 0.12, 0.10, 0.88, 0.82),
                R(-0.68, 0.20, 0.17, 0.58, 0.62),
                R(-1.00, 0.28, 0.24, 0.18, 0.22),
            ),
        ),
        HairMajorLockV14(
            name="hair_back_sweep_right",
            zone="back",
            physical_side="right",
            material_role="mid",
            half_extent=(0.205, 0.220, 0.260),
            ring_sides=6,
            rings=(
                R(1.00, 0.06, -0.10, 0.34, 0.40),
                R(0.58, 0.00, -0.01, 0.82, 0.80),
                R(0.14, -0.04, 0.05, 0.96, 1.00),
                R(-0.30, -0.12, 0.12, 0.84, 0.86),
                R(-0.68, -0.18, 0.18, 0.62, 0.58),
                R(-1.00, -0.24, 0.28, 0.20, 0.24),
            ),
        ),
        HairMajorLockV14(
            name="hair_side_mass_left",
            zone="side",
            physical_side="left",
            material_role="base",
            half_extent=(0.130, 0.175, 0.250),
            ring_sides=6,
            rings=(
                R(1.00, -0.05, -0.10, 0.30, 0.35),
                R(0.58, 0.00, -0.03, 0.82, 0.88),
                R(0.14, 0.05, 0.05, 1.00, 0.96),
                R(-0.30, 0.10, 0.13, 0.86, 0.82),
                R(-0.68, 0.16, 0.22, 0.56, 0.58),
                R(-1.00, 0.22, 0.30, 0.16, 0.20),
            ),
        ),
        HairMajorLockV14(
            name="hair_side_mass_right",
            zone="side",
            physical_side="right",
            material_role="base",
            half_extent=(0.130, 0.175, 0.250),
            ring_sides=6,
            rings=(
                R(1.00, 0.03, -0.11, 0.32, 0.36),
                R(0.58, -0.02, -0.01, 0.78, 0.90),
                R(0.14, -0.07, 0.06, 0.98, 1.00),
                R(-0.30, -0.11, 0.14, 0.88, 0.80),
                R(-0.68, -0.15, 0.24, 0.60, 0.55),
                R(-1.00, -0.19, 0.33, 0.18, 0.22),
            ),
        ),
        HairMajorLockV14(
            name="hair_nape_left",
            zone="nape",
            physical_side="left",
            material_role="shadow",
            half_extent=(0.150, 0.145, 0.195),
            ring_sides=6,
            rings=(
                R(1.00, -0.08, -0.08, 0.34, 0.38),
                R(0.58, -0.02, 0.00, 0.82, 0.86),
                R(0.14, 0.06, 0.08, 1.00, 0.94),
                R(-0.30, 0.14, 0.15, 0.82, 0.78),
                R(-0.68, 0.22, 0.22, 0.52, 0.54),
                R(-1.00, 0.30, 0.28, 0.16, 0.18),
            ),
        ),
        HairMajorLockV14(
            name="hair_nape_center",
            zone="nape",
            physical_side="center",
            material_role="shadow",
            half_extent=(0.155, 0.145, 0.185),
            ring_sides=6,
            rings=(
                R(1.00, 0.04, -0.08, 0.32, 0.40),
                R(0.58, -0.02, 0.01, 0.86, 0.84),
                R(0.14, -0.05, 0.09, 1.00, 0.96),
                R(-0.30, 0.00, 0.17, 0.84, 0.80),
                R(-0.68, 0.05, 0.24, 0.50, 0.56),
                R(-1.00, 0.08, 0.32, 0.14, 0.18),
            ),
        ),
        HairMajorLockV14(
            name="hair_nape_right",
            zone="nape",
            physical_side="right",
            material_role="shadow",
            half_extent=(0.150, 0.145, 0.195),
            ring_sides=6,
            rings=(
                R(1.00, 0.05, -0.09, 0.36, 0.38),
                R(0.58, 0.01, 0.00, 0.80, 0.88),
                R(0.14, -0.04, 0.08, 0.96, 1.00),
                R(-0.30, -0.10, 0.16, 0.86, 0.76),
                R(-0.68, -0.17, 0.25, 0.56, 0.50),
                R(-1.00, -0.23, 0.34, 0.18, 0.16),
            ),
        ),
    ),
)


def load_hair_major_lock_profile_v14() -> HairMajorLockProfileV14:
    HUMAN_WARRIOR_M01_HAIR_MAJOR_LOCKS_V14.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_MAJOR_LOCKS_V14
