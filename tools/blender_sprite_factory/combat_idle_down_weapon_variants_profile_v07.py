from __future__ import annotations

from dataclasses import replace

from combat_idle_down_weapon_variants_profile_v06 import (
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V06,
    WeaponStanceProfileV05,
)


ONE_HAND_SIDE_X = 0.62
ONE_HAND_BEHIND_Y = 0.58
ONE_HAND_DOWN_Z = -0.72


HUMAN_WARRIOR_M01_WEAPON_STANCES_V07 = replace(
    HUMAN_WARRIOR_M01_WEAPON_STANCES_V06,
    revision="v07",
    variants=(
        replace(
            HUMAN_WARRIOR_M01_WEAPON_STANCES_V06.variants[0],
            display_name="Одноручная боковая низкая — клинок назад",
            animation_id="combat_idle_onehand_low_v07",
            weapon_id="sword_01_onehand_backside_v07",
        ),
        replace(
            HUMAN_WARRIOR_M01_WEAPON_STANCES_V06.variants[1],
            display_name="Одноручная боковая боевая — клинок назад",
            animation_id="combat_idle_onehand_ready_v07",
            weapon_id="sword_01_onehand_backside_v07",
        ),
        HUMAN_WARRIOR_M01_WEAPON_STANCES_V06.variants[2],
        HUMAN_WARRIOR_M01_WEAPON_STANCES_V06.variants[3],
    ),
)


def load_weapon_stance_profile_v07(character_id: str) -> WeaponStanceProfileV05:
    profile = HUMAN_WARRIOR_M01_WEAPON_STANCES_V07
    if character_id != profile.character_id:
        raise KeyError(f"No weapon stance v07 profile for character_id={character_id}")
    if profile.revision != "v07" or profile.direction != "down":
        raise ValueError("Weapon stance v07 identity drifted")
    expected_ids = (
        "onehand_low",
        "onehand_ready",
        "twohand_center_low",
        "twohand_center_high",
    )
    if tuple(item.variant_id for item in profile.variants) != expected_ids:
        raise ValueError("Weapon stance v07 order drifted")
    if not 0.55 <= ONE_HAND_SIDE_X <= 0.72:
        raise ValueError("One-hand v07 sword must move clearly to the side")
    if not 0.45 <= ONE_HAND_BEHIND_Y <= 0.70:
        raise ValueError("One-hand v07 sword must move behind the hero")
    if not -0.82 <= ONE_HAND_DOWN_Z <= -0.58:
        raise ValueError("One-hand v07 sword must keep its tip downward")

    previous = HUMAN_WARRIOR_M01_WEAPON_STANCES_V06.variants
    for index, item in enumerate(profile.variants):
        if item.pose != previous[index].pose:
            raise ValueError(f"Variant {item.variant_id} changed the approved body pose")
        if index < 2:
            if not item.animation_id.endswith("_v07"):
                raise ValueError(f"Variant {item.variant_id} did not advance to v07")
            if item.weapon_id != "sword_01_onehand_backside_v07":
                raise ValueError(f"Variant {item.variant_id} uses the wrong one-hand sword")
            if item.blade_tip != "down":
                raise ValueError(f"Variant {item.variant_id} must keep the blade tip down")
        else:
            if item != previous[index]:
                raise ValueError(f"Two-hand variant {item.variant_id} must remain exact v06")
    return profile
