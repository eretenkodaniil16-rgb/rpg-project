from __future__ import annotations

from dataclasses import dataclass

from combat_idle_directional_weapon_profile_v12 import (
    load_combat_idle_directional_weapon_profile_v12,
)


@dataclass(frozen=True)
class OneHandSideCorrectionV13:
    direction: str
    blade_vector: tuple[float, float, float]
    anchor_offset: tuple[float, float, float]
    minimum_sprite_width: int
    maximum_horizontal_to_vertical_ratio: float


@dataclass(frozen=True)
class CombatIdleDirectionalWeaponProfileV13:
    character_id: str
    revision: str
    corrected_sides: tuple[OneHandSideCorrectionV13, ...]
    locked_directions: tuple[str, ...]
    locked_twohand_revision: str


HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_WEAPON_V13 = (
    CombatIdleDirectionalWeaponProfileV13(
        character_id="human_warrior_m01",
        revision="v13",
        corrected_sides=(
            OneHandSideCorrectionV13(
                direction="left",
                blade_vector=(-0.72, 0.12, -0.70),
                anchor_offset=(-0.30, -0.02, -0.08),
                minimum_sprite_width=54,
                maximum_horizontal_to_vertical_ratio=1.15,
            ),
            OneHandSideCorrectionV13(
                direction="right",
                blade_vector=(-0.52, 0.18, -0.86),
                anchor_offset=(-0.08, 0.04, -0.04),
                minimum_sprite_width=45,
                maximum_horizontal_to_vertical_ratio=0.80,
            ),
        ),
        locked_directions=("down", "up"),
        locked_twohand_revision="v12_exact_from_v11",
    )
)


def load_combat_idle_directional_weapon_profile_v13(
    character_id: str,
) -> CombatIdleDirectionalWeaponProfileV13:
    profile = HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_WEAPON_V13
    if character_id != profile.character_id:
        raise KeyError(
            f"No combat idle directional weapon v13 profile for character_id={character_id}"
        )
    previous = load_combat_idle_directional_weapon_profile_v12(character_id)
    if profile.revision != "v13":
        raise ValueError("Combat idle directional weapon v13 revision drifted")
    if tuple(item.direction for item in profile.corrected_sides) != ("left", "right"):
        raise ValueError("Combat idle directional weapon v13 side order drifted")
    if profile.locked_directions != ("down", "up"):
        raise ValueError("Combat idle directional weapon v13 locked directions drifted")
    if tuple(item.direction for item in previous.corrected_onehand_directions) != (
        "left",
        "right",
        "up",
    ):
        raise ValueError("Combat idle directional weapon v13 lost v12 source history")
    for item in profile.corrected_sides:
        horizontal = abs(item.blade_vector[0])
        vertical = abs(item.blade_vector[2])
        if vertical <= 0.0 or horizontal / vertical > item.maximum_horizontal_to_vertical_ratio:
            raise ValueError(
                f"One-hand {item.direction} v13 blade is too horizontal"
            )
        if item.blade_vector[2] >= -0.65:
            raise ValueError(
                f"One-hand {item.direction} v13 blade tip must remain clearly down"
            )
        if item.minimum_sprite_width < 45:
            raise ValueError(
                f"One-hand {item.direction} v13 readability budget is too small"
            )
        if max(abs(value) for value in item.anchor_offset) > 0.35:
            raise ValueError(
                f"One-hand {item.direction} v13 anchor offset exceeds safe budget"
            )
    return profile
