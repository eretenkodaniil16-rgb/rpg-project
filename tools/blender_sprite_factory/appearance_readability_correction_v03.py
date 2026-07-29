from __future__ import annotations

from dataclasses import replace

from appearance_readability_correction_v02 import (
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02,
)
from appearance_readability_profile_v01 import AppearanceReadabilityProfileV01


CORRECTION_REVISION = "v03"


def _strengthen_hair_transform(item: object) -> object:
    if item.name == "hair_side_mass_left":
        return replace(
            item,
            scale_multiplier=(1.150, 1.125, 1.145),
            world_offset=(0.010, -0.020, -0.020),
            rotation_delta_degrees=(2.5, -1.5, -3.0),
        )
    if item.name == "hair_side_mass_right":
        return replace(
            item,
            scale_multiplier=(1.155, 1.130, 1.150),
            world_offset=(-0.009, -0.020, -0.020),
            rotation_delta_degrees=(3.0, 1.0, 3.5),
        )
    if item.name == "hair_nape_center":
        return replace(item, scale_multiplier=(1.080, 1.085, 1.075))
    return item


def _strengthen_temple_fill(item: object) -> object:
    if item.physical_side == "left":
        return replace(
            item,
            location=(0.305, -0.238, 4.405),
            scale=(0.152, 0.154, 0.218),
            rotation_degrees=(12.0, -5.0, -9.0),
        )
    return replace(
        item,
        location=(-0.315, -0.246, 4.395),
        scale=(0.160, 0.158, 0.224),
        rotation_degrees=(14.0, 3.0, 7.0),
    )


def _restrain_clothing_transform(item: object) -> object:
    if item.name == "scarf_wrap":
        return replace(item, scale_multiplier=(1.080, 1.070, 1.080))
    if item.name == "scarf_front":
        return replace(item, scale_multiplier=(1.120, 1.090, 1.090))
    return replace(item, scale_multiplier=(1.000, 1.000, 1.000), world_offset=(0.0, 0.0, 0.0))


HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V03 = replace(
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02,
    quantization_additions=(
        "#8A1F2D",
        "#C33A4C",
    ),
    material_overrides=(("scarf", "#8A1F2D"),),
    scarf_highlight_hex="#C33A4C",
    hair_transforms=tuple(
        _strengthen_hair_transform(item)
        for item in HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02.hair_transforms
    ),
    temple_fills=tuple(
        _strengthen_temple_fill(item)
        for item in HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02.temple_fills
    ),
    object_transforms=tuple(
        _restrain_clothing_transform(item)
        for item in HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02.object_transforms
    ),
)


def load_appearance_readability_corrected_v03(
    character_id: str,
) -> AppearanceReadabilityProfileV01:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No appearance readability correction v03 for character_id={character_id}")
    profile = HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V03
    if profile.material_override_map() != {"scarf": "#8A1F2D"}:
        raise ValueError("Appearance correction v03 must restore original non-scarf materials")
    if profile.scarf_highlight_hex not in profile.quantization_additions:
        raise ValueError("Appearance correction v03 requires a quantized scarf highlight")
    if len(profile.temple_fills) != 2 or len(profile.hair_transforms) != 5:
        raise ValueError("Appearance correction v03 must retain the established hair module contract")
    for item in profile.hair_transforms:
        if any(value < 1.0 for value in item.scale_multiplier):
            raise ValueError(f"Appearance correction v03 reduced hair volume: {item.name}")
    return profile
