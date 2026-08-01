from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HairZone = Literal["side", "back", "nape"]


@dataclass(frozen=True)
class HairLockExposureV15:
    name: str
    zone: HairZone
    physical_side: str
    scale_multiplier: tuple[float, float, float]
    world_offset: tuple[float, float, float]
    rotation_delta_degrees: tuple[float, float, float]

    def assert_valid(self) -> None:
        if self.physical_side not in {"left", "right", "center"}:
            raise ValueError(f"Invalid physical side for {self.name}")
        if any(value <= 0.0 for value in self.scale_multiplier):
            raise ValueError(f"Exposure scale must stay positive: {self.name}")
        if any(value > 1.16 for value in self.scale_multiplier):
            raise ValueError(f"Exposure scale is too large: {self.name}")
        if abs(self.world_offset[0]) > 0.025:
            raise ValueError(f"Exposure lateral offset exceeds the head budget: {self.name}")
        if not 0.0 <= self.world_offset[1] <= 0.045:
            raise ValueError(f"Exposure rear offset is invalid: {self.name}")
        if not -0.055 <= self.world_offset[2] <= 0.020:
            raise ValueError(f"Exposure vertical offset is invalid: {self.name}")
        if any(abs(value) > 3.0 for value in self.rotation_delta_degrees):
            raise ValueError(f"Exposure rotation delta is too large: {self.name}")


@dataclass(frozen=True)
class HairLockExposureProfileV15:
    revision: str
    proxy_revision: str
    transforms: tuple[HairLockExposureV15, ...]

    def assert_valid(self) -> None:
        if self.revision != "v15" or self.proxy_revision != "v18":
            raise ValueError("Lock exposure profile must match head v15 / proxy v18")
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
        names = [item.name for item in self.transforms]
        if set(names) != expected_names or len(names) != len(expected_names):
            raise ValueError("Exposure pass must target exactly eight profile locks")
        if len(names) != len(set(names)):
            raise ValueError("Exposure transform names must be unique")
        for item in self.transforms:
            item.assert_valid()

        shell = next(item for item in self.transforms if item.name == "hair_back_shell")
        if max(shell.scale_multiplier) >= 1.0:
            raise ValueError("Central back shell must shrink to reveal the lock tips")
        if shell.world_offset[2] <= 0.0:
            raise ValueError("Central back shell must move slightly upward")

        hanging = [item for item in self.transforms if item.name != "hair_back_shell"]
        if any(item.world_offset[2] >= 0.0 for item in hanging):
            raise ValueError("Exposed side/back/nape locks must descend")
        if any(item.world_offset[1] <= 0.0 for item in hanging):
            raise ValueError("Exposed side/back/nape locks must move behind the crown")

        left = next(item for item in self.transforms if item.name == "hair_side_mass_left")
        right = next(item for item in self.transforms if item.name == "hair_side_mass_right")
        if left.world_offset == tuple(-value for value in right.world_offset):
            raise ValueError("Physical side exposure offsets must not be mirrored")
        if left.rotation_delta_degrees == tuple(
            -value for value in right.rotation_delta_degrees
        ):
            raise ValueError("Physical side exposure rotations must not be mirrored")


HUMAN_WARRIOR_M01_HAIR_LOCK_EXPOSURE_V15 = HairLockExposureProfileV15(
    revision="v15",
    proxy_revision="v18",
    transforms=(
        HairLockExposureV15(
            name="hair_back_shell",
            zone="back",
            physical_side="center",
            scale_multiplier=(0.90, 0.90, 0.88),
            world_offset=(0.000, 0.010, 0.015),
            rotation_delta_degrees=(0.0, 0.0, 0.0),
        ),
        HairLockExposureV15(
            name="hair_back_sweep_left",
            zone="back",
            physical_side="left",
            scale_multiplier=(0.96, 1.00, 1.10),
            world_offset=(0.020, 0.030, -0.035),
            rotation_delta_degrees=(3.0, 0.0, -2.0),
        ),
        HairLockExposureV15(
            name="hair_back_sweep_right",
            zone="back",
            physical_side="right",
            scale_multiplier=(0.98, 1.02, 1.08),
            world_offset=(-0.016, 0.035, -0.030),
            rotation_delta_degrees=(2.0, 0.0, 2.0),
        ),
        HairLockExposureV15(
            name="hair_side_mass_left",
            zone="side",
            physical_side="left",
            scale_multiplier=(0.98, 1.00, 1.08),
            world_offset=(0.018, 0.010, -0.025),
            rotation_delta_degrees=(2.0, 0.0, -2.0),
        ),
        HairLockExposureV15(
            name="hair_side_mass_right",
            zone="side",
            physical_side="right",
            scale_multiplier=(1.00, 1.02, 1.06),
            world_offset=(-0.014, 0.016, -0.022),
            rotation_delta_degrees=(1.0, 0.0, 2.0),
        ),
        HairLockExposureV15(
            name="hair_nape_left",
            zone="nape",
            physical_side="left",
            scale_multiplier=(0.96, 1.00, 1.12),
            world_offset=(0.018, 0.035, -0.045),
            rotation_delta_degrees=(2.0, 0.0, -2.0),
        ),
        HairLockExposureV15(
            name="hair_nape_center",
            zone="nape",
            physical_side="center",
            scale_multiplier=(0.92, 1.00, 1.15),
            world_offset=(0.000, 0.040, -0.050),
            rotation_delta_degrees=(2.0, 0.0, 0.0),
        ),
        HairLockExposureV15(
            name="hair_nape_right",
            zone="nape",
            physical_side="right",
            scale_multiplier=(0.98, 1.02, 1.10),
            world_offset=(-0.014, 0.032, -0.040),
            rotation_delta_degrees=(1.0, 0.0, 2.0),
        ),
    ),
)


def load_hair_lock_exposure_profile_v15() -> HairLockExposureProfileV15:
    HUMAN_WARRIOR_M01_HAIR_LOCK_EXPOSURE_V15.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_LOCK_EXPOSURE_V15
