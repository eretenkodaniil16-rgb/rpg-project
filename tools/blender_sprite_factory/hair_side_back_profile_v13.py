from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HairZone = Literal["side", "back", "nape"]


@dataclass(frozen=True)
class HairObjectTransformV13:
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
            raise ValueError(f"Hair scale multiplier must stay positive: {self.name}")
        if any(value > 1.30 for value in self.scale_multiplier):
            raise ValueError(f"Hair scale multiplier is too large: {self.name}")
        if abs(self.world_offset[0]) > 0.03:
            raise ValueError(f"Hair lateral offset exceeds the locked head budget: {self.name}")
        if not -0.06 <= self.world_offset[2] <= 0.01:
            raise ValueError(f"Hair vertical offset exceeds the medium-length budget: {self.name}")
        if any(abs(value) > 8.0 for value in self.rotation_delta_degrees):
            raise ValueError(f"Hair rotation delta is too large: {self.name}")


@dataclass(frozen=True)
class HairSideBackProfileV13:
    revision: str
    proxy_revision: str
    transforms: tuple[HairObjectTransformV13, ...]

    def assert_valid(self) -> None:
        if self.revision != "v13" or self.proxy_revision != "v16":
            raise ValueError("Side/back profile must match head v13 / proxy v16")

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
            raise ValueError("Side/back pass must target exactly eight existing hair masses")
        if len(names) != len(set(names)):
            raise ValueError("Side/back transform names must be unique")
        for item in self.transforms:
            item.assert_valid()

        left_side = next(item for item in self.transforms if item.name == "hair_side_mass_left")
        right_side = next(item for item in self.transforms if item.name == "hair_side_mass_right")
        if left_side.scale_multiplier == right_side.scale_multiplier:
            raise ValueError("Physical side masses must remain asymmetrical")
        if left_side.rotation_delta_degrees == tuple(
            -value for value in right_side.rotation_delta_degrees
        ):
            raise ValueError("Side transforms must not be mirrored copies")

        nape_items = [item for item in self.transforms if item.zone == "nape"]
        if len(nape_items) != 3:
            raise ValueError("Rear silhouette needs three existing nape masses")
        if any(item.world_offset[2] >= 0.0 for item in nape_items):
            raise ValueError("Nape masses must descend to form a hanging lower edge")


HUMAN_WARRIOR_M01_HAIR_SIDE_BACK_V13 = HairSideBackProfileV13(
    revision="v13",
    proxy_revision="v16",
    transforms=(
        HairObjectTransformV13(
            name="hair_back_shell",
            zone="back",
            physical_side="center",
            scale_multiplier=(0.96, 1.03, 1.02),
            world_offset=(0.000, 0.015, -0.015),
            rotation_delta_degrees=(3.0, 0.0, 0.0),
        ),
        HairObjectTransformV13(
            name="hair_back_sweep_left",
            zone="back",
            physical_side="left",
            scale_multiplier=(1.04, 1.02, 1.18),
            world_offset=(0.015, 0.020, -0.030),
            rotation_delta_degrees=(6.0, 0.0, -4.0),
        ),
        HairObjectTransformV13(
            name="hair_back_sweep_right",
            zone="back",
            physical_side="right",
            scale_multiplier=(1.02, 1.04, 1.14),
            world_offset=(-0.012, 0.018, -0.020),
            rotation_delta_degrees=(5.0, 0.0, 3.0),
        ),
        HairObjectTransformV13(
            name="hair_side_mass_left",
            zone="side",
            physical_side="left",
            scale_multiplier=(1.05, 1.00, 1.22),
            world_offset=(0.015, 0.015, -0.035),
            rotation_delta_degrees=(4.0, 0.0, -4.0),
        ),
        HairObjectTransformV13(
            name="hair_side_mass_right",
            zone="side",
            physical_side="right",
            scale_multiplier=(1.05, 1.02, 1.18),
            world_offset=(-0.010, 0.025, -0.025),
            rotation_delta_degrees=(3.0, 0.0, 3.0),
        ),
        HairObjectTransformV13(
            name="hair_nape_left",
            zone="nape",
            physical_side="left",
            scale_multiplier=(1.10, 1.00, 1.22),
            world_offset=(0.015, 0.010, -0.030),
            rotation_delta_degrees=(4.0, 0.0, -6.0),
        ),
        HairObjectTransformV13(
            name="hair_nape_center",
            zone="nape",
            physical_side="center",
            scale_multiplier=(1.08, 1.02, 1.18),
            world_offset=(0.000, 0.018, -0.040),
            rotation_delta_degrees=(5.0, 0.0, 0.0),
        ),
        HairObjectTransformV13(
            name="hair_nape_right",
            zone="nape",
            physical_side="right",
            scale_multiplier=(1.08, 1.03, 1.15),
            world_offset=(-0.010, 0.015, -0.020),
            rotation_delta_degrees=(3.0, 0.0, 5.0),
        ),
    ),
)


def load_hair_side_back_profile_v13() -> HairSideBackProfileV13:
    HUMAN_WARRIOR_M01_HAIR_SIDE_BACK_V13.assert_valid()
    return HUMAN_WARRIOR_M01_HAIR_SIDE_BACK_V13
