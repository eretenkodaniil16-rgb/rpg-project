from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


HairZone = Literal["side", "nape"]
PhysicalSide = Literal["left", "right", "center"]


@dataclass(frozen=True)
class HairVolumeTransformV01:
    name: str
    zone: HairZone
    physical_side: PhysicalSide
    scale_multiplier: tuple[float, float, float]
    world_offset: tuple[float, float, float]
    rotation_delta_degrees: tuple[float, float, float]

    def assert_valid(self) -> None:
        if self.zone not in {"side", "nape"}:
            raise ValueError(f"Unsupported hair zone: {self.name}")
        if self.physical_side not in {"left", "right", "center"}:
            raise ValueError(f"Invalid physical side: {self.name}")
        if any(value < 1.0 or value > 1.12 for value in self.scale_multiplier):
            raise ValueError(f"Hair fill multiplier is outside the safe density budget: {self.name}")
        if any(abs(value) > 0.020 for value in self.world_offset):
            raise ValueError(f"Hair fill offset is too large: {self.name}")
        if any(abs(value) > 4.0 for value in self.rotation_delta_degrees):
            raise ValueError(f"Hair fill rotation is too large: {self.name}")


@dataclass(frozen=True)
class TempleFillSpecV01:
    name: str
    physical_side: Literal["left", "right"]
    location: tuple[float, float, float]
    scale: tuple[float, float, float]
    rotation_degrees: tuple[float, float, float]

    def assert_valid(self) -> None:
        if self.physical_side not in {"left", "right"}:
            raise ValueError(f"Temple fill needs a physical side: {self.name}")
        if any(value <= 0.0 for value in self.scale):
            raise ValueError(f"Temple fill scale must be positive: {self.name}")
        if not 0.08 <= self.scale[0] <= 0.14:
            raise ValueError(f"Temple fill width is outside the local coverage budget: {self.name}")
        if not 0.09 <= self.scale[1] <= 0.14:
            raise ValueError(f"Temple fill depth is outside the local coverage budget: {self.name}")
        if not 0.15 <= self.scale[2] <= 0.20:
            raise ValueError(f"Temple fill height is outside the medium-hair budget: {self.name}")
        if not -0.24 <= self.location[1] <= -0.16:
            raise ValueError(f"Temple fill must remain in the front-side transition: {self.name}")


@dataclass(frozen=True)
class ObjectTransformV01:
    name: str
    scale_multiplier: tuple[float, float, float]
    world_offset: tuple[float, float, float]

    def assert_valid(self) -> None:
        if any(value < 1.0 or value > 1.14 for value in self.scale_multiplier):
            raise ValueError(f"Appearance transform is outside the readability budget: {self.name}")
        if any(abs(value) > 0.030 for value in self.world_offset):
            raise ValueError(f"Appearance offset is too large: {self.name}")


@dataclass(frozen=True)
class ClothingDetailSpecV01:
    name: str
    module_id: str
    bone_name: str
    material_slot_id: str
    location: tuple[float, float, float]
    dimensions: tuple[float, float, float]
    bevel: float

    def assert_valid(self) -> None:
        if self.module_id != "torso_armor":
            raise ValueError(f"Readability detail must stay in torso_armor: {self.name}")
        if self.bone_name not in {"chest", "pelvis"}:
            raise ValueError(f"Unsupported clothing detail bone: {self.name}")
        if any(value <= 0.0 for value in self.dimensions):
            raise ValueError(f"Clothing detail dimensions must be positive: {self.name}")
        if not 0.0 <= self.bevel <= 0.04:
            raise ValueError(f"Clothing detail bevel is too large: {self.name}")


@dataclass(frozen=True)
class AppearanceReadabilityProfileV01:
    revision: str
    head_revision: str
    proxy_revision: str
    quantization_additions: tuple[str, ...]
    material_overrides: tuple[tuple[str, str], ...]
    scarf_highlight_hex: str
    hair_transforms: tuple[HairVolumeTransformV01, ...]
    temple_fills: tuple[TempleFillSpecV01, ...]
    object_transforms: tuple[ObjectTransformV01, ...]
    clothing_details: tuple[ClothingDetailSpecV01, ...]

    def material_override_map(self) -> dict[str, str]:
        return dict(self.material_overrides)

    def assert_valid(self) -> None:
        if (self.revision, self.head_revision, self.proxy_revision) != ("v01", "v22", "v25"):
            raise ValueError("Appearance profile must match appearance v01 / head v22 / proxy v25")
        for color in (*self.quantization_additions, self.scarf_highlight_hex):
            if len(color) != 7 or not color.startswith("#"):
                raise ValueError(f"Invalid appearance color: {color}")
        if len(set(self.quantization_additions)) != len(self.quantization_additions):
            raise ValueError("Appearance quantization additions must be unique")

        overrides = self.material_override_map()
        expected_override_slots = {"scarf", "leather_mid", "chainmail", "silver"}
        if set(overrides) != expected_override_slots:
            raise ValueError("Appearance v01 must override the four approved readability slots")
        if not set(overrides.values()).issubset(set(self.quantization_additions)):
            raise ValueError("Every material override must be present in the quantization additions")
        if self.scarf_highlight_hex not in self.quantization_additions:
            raise ValueError("Scarf highlight must be present in the quantization palette")

        expected_hair_targets = {
            "hair_side_mass_left",
            "hair_side_mass_right",
            "hair_nape_left",
            "hair_nape_center",
            "hair_nape_right",
        }
        if {item.name for item in self.hair_transforms} != expected_hair_targets:
            raise ValueError("Appearance v01 must expand all and only retained side/nape masses")
        for item in self.hair_transforms:
            item.assert_valid()

        if {item.name for item in self.temple_fills} != {
            "hair_temple_fill_left",
            "hair_temple_fill_right",
        }:
            raise ValueError("Appearance v01 requires two explicit temple fill modules")
        for item in self.temple_fills:
            item.assert_valid()
        left_fill = next(item for item in self.temple_fills if item.physical_side == "left")
        right_fill = next(item for item in self.temple_fills if item.physical_side == "right")
        if left_fill.scale == right_fill.scale:
            raise ValueError("Temple fills must remain intentionally asymmetric")
        if left_fill.rotation_degrees == tuple(-value for value in right_fill.rotation_degrees):
            raise ValueError("Temple fills must not be mirrored copies")

        expected_objects = {"scarf_wrap", "scarf_front", "armor_chest", "belt"}
        if {item.name for item in self.object_transforms} != expected_objects:
            raise ValueError("Appearance v01 must transform the approved four clothing objects")
        for item in self.object_transforms:
            item.assert_valid()

        expected_details = {"armor_chest_lower_trim", "belt_buckle_front"}
        if {item.name for item in self.clothing_details} != expected_details:
            raise ValueError("Appearance v01 requires the approved two clothing accents")
        for item in self.clothing_details:
            item.assert_valid()


HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01 = AppearanceReadabilityProfileV01(
    revision="v01",
    head_revision="v22",
    proxy_revision="v25",
    quantization_additions=(
        "#741522",
        "#A83242",
        "#6B371C",
        "#5B5852",
        "#9B958F",
    ),
    material_overrides=(
        ("scarf", "#741522"),
        ("leather_mid", "#6B371C"),
        ("chainmail", "#5B5852"),
        ("silver", "#9B958F"),
    ),
    scarf_highlight_hex="#A83242",
    hair_transforms=(
        HairVolumeTransformV01(
            name="hair_side_mass_left",
            zone="side",
            physical_side="left",
            scale_multiplier=(1.085, 1.060, 1.100),
            world_offset=(0.006, -0.016, -0.014),
            rotation_delta_degrees=(1.5, -1.0, -2.0),
        ),
        HairVolumeTransformV01(
            name="hair_side_mass_right",
            zone="side",
            physical_side="right",
            scale_multiplier=(1.095, 1.065, 1.105),
            world_offset=(-0.005, -0.018, -0.012),
            rotation_delta_degrees=(2.0, 1.0, 2.5),
        ),
        HairVolumeTransformV01(
            name="hair_nape_left",
            zone="nape",
            physical_side="left",
            scale_multiplier=(1.060, 1.050, 1.060),
            world_offset=(0.004, 0.010, -0.010),
            rotation_delta_degrees=(1.0, 0.0, -1.0),
        ),
        HairVolumeTransformV01(
            name="hair_nape_center",
            zone="nape",
            physical_side="center",
            scale_multiplier=(1.055, 1.060, 1.055),
            world_offset=(0.000, 0.012, -0.010),
            rotation_delta_degrees=(1.0, 0.0, 0.0),
        ),
        HairVolumeTransformV01(
            name="hair_nape_right",
            zone="nape",
            physical_side="right",
            scale_multiplier=(1.065, 1.055, 1.060),
            world_offset=(-0.003, 0.009, -0.009),
            rotation_delta_degrees=(1.5, 0.0, 1.5),
        ),
    ),
    temple_fills=(
        TempleFillSpecV01(
            name="hair_temple_fill_left",
            physical_side="left",
            location=(0.335, -0.190, 4.430),
            scale=(0.108, 0.112, 0.176),
            rotation_degrees=(10.0, -4.0, -7.0),
        ),
        TempleFillSpecV01(
            name="hair_temple_fill_right",
            physical_side="right",
            location=(-0.345, -0.208, 4.420),
            scale=(0.120, 0.120, 0.188),
            rotation_degrees=(12.0, 3.0, 5.0),
        ),
    ),
    object_transforms=(
        ObjectTransformV01("scarf_wrap", (1.080, 1.060, 1.080), (0.000, -0.015, 0.015)),
        ObjectTransformV01("scarf_front", (1.120, 1.080, 1.080), (0.000, -0.025, 0.015)),
        ObjectTransformV01("armor_chest", (1.040, 1.030, 1.020), (0.000, -0.010, 0.000)),
        ObjectTransformV01("belt", (1.040, 1.040, 1.100), (0.000, -0.010, 0.000)),
    ),
    clothing_details=(
        ClothingDetailSpecV01(
            name="armor_chest_lower_trim",
            module_id="torso_armor",
            bone_name="chest",
            material_slot_id="dark_steel",
            location=(0.000, -0.455, 2.760),
            dimensions=(0.860, 0.070, 0.100),
            bevel=0.020,
        ),
        ClothingDetailSpecV01(
            name="belt_buckle_front",
            module_id="torso_armor",
            bone_name="pelvis",
            material_slot_id="silver",
            location=(0.000, -0.500, 2.280),
            dimensions=(0.240, 0.080, 0.180),
            bevel=0.025,
        ),
    ),
)


def load_appearance_readability_profile_v01(character_id: str) -> AppearanceReadabilityProfileV01:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No appearance readability v01 profile for character_id={character_id}")
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01.assert_valid()
    return HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01
