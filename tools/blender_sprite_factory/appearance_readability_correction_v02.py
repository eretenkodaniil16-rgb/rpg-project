from __future__ import annotations

from dataclasses import replace

from appearance_readability_profile_v01 import (
    AppearanceReadabilityProfileV01,
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01,
)


CORRECTION_REVISION = "v02"


def _correct_hair_transform(item: object) -> object:
    if item.name == "hair_side_mass_left":
        return replace(
            item,
            scale_multiplier=(1.120, 1.100, 1.120),
            world_offset=(0.008, -0.020, -0.018),
            rotation_delta_degrees=(2.0, -1.5, -2.5),
        )
    if item.name == "hair_side_mass_right":
        return replace(
            item,
            scale_multiplier=(1.120, 1.110, 1.120),
            world_offset=(-0.007, -0.020, -0.018),
            rotation_delta_degrees=(2.5, 1.0, 3.0),
        )
    return item


def _correct_temple_fill(item: object) -> object:
    if item.physical_side == "left":
        return replace(
            item,
            location=(0.320, -0.220, 4.405),
            scale=(0.132, 0.136, 0.196),
            rotation_degrees=(11.0, -5.0, -8.0),
        )
    return replace(
        item,
        location=(-0.330, -0.232, 4.395),
        scale=(0.140, 0.140, 0.200),
        rotation_degrees=(13.0, 3.0, 6.0),
    )


def _correct_object_transform(item: object) -> object:
    if item.name == "scarf_wrap":
        return replace(item, scale_multiplier=(1.100, 1.080, 1.100))
    if item.name == "scarf_front":
        return replace(item, scale_multiplier=(1.140, 1.100, 1.100))
    return item


HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02 = replace(
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01,
    quantization_additions=(
        "#8A1F2D",
        "#C33A4C",
        "#6B371C",
        "#5B5852",
        "#9B958F",
    ),
    material_overrides=(
        ("scarf", "#8A1F2D"),
        ("leather_mid", "#6B371C"),
        ("chainmail", "#5B5852"),
        ("silver", "#9B958F"),
    ),
    scarf_highlight_hex="#C33A4C",
    hair_transforms=tuple(
        _correct_hair_transform(item)
        for item in HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01.hair_transforms
    ),
    temple_fills=tuple(
        _correct_temple_fill(item)
        for item in HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01.temple_fills
    ),
    object_transforms=tuple(
        _correct_object_transform(item)
        for item in HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_V01.object_transforms
    ),
)


def load_appearance_readability_corrected_v02(
    character_id: str,
) -> AppearanceReadabilityProfileV01:
    if character_id != "human_warrior_m01":
        raise KeyError(f"No appearance readability correction v02 for character_id={character_id}")
    HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02.assert_valid()
    return HUMAN_WARRIOR_M01_APPEARANCE_READABILITY_CORRECTED_V02
