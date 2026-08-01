from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HairTransitionZone = Literal["side", "nape"]


@dataclass(frozen=True)
class HairSideNapeTransformV21:
    name: str
    zone: HairTransitionZone
    physical_side: str
    scale_multiplier: tuple[float, float, float]
    world_offset: tuple[float, float, float]
    rotation_delta_degrees: tuple[float, float, float]

    def assert_valid(self) -> None:
        if self.zone not in {"side", "nape"}:
            raise ValueError(f"Unsupported side/nape zone: {self.name}")
        if self.physical_side not in {"left", "right", "center"}:
            raise ValueError(f"Invalid physical side: {self.name}")
        if any(value < 1.0 for value in self.scale_multiplier):
            raise ValueError(f"Proxy v24 must not reduce visible hair density: {self.name}")
        if any(value > 1.08 for value in self.scale_multiplier):
            raise ValueError(f"Proxy v24 volume multiplier is too large: {self.name}")
        if abs(self.world_offset[0]) > 0.015:
            raise ValueError(f"Proxy v24 lateral offset exceeds the head budget: {self.name}")
        if not 0.0 <= self.world_offset[1] <= 0.026:
            raise ValueError(f"Proxy v24 depth offset is outside the local transition budget: {self.name}")
        if not -0.020 <= self.world_offset[2] <= 0.0:
            raise ValueError(f"Proxy v24 would create hair outside the medium-length budget: {self.name}")
        if any(abs(value) > 3.0 for value in self.rotation_delta_degrees):
            raise ValueError(f"Proxy v24 rotation delta is too large: {self.name}")


@dataclass(frozen=True)
class HairSideNapeVolumeProfileV21:
    revision: str
    proxy_revision: str
    transforms: tuple[HairSideNapeTransformV21, ...]

    def assert_valid(self) -> None:
        if self.revision != "v21" or self.proxy_revision != "v24":
            raise ValueError("Side/nape volume profile must match head v21 / proxy v24")

        expected_names = {
            "hair_side_mass_left",
            "hair_side_mass_right",
            "hair_nape_left",
            "hair_nape_center",
            "hair_nape_right",
        }
        names = [item.name for item in self.transforms]
        if set(names) != expected_names or len(names) != len(expected_names):
            raise ValueError("Proxy v24 must target exactly five retained side/nape masses")
        if len(names) != len(set(names)):
            raise ValueError("Proxy v24 transform targets must be unique")

        for item in self.transforms:
            item.assert_valid()

        side_items = [item for item in self.transforms if item.zone == "side"]
        nape_items = [item for item in self.transforms if item.zone == "nape"]
        if len(side_items) != 2 or len(nape_items) != 3:
            raise ValueError("Proxy v24 requires two side masses and three nape masses")

        left_side = next(item for item in side_items if item.physical_side == "left")
        right_side = next(item for item in side_items if item.physical_side == "right")
        if left_side.scale_multiplier == right_side.scale_multiplier:
            raise ValueError("Physical side volumes must remain intentionally asymmetrical")
        if left_side.rotation_delta_degrees == tuple(
            -value for value in right_side.rotation_delta_degrees
        ):
            raise ValueError("Proxy v24 side transforms must not be mirrored copies")

        if any(item.scale_multiplier[2] > 1.06 for item in nape_items):
            raise ValueError("Proxy v24 must not turn the nape into long hanging hair")
        if any(item.world_offset[2] < -0.020 for item in nape_items):
            raise ValueError("Proxy v24 nape descent exceeds the medium-length contract")


HUMAN_WARRIOR_M01_HAIR_SIDE_NAPE_VOLUME_V21 = HairSideNapeVolumeProfileV21(
    revision="v21",
    proxy_revision="v24",
    transforms=(
        HairSideNapeTransformV21(
            name="hair_side_mass_left",
            zone="side",
            physical_side="left",
            scale_multiplier=(1.060, 1.045, 1.050),
            world_offset=(0.012, 0.020, -0.012),
            rotation_delta_degrees=(2.0, 0.0, -2.5),
        ),
        HairSideNapeTransformV21(
            name="hair_side_mass_right",
            zone="side",
            physical_side="right",
            scale_multiplier=(1.050, 1.055, 1.040),
            world_offset=(-0.010, 0.023, -0.010),
            rotation_delta_degrees=(1.5, 0.0, 2.0),
        ),
        HairSideNapeTransformV21(
            name="hair_nape_left",
            zone="nape",
            physical_side="left",
            scale_multiplier=(1.040, 1.035, 1.055),
            world_offset=(0.010, 0.018, -0.015),
            rotation_delta_degrees=(2.0, 0.0, -2.0),
        ),
        HairSideNapeTransformV21(
            name="hair_nape_center",
            zone="nape",
            physical_side="center",
            scale_multiplier=(1.030, 1.045, 1.045),
            world_offset=(0.000, 0.024, -0.018),
            rotation_delta_degrees=(2.0, 0.0, 0.0),
        ),
        HairSideNapeTransformV21(
            name="hair_nape_right",
            zone="nape",
            physical_side="right",
            scale_multiplier=(1.045, 1.040, 1.050),
            world_offset=(-0.008, 0.020, -0.012),
            rotation_delta_degrees=(1.5, 0.0, 1.5),
        ),
    ),
)


def load_hair_side_nape_volume_profile_v21() -> HairSideNapeVolumeProfileV21:
    HUMAN_WARRIOR_M01_HAIR_SIDE_NAPE_VOLUME_V21.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_SIDE_NAPE_VOLUME_V21
