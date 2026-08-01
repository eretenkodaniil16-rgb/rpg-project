from __future__ import annotations

from dataclasses import dataclass

from combat_idle_directional_profile_v11 import (
    DIRECTION_ORDER,
    load_combat_idle_directional_profile_v11,
)


@dataclass(frozen=True)
class OneHandDirectionVectorV12:
    direction: str
    side_x: float
    depth_y: float
    vertical_z: float
    minimum_sprite_width: int

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.side_x, self.depth_y, self.vertical_z)


@dataclass(frozen=True)
class CombatIdleDirectionalWeaponProfileV12:
    character_id: str
    revision: str
    directions: tuple[str, ...]
    corrected_onehand_directions: tuple[OneHandDirectionVectorV12, ...]
    preserved_down_source: str
    preserved_twohand_source: str


HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_WEAPON_V12 = (
    CombatIdleDirectionalWeaponProfileV12(
        character_id="human_warrior_m01",
        revision="v12",
        directions=DIRECTION_ORDER,
        corrected_onehand_directions=(
            OneHandDirectionVectorV12(
                direction="left",
                side_x=0.75,
                depth_y=0.15,
                vertical_z=-0.65,
                minimum_sprite_width=44,
            ),
            OneHandDirectionVectorV12(
                direction="right",
                side_x=-0.75,
                depth_y=0.15,
                vertical_z=-0.55,
                minimum_sprite_width=44,
            ),
            OneHandDirectionVectorV12(
                direction="up",
                side_x=0.45,
                depth_y=-0.10,
                vertical_z=-0.80,
                minimum_sprite_width=44,
            ),
        ),
        preserved_down_source="combat_idle_onehand_ready_directional_v11_down",
        preserved_twohand_source="combat_idle_twohand_center_high_directional_v11",
    )
)


def load_combat_idle_directional_weapon_profile_v12(
    character_id: str,
) -> CombatIdleDirectionalWeaponProfileV12:
    profile = HUMAN_WARRIOR_M01_COMBAT_IDLE_DIRECTIONAL_WEAPON_V12
    if character_id != profile.character_id:
        raise KeyError(
            f"No combat idle directional weapon v12 profile for character_id={character_id}"
        )
    if profile.revision != "v12" or profile.directions != DIRECTION_ORDER:
        raise ValueError("Combat idle directional weapon v12 identity drifted")
    directional = load_combat_idle_directional_profile_v11(character_id)
    if tuple(item.direction for item in profile.corrected_onehand_directions) != (
        "left",
        "right",
        "up",
    ):
        raise ValueError("Combat idle directional weapon v12 correction order drifted")
    if tuple(candidate.candidate_id for candidate in directional.candidates) != (
        "onehand_ready",
        "twohand_center_high",
    ):
        raise ValueError("Combat idle directional weapon v12 lost selected sources")
    for item in profile.corrected_onehand_directions:
        if abs(item.side_x) < 0.40:
            raise ValueError(f"One-hand {item.direction} v12 lacks lateral readability")
        if item.vertical_z >= -0.45:
            raise ValueError(f"One-hand {item.direction} v12 blade tip is not clearly down")
        if item.minimum_sprite_width < 40:
            raise ValueError(f"One-hand {item.direction} v12 width budget is too weak")
    return profile
